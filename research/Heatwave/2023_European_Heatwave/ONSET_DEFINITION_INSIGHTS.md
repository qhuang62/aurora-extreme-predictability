# Heatwave Onset Definition - Insights & Future Improvements

**Date**: November 23, 2025
**Status**: Findings to revisit later

---

## Current Situation

### Baseline Analysis Results (Aug 2023 European Heatwave)

**Current onset definition**: First time regional mean T2m > 30°C
- **Detected onset**: Aug 20, 2023 12:00 UTC
- **Peak**: Aug 23, 2023 12:00 UTC
- **Duration**: 36 hours (1.5 days)
- **Recovery**: Aug 24, 2023 18:00 UTC

**Peak spatial extent**: 71.2% of region above 30°C

### The Problem

The detected onset (Aug 20) is **only 3 days before peak** (Aug 23), and total duration is only 1.5 days. This doesn't match the historical record of a **17-day sustained heatwave** (Lyon: 17 consecutive days > 30°C from Aug 9-25).

**Why the discrepancy?**
- **Regional mean > 30°C is too strict**: Averaging over the entire region (42-48°N, 2°W-8°E) includes cooler northern areas
- Northern France and Switzerland may not reach 30°C until the peak
- Southern areas (Lyon, Bilbao) likely exceeded 30°C much earlier

---

## Comparison with Freeze Events

### Freeze Onset Definition
**Beast from East**: First time regional mean T2m < 0°C
- **Onset**: Feb 27, 2018 (from baseline analysis)
- **Peak**: Mar 1, 2018
- **Gap**: ~2 days between onset and peak

**Key insight**: For freeze, 0°C is a meaningful **absolute threshold** because it's the freezing point. Water freezes, snow accumulates, infrastructure impacts begin immediately.

### Heatwave Difference
**30°C for heatwave is NOT equivalent to 0°C for freeze:**
- 30°C is arbitrary (not a physical threshold like freezing)
- Heat health impacts begin at different temperatures for different populations
- Regional averaging dampens local extremes
- Some areas (Lyon) hit 30°C on Aug 9, others (northern regions) not until Aug 20

**Result**: Using "regional mean > 30°C" misses the early phase of the heatwave where significant areas were already hot.

---

## Proposed Alternative: Spatial Percentage Threshold

### Methodology

Instead of:
```python
onset = first_time(regional_mean > 30°C)
```

Use:
```python
onset = first_time(spatial_extent_above_30°C > 25%)
```

**Rationale**:
1. More physically meaningful for distributed heat events
2. Captures onset when "significant portion" of region is affected
3. Better matches operational heat warnings (issued when some areas exceed thresholds)
4. Accounts for spatial heterogeneity in heatwaves

### Expected Impact

**Hypothesis**: With 25% spatial threshold, onset would move earlier to ~Aug 9-12
- Peak spatial extent: 71.2% > 30°C (Aug 23)
- If 25% threshold used, likely detects onset when southern France first heats up
- Duration would increase from 1.5 days to ~10-14 days (more realistic)

### Comparison Across Event Types

| Event Type | Onset Definition | Rationale |
|------------|------------------|-----------|
| **Freeze** | Regional mean < 0°C | Absolute physical threshold (freezing point) |
| **Heatwave** | 25% of region > 30°C | Spatial threshold (distributed impacts) |
| **TC** | TC center detection | Feature tracking (position) |
| **AR** | IVT > threshold | Integrated quantity |

**Key principle**: Onset definition should match the **physics** and **operational relevance** of each event type.

---

## Evidence from Baseline Analysis

### Spatial Extent Time Series

From baseline output:
- **Aug 20 (detected onset)**: Regional mean crosses 30°C
- **Aug 23 (peak)**: 71.2% of region > 30°C

**Question**: What % of region was > 30°C on Aug 9, 12, 15?
- If 25% of region exceeded 30°C by Aug 9, that's a better onset marker
- If only 5%, then Aug 20 onset is correct

**Action needed**: Add spatial extent percentage to onset detection criteria.

### Literature Comparison

**Lyon-specific**: 17 days > 30°C (Aug 9-25)
- Lyon is in southern part of our region
- Regional average includes cooler areas to the north
- **Suggests**: Spatial threshold would align better with city-level observations

---

## Decision for Current Analysis

**For now, proceed with Aug 20 onset** (regional mean > 30°C) for:
1. **Consistency with freeze methodology** (both use regional mean)
2. **Simplicity**: Easier to compare directly with freeze results
3. **Conservative estimate**: Tests Aurora on shorter, more intense period

**Trade-offs**:
- Misses early heatwave development (Aug 9-19)
- Underestimates event duration
- May affect lead time analysis (7-day lead from Aug 2 targets Aug 9, but "onset" is Aug 20)

---

## Future Improvements (To Revisit)

### Short-term (Before Paper Submission)
1. **Add diagnostic**: Plot spatial extent (% > 30°C) vs time
   - Shows when 25%, 50%, 75% thresholds crossed
   - Validates whether Aug 9 onset makes sense
2. **Document in paper**: Explain onset definition choices and limitations
3. **Compare both definitions**: Run Stage 1 with both onset dates, see if results differ

### Medium-term (Revision or Follow-up)
1. **Implement spatial percentage onset**:
   ```python
   def detect_onset_timing_heat_spatial(t2m_fields, times,
                                         temp_threshold=30.0,
                                         spatial_threshold=0.25):
       """Detect onset when X% of region exceeds temperature threshold."""
       for i, field in enumerate(t2m_fields):
           fraction_hot = (field > temp_threshold).sum() / field.size
           if fraction_hot > spatial_threshold:
               return times[i]
       return None
   ```
2. **Sensitivity analysis**: Test 10%, 25%, 50% spatial thresholds
3. **Cross-event comparison**: Does freeze also benefit from spatial threshold?

### Long-term (Future Research)
1. **Physics-based onset**: Heat stress indices (apparent temperature, wet bulb)
2. **Multi-variable onset**: Combine T2m + humidity + wind for human impact
3. **Sub-regional analysis**: Lyon-specific vs regional-average metrics
4. **Percentile-based**: Onset when T exceeds 90th percentile of climatology

---

## Implications for Stage 1 Analysis

### Current Configuration (Aug 20 onset)

**Lead time configs**:
- 21-day: Init Jul 19 → Target Aug 9 (but "onset" is Aug 20, 11 days later!)
- 14-day: Init Jul 26 → Target Aug 9
- 7-day: Init Aug 2 → Target Aug 9
- 1-day: Init Aug 8 → Target Aug 9

**Mismatch**: All forecasts target Aug 9, but detected onset is Aug 20!

**Options**:
1. **Keep Aug 9 target** (literature-based, Lyon-specific)
   - Pro: Tests early heatwave prediction
   - Con: Onset metrics will show large errors (onset detected 11 days late by definition)
2. **Change target to Aug 20** (data-driven, regional mean)
   - Pro: Consistent with baseline analysis
   - Con: Misses early development, shorter lead times
3. **Use both** (dual analysis)
   - Report metrics for both Aug 9 (heat arrival in southern region) and Aug 20 (regional mean threshold)

---

## Recommendation

**For current Stage 1 run**:
- Proceed with Aug 9 target (as coded in stage1 script)
- Document that this represents "heat arrival in affected areas" not "regional mean threshold"
- In results, report:
  - Onset timing relative to Aug 9 (heat arrival in Lyon)
  - Onset timing relative to Aug 20 (regional mean > 30°C)
  - Peak timing relative to Aug 23 (both definitions agree)

**For paper**:
- Methods section: Explain onset definition challenge
- Results: Report both metrics
- Discussion: Acknowledge limitation, suggest spatial threshold for future work

**For future work**:
- Implement spatial percentage threshold
- Re-run baseline with 25% threshold
- Validate against city-level observations (Lyon, Toulouse, Bilbao)

---

## Key Insights Summary

1. **Regional mean is appropriate for freeze** (0°C is physical threshold)
2. **Regional mean is problematic for heatwave** (30°C is arbitrary, misses spatial heterogeneity)
3. **Spatial percentage threshold is more appropriate** for distributed heat events
4. **Duration discrepancy** (1.5 days vs 17 days) indicates onset definition issue
5. **Lead time analysis may be affected** if onset target doesn't match detection criteria

**Bottom line**: This is a **methodological insight** worth documenting and revisiting, but not blocking for current analysis. Proceed with Aug 20 onset, document limitations, and flag for future improvement.

---

## Action Items (Future)

- [ ] Plot spatial extent (% > 30°C) time series from baseline
- [ ] Test 25% spatial threshold onset detection
- [ ] Compare Aug 9 vs Aug 20 onset in Stage 1 metrics
- [ ] Add sensitivity analysis to supplementary material
- [ ] Cite this in paper limitations section

**Status**: Documented for future reference, proceeding with Aug 20 onset for now.
