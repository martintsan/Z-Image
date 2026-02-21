"""Configuration for the Z-Image FastAPI service."""

import os
from pathlib import Path

# Project root (parent of server/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# sd-server binary
SD_SERVER_BIN = Path(
    os.environ.get(
        "SD_SERVER_BIN",
        PROJECT_ROOT / "stable-diffusion.cpp" / "build" / "bin" / "sd-server",
    )
)

# Model paths
MODELS_DIR = Path(os.environ.get("MODELS_DIR", PROJECT_ROOT / "models"))
DIFFUSION_MODEL = MODELS_DIR / os.environ.get(
    "DIFFUSION_MODEL", "z_image_turbo-Q6_K.gguf"
)
VAE_MODEL = MODELS_DIR / os.environ.get(
    "VAE_MODEL", "vae/split_files/vae/ae.safetensors"
)
LLM_MODEL = MODELS_DIR / os.environ.get(
    "LLM_MODEL", "text_encoder/Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
)
LORA_DIR = MODELS_DIR / os.environ.get("LORA_DIR", "loras")

# sd-server settings
SD_SERVER_HOST = os.environ.get("SD_SERVER_HOST", "127.0.0.1")
SD_SERVER_PORT = int(os.environ.get("SD_SERVER_PORT", "7860"))

# FastAPI settings
FASTAPI_HOST = os.environ.get("FASTAPI_HOST", "0.0.0.0")
FASTAPI_PORT = int(os.environ.get("FASTAPI_PORT", "8000"))

# Generation defaults (matching generate.sh)
DEFAULT_WIDTH = int(os.environ.get("DEFAULT_WIDTH", "1024"))
DEFAULT_HEIGHT = int(os.environ.get("DEFAULT_HEIGHT", "1024"))
DEFAULT_STEPS = int(os.environ.get("DEFAULT_STEPS", "8"))
DEFAULT_CFG_SCALE = float(os.environ.get("DEFAULT_CFG_SCALE", "1.0"))

# Limits
MAX_WIDTH = 2048
MAX_HEIGHT = 2048
MAX_STEPS = 150
MAX_BATCH_SIZE = 8

# sd-server startup
SD_SERVER_STARTUP_TIMEOUT = int(os.environ.get("SD_SERVER_STARTUP_TIMEOUT", "120"))
SD_SERVER_HEALTH_INTERVAL = 2  # seconds between health polls during startup
