"""gettext setup, locale selection and ``_()``.

Catalogs live in ``src/roomscope/locale/<lang>/LC_MESSAGES/roomscope.po``.
``.mo`` files are produced by the Hatch build hook and are not committed.
English is the source language and needs no catalog.

Selection order (ARCHITECTURE_V1.md §5.6): ``--lang``, ``settings.language``,
``ROOMSCOPE_LANG``, the system locale; English when nothing matches.
"""

from __future__ import annotations

import gettext
import locale as py_locale
import os
from pathlib import Path
from typing import Any

DOMAIN = "roomscope"
ENV_LANG = "ROOMSCOPE_LANG"
DEFAULT_LANG = "en"

_LOCALE_DIR = Path(__file__).resolve().parent / "locale"
_current = DEFAULT_LANG
_translation: gettext.NullTranslations = gettext.NullTranslations()


def locale_dir() -> Path:
    return _LOCALE_DIR


def current_locale() -> str:
    return _current


def available_locales() -> list[str]:
    """Locales that have a catalog, plus English (the source language)."""
    found = {DEFAULT_LANG}
    if _LOCALE_DIR.is_dir():
        for child in _LOCALE_DIR.iterdir():
            messages = child / "LC_MESSAGES"
            if (messages / f"{DOMAIN}.mo").is_file() or (messages / f"{DOMAIN}.po").is_file():
                found.add(child.name)
    return sorted(found)


def normalize_lang(tag: str | None) -> str:
    """Map a BCP-47 / locale tag onto a catalog directory name."""
    if not tag:
        return DEFAULT_LANG
    raw = tag.strip().replace("-", "_")
    if not raw:
        return DEFAULT_LANG
    lower = raw.lower()
    if lower in {"c", "posix"}:
        return DEFAULT_LANG
    if lower in {"zh", "zh_cn", "zh_hans", "zh_sg", "zh_chs"}:
        return "zh_CN"
    if "_" in raw:
        lang, _, region = raw.partition("_")
        return f"{lang.lower()}_{region.upper()}" if region else lang.lower()
    return raw.lower()


def resolve_language(explicit: str | None = None) -> str:
    """Pick a language without activating it."""
    if explicit:
        return normalize_lang(explicit)
    try:
        from roomscope.settings import load_settings

        configured = load_settings().language
    except Exception:
        configured = ""
    if configured:
        return normalize_lang(configured)
    env = os.environ.get(ENV_LANG)
    if env:
        return normalize_lang(env)
    return _system_language()


def activate(lang: str | None = None) -> str:
    """Install the catalog for ``lang`` (resolved if omitted) and return it.

    ``lang is None`` follows the selection order. Pass ``"en"`` to force English.
    """
    global _current, _translation
    chosen = resolve_language(None) if lang is None else normalize_lang(lang)
    loaded = _load_translation(chosen)
    if chosen != DEFAULT_LANG and _is_null(loaded):
        chosen = DEFAULT_LANG
        loaded = gettext.NullTranslations()
    _translation = loaded
    _current = chosen
    return _current


def _(message: str) -> str:
    """Translate ``message``. Named placeholders are expanded by the caller."""
    return _translation.gettext(message)


def ngettext(singular: str, plural: str, n: int) -> str:
    return _translation.ngettext(singular, plural, n)


def format_message(template: str, **params: Any) -> str:
    """gettext + ``str.format`` with ASCII digits (never locale-aware numbers)."""
    return _(template).format(**params)


def parse_po(path: Path) -> dict[str, str]:
    """Parse a gettext ``.po`` file into msgid → msgstr (empty msgstr skipped)."""
    catalog: dict[str, str] = {}
    msgid = ""
    msgstr = ""
    collecting: str | None = None

    def _commit() -> None:
        nonlocal msgid, msgstr
        if msgid and msgstr:
            catalog[msgid] = msgstr
        msgid = ""
        msgstr = ""

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("msgid "):
            _commit()
            collecting = "id"
            msgid = _unquote(line[6:])
            msgstr = ""
            continue
        if line.startswith("msgstr "):
            collecting = "str"
            msgstr = _unquote(line[7:])
            continue
        if line.startswith('"') and collecting == "id":
            msgid += _unquote(line)
        elif line.startswith('"') and collecting == "str":
            msgstr += _unquote(line)
    _commit()
    catalog.pop("", None)
    return catalog


def write_mo(catalog: dict[str, str], path: Path) -> None:
    """Write a GNU ``.mo`` file that :class:`gettext.GNUTranslations` can read."""
    # Header (required by gettext)
    entries = {"": "Content-Type: text/plain; charset=UTF-8\n", **catalog}
    keys = sorted(entries)
    encoded = [(key.encode("utf-8"), entries[key].encode("utf-8")) for key in keys]
    key_start = 28 + 16 * len(encoded)
    value_start = key_start + sum(len(k) + 1 for k, _ in encoded)
    key_offsets: list[tuple[int, int]] = []
    value_offsets: list[tuple[int, int]] = []
    offset = key_start
    for key, _ in encoded:
        key_offsets.append((len(key), offset))
        offset += len(key) + 1
    offset = value_start
    for _, value in encoded:
        value_offsets.append((len(value), offset))
        offset += len(value) + 1
    import struct

    count = len(encoded)
    buf = bytearray()
    buf += struct.pack("<Iiiiiii", 0x950412DE, 0, count, 28, 28 + 8 * count, 0, 0)
    for length, off in key_offsets:
        buf += struct.pack("<II", length, off)
    for length, off in value_offsets:
        buf += struct.pack("<II", length, off)
    for key, _ in encoded:
        buf += key + b"\x00"
    for _, value in encoded:
        buf += value + b"\x00"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(buf))


def compile_catalogs(root: Path | None = None) -> list[Path]:
    """Compile every ``roomscope.po`` under ``root`` to ``roomscope.mo``."""
    base = root or _LOCALE_DIR
    written: list[Path] = []
    if not base.is_dir():
        return written
    for po in base.glob(f"*/LC_MESSAGES/{DOMAIN}.po"):
        catalog = parse_po(po)
        mo = po.with_suffix(".mo")
        write_mo(catalog, mo)
        written.append(mo)
    return written


def _system_language() -> str:
    for candidate in (
        os.environ.get("LC_ALL"),
        os.environ.get("LC_MESSAGES"),
        os.environ.get("LANG"),
    ):
        if candidate:
            tag = candidate.split(".", 1)[0]
            if tag:
                return normalize_lang(tag)
    try:
        detected = py_locale.getlocale()[0]
    except (ValueError, TypeError):
        detected = None
    if detected:
        return normalize_lang(detected)
    return DEFAULT_LANG


def _load_translation(lang: str) -> gettext.NullTranslations:
    if lang == DEFAULT_LANG:
        return gettext.NullTranslations()
    messages = _LOCALE_DIR / lang / "LC_MESSAGES"
    mo = messages / f"{DOMAIN}.mo"
    po = messages / f"{DOMAIN}.po"
    if not mo.is_file() and po.is_file():
        try:
            write_mo(parse_po(po), mo)
        except OSError:
            return _PoTranslations(parse_po(po))
    if mo.is_file():
        with mo.open("rb") as handle:
            return gettext.GNUTranslations(handle)
    if po.is_file():
        return _PoTranslations(parse_po(po))
    return gettext.NullTranslations()


def _is_null(translation: gettext.NullTranslations) -> bool:
    return translation.__class__ is gettext.NullTranslations


def _unquote(fragment: str) -> str:
    text = fragment.strip()
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    return (
        text.replace(r"\n", "\n")
        .replace(r"\t", "\t")
        .replace(r"\"", '"')
        .replace(r"\\", "\\")
    )


class _PoTranslations(gettext.NullTranslations):
    """In-memory catalog used when a ``.mo`` cannot be written."""

    def __init__(self, catalog: dict[str, str]) -> None:
        super().__init__()
        self._catalog = catalog

    def gettext(self, message: str) -> str:
        return self._catalog.get(message, message)

    def ngettext(self, msgid1: str, msgid2: str, n: int) -> str:
        return self.gettext(msgid1 if n == 1 else msgid2)
