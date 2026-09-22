# Security Policy

## Supported versions

RoomScope is pre-alpha (`0.1.0.dev1` on `main`). Only `main` is maintained.
There is no numbered release yet.

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting on this repository
(**Security → Report a vulnerability**). Do not open a public issue for a
report that could be abused.

If private reporting is not enabled yet, contact the repository owner through
GitHub. You should hear back within a few days.

## What is not a security issue

Wrong RT60 figures, surprising validity flags, GUI layout bugs and similar
analysis or usability problems are ordinary bugs. Please open a
[measurement](.github/ISSUE_TEMPLATE/measurement.yml) or
[bug](.github/ISSUE_TEMPLATE/bug.yml) issue and attach the files listed in
[CONTRIBUTING.md](CONTRIBUTING.md).

## Safety of Standalone Mode

RoomScope plays a test sweep through a loudspeaker. Defaults stay conservative
(−20 dBFS in Standalone Mode; −12 dBFS for generated sweep files). Nothing in
this project changes system volume, audio-device configuration, or DAW
settings. Please report any change that would do so as a security issue.
