"""FastAPI application for Z-Image."""

from __future__ import annotations

import base64
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from . import config, sd_backend
from .models import (
    ErrorResponse,
    GenerationResponse,
    HealthResponse,
    Img2ImgRequest,
    InpaintRequest,
    LoraInfo,
    SamplerInfo,
    SchedulerInfo,
    Txt2ImgRequest,
)

logger = logging.getLogger("z-image.api")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start sd-server on startup, stop on shutdown."""
    await sd_backend.start()
    yield
    sd_backend.stop()


app = FastAPI(
    title="Z-Image API",
    description="Image generation API powered by Z-Image-Turbo via stable-diffusion.cpp",
    version="1.0.0",
    lifespan=lifespan,
)


async def _proxy_to_sd(
    endpoint: str, payload: dict
) -> GenerationResponse:
    """Forward a generation request to sd-server and return the result."""
    client = sd_backend.get_client()
    try:
        resp = await client.post(endpoint, json=payload)
    except httpx.ConnectError:
        raise HTTPException(503, "sd-server is not reachable")

    if resp.status_code != 200:
        detail = resp.text
        try:
            detail = resp.json().get("error", detail)
        except Exception:
            pass
        raise HTTPException(resp.status_code, detail)

    data = resp.json()
    return GenerationResponse(
        images=data.get("images", []),
        parameters=data.get("parameters", {}),
        info=data.get("info", ""),
    )


# ---------------------------------------------------------------------------
# Generation endpoints
# ---------------------------------------------------------------------------


@app.post(
    "/api/v1/txt2img",
    response_model=GenerationResponse,
    responses={400: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
    summary="Text-to-image generation",
)
async def txt2img(req: Txt2ImgRequest):
    payload = {
        "prompt": req.prompt,
        "negative_prompt": req.negative_prompt,
        "width": req.width,
        "height": req.height,
        "steps": req.steps,
        "cfg_scale": req.cfg_scale,
        "seed": req.seed,
        "batch_size": req.batch_size,
        "sampler_name": req.sampler_name,
        "scheduler": req.scheduler,
        "clip_skip": req.clip_skip,
    }
    return await _proxy_to_sd("/sdapi/v1/txt2img", payload)


@app.post(
    "/api/v1/img2img",
    response_model=GenerationResponse,
    responses={400: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
    summary="Image-to-image generation",
)
async def img2img(
    prompt: str = Form(...),
    negative_prompt: str = Form(""),
    width: int = Form(config.DEFAULT_WIDTH),
    height: int = Form(config.DEFAULT_HEIGHT),
    steps: int = Form(config.DEFAULT_STEPS),
    cfg_scale: float = Form(config.DEFAULT_CFG_SCALE),
    seed: int = Form(-1),
    batch_size: int = Form(1),
    sampler_name: str = Form(""),
    scheduler: str = Form(""),
    clip_skip: int = Form(-1),
    strength: float = Form(0.75),
    image: UploadFile = File(..., description="Input image"),
):
    image_bytes = await image.read()
    image_b64 = base64.b64encode(image_bytes).decode()

    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "width": width,
        "height": height,
        "steps": steps,
        "cfg_scale": cfg_scale,
        "seed": seed,
        "batch_size": batch_size,
        "sampler_name": sampler_name,
        "scheduler": scheduler,
        "clip_skip": clip_skip,
        "init_images": [image_b64],
        "denoising_strength": strength,
    }
    return await _proxy_to_sd("/sdapi/v1/img2img", payload)


@app.post(
    "/api/v1/inpaint",
    response_model=GenerationResponse,
    responses={400: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
    summary="Inpainting generation",
)
async def inpaint(
    prompt: str = Form(...),
    negative_prompt: str = Form(""),
    width: int = Form(config.DEFAULT_WIDTH),
    height: int = Form(config.DEFAULT_HEIGHT),
    steps: int = Form(config.DEFAULT_STEPS),
    cfg_scale: float = Form(config.DEFAULT_CFG_SCALE),
    seed: int = Form(-1),
    batch_size: int = Form(1),
    sampler_name: str = Form(""),
    scheduler: str = Form(""),
    clip_skip: int = Form(-1),
    strength: float = Form(0.75),
    inpainting_mask_invert: bool = Form(False),
    image: UploadFile = File(..., description="Input image"),
    mask: UploadFile = File(..., description="Mask image"),
):
    image_bytes = await image.read()
    mask_bytes = await mask.read()
    image_b64 = base64.b64encode(image_bytes).decode()
    mask_b64 = base64.b64encode(mask_bytes).decode()

    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "width": width,
        "height": height,
        "steps": steps,
        "cfg_scale": cfg_scale,
        "seed": seed,
        "batch_size": batch_size,
        "sampler_name": sampler_name,
        "scheduler": scheduler,
        "clip_skip": clip_skip,
        "init_images": [image_b64],
        "mask": mask_b64,
        "denoising_strength": strength,
        "inpainting_mask_invert": int(inpainting_mask_invert),
    }
    return await _proxy_to_sd("/sdapi/v1/img2img", payload)


# ---------------------------------------------------------------------------
# Info endpoints
# ---------------------------------------------------------------------------


@app.get(
    "/api/v1/samplers",
    response_model=list[SamplerInfo],
    summary="List available samplers",
)
async def list_samplers():
    client = sd_backend.get_client()
    try:
        resp = await client.get("/sdapi/v1/samplers")
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError:
        raise HTTPException(503, "sd-server is not reachable")


@app.get(
    "/api/v1/schedulers",
    response_model=list[SchedulerInfo],
    summary="List available schedulers",
)
async def list_schedulers():
    client = sd_backend.get_client()
    try:
        resp = await client.get("/sdapi/v1/schedulers")
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError:
        raise HTTPException(503, "sd-server is not reachable")


@app.get(
    "/api/v1/loras",
    response_model=list[LoraInfo],
    summary="List available LoRAs",
)
async def list_loras():
    client = sd_backend.get_client()
    try:
        resp = await client.get("/sdapi/v1/loras")
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError:
        raise HTTPException(503, "sd-server is not reachable")


@app.get(
    "/api/v1/health",
    response_model=HealthResponse,
    summary="Health check",
)
async def health():
    sd_ok = sd_backend.is_running()
    return HealthResponse(
        status="ok" if sd_ok else "degraded",
        sd_server="running" if sd_ok else "stopped",
        model=config.DIFFUSION_MODEL.name,
        default_width=config.DEFAULT_WIDTH,
        default_height=config.DEFAULT_HEIGHT,
        default_steps=config.DEFAULT_STEPS,
        default_cfg_scale=config.DEFAULT_CFG_SCALE,
    )
