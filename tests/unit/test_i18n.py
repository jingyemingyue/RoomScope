from __future__ import annotations

from roomscope.core.pipeline import Reference, analyze, synthetic_recording
from roomscope.i18n import (
    _,
    activate,
    available_locales,
    current_locale,
    format_message,
    normalize_lang,
    parse_po,
)
from roomscope.interpretation import interpret
from roomscope.models.configuration import SweepSettings
from tests.conftest import make_rir


def test_normalize_and_available_locales() -> None:
    assert normalize_lang("zh-CN") == "zh_CN"
    assert normalize_lang("zh") == "zh_CN"
    assert "en" in available_locales()
    assert "zh_CN" in available_locales()


def test_english_is_source_and_chinese_translates_findings(
    short_sweep: SweepSettings,
) -> None:
    activate("en")
    assert current_locale() == "en"
    assert _("RoomScope analysis") == "RoomScope analysis"
    ir = make_rir(short_sweep.sample_rate, rt60_s=0.35, reflections=[(0.018, 0.4)])
    rec = synthetic_recording(short_sweep, ir, noise_rms=2e-5)
    result = analyze(rec, Reference.from_settings(short_sweep))
    english = interpret(result, "generic")
    assert english
    assert all(item.locale == "en" for item in english)
    activate("zh_CN")
    assert current_locale() == "zh_CN"
    assert _("RoomScope analysis") == "RoomScope 分析"
    chinese = interpret(result, "generic")
    assert chinese
    assert all(item.locale == "zh_CN" for item in chinese)
    assert any(any("\u4e00" <= ch <= "\u9fff" for ch in item.message) for item in chinese)
    activate("en")


def test_numbers_stay_ascii() -> None:
    activate("zh_CN")
    text = format_message("Sample rate: {rate} Hz    created: {created}", rate=48000, created="t")
    assert "48000" in text
    assert "." in format_message(
        "The broadband decay is short (estimated RT60 {rt:.2f} s). "
        "This is typical of a treated or small, well-damped room.",
        rt=0.45,
    )
    activate("en")


def test_daw_chrome_is_in_the_chinese_catalog() -> None:
    activate("zh_CN")
    assert _("Analyze") == "分析"
    assert _("Step 1 - Generate Test Signal").startswith("步骤")
    activate("en")


def test_cli_help_and_report_labels_are_in_the_chinese_catalog() -> None:
    activate("zh_CN")
    assert _("write the ESS test signal WAV (+ JSON sidecar)").startswith("写出")
    assert _(
        "Reverberation (extrapolated to 60 dB; 'insuff.' = insufficient decay range)"
    ).startswith("混响")
    assert _("Comparable: {value}").startswith("可对比")
    activate("en")


def test_parse_po_round_trip(tmp_path) -> None:
    import gettext

    from roomscope.i18n import write_mo

    po = tmp_path / "roomscope.po"
    po.write_text('msgid "Hello"\nmsgstr "你好"\n', encoding="utf-8")
    catalog = parse_po(po)
    assert catalog["Hello"] == "你好"
    mo = tmp_path / "roomscope.mo"
    write_mo(catalog, mo)
    with mo.open("rb") as handle:
        trans = gettext.GNUTranslations(handle)
    assert trans.gettext("Hello") == "你好"
