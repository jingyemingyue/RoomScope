## Summary

What changed, and why.

## Kind of change

- [ ] DSP / measurement
- [ ] CLI / GUI / Python API
- [ ] Tests / CI
- [ ] Docs / license / provenance

## Checklist

- [ ] `pytest`, `ruff check . && ruff format --check .`, and `mypy` pass locally
- [ ] Every DSP change has a synthetic test with a known expected result
- [ ] New or changed metrics state their algorithm source, units and validity in `docs/MEASUREMENT_METHODOLOGY.md`
- [ ] New dependencies are recorded in `docs/DEPENDENCIES.md` (copyleft needs a discussion here)
- [ ] No third-party source was copied. If adapting code was unavoidable, `docs/THIRD_PARTY_REVIEW.md` and `docs/CODE_PROVENANCE.md` are updated and the upstream copyright notice is kept
- [ ] `CHANGELOG.md` is updated

## Notes for reviewers
