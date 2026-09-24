# RoomScope release plan

Status: adopted 2026-09-24. This document says which versions RoomScope
will cut, what each one must prove before it is cut, and how a release is
mechanically produced. It does not change the scope contract in
[ARCHITECTURE_V1.md](ARCHITECTURE_V1.md) §3; it schedules it. A Chinese
digest is in [RELEASE_PLAN.zh-CN.md](RELEASE_PLAN.zh-CN.md); the English
text is authoritative.

No dates. The exit criteria are the schedule (ARCHITECTURE_V1.md §10).

## 1. Where the project stands (2026-09-24)

* `main` carries the v0.1 foundation plus milestones 0.2 (reopen and
  compare), 0.3 (trust the chain), 0.4 (for everyone) and the 1.0-rc
  *software* items (Placement tab, validation protocol, packaging
  scaffolding, robustness). They were reviewed and merged on 2026-09-24
  (PRs #5, #6, #7, #8); the review findings are GitHub issues #9–#16.
* No tag and no GitHub Release exist yet. The repository is private.
* **Update (2026-09-24, later the same day):** the review follow-ups
  #9–#17 (#17, the QML part of the bundle gate, was found after this plan
  was written) are fixed on the branch `v0.4.1-review-followups`, which
  sets the version to 0.4.1. Because #17 had to be closed before any
  bundle is published (§4), 0.4.0 is not expected to get a Release of its
  own: once that pull request is merged with CI green, the first draft
  Release is v0.4.1. Nothing else in this plan changes.
* Everything that requires a person in a real room is **not** done: the
  hardware matrix ([HARDWARE_TESTS.md](HARDWARE_TESTS.md)) has no PASS cell
  and the validation campaign ([VALIDATION.md](VALIDATION.md)) has not been
  run. The maintainer has no measurement hardware available in the near
  term, so those items are scheduled last and may be filled by
  contributors after the repository opens.
* Signing identities, the PyPI project name, trusted publishing and the
  public flip are maintainer decisions and are all still open
  (ARCHITECTURE_V1.md §13).

## 2. Version ladder

| Version | Purpose | Must be true before it is cut | Not claimed |
| --- | --- | --- | --- |
| **0.4.0** | First pre-release: everything on `main` today, as a draft Release with unsigned bundles for the maintainer's own testing | CI green on Linux / macOS / Windows and Python 3.12–3.14; `ruff`, `mypy`, the schema job and the bundle gates pass; the license bundle carries the verbatim LGPL-3.0 / GPL-3.0 / PortAudio texts; `CHANGELOG.md` has a `[0.4.0]` section; `docs/STATUS.md` has a dated snapshot | Any hardware result; a person installing a bundle on macOS / Windows; PyPI; public availability |
| **0.4.x** | Patch releases for the review follow-ups | Each patch closes at least one of #9–#17 with a synthetic test; no new feature (0.4.1 closes all nine) | — |
| **0.5.0** | "Trusted by a human": the first version whose Standalone Mode and DAW workflow were run on real hardware at least once | One dated PASS row per cell of the hardware matrix on at least one platform (device enumeration, sample-rate negotiation, channel mapping, loopback capture, Stop during playback, a full Standalone measurement, the same signal through one DAW); #12 and #13 (loopback time origin, real-time callback) closed; #14 (zh-CN catalog complete, safety warning translated) closed; #15 (ISO 3382-2 table source) closed | The validation campaign; API / schema freeze; signing |
| **1.0.0rc1** | Freeze and prove (ARCHITECTURE_V1.md §10, row 1.0-rc) | No open MUST item of §3.1: hardware matrix executed at least once per platform (M10); validation campaign published with its data (M11); signed bundles or an explicit maintainer decision to ship unsigned (M9); public-repository checklist executed (M13, §9.1); API and schema integers frozen; SECURITY / CONTRIBUTING / STATUS updated for the freeze; PyPI pre-release if trusted publishing is configured | — |
| **1.0.0** | Release | Fixes from the candidate only; release notes name the validation results and the known limitations | — |

Minor releases between these rows are allowed whenever a MUST or SHOULD
item lands and CI is green on every platform; patch releases are for fixes
only (ARCHITECTURE_V1.md §9.2).

## 3. How a release is produced

The pipeline is `.github/workflows/release.yml`
([source](../.github/workflows/release.yml)). It is driven by the version
in `pyproject.toml`, and the maintainer keeps the last word.

> **Workflow status (2026-09-24).** The version-driven `.github/workflows/release.yml`
> is included in PR #18. Its PR validation run builds and smoke-tests the
> Linux, macOS and Windows bundles without opening a draft or publishing to
> PyPI. The workflow becomes active on `main` when the PR is merged; the
> merge changes `pyproject.toml` to 0.4.1 and is intended to create the
> first v0.4.1 draft after the release jobs pass. Check the merged commit's
> CI and the draft assets before publishing. Do not push a tag while the
> older tag-only workflow is still on `main`.

1. **Prepare the release commit on `main`.** Set `project.version` in
   `pyproject.toml` to the new version (no `.dev` suffix). Move the
   `[Unreleased]` entries of `CHANGELOG.md` under a `## [<version>] -
   <date>` heading. Add a dated snapshot to `docs/STATUS.md` that says what
   was actually run. Re-check `docs/DEPENDENCIES.md` §3–§4 if any dependency
   version changed. Commit and push (or merge the PR).
2. **CI opens a draft.** Because `pyproject.toml` changed on `main` and no
   tag `v<version>` exists, the workflow runs lint, type-check and the
   test suite, builds sdist and wheel, builds the unsigned bundles on the
   three OS runners (license bundle → PyInstaller → strip GPL-only Qt
   modules and ASIO DLLs → bundle gate → smoke test → archive → checksums),
   produces the SBOM and lock file, and opens a **draft** GitHub Release
   named `v<version>` with the CHANGELOG section as its body and every
   archive attached. **No tag exists at this point.** A version containing
   `.dev` never opens a draft.
3. **The maintainer decides.** Download the bundles from the draft and try
   them on a real machine (the `docs/user-guide` Gatekeeper / SmartScreen
   steps apply to unsigned builds). Publish the draft to release, or delete
   it to abort. Publishing creates the tag `v<version>` on the release
   commit — that click is the release decision the project brief reserves
   for the maintainer.
   A tag the maintainer pushes by hand takes the same path: the tag run
   builds everything and opens (or updates) the draft for that tag.
4. **The tag run.** Pushing the tag (which publishing does) re-runs the
   quality gates against the tag and, only if the repository variable
   `ROOMSCOPE_PUBLISH_PYPI` is `true` and the `pypi` environment and PyPI
   trusted publisher exist, uploads the wheel and sdist to PyPI. Until the
   maintainer sets that up, nothing reaches PyPI.

Rules that follow from this: the version in `pyproject.toml` is the single
source of truth (`roomscope.__version__` reads it from package metadata); a
tag whose name does not equal `v<pyproject version>` fails the workflow;
tags come only from publishing a draft or from the maintainer's own push;
published history is never rewritten.

## 4. Gates that apply to every release

* CI (`ci.yml`) green on the release commit: lint, mypy, docs link check,
  docs site build, `check_src_safety.py`, schema job, the test matrix
  (Ubuntu 3.12 / 3.13 / 3.14, macOS 3.12, Windows 3.12), the 85 % coverage
  gate on `core` and `models`, the package job, the installed-Essentials
  GPL gate.
* Release workflow green: bundle gate with `--strip --require-licenses`,
  smoke test (`--version`, fake-backend measurement, offscreen GUI) on
  each OS.
* No `UNKNOWN / NEEDS REVIEW` item in `DEPENDENCIES.md` §6 that affects
  the binary being shipped; the license bundle lists `unresolved: none`.
* `docs/STATUS.md` states what was run and what was not. Nothing is
  marked PASS that was not run; hardware cells stay empty until a person
  fills them with a date and an interface name.
* `CHANGELOG.md` has the version's section; overclaims found in review
  are corrected in the same release (for 0.4.0: the zh-CN catalog covered
  three of seven profiles, see #14; closed in 0.4.1).

## 5. Maintainer decisions still open

| Decision | Needed by | State |
| --- | --- | --- |
| Public flip of the repository (ARCHITECTURE_V1.md §9.1 checklist: description and topics, branch protection on `main`, CODEOWNERS present, private vulnerability reporting, labels, Discussions, pinned roadmap) | 1.0.0rc1 (recommended at the first candidate so it gets outside testing) | Open |
| Apple Developer ID + notarization, Windows Authenticode; or ship 1.0 unsigned with documentation | 1.0.0rc1 | Open; 0.x bundles are unsigned by design |
| PyPI: register `roomscope`, configure trusted publishing, create the `pypi` environment with required reviewers, set `ROOMSCOPE_PUBLISH_PYPI=true` | First version the maintainer wants on PyPI (earliest 0.5.0) | Open; the workflow stays off until then |
| Validation campaign: rooms, reference instrument (REW as a comparison instrument only), who runs it | 1.0.0rc1 | Open; no hardware available near-term |
| DCO sign-off requirement | Public flip | Open |
| Dependabot PRs #3 / #4 (actions/checkout 4→7, actions/setup-python 5→7) | Any time | Merge when Dependabot has rebased them onto the SHA-pinned workflows and CI is green |

## 6. Review follow-ups (2026-09-24)

Opened while merging the milestone PRs; none blocks 0.4.0, several block
0.5.0 (see §2). All nine are fixed in 0.4.1 (CHANGELOG `[0.4.1]`); an issue
is closed when that pull request is merged.

| Issue | Area | Severity | 0.4.1 |
| --- | --- | --- | --- |
| #9 | `compare`: frequency-response delta interpolates the raw spectrum before smoothing | medium | smoothed on the native grid first |
| #10 | `analyze_impulse_response` / `analyze-ir` untested | medium | tested; a quadratic pass search and non-IR input fixed on the way |
| #11 | session loader follows absolute member paths | low (security) | members confined to the session folder |
| #12 | loopback FIR window advances the compensated response by ~5 ms | medium | FIR origin at its peak, linear division, settling net of noise over the valid record |
| #13 | PortAudio: progress inside the real-time callback; swallowed callback errors | medium | progress polled, errors fail the take, channels validated first |
| #14 | zh-CN catalog incomplete; safety warning untranslated; `.mo` not shipped | high for the i18n claim | all profiles, contexts, hashed `.mo` in the wheel |
| #15 | ISO 3382-2 Table 1: source unnamed; engineering class ignores microphone count | medium | Table 1 read from the standard, every row checked |
| #16 | `check_src_safety.py` gaps; coverage figure unrecorded | low | aliases / dynamic imports; 90.20 % recorded |
| #17 | bundle gate misses the virtual-keyboard QML plugins | must close before any bundle is published | QML matched by directory; any QML tree fails |

## 7. What this plan does not do

It does not make the repository public, create a numbered Release, change
the license, push a tag, rewrite history, or claim any hardware result.
Each of those is either a maintainer click or a person in a room.
