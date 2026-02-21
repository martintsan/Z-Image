"""Pydantic request/response schemas for the Z-Image API."""

from __future__ import annotations

from pydantic import BaseModel, Field

from . import config


class Txt2ImgRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Text prompt for generation")
    negative_prompt: str = Field("", description="Negative prompt")
    width: int = Field(config.DEFAULT_WIDTH, ge=64, le=config.MAX_WIDTH, multiple_of=64)
    height: int = Field(
        config.DEFAULT_HEIGHT, ge=64, le=config.MAX_HEIGHT, multiple_of=64
    )
    steps: int = Field(config.DEFAULT_STEPS, ge=1, le=config.MAX_STEPS)
    cfg_scale: float = Field(config.DEFAULT_CFG_SCALE, ge=0.0, le=30.0)
    seed: int = Field(-1, description="RNG seed (-1 for random)")
    batch_size: int = Field(1, ge=1, le=config.MAX_BATCH_SIZE)
    sampler_name: str = Field("", description="Sampler name (empty = server default)")
    scheduler: str = Field("", description="Scheduler name (empty = server default)")
    clip_skip: int = Field(-1, description="CLIP skip layers (-1 = default)")


class Img2ImgRequest(Txt2ImgRequest):
    strength: float = Field(
        0.75, ge=0.0, le=1.0, description="Denoising strength"
    )


class InpaintRequest(Img2ImgRequest):
    inpainting_mask_invert: bool = Field(
        False, description="Invert the mask before applying"
    )


class GenerationResponse(BaseModel):
    images: list[str] = Field(
        ..., description="List of base64-encoded PNG images"
    )
    parameters: dict = Field(
        default_factory=dict, description="Parameters used for generation"
    )
    info: str = Field("", description="Additional info")


class SamplerInfo(BaseModel):
    name: str
    aliases: list[str] = []
    options: dict = {}


class SchedulerInfo(BaseModel):
    name: str
    label: str


class LoraInfo(BaseModel):
    name: str
    path: str


class HealthResponse(BaseModel):
    status: str
    sd_server: str
    model: str
    default_width: int
    default_height: int
    default_steps: int
    default_cfg_scale: float


class ErrorResponse(BaseModel):
    error: str
    message: str = ""
