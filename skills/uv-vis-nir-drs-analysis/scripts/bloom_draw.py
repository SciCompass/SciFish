#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

import numpy as np
from scipy.signal import savgol_filter

try:
    from line_fit import find_linear_correlation_region

    HAS_LINE_FIT_RULE = True
except Exception:
    # Fallback to rolling-window extraction when sklearn/line_fit is unavailable.
    find_linear_correlation_region = None
    HAS_LINE_FIT_RULE = False

# Default thresholds align with the strict Eg screening workflow.
MIN_SEGMENT_LENGTH_RATIO = 0.10
TOP_N_RESULTS = 2
R2_THRESHOLD = 0.995
EG_RANGE_EV = (1.5, 4.5)
MIN_POINTS_FOR_EG = 80
MIN_SIGNAL_SPAN = 0.02
SLOPE_MIN_ABS = 0.1
SLOPE_MIN_RATIO = 0.3


def infer_signal_mode(metadata: dict[str, Any]) -> tuple[str, str]:
    raw_label = str(metadata.get("光度值类型", "") or metadata.get("signal_type", "")).strip()
    normalized = raw_label.lower().replace(" ", "")
    if any(token in normalized for token in ("吸收", "absorb", "a", "abs")):
        return "absorbance", raw_label or "absorbance"
    if any(token in normalized for token in ("透过", "trans", "%t", "t%")):
        return "transmittance", raw_label or "transmittance"
    if any(token in normalized for token in ("反射", "漫反射", "reflect", "%r", "r%")):
        return "reflectance", raw_label or "reflectance"
    return "unknown", raw_label or "unknown"


def _moving_average(y: np.ndarray, ratio: float = 0.015) -> np.ndarray:
    n = len(y)
    if n < 7:
        return y.copy()
    window = max(5, int(n * ratio))
    if window % 2 == 0:
        window += 1
    kernel = np.ones(window) / float(window)
    return np.convolve(y, kernel, mode="same")


def _smooth_signal(y: np.ndarray, ratio: float = 0.015) -> np.ndarray:
    n = len(y)
    if n < 7:
        return y.copy()
    window = max(7, int(n * ratio))
    if window % 2 == 0:
        window += 1
    if window >= n:
        window = n - 1 if (n - 1) % 2 == 1 else n - 2
    if window < 5:
        return _moving_average(y, ratio=ratio)
    polyorder = 2 if window >= 7 else 1
    try:
        return savgol_filter(y, window_length=window, polyorder=polyorder, mode="interp")
    except Exception:
        return _moving_average(y, ratio=ratio)


def _linear_fit(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    slope, intercept = np.polyfit(x, y, deg=1)
    fitted = slope * x + intercept
    residual = np.sum((y - fitted) ** 2)
    total = np.sum((y - np.mean(y)) ** 2)
    if total <= 0:
        return float(slope), float(intercept), 0.0
    r2 = 1.0 - float(residual / total)
    return float(slope), float(intercept), r2


def _normalize_input(
    wavelength_nm: list[float] | np.ndarray,
    signal_values: list[float] | np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(wavelength_nm, dtype=float)
    y = np.asarray(signal_values, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y) & (x > 0)
    x = x[mask]
    y = y[mask]
    if len(x) == 0:
        return x, y
    order = np.argsort(x)
    return x[order], y[order]


def _sample_form_is_explicitly_non_eligible(metadata: dict[str, Any]) -> bool:
    text = " ".join(str(value) for value in metadata.values() if value is not None).lower()
    non_eligible_tokens = (
        "solution",
        "liquid",
        "film",
        "coating",
        "fiber",
        "溶液",
        "液体",
        "薄膜",
        "涂层",
        "纤维",
    )
    return any(token in text for token in non_eligible_tokens)


def _prepare_tauc_axes(
    wavelength_nm: np.ndarray, signal_values: np.ndarray, mode: str
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    conversion_factor = 1024.0 if mode == "reflectance" else 1240.0
    hv = conversion_factor / wavelength_nm

    if mode == "absorbance":
        mask = signal_values > 0
        base = signal_values[mask] * hv[mask]
        hv = hv[mask]
    elif mode == "transmittance":
        y = signal_values.copy()
        if np.nanmax(y) > 2.0:
            y = y / 100.0
        mask = (y > 0) & (y < 1)
        hv = hv[mask]
        alpha = -np.log10(y[mask])
        base = alpha * hv
    elif mode == "reflectance":
        y = signal_values.copy()
        if np.nanmax(y) > 2.0:
            y = y / 100.0
        mask = (y > 0) & (y < 1)
        hv = hv[mask]
        fr = ((1.0 - y[mask]) ** 2) / (2.0 * y[mask])
        base = fr * hv
    else:
        return np.array([]), np.array([]), np.array([])

    if len(hv) == 0:
        return np.array([]), np.array([]), np.array([])

    hv_order = np.argsort(hv)
    hv = hv[hv_order]
    base = np.clip(base[hv_order], a_min=0.0, a_max=None)
    indirect = np.sqrt(base)
    direct = np.square(base)
    return hv, indirect, direct


def _extract_eg_candidates(hv: np.ndarray, y: np.ndarray) -> list[dict[str, float]]:
    if len(hv) < MIN_POINTS_FOR_EG:
        return []
    y_smoothed = _smooth_signal(y)
    y_span_total = float(np.ptp(y_smoothed))
    if y_span_total <= 0:
        return []

    window = max(10, int(len(hv) * MIN_SEGMENT_LENGTH_RATIO))
    min_segment_points = 2
    candidates: list[dict[str, float]] = []

    def append_candidate(xv_raw: np.ndarray, yv_raw: np.ndarray, slope_raw: float, intercept_raw: float, r2_raw: float) -> None:
        xv = np.asarray(xv_raw, dtype=float).reshape(-1)
        yv = np.asarray(yv_raw, dtype=float).reshape(-1)
        if len(xv) < 2 or len(yv) < 2:
            return
        segment_span = float(np.ptp(yv))
        slope = float(slope_raw)
        intercept = float(intercept_raw)
        r2 = float(r2_raw)
        if segment_span < y_span_total * MIN_SEGMENT_LENGTH_RATIO:
            return
        if slope <= 0:
            return
        if slope < SLOPE_MIN_ABS:
            return
        if slope < (SLOPE_MIN_RATIO * y_span_total):
            return
        if r2 < R2_THRESHOLD:
            return
        eg = -intercept / slope
        if not (EG_RANGE_EV[0] <= eg <= EG_RANGE_EV[1]):
            return
        if float(np.min(xv)) >= 4.5:
            return
        candidates.append(
            {
                "eg_ev": round(float(eg), 4),
                "slope": round(slope, 6),
                "intercept": round(intercept, 6),
                "r2": round(r2, 6),
                "segment_y_span": round(segment_span, 6),
                "segment_hv_min_ev": round(float(np.min(xv)), 4),
                "segment_hv_max_ev": round(float(np.max(xv)), 4),
                "segment_points": int(len(xv)),
            }
        )

    if HAS_LINE_FIT_RULE and find_linear_correlation_region is not None:
        merged_x, merged_y, slopes, intercepts, r2_values = find_linear_correlation_region(
            hv.tolist(),
            y_smoothed.tolist(),
            R_tol=R2_THRESHOLD,
            min_segment_points=min_segment_points,
        )
        for xv, yv, slope, intercept, r2 in zip(merged_x, merged_y, slopes, intercepts, r2_values):
            append_candidate(xv, yv, slope, intercept, r2)

    # Fallback retains previous behavior if segmented rule finds nothing.
    if not candidates:
        for start in range(0, len(hv) - window + 1):
            end = start + window
            xv = hv[start:end]
            yv = y_smoothed[start:end]
            if len(xv) < 2:
                continue
            slope, intercept, r2 = _linear_fit(xv, yv)
            append_candidate(xv, yv, slope, intercept, r2)

    if not candidates:
        return []

    def _score_decile(values: list[float]) -> list[int]:
        if not values:
            return []
        vmin = float(min(values))
        vmax = float(max(values))
        if abs(vmax - vmin) < 1e-12:
            return [10 for _ in values]
        scores: list[int] = []
        for value in values:
            ratio = (float(value) - vmin) / (vmax - vmin)
            score = int(np.floor(ratio * 10.0)) + 1
            if score > 10:
                score = 10
            if score < 1:
                score = 1
            scores.append(score)
        return scores

    y_scores = _score_decile([item["segment_y_span"] for item in candidates])
    k_scores = _score_decile([item["slope"] for item in candidates])
    ranked: list[dict[str, float]] = []
    for idx, item in enumerate(candidates):
        candidate = dict(item)
        candidate["score_dy"] = y_scores[idx]
        candidate["score_k"] = k_scores[idx]
        candidate["score_total"] = int(y_scores[idx] + k_scores[idx])
        ranked.append(candidate)

    dedup: dict[float, dict[str, float]] = {}
    for item in sorted(
        ranked,
        key=lambda v: (
            -v["score_total"],
            v["segment_hv_min_ev"],
            -v["r2"],
            -v["segment_y_span"],
        ),
    ):
        key = round(item["eg_ev"], 2)
        if key not in dedup:
            dedup[key] = item
        if len(dedup) >= TOP_N_RESULTS:
            break
    return list(dedup.values())


def build_eg_assessment(
    metadata: dict[str, Any],
    wavelength_nm: list[float] | np.ndarray,
    signal_values: list[float] | np.ndarray,
) -> dict[str, Any]:
    mode, raw_label = infer_signal_mode(metadata)
    x, y = _normalize_input(wavelength_nm, signal_values)

    result: dict[str, Any] = {
        "signal_mode": mode,
        "signal_label": raw_label,
        "should_calculate_eg": False,
        "meaningful_for_eg": False,
        "decision": "peak_only",
        "reason": "",
        "selected_direct_eg_ev": None,
        "selected_indirect_eg_ev": None,
        "direct_candidates_ev": [],
        "indirect_candidates_ev": [],
    }

    if mode == "unknown":
        result["reason"] = "Unsupported or missing signal type metadata."
        return result
    if mode not in ("reflectance", "absorbance"):
        result["reason"] = "Eg analysis is allowed only for reflectance (R%) or absorbance (A) modes."
        return result
    if _sample_form_is_explicitly_non_eligible(metadata):
        result["reason"] = "Eg analysis is restricted to powder/bulk-like samples."
        return result
    if len(x) < MIN_POINTS_FOR_EG:
        result["reason"] = f"Too few points for Eg screening (<{MIN_POINTS_FOR_EG})."
        return result
    if float(np.ptp(y)) < MIN_SIGNAL_SPAN:
        result["reason"] = "Signal dynamic range is too small for reliable Eg fitting."
        return result

    conversion_factor = 1024.0 if mode == "reflectance" else 1240.0
    window_low_nm = conversion_factor / EG_RANGE_EV[1]
    window_high_nm = conversion_factor / EG_RANGE_EV[0]
    overlap_low = max(float(np.min(x)), float(window_low_nm))
    overlap_high = min(float(np.max(x)), float(window_high_nm))
    if overlap_high <= overlap_low:
        result["reason"] = (
            f"No wavelength overlap with the {EG_RANGE_EV[0]:.1f}-{EG_RANGE_EV[1]:.1f} eV "
            f"screening window ({window_low_nm:.0f}-{window_high_nm:.0f} nm)."
        )
        return result

    result["should_calculate_eg"] = True
    hv, indirect, direct = _prepare_tauc_axes(x, y, mode)
    if len(hv) < MIN_POINTS_FOR_EG:
        result["reason"] = "Insufficient valid transformed points after mode-specific filtering."
        return result

    direct_candidates = _extract_eg_candidates(hv, direct)
    indirect_candidates = _extract_eg_candidates(hv, indirect)
    result["direct_candidates_ev"] = direct_candidates
    result["indirect_candidates_ev"] = indirect_candidates

    if not direct_candidates and not indirect_candidates:
        result["reason"] = "No valid linear Tauc segment passed the configured thresholds."
        return result

    result["meaningful_for_eg"] = True
    result["decision"] = "compute_eg"
    result["reason"] = "At least one Tauc linear segment satisfies the Eg rule thresholds."
    if direct_candidates:
        result["selected_direct_eg_ev"] = direct_candidates[0]["eg_ev"]
    if indirect_candidates:
        result["selected_indirect_eg_ev"] = indirect_candidates[0]["eg_ev"]
    return result


__all__ = ["build_eg_assessment", "infer_signal_mode"]
