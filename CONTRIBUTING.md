# Contributing to RoomScope

Thank you for helping build a measurement tool people can trust. The rules
below exist so that every number RoomScope prints stays defensible.

## Ground rules

1. **Correctness before features.** A metric that cannot be computed reliably
   is reported as `insufficient_decay_range` / `unreliable`, never as a
   plausible-looking number.
2. **Cite the method.** Any new DSP function states its algorithm source
   (paper, standard) in the module docstring and in
   `docs/MEASUREMENT_METHODOLOGY.md`, with units and validity conditions.
3. **Clean-room by default.** Implement from the published equations. Do not
   paste code from other repositories, Stack Overflow, blog posts or AI
   answers. If adapting third-party code is unavoidable, first record it in
   `docs/THIRD_PARTY_REVIEW.md` and `docs/CODE_PROVENANCE.md` and keep the
   upstream copyright notice. Code from repositories without a clear license
   is never used.
4. **License review before dependencies.** Every new package (runtime or dev)
   gets a row in `docs/DEPENDENCIES.md` with its upstream license, bundled
   native libraries and obligations. Copyleft (GPL/AGPL/LGPL/MPL) dependencies
   need an explicit discussion in the pull request.
5. **Core stays pure.** `roomscope.core` takes and returns NumPy arrays and
   dataclasses; no Qt, no device access, no file I/O. Front ends only call
   `roomscope.core.pipeline.analyze`.
6. **Honest units.** dBFS unless calibrated. No "room score".
7. **Safety.** Nothing changes system volume, audio configuration or DAW
   settings. Default playback levels stay conservative.
8. **Only LGPL Qt modules** (QtCore, QtGui, QtWidgets). Never import
   GPL-only modules such as QtCharts, QtDataVisualization or QtGraphs.

## Development setup

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,gui]"
pytest                    # unit + integration + offscreen GUI smoke tests
ruff check . && ruff format --check .
mypy
```

All three must pass before a pull request is opened. Tests that need audio
hardware are not part of the suite; synthetic signals are used instead.

## Tests

* Add a synthetic test with a known expected result for every DSP change
  (`tests/conftest.py` has helpers for synthetic rooms and exponential decays).
* Keep tests fast: use short sweeps (2 s) and 48 kHz unless the test is about
  sample rates.
* Never rely on a real room recording as the only evidence.

## Commit and release policy

* One logical change per commit, with a message that says *why*.
* Do not create tags/releases, change the license, or delete remote branches
  without maintainer approval.
* `CHANGELOG.md` is updated in the same pull request.

## Reporting measurement problems

Please attach: the sweep sidecar JSON, the recorded WAV (or a link), the
`result.json`, your DAW/interface and sample rate, and what you expected.
