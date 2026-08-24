"""Phase-aware environment verification for the AI Engineering curriculum.

Two things this does that a naive checker does not.

1. It knows which phase each dependency is first needed in, and reports anything not
   yet due as DEFER rather than FAIL. A checker that reports a healthy Phase 0 machine
   as broken teaches you to ignore it, and an ignored checker is worse than none.

2. It distinguishes a CPU-only PyTorch build from a CUDA build with no visible device.
   These are different faults with different fixes, and `cuda.is_available()` collapses
   both into a bare False. On Windows the CPU-only case is the default and silent: the
   PyPI Windows wheel is ~122 MB against ~427 MB on Linux, because it ships no CUDA
   kernels at all. Training still runs. It is just ~40x slower, forever, with no error.

Usage:
    python check_env.py            # check against Phase 0
    python check_env.py --phase 3  # check what Phase 3 will need, before starting it
"""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum

EXIT_OK = 0
EXIT_MISSING_REQUIRED = 1
MIN_PYTHON = (3, 11)


class Status(Enum):
    OK = "PASS"
    DEFER = "DEFER"
    MISSING = "FAIL"
    WARN = "WARN"


@dataclass(frozen=True)
class Dependency:
    """A tool the curriculum expects, and the phase it first expects it in."""

    name: str
    kind: str  # "module" | "binary"
    target: str
    required_from_phase: int
    reason: str


DEPENDENCIES: tuple[Dependency, ...] = (
    Dependency("Jupyter", "module", "jupyter", 0, "Notebook lessons in Phase 0"),
    Dependency("Git", "binary", "git", 0, "Phase 0 Lesson 02"),
    Dependency("NumPy", "module", "numpy", 1, "Math foundations onward"),
    Dependency("Matplotlib", "module", "matplotlib", 1, "Plotting from Phase 1"),
    Dependency("scikit-learn", "module", "sklearn", 2, "ML fundamentals"),
    Dependency("PyTorch", "module", "torch", 3, "Deep learning core onward"),
    Dependency("Rust (cargo)", "binary", "cargo", 12, "Performance lessons"),
    Dependency("Node.js", "binary", "node", 13, "TypeScript phases 13-17"),
)


def find_module(name: str) -> bool:
    """Report whether a module is importable WITHOUT importing it.

    `try: import torch` would answer this too, and costs ~2s plus a CUDA context
    allocation, and raises rather than returns False when a driver is half-broken.
    find_spec asks the import machinery to locate the module and stop there.
    """
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        # A namespace package shadowing a real one, or a broken parent package.
        return False


def version_of(name: str) -> str:
    """Distribution version, or '?' when metadata is absent (editable/vendored)."""
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "?"


def check(dep: Dependency, phase: int) -> tuple[Status, str]:
    present = find_module(dep.target) if dep.kind == "module" else bool(shutil.which(dep.target))
    if present:
        detail = version_of(dep.target) if dep.kind == "module" else (shutil.which(dep.target) or "")
        return Status.OK, detail
    if dep.required_from_phase > phase:
        return Status.DEFER, f"not needed until Phase {dep.required_from_phase}"
    return Status.MISSING, dep.reason


def gpu_report() -> list[tuple[Status, str, str]]:
    """Diagnose the GPU stack, separating the faults that is_available() conflates."""
    rows: list[tuple[Status, str, str]] = []

    if not find_module("torch"):
        smi = shutil.which("nvidia-smi")
        if smi:
            try:
                out = subprocess.run(
                    [smi, "--query-gpu=name,memory.total,driver_version",
                     "--format=csv,noheader"],
                    capture_output=True, text=True, timeout=15, check=False,
                )
                if out.returncode == 0 and out.stdout.strip():
                    rows.append((Status.OK, "GPU (via nvidia-smi)", out.stdout.strip()))
                else:
                    rows.append((Status.WARN, "nvidia-smi", "present but returned no GPU"))
            except (OSError, subprocess.SubprocessError) as exc:
                rows.append((Status.WARN, "nvidia-smi", f"failed: {exc}"))
        else:
            rows.append((Status.DEFER, "GPU", "no torch and no nvidia-smi — cannot assess"))
        return rows

    import torch  # safe now: we only reach here once find_spec located it

    built_cuda = torch.version.cuda  # None => the wheel contains no CUDA kernels
    if built_cuda is None:
        rows.append((
            Status.MISSING, "PyTorch build",
            f"{torch.__version__} is CPU-ONLY (torch.version.cuda is None). "
            "On Windows this is what PyPI serves by default. Reinstall from the "
            "PyTorch CUDA index or the GPU will never be used.",
        ))
        return rows

    rows.append((Status.OK, "PyTorch build", f"{torch.__version__}, built against CUDA {built_cuda}"))

    if not torch.cuda.is_available():
        rows.append((
            Status.MISSING, "CUDA runtime",
            "CUDA build present but no device visible — driver too old, GPU claimed "
            "by another process, or no NVIDIA hardware.",
        ))
        return rows

    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        gb = props.total_memory / 1024**3
        cap = f"{props.major}.{props.minor}"
        rows.append((Status.OK, f"GPU {i}", f"{props.name}  {gb:.1f} GB  compute {cap}"))
        # bf16 needs Ampere (8.0+). Below that, use fp16 and expect more overflow pain.
        bf16 = "yes" if props.major >= 8 else "NO — use fp16"
        rows.append((Status.OK if props.major >= 8 else Status.WARN, "  bf16 support", bf16))

    # A build can be correct and still fail at the first real allocation.
    try:
        a = torch.randn(64, 64, device="cuda")
        _ = (a @ a).sum().item()
        torch.cuda.synchronize()
        rows.append((Status.OK, "  live matmul", "executed on device"))
    except Exception as exc:  # noqa: BLE001 - any failure here is worth surfacing verbatim
        rows.append((Status.MISSING, "  live matmul", f"FAILED: {type(exc).__name__}: {exc}"))

    return rows


ICON = {Status.OK: "PASS ", Status.DEFER: "DEFER", Status.MISSING: "FAIL ", Status.WARN: "WARN "}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--phase", type=int, default=0, help="phase to check readiness for")
    args = ap.parse_args()

    failed = 0
    print(f"Environment check — Phase {args.phase}\n")

    py_ok = sys.version_info >= MIN_PYTHON
    print(f"  {ICON[Status.OK if py_ok else Status.MISSING]}  {'Python':16} "
          f"{'.'.join(map(str, sys.version_info[:3]))}")
    failed += 0 if py_ok else 1

    for dep in DEPENDENCIES:
        status, detail = check(dep, args.phase)
        print(f"  {ICON[status]}  {dep.name:16} {detail}")
        failed += status is Status.MISSING

    print("\n  GPU")
    for status, label, detail in gpu_report():
        print(f"  {ICON[status]}  {label:16} {detail}")
        failed += status is Status.MISSING and args.phase >= 3

    print()
    if failed:
        print(f"{failed} required check(s) failed for Phase {args.phase}.")
        return EXIT_MISSING_REQUIRED
    print(f"Ready for Phase {args.phase}.")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
