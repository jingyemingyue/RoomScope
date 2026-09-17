from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from scipy.signal import fftconvolve

from roomscope.cli.main import main
from roomscope.io.wav import read_wav, write_wav
from tests.conftest import make_rir


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "roomscope" in capsys.readouterr().out


def test_sweep_and_analyze_commands(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    sweep = tmp_path / "sweep.wav"
    assert main(["sweep", "--out", str(sweep), "--duration", "2", "--post-silence", "1.5"]) == 0
    assert sweep.is_file() and (tmp_path / "sweep.roomscope-sweep.json").is_file()

    signal = read_wav(sweep)
    ir = make_rir(signal.sample_rate, rt60_s=0.4, reflections=[(0.018, 0.35)], diffuse_level=0.01)
    rec = fftconvolve(signal.samples, ir)[: signal.n_samples + ir.shape[0]]
    rec = np.stack([np.zeros_like(rec), rec], axis=1)
    recording = write_wav(tmp_path / "recording.wav", rec, signal.sample_rate, subtype="FLOAT")

    out = tmp_path / "session"
    code = main(
        [
            "analyze",
            "--recording",
            str(recording),
            "--sweep",
            str(sweep),
            "--out",
            str(out),
            "--room",
            "R",
        ]
    )
    captured = capsys.readouterr()
    assert code == 0
    assert "RoomScope analysis" in captured.out
    assert "18.0 ms" in captured.out
    assert (out / "session.json").is_file() and (out / "result.json").is_file()

    code = main(
        [
            "analyze",
            "--recording",
            str(recording),
            "--sweep",
            str(sweep),
            "--json",
            "--no-curves",
            "--channel",
            "1",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["decay"]["broadband"]["rt60_estimate_s"] == pytest.approx(0.4, rel=0.15)
    assert payload["findings"]


def test_analyze_missing_file_returns_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(
        [
            "analyze",
            "--recording",
            str(tmp_path / "nope.wav"),
            "--sweep",
            str(tmp_path / "nope2.wav"),
        ]
    )
    assert code == 1
    assert "error:" in capsys.readouterr().err


def test_measure_refuses_loud_level_without_acknowledgement(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["measure", "--out", str(tmp_path / "m"), "--level", "-3"])
    assert code == 2
    assert "acknowledge" in capsys.readouterr().err
