---
description: 
alwaysApply: true
---

# Z-Image Project Guide

## Project Overview

Z-Image (造相) is an efficient image generation system built around a 6B-parameter Single-Stream Diffusion Transformer (S3-DiT) developed by Tongyi-MAI (Alibaba). It provides text-to-image, image-to-image, and inpainting capabilities.

## Architecture

```
Browser (Next.js :3000) → FastAPI (:8000) → sd-server C++ (:7860) → Z-Image DiT model
```

- **C++ Backend**: `stable-diffusion.cpp/build/bin/sd-server` — GGUF-quantized inference engine, A1111-compatible API
- **Python API**: `server/` — FastAPI service that manages and proxies to sd-server
- **Web Frontend**: `web/` — Next.js 15 + TypeScript + Tailwind CSS

## Key Files

### Backend (server/)
- `server/app.py` — FastAPI app, all REST endpoints, uses `_proxy_to_sd()` to forward requests
- `server/config.py` — All settings via environment variables (ports, model paths, defaults)
- `server/sd_backend.py` — Spawns/manages sd-server subprocess, health polling
- `server/models.py` — Pydantic request/response schemas

### Frontend (web/)
- `web/app/page.tsx` — Root page, orchestrates generation + gallery state
- `web/components/GeneratorForm.tsx` — Main form with tab-based mode switcher + DropZone uploads
- `web/lib/api.ts` — API client (txt2img=JSON, img2img/inpaint=FormData)
- `web/lib/types.ts` — TypeScript interfaces, GenerationMode, ASPECT_RATIOS
- `web/components/Gallery.tsx` — Image gallery grid
- `web/components/Lightbox.tsx` — Full-screen image viewer
- `web/components/ProgressWater.tsx` — Animated progress indicator
- `web/next.config.ts` — Rewrites `/api/v1/*` to FastAPI at localhost:8000

### Model / Inference
- `src/` — PyTorch native inference path (alternative to C++ backend)
- `src/zimage/pipeline.py` — PyTorch generation pipeline
- `src/config/model.py` — Architecture hyperparameters (dim=3840, 30 layers, 30 heads)
- `stable-diffusion.cpp/` — C++ inference engine (git submodule)

## Models

| Component | File | Format |
|---|---|---|
| Diffusion (DiT) | `models/z_image_turbo-Q6_K.gguf` | GGUF 6-bit |
| VAE | `models/vae/split_files/vae/ae.safetensors` | safetensors |
| Text Encoder | `models/text_encoder/Qwen3-4B-Instruct-2507-Q4_K_M.gguf` | GGUF 4-bit |

Text encoder is Qwen3-4B-Instruct (LLM, not CLIP) — enables bilingual Chinese/English.

## sd-server API

The C++ sd-server exposes A1111-compatible endpoints:
- `POST /sdapi/v1/txt2img` — JSON body with prompt, dimensions, steps, etc.
- `POST /sdapi/v1/img2img` — JSON with `init_images` (base64 array) + `denoising_strength`
- `POST /v1/images/edits` — Multipart with `image[]` files (Kontext-style reference images become `ref_images`)
- Supports `extra_images` field in txt2img JSON — passed as reference images to the model

## Development Commands

**IMPORTANT**: The project uses a Python virtual environment at `.venv/`. Always use `.venv/bin/python` and `.venv/bin/pip` — do NOT use system `python3` or `pip3`.

```bash
# Build sd-server (requires CUDA toolkit)
cd stable-diffusion.cpp && mkdir build && cd build
cmake .. -DSD_CUDA=ON && make -j$(nproc)

# Install Python dependencies (MUST use .venv)
.venv/bin/pip install -r requirements.txt

# Start backend (MUST use .venv)
.venv/bin/python -m uvicorn server.app:app --host 0.0.0.0 --port 8000

# Start frontend
cd web && npm install && npm run dev

# Docker
docker compose up --build

# Direct CLI generation
./generate.sh -p "your prompt"
./generate.sh -p "style description" -i input.png -s 0.6  # img2img
```

## Conventions

- API endpoints follow `/api/v1/<feature>` pattern
- txt2img uses JSON body; img2img/inpaint use multipart FormData
- FastAPI proxies all generation to sd-server via `_proxy_to_sd(endpoint, payload)`
- Frontend uses tab-based mode switching in GeneratorForm
- Image dimensions must be multiples of 64, range 64–2048
- Default generation: 1024x1024, 8 steps, cfg_scale=1.0, euler sampler
- All generated images are base64-encoded PNGs in responses

## Environment Variables

Key config (see `server/config.py`):
- `SD_SERVER_PORT` (7860) — internal C++ server port
- `FASTAPI_PORT` (8000) — public API port
- `DEFAULT_WIDTH/HEIGHT` (1024) — default image dimensions
- `DEFAULT_STEPS` (8) — default denoising steps
- `DIFFUSION_MODEL`, `VAE_MODEL`, `LLM_MODEL` — model file paths
