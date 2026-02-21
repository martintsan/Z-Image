"""sd-server process lifecycle manager."""

from __future__ import annotations

import asyncio
import logging
import subprocess

import httpx

from . import config

logger = logging.getLogger("z-image.backend")

_process: subprocess.Popen | None = None
_client: httpx.AsyncClient | None = None


def _sd_server_url(path: str = "") -> str:
    return f"http://{config.SD_SERVER_HOST}:{config.SD_SERVER_PORT}{path}"


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=_sd_server_url(),
            timeout=httpx.Timeout(300.0, connect=10.0),
        )
    return _client


async def start() -> None:
    """Start sd-server as a subprocess and wait until it's ready."""
    global _process

    if _process is not None and _process.poll() is None:
        logger.info("sd-server already running (pid=%d)", _process.pid)
        return

    cmd = [
        str(config.SD_SERVER_BIN),
        "--diffusion-model", str(config.DIFFUSION_MODEL),
        "--vae", str(config.VAE_MODEL),
        "--llm", str(config.LLM_MODEL),
        "--listen-port", str(config.SD_SERVER_PORT),
        "-l", config.SD_SERVER_HOST,
        "--cfg-scale", str(config.DEFAULT_CFG_SCALE),
        "--steps", str(config.DEFAULT_STEPS),
        "-H", str(config.DEFAULT_HEIGHT),
        "-W", str(config.DEFAULT_WIDTH),
        "--diffusion-fa",
        "--offload-to-cpu",
    ]

    if config.LORA_DIR.is_dir():
        cmd.extend(["--lora-model-dir", str(config.LORA_DIR)])

    logger.info("Starting sd-server: %s", " ".join(cmd))
    _process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    # Stream sd-server output to our logger in background
    asyncio.get_event_loop().run_in_executor(None, _stream_output, _process)

    # Poll until sd-server is ready
    timeout = config.SD_SERVER_STARTUP_TIMEOUT
    interval = config.SD_SERVER_HEALTH_INTERVAL
    elapsed = 0.0
    client = get_client()

    while elapsed < timeout:
        if _process.poll() is not None:
            raise RuntimeError(
                f"sd-server exited during startup with code {_process.returncode}"
            )
        try:
            resp = await client.get("/sdapi/v1/samplers")
            if resp.status_code == 200:
                logger.info("sd-server is ready (took %.1fs)", elapsed)
                return
        except httpx.ConnectError:
            pass
        await asyncio.sleep(interval)
        elapsed += interval

    stop()
    raise TimeoutError(
        f"sd-server did not become ready within {timeout}s"
    )


def _stream_output(proc: subprocess.Popen) -> None:
    """Read sd-server stdout/stderr and forward to logger."""
    assert proc.stdout is not None
    for line in iter(proc.stdout.readline, b""):
        text = line.decode("utf-8", errors="replace").rstrip()
        if text:
            logger.info("[sd-server] %s", text)
    proc.stdout.close()


def stop() -> None:
    """Terminate the sd-server subprocess."""
    global _process, _client
    if _client is not None and not _client.is_closed:
        # Can't await in sync context; mark for cleanup
        _client = None
    if _process is not None and _process.poll() is None:
        logger.info("Stopping sd-server (pid=%d)", _process.pid)
        _process.terminate()
        try:
            _process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            logger.warning("sd-server did not exit, killing")
            _process.kill()
            _process.wait()
    _process = None


def is_running() -> bool:
    return _process is not None and _process.poll() is None
