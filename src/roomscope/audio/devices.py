"""Audio device enumeration through PortAudio (``sounddevice``).

``sounddevice`` is imported lazily so that the DSP core and the Universal DAW
Mode work on systems without a usable PortAudio backend.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from roomscope.errors import AudioBackendUnavailableError, AudioDeviceError


def sounddevice_module() -> Any:
    try:
        import sounddevice
    except (ImportError, OSError) as exc:
        raise AudioBackendUnavailableError(
            "the audio backend (sounddevice / PortAudio) is not available; "
            "Standalone Mode needs it, Universal DAW Mode does not"
        ) from exc
    return sounddevice


@dataclass(frozen=True)
class DeviceInfo:
    index: int
    name: str
    host_api: str
    max_input_channels: int
    max_output_channels: int
    default_sample_rate: float
    is_default_input: bool
    is_default_output: bool

    @property
    def is_input(self) -> bool:
        return self.max_input_channels > 0

    @property
    def is_output(self) -> bool:
        return self.max_output_channels > 0


def list_devices() -> list[DeviceInfo]:
    sd = sounddevice_module()
    try:
        raw = sd.query_devices()
        host_apis = sd.query_hostapis()
        defaults = sd.default.device
    except Exception as exc:
        raise AudioDeviceError(f"cannot query audio devices: {exc}") from exc
    default_in, default_out = (
        (defaults[0], defaults[1]) if isinstance(defaults, tuple | list) else (defaults, defaults)
    )
    devices: list[DeviceInfo] = []
    for index, info in enumerate(raw):
        api_index = int(info.get("hostapi", 0))
        api_name = (
            str(host_apis[api_index]["name"]) if 0 <= api_index < len(host_apis) else "unknown"
        )
        devices.append(
            DeviceInfo(
                index=index,
                name=str(info.get("name", f"device {index}")),
                host_api=api_name,
                max_input_channels=int(info.get("max_input_channels", 0)),
                max_output_channels=int(info.get("max_output_channels", 0)),
                default_sample_rate=float(info.get("default_samplerate", 0.0)),
                is_default_input=index == default_in,
                is_default_output=index == default_out,
            )
        )
    return devices


def check_sample_rate(device_index: int, sample_rate: int, *, kind: str) -> None:
    """Raise :class:`AudioDeviceError` if the device cannot run at ``sample_rate``."""
    sd = sounddevice_module()
    try:
        if kind == "input":
            sd.check_input_settings(device=device_index, samplerate=sample_rate)
        else:
            sd.check_output_settings(device=device_index, samplerate=sample_rate)
    except Exception as exc:
        raise AudioDeviceError(
            f"{kind} device {device_index} does not support {sample_rate} Hz: {exc}"
        ) from exc
