"""
Genus-to-icon mapping for the species leaf icons on the Mapbox tree layer.

Icon names correspond 1:1 to PNG filenames in giessdenkiez-de/public/images/leafs/.
Matching is done by substring (case-insensitive, ß-normalised) so both Berlin-style
uppercase names ("AHORN") and Bonn-style compound names ("Spitz-Ahorn") resolve
to the same icon.

List is sorted longest-first so ROSSKASTANIE always wins over a hypothetical shorter
match, and WEIßDORN (normalised to WEISSDORN) wins over DORN.
"""

GENUS_ICONS = [
    "ROSSKASTANIE",
    "HAINBUCHE",
    "MEHLBEERE",
    "WEIßDORN",
    "PLATANE",
    "ROBINIE",
    "PAPPEL",
    "AHORN",
    "BIRKE",
    "BUCHE",
    "EICHE",
    "ERLE",
    "ESCHE",
    "HASEL",
    "KIEFER",
    "LINDE",
    "ULME",
    "WEIDE",
    "APFEL",
]


def _normalise(s: str) -> str:
    """Uppercase and replace ß with SS so comparisons are ß-safe.

    Python's str.upper() converts ß → SS (two chars), which means
    "Weißdorn".upper() == "WEISSDORN" but "WEIßDORN" still contains ß.
    Normalising both sides ensures consistent matching.
    """
    return s.upper().replace("ß", "SS")


# Pre-normalise icon keys once at import time.
_NORMALISED_ICONS = [(_normalise(icon), icon) for icon in GENUS_ICONS]


def get_genus_icon(gattung_deutsch: str | None) -> str:
    """Return the icon name for a given German genus/species string.

    Returns "UNBEKANNT" when the input is falsy or no icon key matches.
    """
    if not gattung_deutsch:
        return "UNBEKANNT"
    upper = _normalise(gattung_deutsch)
    for normalised, original in _NORMALISED_ICONS:
        if normalised in upper:
            return original
    return "UNBEKANNT"
