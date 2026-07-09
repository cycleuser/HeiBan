"""Measurement converters for OOXML units.

OOXML uses:
- EMU (English Metric Units) for DrawingML: 1 cm = 360000 EMU, 1 inch = 914400 EMU
- Twips for WordprocessingML: 1 cm = 567 twips, 1 inch = 1440 twips
- Points for font sizes: 1 pt = 12700 EMU
"""

# EMU constants
EMU_PER_MM = 36000
EMU_PER_CM = 360000
EMU_PER_INCH = 914400
EMU_PER_PT = 12700
EMU_PER_PX = 9525  # approximate, assuming 96 DPI

# Twip constants
TWIP_PER_MM = 56.7
TWIP_PER_CM = 567
TWIP_PER_INCH = 1440
TWIP_PER_PT = 20


# --- EMU conversions ---

def cm_to_emu(cm: float) -> int:
    return round(cm * EMU_PER_CM)


def mm_to_emu(mm: float) -> int:
    return round(mm * EMU_PER_MM)


def inches_to_emu(inches: float) -> int:
    return round(inches * EMU_PER_INCH)


def pt_to_emu(pt: float) -> int:
    return round(pt * EMU_PER_PT)


def px_to_emu(px: float) -> int:
    """Approximate EMU from pixels (96 DPI)."""
    return round(px * EMU_PER_PX)


def emu_to_cm(emu: int) -> float:
    return emu / EMU_PER_CM


def emu_to_inches(emu: int) -> float:
    return emu / EMU_PER_INCH


def emu_to_pt(emu: int) -> float:
    return emu / EMU_PER_PT


# --- Twip conversions ---

def cm_to_twip(cm: float) -> int:
    return round(cm * TWIP_PER_CM)


def mm_to_twip(mm: float) -> int:
    return round(mm * TWIP_PER_MM)


def inches_to_twip(inches: float) -> int:
    return round(inches * TWIP_PER_INCH)


def pt_to_twip(pt: float) -> int:
    return round(pt * TWIP_PER_PT)


def twip_to_cm(twip: int) -> float:
    return twip / TWIP_PER_CM


def twip_to_pt(twip: int) -> float:
    return twip / TWIP_PER_PT


# --- Utility ---

def parse_measure(value: str) -> int:
    """Parse a measurement string like '2cm', '1in', '12pt', '100px' into EMU.

    Falls back to treating bare numbers as pixels.
    """
    value = value.strip().lower()
    if value.endswith("cm"):
        return cm_to_emu(float(value[:-2]))
    if value.endswith("mm"):
        return mm_to_emu(float(value[:-2]))
    if value.endswith("in"):
        return inches_to_emu(float(value[:-2]))
    if value.endswith("pt"):
        return pt_to_emu(float(value[:-2]))
    if value.endswith("px"):
        return px_to_emu(float(value[:-2]))
    # bare number → px
    try:
        return px_to_emu(float(value))
    except ValueError:
        raise ValueError(f"Cannot parse measurement: {value!r}")
