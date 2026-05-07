# Eg Algorithm Flow (Script-Aligned)

This reference maps the current Eg implementation in:

- `scripts/summarize_uvvis_drs.py`
- `scripts/bloom_draw.py`
- `scripts/line_fit.py`
- `scripts/plot_tauc_uvvis_drs.py`

Use this as the source of truth when reporting Eg results.

## 1) Mode-aware Tauc preprocessing

Signal mode is inferred from metadata (`光度值类型` or `signal_type`):

- `absorbance`: labels containing `吸收/abs`
- `transmittance`: labels containing `透过/trans/%t/t%`
- `reflectance`: labels containing `反射/漫反射/reflect/%r/r%`
- otherwise `unknown` (Eg disabled)

Photon energy conversion currently uses:

- absorbance / transmittance: `hv (eV) = 1240 / wavelength_nm`
- reflectance (DRS): `hv (eV) = 1024 / wavelength_nm`

Mode transform:

- `absorbance`: `base = absorbance * hv` for points where absorbance `> 0`
- `transmittance`: if max signal `> 2`, divide by 100 first; keep `0 < T < 1`; `alpha = -log10(T)`; `base = alpha * hv`
- `reflectance`: if max signal `> 2`, divide by 100 first; keep `0 < R < 1`; `F(R) = (1-R)^2/(2R)`; `base = F(R) * hv`

Tauc axes:

- indirect channel: `sqrt(base)`
- direct channel: `base^2`

## 2) Eg screening entry conditions

Eg evaluation starts only when all checks pass:

- mode is not `unknown`
- mode is either `absorbance` or `reflectance` (transmittance mode is excluded for Eg in this workflow)
- sample metadata is not explicitly tagged as non powder/bulk (for example solution/liquid/film/coating/fiber)
- points `>= 80`
- raw signal span (`max-min`) `>= 0.02`
- wavelength overlaps screening window implied by Eg range:
  - absorbance: `1.5-4.5 eV` -> approx `276-827 nm`
  - reflectance: `1.5-4.5 eV` -> approx `228-683 nm`
- transformed valid points still `>= 80`

Otherwise `decision = peak_only` with a concrete `reason`.

## 3) Linear-region candidate extraction

Candidate extraction runs independently for direct and indirect channels.

### 3.1 Smoothing

- Uses Savitzky-Golay smoothing (`savgol_filter`, dynamic odd window, `polyorder=2`)
- Falls back to moving-average if Savitzky-Golay cannot be applied

### 3.2 Primary path: recursive segmentation (`line_fit.py`)

`find_linear_correlation_region(...)` is called with:

- `R_tol = 0.995` (from `R2_THRESHOLD`)
- `min_segment_points = 2`

The function:

1. Recursively splits low-correlation segments
2. Keeps segments that satisfy R threshold
3. Sorts segments by x-median
4. Tries to merge adjacent segments if merged R remains above threshold

### 3.3 Fallback path: rolling window

If recursive segmentation yields zero valid candidates:

- slide a window with `window = max(10, int(len(hv) * 0.10))`
- linear-fit each window with `np.polyfit`

### 3.4 Candidate filters (shared)

For each fitted segment/window, keep candidate only if all pass:

- segment y-span >= `10%` of smoothed full y-span
- slope > 0
- slope >= `0.1`
- slope >= `0.3 * (y_max - y_min)` where `y_max - y_min` is full smoothed-span of this Tauc channel
- `r2 >= 0.995`
- `Eg = -intercept/slope` in `[1.5, 4.5] eV`
- segment minimum photon energy `< 4.5 eV`

## 4) Ranking and selected Eg

After collecting candidates:

1. Score `segment_y_span` by decile (10 bins): largest span gets `10`, smallest gets `1`
2. Score slope `k` by decile (10 bins): largest slope gets `10`, smallest gets `1`
3. Sum scores: `score_total = score_dy + score_k`
4. Sort by:
   - `score_total` descending
   - then left boundary (`segment_hv_min_ev`) ascending
   - then `r2` descending
5. Deduplicate by rounded Eg bucket (`round(eg_ev, 2)`)
6. Keep top 2 (`TOP_N_RESULTS = 2`)

Outputs:

- `direct_candidates_ev[]`
- `indirect_candidates_ev[]`
- `selected_direct_eg_ev`: first direct candidate Eg
- `selected_indirect_eg_ev`: first indirect candidate Eg

Decision:

- `compute_eg` if either direct or indirect candidate list is non-empty
- otherwise `peak_only`

## 5) Plot and reporting behavior

`scripts/plot_tauc_uvvis_drs.py` plots only samples with `decision = compute_eg`:

- left panel currently plots indirect channel (`sqrt(base)`)
- right panel currently plots direct channel (`base^2`)
- overlays selected linear fit and vertical Eg marker

Always report both:

- Eg decision (`compute_eg` vs `peak_only`)
- skip reason when Eg is not produced

## 6) Theory-vs-current implementation notes

When writing reports or planning future upgrades, keep these explicit:

- Current code now uses `1024/lambda` for reflectance mode and `1240/lambda` for absorbance/transmittance.
- Current smoothing path is Savitzky-Golay with moving-average fallback.
- Current default thresholds follow the latest filtering rules (`R2 >= 0.995`, Eg range `1.5-4.5 eV`, min segment span 10%, top 2 candidates).
