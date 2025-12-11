# Stage 1 Onset Date Update - Based on Baseline Analysis

**Date**: November 23, 2025
**Status**: Updated to match baseline detection results

---

## Problem Identified

The **stage1 script onset dates were NOT updated** after running baseline analysis:

### Before Update (Inconsistent):
- **Stage1 onset_date**: Aug 9, 2023 (literature-based, Lyon-specific)
- **Baseline detected onset**: Aug 20, 2023 12:00 UTC (regional mean > 30°C)
- **Gap**: 11 days discrepancy!

### Why This Matters:
1. Metrics would be calculated against wrong target dates
2. Lead time analysis would be misleading (targeting Aug 9 but onset is Aug 20)
3. Inconsistent with our methodology (using ERA5 baseline to define event)

---

## Changes Made to `heatwave_stage1_detection.py`

### 1. Event Timeline (lines 66-69)

**Before:**
```python
'onset_date': '2023-08-09',      # Regional mean > 30°C
'peak_date': '2023-08-23',       # Hottest day (could also use Aug 24)
'recovery_date': '2023-08-26',   # Regional mean < 30°C
```

**After:**
```python
'onset_date': '2023-08-20',      # Regional mean > 30°C (detected: Aug 20, 12:00 UTC)
'peak_date': '2023-08-23',       # Hottest day (detected: Aug 23, 12:00 UTC)
'recovery_date': '2023-08-24',   # Regional mean < 30°C (detected: Aug 24, 18:00 UTC)
```

**Changes:**
- Onset: Aug 9 → **Aug 20** (matches baseline detection)
- Peak: Aug 23 (unchanged - already correct)
- Recovery: Aug 26 → **Aug 24** (matches baseline detection)

---

### 2. Lead Time Configurations (lines 78-114)

All lead time configs updated to target **Aug 20 onset** instead of Aug 9.

| Lead Time | Init Date | Time Index | Forecast Days | Steps |
|-----------|-----------|------------|---------------|-------|
| **1-day** | Aug 19, 12:00 | 126 | 8 days | 31 |
| **7-day** | Aug 13, 12:00 | 102 | 14 days | 55 |
| **14-day** | Aug 6, 12:00 | 74 | 21 days | 83 |
| **21-day** | Jul 30, 12:00 | 46 | 28 days | 111 |

**Before (targeting Aug 9):**
```
1-day:  Init Aug 8  (1 day before Aug 9)
7-day:  Init Aug 2  (7 days before Aug 9)
14-day: Init Jul 26 (14 days before Aug 9)
21-day: Init Jul 19 (21 days before Aug 9)
```

**After (targeting Aug 20):**
```
1-day:  Init Aug 19 (1 day before Aug 20)
7-day:  Init Aug 13 (7 days before Aug 20)
14-day: Init Aug 6  (14 days before Aug 20)
21-day: Init Jul 30 (21 days before Aug 20)
```

---

## Time Index Calculation Verification

Data starts: **Jul 19, 00:00 UTC = index 0**
6-hourly timesteps (4 per day)

| Init Time | Hours from Start | Days | Time Index |
|-----------|-----------------|------|------------|
| Aug 19, 12:00 | 756.0 | 31.5 | **126** ✓ |
| Aug 13, 12:00 | 612.0 | 25.5 | **102** ✓ |
| Aug 6, 12:00 | 444.0 | 18.5 | **74** ✓ |
| Jul 30, 12:00 | 276.0 | 11.5 | **46** ✓ |

All indices verified correct!

---

## Comparison: Old vs New Lead Times

### 1-Day Lead Time
- **Old**: Init Aug 8 → Target Aug 9 (but onset is Aug 20, 11 days late!)
- **New**: Init Aug 19 → Target Aug 20 (consistent) ✅

### 7-Day Lead Time
- **Old**: Init Aug 2 → Target Aug 9 (but onset is Aug 20, 18 days away!)
- **New**: Init Aug 13 → Target Aug 20 (exactly 7 days) ✅

### 14-Day Lead Time
- **Old**: Init Jul 26 → Target Aug 9 (14 days, but onset is Aug 20)
- **New**: Init Aug 6 → Target Aug 20 (exactly 14 days) ✅

### 21-Day Lead Time
- **Old**: Init Jul 19 → Target Aug 9 (21 days, but onset is Aug 20)
- **New**: Init Jul 30 → Target Aug 20 (exactly 21 days) ✅

---

## Impact on Forecast Length

Because onset moved later (Aug 9 → Aug 20), forecasts are now **shorter**:

| Lead Time | Old Forecast Length | New Forecast Length | Reduction |
|-----------|-------------------|---------------------|-----------|
| 1-day | 19 days (75 steps) | 8 days (31 steps) | -11 days |
| 7-day | 25 days (99 steps) | 14 days (55 steps) | -11 days |
| 14-day | 32 days (127 steps) | 21 days (83 steps) | -11 days |
| 21-day | 39 days (155 steps) | 28 days (111 steps) | -11 days |

**Why?**
- All forecasts still end at Aug 27 (end of data)
- But init dates moved 11 days later
- Therefore forecast period is 11 days shorter

**This is correct!** We only need to forecast through the event recovery (Aug 24), not all the way to Aug 27.

---

## Baseline Analysis Results (from `heatwave_baseline_analysis.py`)

```
Key Event Dates:
  Onset (regional mean > 30°C): 2023-08-20T12:00:00.000000000
  Peak heat: 2023-08-23T12:00:00.000000000
    Regional mean: 30.6°C
    Regional max: 42.0°C
  Maximum spatial extent (T > 30°C): 2023-08-23T12:00:00.000000000
    Fraction of region: 71.2%
  Recovery (regional mean returns < 30°C): 2023-08-24T18:00:00.000000000
  Duration (regional mean > 30°C): 36h (1.5 days)
```

---

## Methodology Note

This update aligns the stage1 script with the **data-driven baseline analysis**, which is our standard methodology:

1. ✅ Run baseline analysis on ERA5 to detect event timeline
2. ✅ Use detected dates to configure forecasts
3. ✅ Evaluate Aurora predictions against baseline-detected events

This is consistent with how freeze events were handled:
- **Freeze baseline** detected onset Feb 27, 2018
- **Freeze stage1** used Feb 27 onset for lead time targeting

Now heatwave follows the same pattern!

---

## Onset Definition Caveat

The detected onset (Aug 20) is **11 days later** than the literature-based onset (Aug 9) because:
- Aug 20: Regional mean > 30°C (strict criterion, includes cooler northern areas)
- Aug 9: Lyon-specific onset (southern part of region, 17-day event)

This is a **known limitation** documented in `ONSET_DEFINITION_INSIGHTS.md`. The regional mean threshold may underestimate heatwave duration.

**Future improvement**: Use spatial percentage threshold (e.g., 25% of region > 30°C) instead of regional mean.

For now, we proceed with **Aug 20 onset** for consistency with baseline analysis and freeze methodology.

---

## Status

✅ Stage1 script updated to match baseline analysis
✅ All time indices verified
✅ Lead time targeting now consistent
✅ Ready to run stage1 forecasts

**Note**: If you have already run stage1 with old dates, delete the cached predictions:
```bash
rm prediction_output/predictions_*day.pkl
```

Then re-run with updated onset dates.
