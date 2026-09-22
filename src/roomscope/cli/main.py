"""``roomscope`` command-line interface.

Subcommands: ``sweep``, ``analyze``, ``show``, ``devices``, ``measure``, ``gui``.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from roomscope import __version__
from roomscope.cli.report import format_comparison_report, format_report
from roomscope.errors import MeasurementCancelledError, RoomScopeError
from roomscope.interpretation import available_profiles
from roomscope.logging_config import configure_logging
from roomscope.models.configuration import (
    DEFAULT_SAMPLE_RATE,
    SUPPORTED_SAMPLE_RATES,
    AnalysisSettings,
    SweepSettings,
)

log = logging.getLogger("roomscope.cli")


def _add_sweep_arguments(parser: argparse.ArgumentParser, *, default_level: float) -> None:
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=DEFAULT_SAMPLE_RATE,
        choices=SUPPORTED_SAMPLE_RATES,
        help="sample rate (Hz)",
    )
    parser.add_argument(
        "--duration", type=float, default=10.0, help="sweep duration in seconds (default 10)"
    )
    parser.add_argument(
        "--start-hz", type=float, default=20.0, help="sweep start frequency (default 20)"
    )
    parser.add_argument(
        "--end-hz", type=float, default=20000.0, help="sweep end frequency (default 20000)"
    )
    parser.add_argument(
        "--fade-in", type=float, default=0.05, help="fade-in in seconds (default 0.05)"
    )
    parser.add_argument(
        "--fade-out", type=float, default=0.01, help="fade-out in seconds (default 0.01)"
    )
    parser.add_argument(
        "--level",
        type=float,
        default=default_level,
        help=f"peak level in dBFS (default {default_level:g})",
    )
    parser.add_argument(
        "--pre-silence", type=float, default=1.0, help="silence before the sweep (s)"
    )
    parser.add_argument(
        "--post-silence", type=float, default=3.0, help="silence after the sweep (s)"
    )


def _sweep_settings(args: argparse.Namespace) -> SweepSettings:
    return SweepSettings(
        sample_rate=args.sample_rate,
        duration_s=args.duration,
        start_hz=args.start_hz,
        end_hz=args.end_hz,
        fade_in_s=args.fade_in,
        fade_out_s=args.fade_out,
        level_dbfs=args.level,
        pre_silence_s=args.pre_silence,
        post_silence_s=args.post_silence,
    )


def _add_analysis_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--channel", type=int, default=None, help="recording channel to analyse (0-based)"
    )
    parser.add_argument(
        "--smoothing", type=int, default=6, help="fractional-octave smoothing 1/N (0 = off)"
    )
    parser.add_argument("--room", default="", help="room name (metadata)")
    parser.add_argument("--position", default="", help="measurement position (metadata)")
    parser.add_argument("--mic", default="", help="microphone name (metadata)")
    parser.add_argument("--notes", default="", help="free-text notes (metadata)")
    parser.add_argument("--no-curves", action="store_true", help="omit curves from result.json")
    parser.add_argument(
        "--json", action="store_true", help="print the result as JSON instead of a report"
    )
    parser.add_argument(
        "--speaker-distance",
        type=float,
        default=None,
        metavar="M",
        help=(
            "straight line from the loudspeaker to the microphone capsule (m), measured "
            "with a tape. Without it no geometry can be derived from the reflections"
        ),
    )
    parser.add_argument(
        "--mic-height",
        type=float,
        default=None,
        metavar="M",
        help=(
            "microphone capsule above the first solid horizontal surface below it (m) -- "
            "the desk top at a desk, otherwise the floor. Needs --speaker-distance"
        ),
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        metavar="C",
        help="air temperature (C); 20 C is assumed, and reported as assumed, without it",
    )
    parser.add_argument(
        "--profile",
        default="generic",
        choices=available_profiles(),
        help="recording profile that shapes the interpretation (default generic)",
    )


def _add_loopback_file_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--loopback",
        type=Path,
        default=None,
        help="separate loopback WAV from the same take (same sample rate)",
    )
    parser.add_argument(
        "--loopback-channel",
        type=int,
        default=None,
        help="0-based loopback channel of the recording (or of --loopback if it is multi-channel)",
    )


def _analysis_settings(
    args: argparse.Namespace, *, loopback_channel: int | None = None
) -> AnalysisSettings:
    channel = getattr(args, "loopback_channel", None)
    return AnalysisSettings(
        channel=args.channel,
        fr_smoothing_fraction=args.smoothing,
        placement_distance_m=args.speaker_distance,
        placement_mic_height_m=args.mic_height,
        placement_temperature_c=args.temperature,
        loopback_channel=loopback_channel if loopback_channel is not None else channel,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="roomscope",
        description="RoomScope: an open-source, DAW-independent recording environment analyzer.",
    )
    parser.add_argument("--version", action="version", version=f"roomscope {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    parser.add_argument(
        "--backend",
        default=None,
        help="audio backend for Standalone Mode: portaudio (default) or fake",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_sweep = sub.add_parser("sweep", help="write the ESS test signal WAV (+ JSON sidecar)")
    p_sweep.add_argument("--out", required=True, type=Path, help="output WAV path")
    _add_sweep_arguments(p_sweep, default_level=-12.0)

    p_an = sub.add_parser("analyze", help="analyse a recording made with the sweep")
    p_an.add_argument(
        "--recording", required=True, type=Path, help="recorded WAV (any length, untrimmed)"
    )
    p_an.add_argument(
        "--sweep", required=True, type=Path, help="sweep WAV or its .roomscope-sweep.json sidecar"
    )
    p_an.add_argument(
        "--out", type=Path, default=None, help="directory for session.json, result.json, IR WAV"
    )
    _add_analysis_arguments(p_an)
    _add_loopback_file_arguments(p_an)

    sub.add_parser("devices", help="list audio devices (Standalone Mode)")

    p_me = sub.add_parser(
        "measure", help="Standalone Mode: play the sweep and record the microphone"
    )
    p_me.add_argument("--out", required=True, type=Path, help="session directory (created)")
    p_me.add_argument(
        "--input-device", type=int, default=None, help="input device index (see 'devices')"
    )
    p_me.add_argument("--output-device", type=int, default=None, help="output device index")
    p_me.add_argument(
        "--input-channel", type=int, default=1, help="input channel, 1-based (default 1)"
    )
    p_me.add_argument(
        "--input-channels",
        default=None,
        help="1-based input channels, comma-separated (e.g. 1,2); overrides --input-channel",
    )
    p_me.add_argument(
        "--output-channel", type=int, default=1, help="output channel, 1-based (default 1)"
    )
    p_me.add_argument(
        "--loopback-channel",
        type=int,
        default=None,
        dest="measure_loopback_channel",
        help="1-based loopback input channel (recorded with the microphone)",
    )
    p_me.add_argument(
        "--acknowledge-level",
        action="store_true",
        help="required for levels above -12 dBFS; confirms the monitor level was set low first",
    )
    _add_sweep_arguments(p_me, default_level=-20.0)
    _add_analysis_arguments(p_me)

    p_show = sub.add_parser(
        "show", help="print a saved session report, or list sessions in a folder"
    )
    p_show.add_argument(
        "path", type=Path, help="session directory, session.json, or folder to list"
    )
    p_show.add_argument(
        "--list",
        action="store_true",
        help="list session.json files under path instead of opening one session",
    )
    p_show.add_argument(
        "--profile",
        default=None,
        choices=available_profiles(),
        help="override the recording profile stored in the session",
    )
    p_show.add_argument(
        "--json", action="store_true", help="print the result as JSON instead of a report"
    )
    p_show.add_argument("--no-curves", action="store_true", help="omit curves from JSON output")

    p_cmp = sub.add_parser("compare", help="compare two saved sessions")
    p_cmp.add_argument("baseline", type=Path, help="baseline session directory or session.json")
    p_cmp.add_argument("candidate", type=Path, help="candidate session directory or session.json")
    p_cmp.add_argument(
        "--out",
        type=Path,
        default=None,
        help="write comparison.json here (file or directory)",
    )
    p_cmp.add_argument(
        "--same-input-gain",
        action="store_true",
        help="declare that the input gain was unchanged (required for a VALID noise delta)",
    )
    p_cmp.add_argument(
        "--profile",
        default=None,
        choices=available_profiles(),
        help="recording profile for comparison findings (default: the candidate session's)",
    )
    p_cmp.add_argument(
        "--json", action="store_true", help="print comparison.json instead of a report"
    )

    p_schema = sub.add_parser("schema", help="print a shipped JSON Schema")
    p_schema.add_argument(
        "name",
        choices=["result", "session", "comparison", "project", "sidecar"],
        help="which schema to print",
    )

    p_ir = sub.add_parser("analyze-ir", help="analyse an impulse-response WAV from another tool")
    p_ir.add_argument("--ir", required=True, type=Path, help="impulse-response WAV")
    p_ir.add_argument(
        "--band",
        nargs=2,
        type=float,
        metavar=("LO", "HI"),
        default=None,
        help="declared excitation band in Hz (required for band metrics)",
    )
    p_ir.add_argument("--out", type=Path, default=None, help="session directory")
    _add_analysis_arguments(p_ir)

    sub.add_parser("gui", help="start the desktop GUI (needs the 'gui' extra)")
    return parser


def cmd_sweep(args: argparse.Namespace) -> int:
    from roomscope.io.wav import write_sweep_file

    settings = _sweep_settings(args)
    wav_path, sidecar = write_sweep_file(settings, args.out)
    print(
        f"Wrote {wav_path} ({settings.total_samples / settings.sample_rate:.1f} s at {settings.sample_rate} Hz, "
        f"sweep {settings.start_hz:g}-{settings.end_hz:g} Hz, {settings.duration_s:g} s, {settings.level_dbfs:g} dBFS)"
    )
    print(f"Wrote {sidecar} (keep it next to the WAV)")
    print(
        "Next: import the WAV into your DAW, play it through the monitors, record the measurement microphone,"
    )
    print(
        "export the recording as WAV and run: roomscope analyze --recording <file> --sweep "
        + str(wav_path)
    )
    return 0


def _run_analysis(
    recording_path: Path,
    reference_path: Path | None,
    args: argparse.Namespace,
    *,
    sweep_settings: SweepSettings | None = None,
    mode: str = "universal_daw",
    out_dir: Path | None = None,
) -> int:
    from roomscope.core.pipeline import Reference, analyze
    from roomscope.interpretation import interpret
    from roomscope.io.recent import remember_session
    from roomscope.io.session_store import save_measurement
    from roomscope.io.wav import load_reference, read_wav
    from roomscope.models.session import MeasurementSession

    recording = read_wav(recording_path)
    if sweep_settings is not None:
        reference = Reference.from_settings(sweep_settings)
    else:
        assert reference_path is not None
        reference = load_reference(reference_path)
    settings = _analysis_settings(args)
    loopback_signal = None
    if getattr(args, "loopback", None) is not None:
        loopback_signal = read_wav(args.loopback)
    result = analyze(recording, reference, settings, loopback=loopback_signal)
    findings = interpret(result, args.profile)

    if out_dir is not None:
        session = MeasurementSession(
            mode=mode,
            room_name=args.room,
            measurement_position=args.position,
            microphone_name=args.mic,
            notes=args.notes,
            sweep_settings=reference.settings or SweepSettings(sample_rate=recording.sample_rate),
            analysis_settings=settings,
            sweep_path=str(reference_path) if reference_path else None,
            recording_path=str(recording_path),
            input_channel=result.analysis_settings.get("channel_analysed"),
            loopback_channel=settings.loopback_channel,
            recording_profile=args.profile,
        )
        session_path = save_measurement(out_dir, session, result, include_curves=not args.no_curves)
        remember_session(out_dir)
        log.info("session saved to %s", session_path)

    if args.json:
        payload = result.to_dict(include_curves=not args.no_curves)
        payload["findings"] = [f.to_dict() for f in findings]
        print(json.dumps(payload, indent=1))
    else:
        print(format_report(result, findings, args.profile))
        if out_dir is not None:
            print(f"\nSaved session to {out_dir}")
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    return _run_analysis(args.recording, args.sweep, args, out_dir=args.out)


def cmd_devices(args: argparse.Namespace) -> int:
    from roomscope.audio.backend import get_backend

    devices = get_backend(args.backend).list_devices()
    print(f"{'idx':>3}  {'in':>3} {'out':>3}  {'rate':>7}  name  [host API]")
    for d in devices:
        flags = ("*in" if d.is_default_input else "") + ("*out" if d.is_default_output else "")
        print(
            f"{d.index:>3}  {d.max_input_channels:>3} {d.max_output_channels:>3}  {d.default_sample_rate:7.0f}  "
            f"{d.name}  [{d.host_api}] {flags}"
        )
    return 0


def cmd_measure(args: argparse.Namespace) -> int:
    from roomscope.audio.backend import SAFE_MAX_LEVEL_DBFS, SAFETY_MESSAGE, get_backend
    from roomscope.core.sweep import measurement_signal
    from roomscope.io.wav import write_sweep_file, write_wav

    settings = _sweep_settings(args)
    if settings.level_dbfs > SAFE_MAX_LEVEL_DBFS and not args.acknowledge_level:
        print(
            f"Level {settings.level_dbfs:g} dBFS is above {SAFE_MAX_LEVEL_DBFS:g} dBFS. "
            "Set the monitor level low first and pass --acknowledge-level to confirm.",
            file=sys.stderr,
        )
        return 2
    backend = get_backend(args.backend)
    print(SAFETY_MESSAGE)
    if args.input_device is not None:
        backend.check_sample_rate(args.input_device, settings.sample_rate, kind="input")
    if args.output_device is not None:
        backend.check_sample_rate(args.output_device, settings.sample_rate, kind="output")
    if args.input_channels:
        channels = [
            int(part.strip()) for part in str(args.input_channels).split(",") if part.strip()
        ]
    else:
        channels = [int(args.input_channel)]
    hardware_loopback = getattr(args, "measure_loopback_channel", None)
    if hardware_loopback is not None and hardware_loopback not in channels:
        channels.append(hardware_loopback)
    analysis_loopback = None if hardware_loopback is None else channels.index(hardware_loopback)
    # so _analysis_settings does not read a missing 0-based flag
    args.loopback_channel = analysis_loopback
    args.channel = (
        0 if hardware_loopback is None else (0 if channels[0] != hardware_loopback else 1)
    )
    if args.channel >= len(channels):
        args.channel = 0
    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    sweep_path, _ = write_sweep_file(settings, out_dir / "sweep.wav")
    print(
        f"Playing sweep on output channel {args.output_channel}, recording input "
        f"channel(s) {','.join(str(c) for c in channels)} via {backend.name} ..."
    )
    fractions: list[float] = []

    def _progress(fraction: float) -> None:
        fractions.append(fraction)
        if len(fractions) == 1 or fraction >= 1.0 or len(fractions) % 8 == 0:
            print(f"  {fraction * 100.0:5.1f} %", file=sys.stderr)

    recording = backend.play_and_record(
        measurement_signal(settings),
        settings.sample_rate,
        input_device=args.input_device,
        output_device=args.output_device,
        input_channels=channels,
        output_channel=args.output_channel,
        level_dbfs=settings.level_dbfs,
        progress=_progress,
    )
    recording_path = write_wav(
        out_dir / "recording.wav", recording.samples, settings.sample_rate, subtype="FLOAT"
    )
    print(f"Recorded {recording.duration_s:.1f} s to {recording_path}")
    return _run_analysis(
        recording_path,
        sweep_path,
        args,
        sweep_settings=settings,
        mode="standalone",
        out_dir=out_dir,
    )


def cmd_show(args: argparse.Namespace) -> int:
    from roomscope.interpretation import interpret
    from roomscope.io.session_store import list_sessions, load_measurement

    if args.list:
        listings = list_sessions(args.path)
        if not listings:
            print(f"No session.json files under {args.path}")
            return 0
        for item in listings:
            print(f"{item.path}\t{item.label}")
        return 0

    loaded = load_measurement(args.path)
    profile = args.profile or loaded.session.recording_profile or "generic"
    if profile not in available_profiles():
        profile = "generic"
    findings = interpret(loaded.result, profile)
    if args.json:
        payload = loaded.result.to_dict(include_curves=not args.no_curves)
        payload["findings"] = [f.to_dict() for f in findings]
        payload["session"] = loaded.session.to_dict()
        print(json.dumps(payload, indent=1))
    else:
        print(format_report(loaded.result, findings, profile))
        print(f"\nSession: {loaded.directory}")
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    from dataclasses import replace

    from roomscope.core.compare import compare
    from roomscope.interpretation import interpret_comparison
    from roomscope.io.session_store import load_measurement, save_comparison
    from roomscope.models.comparison import CompareSettings

    baseline = load_measurement(args.baseline)
    candidate = load_measurement(args.candidate)
    settings = CompareSettings(same_input_gain=args.same_input_gain)
    comparison = replace(
        compare(baseline.result, candidate.result, settings=settings),
        baseline_session=str(baseline.directory),
        candidate_session=str(candidate.directory),
    )
    profile = args.profile or candidate.session.recording_profile or "generic"
    if profile not in available_profiles():
        profile = "generic"
    findings = interpret_comparison(comparison, profile)
    if args.out is not None:
        save_comparison(args.out, comparison)
    if args.json:
        payload = comparison.to_dict()
        payload["findings"] = [f.to_dict() for f in findings]
        print(json.dumps(payload, indent=1))
    else:
        print(format_comparison_report(comparison, findings, profile))
        if args.out is not None:
            print(f"\nWrote comparison to {args.out}")
    return 0


def cmd_schema(args: argparse.Namespace) -> int:
    from roomscope.schemas import schema_text

    sys.stdout.write(schema_text(args.name))
    return 0


def cmd_analyze_ir(args: argparse.Namespace) -> int:
    from roomscope.core.pipeline import analyze_impulse_response
    from roomscope.interpretation import interpret
    from roomscope.io.recent import remember_session
    from roomscope.io.session_store import save_measurement
    from roomscope.io.wav import read_wav
    from roomscope.models.session import MeasurementSession

    ir = read_wav(args.ir)
    settings = _analysis_settings(args)
    band = (float(args.band[0]), float(args.band[1])) if args.band else None
    result = analyze_impulse_response(ir, settings, excitation_band=band)
    findings = interpret(result, args.profile)
    if args.out is not None:
        session = MeasurementSession(
            mode="analyze_ir",
            room_name=args.room,
            measurement_position=args.position,
            microphone_name=args.mic,
            notes=args.notes,
            analysis_settings=settings,
            recording_path=str(args.ir),
            recording_profile=args.profile,
        )
        save_measurement(args.out, session, result, include_curves=not args.no_curves)
        remember_session(args.out)
    if args.json:
        payload = result.to_dict(include_curves=not args.no_curves)
        payload["findings"] = [f.to_dict() for f in findings]
        print(json.dumps(payload, indent=1))
    else:
        print(format_report(result, findings, args.profile))
        if args.out is not None:
            print(f"\nSaved session to {args.out}")
    return 0


def cmd_gui(_: argparse.Namespace) -> int:
    try:
        from roomscope.ui.app import run_app
    except ImportError as exc:
        print(
            f"The GUI needs PySide6 Essentials: pip install 'roomscope[gui]' ({exc})",
            file=sys.stderr,
        )
        return 2
    return int(run_app())


COMMANDS = {
    "sweep": cmd_sweep,
    "analyze": cmd_analyze,
    "analyze-ir": cmd_analyze_ir,
    "show": cmd_show,
    "compare": cmd_compare,
    "schema": cmd_schema,
    "devices": cmd_devices,
    "measure": cmd_measure,
    "gui": cmd_gui,
}


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(logging.DEBUG if args.verbose else logging.WARNING)
    try:
        return COMMANDS[args.command](args)
    except MeasurementCancelledError as exc:
        print(f"stopped: {exc}", file=sys.stderr)
        return 130
    except RoomScopeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
