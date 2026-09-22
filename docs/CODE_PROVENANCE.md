# Code provenance

Last reviewed: 2026-09-17 (v0.1 foundation).

## Vendored or adapted third-party source files

**No third-party source files currently vendored.**

No file in `src/`, `tests/`, `examples/` or `scripts/` was copied or adapted
from another repository, gist, blog post, Q&A site or AI answer of unknown
origin. All DSP is implemented from the published equations and step
descriptions cited in MEASUREMENT_METHODOLOGY.md.

The table below is empty by design and must be filled in before any
third-party code enters the tree:

| local file | upstream file | upstream project | upstream URL | commit hash | copyright holder | license | modification description |
| --- | --- | --- | --- | --- | --- | --- | --- |
| (none) | | | | | | | |

## Third-party *libraries* (used, not copied)

RoomScope imports NumPy, SciPy, soundfile, sounddevice, matplotlib and
(optionally) PySide6 as ordinary dependencies. Their licenses, bundled native
libraries and redistribution obligations are recorded in DEPENDENCIES.md.
Using a library through its public API is not vendoring and creates no
entry above.

## Verbatim texts that are *not* code

| file | source | reason |
| --- | --- | --- |
| `LICENSE` | https://www.apache.org/licenses/LICENSE-2.0.txt (SHA-256 cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30) | the license text itself, reproduced verbatim as required |
| `docs/PROJECT_BRIEF.zh-CN.md` | project owner's brief | project's own material |

## Conceptual references only

The repositories listed in THIRD_PARTY_REVIEW.md were studied for feature
design and algorithm names only. In particular, no code was taken from the
GPL projects DRC and Aliki, from the proprietary Room EQ Wizard, or from the
unlicensed gists and course projects that surfaced in searches.

The image-source mathematics in `core/placement.py` (and the synthetic
arrivals its tests are built from) was implemented clean-room from the
published relation in Allen & Berkley (1979); no code was taken from
pyroomacoustics (MIT, EPFL-LCAV), which THIRD_PARTY_REVIEW.md records as
evaluated and not adopted — adopting it would also bring its Eigen
(MPL-2.0) obligation, see DEPENDENCIES.md. RoomScope does not implement
room-shape-from-echoes / echo sorting (Dokmanić et al., 2013); it is cited in
MEASUREMENT_METHODOLOGY.md §9 as the published method the project declines,
and no implementation of it was consulted.

## How to update this file

When adapting or copying third-party code becomes necessary:

1. Complete the license check in THIRD_PARTY_REVIEW.md first.
2. Add a row above with every column filled (no "unknown").
3. Keep the upstream copyright and license notice in the local file.
4. Add the notice to `NOTICE` if the upstream license requires it
   (Apache-2.0 NOTICE files, BSD advertising clauses, etc.).
