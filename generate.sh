#!/bin/bash
# Z-Image-Turbo Image Generator
#
# Usage:
#   Text-to-Image:  ./generate.sh -p "your prompt"
#   Image-to-Image: ./generate.sh -p "your prompt" -i input.png
#
# Options:
#   -p  Prompt (required)
#   -n  Negative prompt
#   -i  Input image for img2img
#   -s  Strength for img2img (0.0-1.0, default: 0.75)
#   -o  Output file (default: output.png)
#   -W  Width (default: 1024)
#   -H  Height (default: 1024)
#   -S  Steps (default: 8)
#   --seed  Seed (default: random, use a fixed number to reproduce)
#
# Examples:
#   ./generate.sh -p "A cat on the moon"
#   ./generate.sh -p "A cat on the moon" -n "blurry, low quality"
#   ./generate.sh -p "oil painting style" -i photo.png -s 0.6
#   ./generate.sh -p "A landscape" -o landscape.png -W 1536 -H 768

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Defaults
PROMPT=""
NEGATIVE=""
INIT_IMG=""
STRENGTH=0.75
OUTPUT="output.png"
WIDTH=1024
HEIGHT=1024
STEPS=8
SEED=-1

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -p)  PROMPT="$2"; shift 2 ;;
    -n)  NEGATIVE="$2"; shift 2 ;;
    -i)  INIT_IMG="$2"; shift 2 ;;
    -s)  STRENGTH="$2"; shift 2 ;;
    -o)  OUTPUT="$2"; shift 2 ;;
    -W)  WIDTH="$2"; shift 2 ;;
    -H)  HEIGHT="$2"; shift 2 ;;
    -S)  STEPS="$2"; shift 2 ;;
    --seed) SEED="$2"; shift 2 ;;
    *)   echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$PROMPT" ]]; then
  echo "Error: prompt is required. Use -p \"your prompt\""
  echo "Run './generate.sh' and see the header for full usage."
  exit 1
fi

# Build command
CMD=(
  "${SCRIPT_DIR}/stable-diffusion.cpp/build/bin/sd-cli"
  --diffusion-model "${SCRIPT_DIR}/models/z_image_turbo-Q6_K.gguf"
  --vae "${SCRIPT_DIR}/models/vae/split_files/vae/ae.safetensors"
  --llm "${SCRIPT_DIR}/models/text_encoder/Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
  -p "$PROMPT"
  --cfg-scale 1.0
  --steps "$STEPS"
  --seed "$SEED"
  --diffusion-fa
  --offload-to-cpu
  -H "$HEIGHT" -W "$WIDTH"
  -o "$OUTPUT"
)

[[ -n "$NEGATIVE" ]] && CMD+=(-n "$NEGATIVE")
[[ -n "$INIT_IMG" ]] && CMD+=(--init-img "$INIT_IMG" --strength "$STRENGTH")

"${CMD[@]}"
