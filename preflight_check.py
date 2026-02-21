#!/usr/bin/env python3
"""Pre-deployment hardware/software requirements check for Z-Image."""

import shutil
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout + r.stderr
    except FileNotFoundError:
        return -1, f"command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return -1, "timed out"


class PreflightCheck:
    def __init__(self):
        self.passed: list[str] = []
        self.failed: list[str] = []

    def ok(self, msg: str):
        self.passed.append(msg)
        print(f"  ✓ {msg}")

    def fail(self, msg: str):
        self.failed.append(msg)
        print(f"  ✗ {msg}")

    def run_all(self) -> bool:
        print("Z-Image Pre-deployment Check")
        print("=" * 50)

        self.check_gpu()
        self.check_vram()
        self.check_ram()
        self.check_disk()
        self.check_docker()
        self.check_nvidia_container_toolkit()
        self.check_cuda_driver()
        self.check_models()
        self.check_sd_server_binary()

        print()
        print("=" * 50)
        if self.failed:
            print(f"FAILED: {len(self.failed)} check(s) did not pass:")
            for f in self.failed:
                print(f"  - {f}")
            return False
        else:
            print(f"ALL {len(self.passed)} CHECKS PASSED")
            return True

    def check_gpu(self):
        code, out = _run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"])
        if code == 0 and out.strip():
            gpus = [g.strip() for g in out.strip().splitlines()]
            self.ok(f"NVIDIA GPU detected: {', '.join(gpus)}")
        else:
            self.fail("No NVIDIA GPU detected (nvidia-smi failed). CUDA GPU required.")

    def check_vram(self):
        code, out = _run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"]
        )
        if code != 0:
            self.fail("Cannot query VRAM (nvidia-smi failed)")
            return
        try:
            vram_mb = min(int(v.strip()) for v in out.strip().splitlines())
            vram_gb = vram_mb / 1024
            if vram_gb >= 6:
                self.ok(f"VRAM: {vram_gb:.1f} GB (min 6 GB)")
            else:
                self.fail(
                    f"VRAM: {vram_gb:.1f} GB — need at least 6 GB "
                    "(Q4_K needs ~4 GB, Q6_K needs ~6 GB)"
                )
        except (ValueError, IndexError):
            self.fail(f"Cannot parse VRAM from nvidia-smi output: {out.strip()}")

    def check_ram(self):
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        gb = kb / (1024 * 1024)
                        if gb >= 12:
                            self.ok(f"RAM: {gb:.1f} GB (min 12 GB)")
                        else:
                            self.fail(
                                f"RAM: {gb:.1f} GB — need at least 12 GB "
                                "(model offloading uses ~8 GB)"
                            )
                        return
            self.fail("Cannot read MemTotal from /proc/meminfo")
        except OSError:
            self.fail("Cannot read /proc/meminfo")

    def check_disk(self):
        try:
            import shutil as _s

            usage = _s.disk_usage(Path(__file__).parent)
            free_gb = usage.free / (1024**3)
            if free_gb >= 15:
                self.ok(f"Disk: {free_gb:.1f} GB free (min 15 GB)")
            else:
                self.fail(
                    f"Disk: {free_gb:.1f} GB free — need at least 15 GB "
                    "(models ~8 GB + docker layers + temp)"
                )
        except OSError as e:
            self.fail(f"Cannot check disk space: {e}")

    def check_docker(self):
        if shutil.which("docker") is None:
            self.fail("Docker not installed. Install: https://docs.docker.com/engine/install/")
            return
        code, out = _run(["docker", "info"])
        if code == 0:
            self.ok("Docker is installed and running")
        else:
            self.fail("Docker is installed but not running (or permission denied). Try: sudo systemctl start docker")

    def check_nvidia_container_toolkit(self):
        code, out = _run(["docker", "run", "--rm", "--gpus", "all", "nvidia/cuda:12.0.0-base-ubuntu22.04", "nvidia-smi"])
        if code == 0:
            self.ok("NVIDIA Container Toolkit working (docker --gpus)")
        else:
            # Check if nvidia-container-toolkit package exists
            code2, _ = _run(["dpkg", "-l", "nvidia-container-toolkit"])
            if code2 == 0:
                self.fail(
                    "nvidia-container-toolkit installed but GPU passthrough failed. "
                    "Try: sudo systemctl restart docker"
                )
            else:
                self.fail(
                    "NVIDIA Container Toolkit not detected. "
                    "Install: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
                )

    def check_cuda_driver(self):
        code, out = _run(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"]
        )
        if code != 0:
            self.fail("Cannot query CUDA driver version")
            return
        try:
            version = out.strip().splitlines()[0].strip()
            major = int(version.split(".")[0])
            # CUDA 12.x requires driver >= 525
            if major >= 525:
                self.ok(f"NVIDIA driver: {version} (min 525.x for CUDA 12.x)")
            else:
                self.fail(
                    f"NVIDIA driver: {version} — need >= 525.x for CUDA 12.x compatibility"
                )
        except (ValueError, IndexError):
            self.fail(f"Cannot parse driver version: {out.strip()}")

    def check_models(self):
        project_root = Path(__file__).parent
        models_dir = project_root / "models"
        required = [
            "z_image_turbo-Q6_K.gguf",
            "vae/split_files/vae/ae.safetensors",
            "text_encoder/Qwen3-4B-Instruct-2507-Q4_K_M.gguf",
        ]
        missing = [m for m in required if not (models_dir / m).exists()]
        if not missing:
            self.ok(f"All {len(required)} model files present in models/")
        else:
            self.fail(f"Missing model files: {', '.join(missing)}")

    def check_sd_server_binary(self):
        project_root = Path(__file__).parent
        binary = project_root / "stable-diffusion.cpp" / "build" / "bin" / "sd-server"
        if binary.exists() and binary.stat().st_mode & 0o111:
            self.ok(f"sd-server binary found: {binary}")
        else:
            self.fail(
                f"sd-server binary not found at {binary}. "
                "Build with: cd stable-diffusion.cpp && mkdir -p build && cd build && cmake .. -DSD_CUDA=ON && cmake --build . --config Release"
            )


if __name__ == "__main__":
    checker = PreflightCheck()
    success = checker.run_all()
    sys.exit(0 if success else 1)
