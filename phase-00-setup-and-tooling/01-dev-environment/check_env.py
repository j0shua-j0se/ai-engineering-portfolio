"""Phase-aware environment verification for the AI Engineering curriculum.

The course ships a verify.py that fails any missing dependency, which means it reports
a correct environment as broken for the first eleven phases: Rust is not needed until
Phase 12 and PyTorch not until Phase 3. A check that cries wolf gets ignored, and an
ignored check is worse than no check.

This version knows which phase each dependency is first required in and reports anything
not yet due as DEFER rather than FAIL. Exit status is non-zero only for things actually
needed now.

Usage:
    python check_env.py            # check against Phase 0
    python check_env.py --phase 3  # check against Phase 3
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum

EXIT_OK = 0
EXIT_MISSING_REQUIRED = 1
MIN_PYTHON = (3, 10)


class Status(Enum):
    """Outcome of a single dependency check."""

    OK = "PASS"
    DEFER = "DEFER"
    MISSING = "FAIL"


@dataclass(frozen=True)
class Dependency:
    """A tool or package the curriculum expects, and when it first expects it."""

    name: str
    kind: str  # "module" or "binary"
    target: str
    required_from_phase: int
    reason: str


DEPENDENCIES: tuple[Dependency, ...] = (
    Dependency("NumPy", "module", "numpy", 1, "Math foundations onward"),
    Dependency("Matplotlib", "module", "matplotlib", 1, "Plotting from Phase 1"),
    Dependency("Jupyter", "module", "jupyter", 0, "Notebook lessons in Phase 0"),
    Dependency("Git", "binary", "git", 0, "Phase 0 Lesson 02"),
    Dependency("Node.js", "binary", "node", 13, "TypeScript phases 13-17"),
    Dependency("Rust (cargo)", "binary", "cargo", 12, "Performance lessons"),
    Dependency("PyTorch", "module", "torch", 3, "Deep learning core onward"),
)


@dataclass(frozen=True)
class Result:
    """A dependency paired with the outcome of checking for it."""

    dependency: Dependency
    status: Status
    detail: str


def find_module(module_name: str) -> str | None:
    """Return an installed module's version, or None if it cannot be imported."""
    try:
        importlib.import_module(module_name)
    except ImportError:
        return None
    try:
        return importlib.metadata.version(module_name)
    except importlib.metadata.PackageNotFoundError:
        return "installed"


def find_binary(binary_name: str) -> str | None:
    """Return the resolved path of an executable on PATH, or None if absent."""
    return shutil.which(binary_name)


def evaluate(dependency: Dependency, current_phase: int) -> Result:
    """Check one dependency and classify a miss as deferred or genuinely missing."""
    finder = find_module if dependency.kind == "module" else find_binary
    found = finder(dependency.target)

    if found is not None:
        return Result(dependency, Status.OK, found)

    is_due = current_phase >= dependency.required_from_phase
    status = Status.MISSING if is_due else Status.DEFER
    detail = f"needed from Phase {dependency.required_from_phase} — {dependency.reason}"
    return Result(dependency, status, detail)


def describe_python() -> Result:
    """Check the interpreter version and report which interpreter is running."""
    interpreter = Dependency("Python", "binary", sys.executable, 0, "Everything")
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    if sys.version_info < MIN_PYTHON:
        needed = f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]}"
        return Result(interpreter, Status.MISSING, f"{version} — need {needed}+")

    return Result(interpreter, Status.OK, f"{version} at {sys.executable}")


def describe_gpu() -> list[str]:
    """Report GPU availability, preferring torch and falling back to nvidia-smi."""
    if find_module("torch") is not None:
        import torch

        if not torch.cuda.is_available():
            return ["No CUDA device visible to PyTorch — CPU only, which is fine early on"]
        name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
        return [f"{name}", f"{vram_gb:.1f} GB VRAM"]

    if find_binary("nvidia-smi") is None:
        return ["No NVIDIA GPU detected — most lessons run on CPU"]

    return _query_nvidia_smi()


def _query_nvidia_smi() -> list[str]:
    """Read GPU name and memory straight from nvidia-smi when torch is absent."""
    query = "--query-gpu=name,memory.total"
    try:
        output = subprocess.run(
            ["nvidia-smi", query, "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
    except (subprocess.SubprocessError, OSError) as error:
        return [f"nvidia-smi present but unreadable: {error}"]

    detected = output.stdout.strip() or "unknown device"
    return [f"{detected} (PyTorch not installed — install at Phase 3 to use it)"]


def report(results: list[Result], gpu_lines: list[str], current_phase: int) -> int:
    """Print the full report and return the process exit code."""
    print(f"\n=== Environment check — targeting Phase {current_phase} ===\n")

    for result in results:
        print(f"  [{result.status.value:<5}] {result.dependency.name}: {result.detail}")

    print("\nGPU:")
    for line in gpu_lines:
        print(f"  {line}")

    missing = [r for r in results if r.status is Status.MISSING]
    deferred = [r for r in results if r.status is Status.DEFER]

    print(f"\n{len(results) - len(missing) - len(deferred)} ready", end="")
    print(f", {len(deferred)} deferred", end="")
    print(f", {len(missing)} missing\n")

    if missing:
        print("Missing dependencies needed for this phase:")
        for result in missing:
            print(f"  - {result.dependency.name}: {result.detail}")
        print()
        return EXIT_MISSING_REQUIRED

    print("Nothing missing for this phase. Deferred items install when their phase lands.\n")
    return EXIT_OK


def main() -> int:
    """Parse arguments, run every check, and print the report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase",
        type=int,
        default=0,
        help="curriculum phase to check readiness for (default: 0)",
    )
    args = parser.parse_args()

    results = [describe_python()]
    results += [evaluate(dependency, args.phase) for dependency in DEPENDENCIES]

    return report(results, describe_gpu(), args.phase)


if __name__ == "__main__":
    sys.exit(main())
