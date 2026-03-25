"""
Tests for genus_icon.get_genus_icon().

Run from the harvester/src/ directory so the import resolves:

    cd harvester/src
    python -m pytest ../tests/test_genus_icon.py -v

Or from the repo root with PYTHONPATH set:

    PYTHONPATH=harvester/src pytest harvester/tests/test_genus_icon.py -v
"""
import sys
import os

# Ensure harvester/src is on the path so `from genus_icon import ...` resolves.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from genus_icon import get_genus_icon, GENUS_ICONS


class TestGetGenusIconFallback:
    def test_none_returns_UNBEKANNT(self):
        assert get_genus_icon(None) == "UNBEKANNT"

    def test_empty_string_returns_UNBEKANNT(self):
        assert get_genus_icon("") == "UNBEKANNT"

    def test_unknown_species_returns_UNBEKANNT(self):
        assert get_genus_icon("Ginkgo") == "UNBEKANNT"

    def test_whitespace_only_returns_UNBEKANNT(self):
        assert get_genus_icon("   ") == "UNBEKANNT"


class TestGetGenusIconExactMatch:
    """Berlin-style uppercase genus names should match directly."""

    def test_AHORN(self):
        assert get_genus_icon("AHORN") == "AHORN"

    def test_LINDE(self):
        assert get_genus_icon("LINDE") == "LINDE"

    def test_EICHE(self):
        assert get_genus_icon("EICHE") == "EICHE"

    def test_ROSSKASTANIE(self):
        assert get_genus_icon("ROSSKASTANIE") == "ROSSKASTANIE"

    def test_all_known_icons_match_themselves(self):
        for icon in GENUS_ICONS:
            result = get_genus_icon(icon)
            assert result == icon, f"Expected {icon!r} to match itself, got {result!r}"


class TestGetGenusIconSubstringMatch:
    """Bonn-style compound names ('Spitz-Ahorn') should match via substring."""

    def test_spitz_ahorn(self):
        assert get_genus_icon("Spitz-Ahorn") == "AHORN"

    def test_winter_linde(self):
        assert get_genus_icon("Winter-Linde") == "LINDE"

    def test_stiel_eiche(self):
        assert get_genus_icon("Stiel-Eiche") == "EICHE"

    def test_gemeine_birke(self):
        assert get_genus_icon("Gemeine Birke") == "BIRKE"

    def test_gemeine_esche(self):
        assert get_genus_icon("Gemeine Esche") == "ESCHE"

    def test_hänge_birke(self):
        assert get_genus_icon("Hänge-Birke") == "BIRKE"


class TestGetGenusIconCaseInsensitive:
    """Matching must be case-insensitive."""

    def test_lowercase(self):
        assert get_genus_icon("ahorn") == "AHORN"

    def test_mixed_case(self):
        assert get_genus_icon("Ahorn") == "AHORN"

    def test_linde_lowercase(self):
        assert get_genus_icon("linde") == "LINDE"


class TestGetGenusIconEsszett:
    """ß must be matched correctly regardless of normalisation."""

    def test_weissdorn_with_eszett_lowercase(self):
        # "Weißdorn".upper() → "WEISSDORN" in Python (ß → SS)
        # get_genus_icon must still return "WEIßDORN"
        assert get_genus_icon("Weißdorn") == "WEIßDORN"

    def test_weissdorn_with_eszett_uppercase(self):
        # "WEIßDORN".upper() → "WEISSDORN" in Python
        assert get_genus_icon("WEIßDORN") == "WEIßDORN"

    def test_weissdorn_with_ss_variant(self):
        # Some data sources write "WEISSDORN" without ß
        assert get_genus_icon("WEISSDORN") == "WEIßDORN"


class TestGetGenusIconLongestMatchFirst:
    """ROSSKASTANIE must be returned, not a shorter hypothetical match."""

    def test_rosskastanie_full(self):
        assert get_genus_icon("Rosskastanie") == "ROSSKASTANIE"

    def test_rosskastanie_compound(self):
        assert get_genus_icon("Gewöhnliche Rosskastanie") == "ROSSKASTANIE"

    def test_hainbuche_not_buche(self):
        # "HAINBUCHE" contains "BUCHE" — longest match must win.
        assert get_genus_icon("Hainbuche") == "HAINBUCHE"
