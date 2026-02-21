# =============================================================================
# Stage 1: Build stable-diffusion.cpp
# =============================================================================
FROM nvidia/cuda:12.6.3-devel-ubuntu24.04 AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    git cmake build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
RUN git clone --depth 1 https://github.com/leejet/stable-diffusion.cpp.git \
    && cd stable-diffusion.cpp \
    && mkdir build && cd build \
    && cmake .. -DSD_CUDA=ON -DCMAKE_BUILD_TYPE=Release \
    && cmake --build . --config Release -j"$(nproc)"

# =============================================================================
# Stage 2: Runtime
# =============================================================================
FROM nvidia/cuda:12.6.3-runtime-ubuntu24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy sd-server binary
COPY --from=builder /build/stable-diffusion.cpp/build/bin/sd-server /app/bin/sd-server

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy FastAPI service
COPY server/ /app/server/

# Models are mounted as a volume at runtime (too large to bake in)
# VOLUME /app/models

ENV SD_SERVER_BIN=/app/bin/sd-server \
    MODELS_DIR=/app/models \
    FASTAPI_HOST=0.0.0.0 \
    FASTAPI_PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

CMD ["python3", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
