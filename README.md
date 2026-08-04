# AI Engineering — Build Log

Working through [AI Engineering from Scratch](https://github.com/rohitg00/ai-engineering-from-scratch)
(503 lessons, 20 phases) from the first lesson, building every algorithm by hand before
reaching for a library. This repo is the artifact trail: one directory per lesson, each
holding something runnable and a note on what it taught.

I started at Phase 0 by choice. A placement quiz put me at Phase 11; I ignored it. The
gap between recognising a term and being able to derive it is the entire point of doing
this, and starting from the top would have preserved exactly the gap I'm trying to close.

**Status: in progress.** Started 2026-08-04, ~18 h/week. This README updates as it goes —
if the progress table below looks thin, that's because it's honest rather than because
the repo is abandoned.

## Progress

| Phase | Lessons | Done | Status |
|-------|---------|------|--------|
| 00 — Setup & Tooling | 12 | 1 | 🚧 In progress |
| 01 — Math Foundations | 22 | 0 | ⬚ |
| 02 — ML Fundamentals | 18 | 0 | ⬚ |
| 03 — Deep Learning Core | 13 | 0 | ⬚ |
| 04–18 | 438 | 0 | ⬚ |

## Artifacts

| Lesson | Artifact | What it does |
|--------|----------|--------------|
| [00/01 — Dev Environment](phase-00-setup-and-tooling/01-dev-environment) | `check_env.py` | Phase-aware environment verification. Reports missing-but-not-needed-yet dependencies as deferred instead of failed, and handles the Windows Smart App Control case the course material doesn't cover. |

## Environment

Everything here runs on:

- Windows 11, Python 3.13.14 (signed python.org build), `uv` for packages
- NVIDIA RTX 3060 Laptop, 6 GB VRAM — Ampere, so bf16 and FlashAttention-2 are
  available; 6 GB is the real constraint on anything above ~3B parameters
- Node.js for the TypeScript phases; Rust added at Phase 12

Where the course assumes macOS or Linux and the Windows path diverges, the divergence is
documented in the lesson directory rather than silently worked around. Those notes are
the most useful thing in this repo so far.

## Layout

```
phase-NN-name/
  NN-lesson-name/
    README.md      what the lesson taught, what broke, what I'd do differently
    <artifact>     the runnable thing
```

## License

MIT — see [LICENSE](LICENSE). Course material is MIT-licensed by
[rohitg00](https://github.com/rohitg00/ai-engineering-from-scratch); artifacts here are
my own implementations unless a file says otherwise.
