# Phase 0 · Lesson 01 — Dev Environment

**Artifact:** [`check_env.py`](check_env.py) — phase-aware environment verification.

## What the lesson taught

An AI engineering environment is four layers, installed bottom-up:

```
4. AI/ML Libraries      PyTorch, JAX, transformers
3. Language Runtimes    Python, Node, Rust, Julia
2. Package Managers     uv, pnpm, cargo
1. System Foundation    OS, shell, git, GPU drivers
```

The ordering looks wrong at first — `pip` ships *inside* Python, so how is the package
manager below the runtime? Because the stack describes bootstrap order, not containment.
`uv` is a standalone Rust binary that runs before any Python exists, which is why
`uv python install 3.12` is a sensible command and `pip python install 3.12` is not.
`fnm` and `rustup` sit under Node and Rust the same way. `pip` genuinely doesn't.

## Where Windows diverges from the course

The lesson assumes macOS or Linux. Two things bite on Windows and neither is documented
upstream.

**1. Smart App Control kills `uv python install`.** The command downloads an unsigned
python-build-standalone binary; SAC blocks unsigned executables and the install dies.
Disabling SAC to work around this is the wrong trade — it is a one-way door on Windows 11
(re-enabling requires a clean install) and it removes a real protection to save one
download.

The fix is to install a signed interpreter from python.org and forbid `uv` from
substituting its own:

```powershell
uv venv --python 3.13 --python-preference only-system
```

`only-system` is the load-bearing flag. Without it `uv` silently prefers a managed
download and you are back in the same hole. On this machine `uv` owns packages but does
not own the interpreter, which is a slightly unusual split worth knowing about.

**2. Activation is optional and slightly misleading.** `uv venv` prints
`Activate with: .venv\Scripts\activate`, but nothing requires it. `uv pip install` finds
`.venv` in the working directory on its own, and calling `.venv\Scripts\python.exe` by
full path gets the isolated interpreter directly. Activation is PATH manipulation for
interactive convenience — useful, but not the mechanism, and treating it as the mechanism
leads to a lot of confused debugging.

## Why I rewrote the checker

The course's `verify.py` fails any missing dependency. Run it in Phase 0 on a correct
setup and it reports 6/7 with `Fix the failed checks above` — because Rust is absent.
Rust is not needed until Phase 12. PyTorch is not needed until Phase 3.

A check that reports a healthy environment as broken teaches you to ignore it, and an
ignored check is worse than no check at all. So `check_env.py` records the phase each
dependency is first required in:

```python
Dependency("Rust (cargo)", "binary", "cargo", 12, "Performance lessons"),
```

and reports anything not yet due as `DEFER` instead of `FAIL`. Exit code is non-zero only
when something needed *now* is missing, which makes it usable in a pre-lesson hook.

It also reports VRAM rather than a bare `cuda.is_available()` boolean, because on a 6 GB
card the number is the thing that determines what will actually fit.

## Run it

```powershell
# Check readiness for the current phase
python check_env.py

# Check what Phase 3 will need before starting it
python check_env.py --phase 3
```

Falls back to `nvidia-smi` for GPU detection when PyTorch isn't installed yet, so it is
useful before as well as after Phase 3.

## What I'd do differently

The dependency-to-phase mapping is hardcoded. It should be parsed from the curriculum's
`ROADMAP.md`, which already lists every phase — that would keep it correct as the course
adds lessons. Left as-is for now because the mapping is seven entries and parsing the
roadmap is more code than the problem currently justifies.
