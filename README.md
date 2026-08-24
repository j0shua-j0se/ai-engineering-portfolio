# AI Engineering — Build Log

Working through [AI Engineering from Scratch](https://github.com/rohitg00/ai-engineering-from-scratch)
(503 lessons, 20 phases), building each algorithm by hand before reaching for a library.
One directory per lesson, each holding something runnable.

## Setup

Requires [uv](https://docs.astral.sh/uv/) and Python 3.11+.

```bash
uv sync                      # Phase 0 dependencies only
uv sync --extra phase-01     # add Math Foundations deps when you reach Phase 1
uv sync --extra phase-03     # add PyTorch when you reach Phase 3
```

On Windows, force uv to use an already-installed signed interpreter rather than
downloading its own:

```powershell
uv sync --python-preference only-system
```

`uv`'s managed interpreters are unsigned python-build-standalone binaries, which
Smart App Control blocks. There is deliberately no `.python-version` file here — it
would pin a minor version and send uv looking for a download that cannot run.

Dependencies are declared in `pyproject.toml` against the phase that first needs
them, rather than installed all at once. A fresh clone pulls what the current phase
requires and nothing else — PyTorch is a multi-gigabyte download that Phase 0 has no
use for.

## Verifying the environment

```bash
python phase-00-setup-and-tooling/01-dev-environment/check_env.py            # Phase 0
python phase-00-setup-and-tooling/01-dev-environment/check_env.py --phase 3  # before Phase 3
```

Dependencies not yet due are reported `DEFER`, not `FAIL`, so a correct Phase 0 machine
reports clean. Exit status is non-zero only when something needed *now* is missing.

### GPU, on Windows

`uv sync --extra phase-03` resolves torch from PyPI, and the PyPI Windows wheel is
**CPU-only**. It installs and imports without complaint, and then never touches the GPU.
Install from the PyTorch CUDA index instead — take the current `cuXXX` tag from
[pytorch.org/get-started](https://pytorch.org/get-started/locally/):

```powershell
uv pip install torch --index-url https://download.pytorch.org/whl/cuXXX
```

`check_env.py` tells the two failure modes apart, which `torch.cuda.is_available()`
cannot:

| Symptom | Meaning | Fix |
|---|---|---|
| `torch.version.cuda is None` | CPU-only wheel | reinstall from the CUDA index |
| CUDA build, no device visible | driver / hardware | update driver, check `nvidia-smi` |

## Layout

```
phase-NN-name/
  NN-lesson-name/
    README.md      what the lesson taught, what broke, what I'd do differently
    <artifact>     the runnable thing
```

## Progress

| Phase | Lessons | Done | Status |
|-------|---------|------|--------|
| 00 — Setup & Tooling | 12 | 0 | 🚧 In progress |
| 01 — Math Foundations | 22 | 0 | ⬚ |
| 02 — ML Fundamentals | 18 | 0 | ⬚ |
| 03 — Deep Learning Core | 13 | 0 | ⬚ |
| 04–18 | 438 | 0 | ⬚ |

## License

MIT — see [LICENSE](LICENSE). Course material is MIT-licensed by
[rohitg00](https://github.com/rohitg00/ai-engineering-from-scratch); artifacts here are
my own implementations unless a file says otherwise.
