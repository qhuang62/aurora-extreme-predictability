# Field Variables Analysis - Heatwave vs Freeze

**Date**: November 23, 2025
**Issue**: Heatwave baseline was missing field variable tracking compared to freeze

---

## Summary of Findings

### What Was Missing
The **heatwave baseline analysis** only tracked T2m spatial maps (time-averaged, max, variability), but did NOT have the **4-panel line plot** showing temporal evolution of:
- T2m spatial statistics (mean, min, max over time)
- T850 spatial statistics (850 hPa temperature)
- MSL spatial statistics (mean sea level pressure)
- Z500 spatial statistics (500 hPa geopotential height)

### What Was Already Correct
The **heatwave stage1 script** already extracts and caches all 4 field variables:
- `t2m_fields_celsius` (lines 258-259)
- `t850_fields_celsius` (lines 262-263)
- `z500_fields_m` (lines 265-266)
- `msl_fields_hpa` (lines 268-269)

This matches the freeze stage1 implementation exactly!

---

## Physical Reasoning: Why Track Same Variables?

### For Freeze Events (Beast from the East)
1. **T2m** - Surface freezing (< 0°C)
2. **T850** - Cold air mass advection at 850 hPa
3. **MSL** - High pressure blocking (Scandinavian High blocks Atlantic air)
4. **Z500** - Omega blocking pattern at upper levels

### For Heatwave Events (2023 European Heatwave)
1. **T2m** - Surface heat (> 30°C)
2. **T850** - Warm air mass advection at 850 hPa
3. **MSL** - High pressure anticyclone (blocks cooling Atlantic air)
4. **Z500** - Ridge/blocking pattern at upper levels

### Conclusion: Same Physics, Opposite Sign!
Both events involve:
- Persistent **atmospheric blocking** (high pressure systems)
- **Temperature advection** at 850 hPa (cold vs warm)
- **Synoptic-scale patterns** (MSL pressure anomalies)
- **Upper-level ridging/blocking** (Z500 anomalies)

**Therefore, we should track the SAME 4 variables for both event types!**

---

## Changes Made

### 1. Added `extract_atmos_regional_subset()` Function
**File**: `heatwave_baseline_analysis.py` (lines 274-298)

```python
def extract_atmos_regional_subset(ds, variable, level):
    """Extract regional subset for atmospheric variable at specific pressure level."""
    # Handles longitude wrapping and prime meridian crossing
    # Same logic as freeze baseline
```

### 2. Replaced `plot_spatial_statistics()` Function
**File**: `heatwave_baseline_analysis.py` (lines 301-445)

**Before**: 3-panel plot showing T2m time-averaged, max, and variability (spatial maps)

**After**: 4-panel plot showing temporal line plots:
- Panel 1: T2m spatial statistics (mean, min-max range, 30°C and 35°C thresholds)
- Panel 2: T850 spatial statistics (mean, min-max range, 15°C warm air indicator)
- Panel 3: MSL spatial statistics (mean, min-max range)
- Panel 4: Z500 spatial statistics (mean, min-max range, ridging/blocking indicator)

**Key differences from freeze**:
- Red/orange color scheme (instead of blue for freeze)
- Thresholds: 30°C, 35°C for T2m (instead of 0°C, -5°C)
- T850 threshold: 15°C warm air indicator (instead of -5°C freeze indicator)
- Plot titles reference "ridging/blocking" not "blocking" (same mechanism, different name)

### 3. Updated Function Call
**File**: `heatwave_baseline_analysis.py` (line 466)

**Before**: `plot_spatial_statistics(surf_ds)`
**After**: `plot_spatial_statistics(surf_ds, atmos_ds)`

Added `atmos_ds` parameter to access T850 and Z500 data.

---

## Verification Checklist

- [x] Heatwave baseline now tracks same 4 variables as freeze baseline
- [x] Heatwave stage1 already extracts same 4 variables as freeze stage1
- [x] Color schemes inverted (red/hot for heatwave, blue/cold for freeze)
- [x] Thresholds inverted (> 30°C for heat, < 0°C for freeze)
- [x] Both use same plotting structure (4-panel line plots)

---

## Next Steps

1. **Re-run heatwave baseline** to generate new 4-panel spatial statistics plot
   ```bash
   cd /scratch/qhuang62/aurora-extreme-predictability/research/Heatwave/2023_European_Heatwave
   python heatwave_baseline_analysis.py
   ```

2. **Verify outputs**:
   - `baseline_analysis/heatwave_temporal_evolution.png` (3 panels: T2m, spatial extent, hottest T)
   - `baseline_analysis/heatwave_spatial_statistics.png` (4 panels: T2m, T850, MSL, Z500 line plots)

3. **Run stage1 forecasts** when ready (already has correct field extraction)

---

## Comparison Table

| Aspect | Freeze Baseline | Heatwave Baseline (Fixed) |
|--------|----------------|---------------------------|
| **Variables tracked** | T2m, T850, MSL, Z500 | T2m, T850, MSL, Z500 ✅ |
| **Plotting format** | 4-panel line plots | 4-panel line plots ✅ |
| **T2m threshold** | 0°C (freeze line) | 30°C (heat threshold) |
| **T850 threshold** | -5°C (cold air) | 15°C (warm air) |
| **Color scheme** | Blues (cold) | Reds/Oranges (hot) |
| **Direction** | < (below threshold) | > (above threshold) |
| **Spatial extent** | % below 0°C, -5°C, -10°C | % above 30°C, 35°C, 40°C |
| **Peak detection** | argmin (coldest) | argmax (hottest) |

---

## Technical Notes

### Aurora Pressure Level Indexing
Both scripts use the same pressure level indices:
- **850 hPa**: `level_idx=2` (Aurora levels: 1000, 925, **850**, 700, 600, 500, ...)
- **500 hPa**: `level_idx=5` (Aurora levels: 1000, 925, 850, 700, 600, **500**, ...)

### Longitude Wrapping
Both scripts handle prime meridian crossing for the European region:
- Region: 42-48°N, 2°W-8°E
- Longitude conversion: -180/180 ↔ 0/360 coordinate systems

### Date Labeling
Both scripts use index-based x-axis with manual date labels:
- Freeze: Every 12 timesteps = 3 days
- Heatwave: Every 8 timesteps = 2 days (denser labeling for shorter event)

---

**Status**: ✅ Heatwave infrastructure now matches freeze methodology for field variable tracking.
