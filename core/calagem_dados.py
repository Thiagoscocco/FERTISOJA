from __future__ import annotations

from typing import Dict, List, Optional, Tuple

# Numeric tables for soybean liming (Manual RS/SC 2016)
# All doses expressed as t/ha assuming PRNT 100%
# Strings kept ASCII-only to avoid encoding issues on Windows consoles

SMP_TABLE: List[Dict[str, float]] = [
    {"SMP_index": 4.4, "NC_t_ha_pH5_5": 15.0, "NC_t_ha_pH6_0": 21.0, "NC_t_ha_pH6_5": 29.0},
    {"SMP_index": 4.5, "NC_t_ha_pH5_5": 12.5, "NC_t_ha_pH6_0": 17.3, "NC_t_ha_pH6_5": 24.0},
    {"SMP_index": 4.6, "NC_t_ha_pH5_5": 10.9, "NC_t_ha_pH6_0": 15.1, "NC_t_ha_pH6_5": 20.0},
    {"SMP_index": 4.7, "NC_t_ha_pH5_5": 9.6,  "NC_t_ha_pH6_0": 13.3, "NC_t_ha_pH6_5": 17.5},
    {"SMP_index": 4.8, "NC_t_ha_pH5_5": 8.5,  "NC_t_ha_pH6_0": 11.9, "NC_t_ha_pH6_5": 15.7},
    {"SMP_index": 4.9, "NC_t_ha_pH5_5": 7.7,  "NC_t_ha_pH6_0": 10.7, "NC_t_ha_pH6_5": 14.2},
    {"SMP_index": 5.0, "NC_t_ha_pH5_5": 6.6,  "NC_t_ha_pH6_0": 9.9,  "NC_t_ha_pH6_5": 13.3},
    {"SMP_index": 5.1, "NC_t_ha_pH5_5": 6.0,  "NC_t_ha_pH6_0": 9.1,  "NC_t_ha_pH6_5": 12.3},
    {"SMP_index": 5.2, "NC_t_ha_pH5_5": 5.3,  "NC_t_ha_pH6_0": 8.3,  "NC_t_ha_pH6_5": 11.3},
    {"SMP_index": 5.3, "NC_t_ha_pH5_5": 4.8,  "NC_t_ha_pH6_0": 7.5,  "NC_t_ha_pH6_5": 10.4},
    {"SMP_index": 5.4, "NC_t_ha_pH5_5": 4.2,  "NC_t_ha_pH6_0": 6.8,  "NC_t_ha_pH6_5": 9.5},
    {"SMP_index": 5.5, "NC_t_ha_pH5_5": 3.7,  "NC_t_ha_pH6_0": 6.1,  "NC_t_ha_pH6_5": 8.6},
    {"SMP_index": 5.6, "NC_t_ha_pH5_5": 3.2,  "NC_t_ha_pH6_0": 5.4,  "NC_t_ha_pH6_5": 7.8},
    {"SMP_index": 5.7, "NC_t_ha_pH5_5": 2.8,  "NC_t_ha_pH6_0": 4.8,  "NC_t_ha_pH6_5": 7.0},
    {"SMP_index": 5.8, "NC_t_ha_pH5_5": 2.3,  "NC_t_ha_pH6_0": 4.2,  "NC_t_ha_pH6_5": 6.3},
    {"SMP_index": 5.9, "NC_t_ha_pH5_5": 2.0,  "NC_t_ha_pH6_0": 3.7,  "NC_t_ha_pH6_5": 5.6},
    {"SMP_index": 6.0, "NC_t_ha_pH5_5": 1.6,  "NC_t_ha_pH6_0": 3.2,  "NC_t_ha_pH6_5": 4.9},
    {"SMP_index": 6.1, "NC_t_ha_pH5_5": 1.3,  "NC_t_ha_pH6_0": 2.7,  "NC_t_ha_pH6_5": 4.3},
    {"SMP_index": 6.2, "NC_t_ha_pH5_5": 1.0,  "NC_t_ha_pH6_0": 2.2,  "NC_t_ha_pH6_5": 3.7},
    {"SMP_index": 6.3, "NC_t_ha_pH5_5": 0.8,  "NC_t_ha_pH6_0": 1.8,  "NC_t_ha_pH6_5": 3.1},
    {"SMP_index": 6.4, "NC_t_ha_pH5_5": 0.6,  "NC_t_ha_pH6_0": 1.4,  "NC_t_ha_pH6_5": 2.6},
    {"SMP_index": 6.5, "NC_t_ha_pH5_5": 0.4,  "NC_t_ha_pH6_0": 1.1,  "NC_t_ha_pH6_5": 2.1},
    {"SMP_index": 6.6, "NC_t_ha_pH5_5": 0.2,  "NC_t_ha_pH6_0": 0.8,  "NC_t_ha_pH6_5": 1.6},
    {"SMP_index": 6.7, "NC_t_ha_pH5_5": 0.0,  "NC_t_ha_pH6_0": 0.5,  "NC_t_ha_pH6_5": 1.2},
    {"SMP_index": 6.8, "NC_t_ha_pH5_5": 0.0,  "NC_t_ha_pH6_0": 0.3,  "NC_t_ha_pH6_5": 0.8},
    {"SMP_index": 6.9, "NC_t_ha_pH5_5": 0.0,  "NC_t_ha_pH6_0": 0.2,  "NC_t_ha_pH6_5": 0.5},
    {"SMP_index": 7.0, "NC_t_ha_pH5_5": 0.0,  "NC_t_ha_pH6_0": 0.0,  "NC_t_ha_pH6_5": 0.2},
    {"SMP_index": 7.1, "NC_t_ha_pH5_5": 0.0,  "NC_t_ha_pH6_0": 0.0,  "NC_t_ha_pH6_5": 0.0},
]

V_TARGETS: Dict[float, float] = {
    5.5: 65.0,
    6.0: 75.0,
    6.5: 85.0,
}

POLY_COEFFS: Dict[float, Dict[str, float]] = {
    5.5: {"a_intercept": -0.653, "b_MO": 0.480, "c_Al": 1.937},
    6.0: {"a_intercept": -0.516, "b_MO": 0.805, "c_Al": 2.435},
    6.5: {"a_intercept": -0.122, "b_MO": 1.193, "c_Al": 2.713},
}

DECISION_RULES: List[Dict[str, str]] = [
    {"order": "1", "variable": "crop_group", "condition": "grains_soybean", "action": "desired_pH = 6.0"},
    {"order": "2", "variable": "pH_H2O", "condition": "< 5.5", "action": "lime indicated"},
    {"order": "3", "variable": "system", "condition": "conventional_or_PD_implantation", "action": "sample 0-20 cm; use SMP table pH 6.0; apply incorporated"},
    {"order": "4", "variable": "system", "condition": "PD_consolidated_no_restrictions", "action": "sample 0-10 cm; if V% > 65 and Al_sat < 10 skip; else 25% of SMP dose pH 6.0; apply superficial"},
    {"order": "5", "variable": "system", "condition": "PD_consolidated_with_restrictions", "action": "sample 10-20 cm; average SMP; apply incorporated"},
    {"order": "6", "variable": "surface_cap", "condition": "application mode superficial", "action": "limit NC <= 5 t/ha"},
    {"order": "7", "variable": "PRNT_material", "condition": "PRNT != 100%", "action": "NC_adjusted = NC * (100 / PRNT)"},
    {"order": "8", "variable": "SMP_index", "condition": "> 6.3", "action": "consider polynomial NC with MO and Al"},
]

INPUTS_SCHEMA: List[Dict[str, object]] = [
    {"field": "pH_H2O", "type": "float", "unit": "", "required": True},
    {"field": "SMP_index", "type": "float", "unit": "", "required": False},
    {"field": "V_percent", "type": "float", "unit": "%", "required": False},
    {"field": "CTC_pH7", "type": "float", "unit": "cmolc/dm3", "required": False},
    {"field": "Al_cmolc_dm3", "type": "float", "unit": "cmolc/dm3", "required": False},
    {"field": "Al_saturation_percent", "type": "float", "unit": "%", "required": False},
    {"field": "MO_percent", "type": "float", "unit": "%", "required": False},
    {"field": "system", "type": "enum", "unit": "", "required": True},
    {"field": "sampling_depth_cm", "type": "enum", "unit": "", "required": True},
    {"field": "PRNT_percent", "type": "float", "unit": "%", "required": True},
]

OUTPUTS_SCHEMA: List[Dict[str, str]] = [
    {"field": "method", "type": "enum", "unit": "", "description": "SMP | V_percent | Polynomial"},
    {"field": "desired_pH", "type": "float", "unit": "", "description": "Default 6.0 for soybean"},
    {"field": "NC_PRNT100_t_ha", "type": "float", "unit": "t/ha", "description": "Dose at PRNT 100%"},
    {"field": "application_mode", "type": "enum", "unit": "", "description": "Incorporated | Superficial"},
    {"field": "NC_adjusted_for_PRNT_t_ha", "type": "float", "unit": "t/ha", "description": "NC * (100 / PRNT)"},
    {"field": "NC_surface_capped_t_ha", "type": "float", "unit": "t/ha", "description": "If superficial, capped at 5 t/ha"},
    {"field": "notes", "type": "text", "unit": "", "description": "Decision notes"},
]


def _interp(x: float, x0: float, y0: float, x1: float, y1: float) -> float:
    """Simple linear interpolation."""
    if x1 == x0:
        return y0
    t = (x - x0) / (x1 - x0)
    return y0 + t * (y1 - y0)


def _get_two_closest_rows_by_SMP(smp: float) -> Tuple[Dict[str, float], Dict[str, float]]:
    rows = sorted(SMP_TABLE, key=lambda r: r["SMP_index"])
    if smp <= rows[0]["SMP_index"]:
        return rows[0], rows[0]
    if smp >= rows[-1]["SMP_index"]:
        return rows[-1], rows[-1]
    lo = rows[0]
    for hi in rows[1:]:
        if lo["SMP_index"] <= smp <= hi["SMP_index"]:
            return lo, hi
        lo = hi
    return rows[-1], rows[-1]


def lime_dose_from_SMP(smp: float, desired_pH: float = 6.0) -> Optional[float]:
    """Return NC (t/ha, PRNT 100%) via SMP table for the chosen pH target."""
    column = {
        5.5: "NC_t_ha_pH5_5",
        6.0: "NC_t_ha_pH6_0",
        6.5: "NC_t_ha_pH6_5",
    }.get(desired_pH)
    if column is None:
        return None
    lo, hi = _get_two_closest_rows_by_SMP(smp)
    if lo["SMP_index"] == hi["SMP_index"]:
        return float(lo[column])
    return _interp(smp, lo["SMP_index"], lo[column], hi["SMP_index"], hi[column])


def lime_dose_from_V(ctc_pH7: float, v_current: float, desired_pH: float = 6.0) -> Optional[float]:
    """NC (t/ha, PRNT 100%) via the V% method: ((V1 - V2)/100) * CTC."""
    v_target = V_TARGETS.get(desired_pH)
    if v_target is None:
        return None
    return ((v_target - v_current) / 100.0) * ctc_pH7


def lime_dose_from_polynomial(mo_percent: float, al_cmolc: float, desired_pH: float = 6.0) -> Optional[float]:
    """NC (t/ha, PRNT 100%) via polynomial equation for low-buffer soils."""
    coeffs = POLY_COEFFS.get(desired_pH)
    if coeffs is None:
        return None
    return (
        coeffs["a_intercept"]
        + coeffs["b_MO"] * mo_percent
        + coeffs["c_Al"] * al_cmolc
    )


def adjust_for_prnt(nc_prnt100: float, prnt_percent: float) -> float:
    """Adjust dose for the corrective quality (PRNT)."""
    if prnt_percent <= 0:
        return float("inf")
    return nc_prnt100 * (100.0 / prnt_percent)


def cap_surface_application(dose_t_ha: float, cap_t_ha: float = 5.0) -> float:
    """Apply the recommended cap for surface applications."""
    return min(dose_t_ha, cap_t_ha)