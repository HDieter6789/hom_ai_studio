"""Safe, read-only GPU introspection via nvidia-smi.

No user input ever reaches this subprocess call - the command and its
arguments are a fixed list, never built from a string or run through a
shell, so there is no injection surface here.
"""

import shutil
import subprocess

from hom_core.providers.compute_provider import GPUDevice
from hom_core.schemas.worker import GPUInfo

_QUERY_FIELDS = [
    "index",
    "name",
    "memory.total",
    "memory.used",
    "utilization.gpu",
    "temperature.gpu",
]


def nvidia_smi_available() -> bool:
    return shutil.which("nvidia-smi") is not None


def query_gpus() -> list[GPUInfo]:
    if not nvidia_smi_available():
        return []

    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                f"--query-gpu={','.join(_QUERY_FIELDS)}",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
            shell=False,
        )
    except (subprocess.SubprocessError, OSError):
        return []

    gpus: list[GPUInfo] = []
    for line in result.stdout.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != len(_QUERY_FIELDS):
            continue
        index, name, mem_total, mem_used, util, temp = parts
        try:
            gpus.append(
                GPUInfo(
                    index=int(index),
                    name=name,
                    vram_total_gb=round(float(mem_total) / 1024, 2),
                    vram_used_gb=round(float(mem_used) / 1024, 2),
                    utilization_pct=float(util),
                    temperature_c=float(temp) if temp else None,
                )
            )
        except ValueError:
            continue
    return gpus


def query_devices() -> list[GPUDevice]:
    return [GPUDevice(index=g.index, name=g.name, vram_total_gb=g.vram_total_gb) for g in query_gpus()]
