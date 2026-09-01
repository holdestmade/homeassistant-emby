"""Tests for translation completeness.

Home Assistant serves `translations/en.json` at runtime; `strings.json` is
the source file the translation pipeline reads. When a new option is added
to `strings.json` but not to `en.json`, the config flow falls back to
showing the raw option key - which is how `library_scan_interval` and
`server_scan_interval` came to be displayed as-is in the options dialog.

English is always loaded as the fallback for other languages, so a complete
`en.json` is what keeps every locale readable. Missing keys in other
languages are therefore fine; keys that no longer exist are not, since they
are dead weight that outlives the option they described.
"""

from __future__ import annotations

import json
import pathlib

import pytest

COMPONENT = pathlib.Path(__file__).parent.parent / "custom_components" / "embymedia"
STRINGS = COMPONENT / "strings.json"
TRANSLATIONS = COMPONENT / "translations"


def _flatten(obj: object, path: str = "") -> dict[str, object]:
    """Flatten nested translation dicts into dotted keys."""
    flat: dict[str, object] = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            flat.update(_flatten(value, f"{path}.{key}"))
    else:
        flat[path] = obj
    return flat


def _load(path: pathlib.Path) -> dict[str, object]:
    """Load and flatten a translation file."""
    return _flatten(json.loads(path.read_text(encoding="utf-8")))


def _translation_files() -> list[pathlib.Path]:
    """Return every shipped translation file."""
    return sorted(TRANSLATIONS.glob("*.json"))


class TestEnglishIsComplete:
    """en.json must cover strings.json: it is every locale's fallback."""

    def test_no_key_missing_from_english(self) -> None:
        """Every string offered in the UI has an English translation."""
        expected = _load(STRINGS)
        english = _load(TRANSLATIONS / "en.json")

        missing = sorted(set(expected) - set(english))

        assert missing == [], (
            "translations/en.json is missing keys defined in strings.json. "
            "Home Assistant serves en.json, so these render as raw option "
            f"keys in the UI: {missing}"
        )


class TestNoStaleTranslations:
    """No translation may describe an option that no longer exists."""

    @pytest.mark.parametrize("translation", _translation_files(), ids=lambda p: p.name)
    def test_no_keys_beyond_strings(self, translation: pathlib.Path) -> None:
        """Translations do not outlive the strings they translate."""
        expected = _load(STRINGS)
        actual = _load(translation)

        stale = sorted(set(actual) - set(expected))

        assert stale == [], (
            f"{translation.name} defines keys that no longer exist in strings.json: {stale}"
        )


class TestOptionsFlowFieldsAreLabelled:
    """Every field the options flow shows has a label."""

    def test_scan_interval_fields_are_labelled(self) -> None:
        """The polling interval options are named, not shown as raw keys."""
        english = _load(TRANSLATIONS / "en.json")

        for option in ("library_scan_interval", "server_scan_interval"):
            label = english.get(f".options.step.init.data.{option}")
            assert isinstance(label, str) and label
            # A label that merely repeats the key is no label at all
            assert label != option

    def test_all_option_keys_are_labelled(self) -> None:
        """No option in the schema renders as its raw key.

        Guards every option, so a newly added one cannot ship unlabelled.
        """
        import re

        source = (COMPONENT / "config_flow.py").read_text(encoding="utf-8")
        const = (COMPONENT / "const.py").read_text(encoding="utf-8")

        english = _load(TRANSLATIONS / "en.json")
        labelled = {
            key.rsplit(".", 1)[-1] for key in english if key.startswith(".options.step.init.data.")
        }

        options_flow = source[source.index("class EmbyOptionsFlow") :]
        unlabelled = []
        for name in sorted(set(re.findall(r"vol\.Optional\(\s*(CONF_[A-Z_]+)", options_flow))):
            match = re.search(rf'^{name}: Final = "([^"]+)"', const, re.M)
            if match and match.group(1) not in labelled:
                unlabelled.append(match.group(1))

        assert unlabelled == [], f"options flow fields without a label in en.json: {unlabelled}"
