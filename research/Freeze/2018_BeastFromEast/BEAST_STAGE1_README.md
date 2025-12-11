# Beast from the East 2018 - Stage 1 Analysis

## Quick Start

```bash
cd /scratch/qhuang62/aurora-extreme-predictability/research/Freeze/2018_BeastFromEast
python beast_stage1_detection.py
```

**Estimated runtime**: ~5-10 minutes total (depends on GPU availability)
- 1-day lead: ~1 min (19 steps)
- 7-day lead: ~2 min (39 steps)
- 14-day lead: ~3 min (67 steps)
- 21-day lead: ~4 min (95 steps)

**Memory requirements**:
- GPU: 3-4 GB peak
- CPU: 25-30 GB (storing all predictions)

---

## Experimental Design

### Event Timeline (from baseline analysis)

| Phase | Date/Time | Temperature | Definition |
|-------|-----------|-------------|-----------|
| **Onset** | Feb 27, 00:00 UTC | -0.52°C | Regional mean < 0°C (first time) |
| **Peak** | Feb 28, 06:00 UTC | -2.57°C (mean), -31.8°C (min) | Coldest regional mean |
| **Recovery** | Mar 2, 00:00 UTC | +0.29°C | Regional mean > 0°C (returns) |
| **Duration** | 60 hours | - | Time regional mean < 0°C |

### Lead Time Configurations

All forecasts target **onset = Feb 27, 2018**:

| Lead Time | Init Date | Init Time | Target | Forecast Length | Steps |
|-----------|-----------|-----------|--------|-----------------|-------|
| **1-day** | Feb 26 | 12:00 UTC | Feb 27 onset | 5 days | 19 |
| **7-day** | Feb 20 | 12:00 UTC | Feb 27 onset | 10 days | 39 |
| **14-day** | Feb 13 | 12:00 UTC | Feb 27 onset | 17 days | 67 |
| **21-day** | Feb 6 | 12:00 UTC | Feb 27 onset | 24 days | 95 |

**Note**: Longer forecasts needed to capture full event (onset → peak → recovery)

---

## Output Files

### 1. **beast_stage1_metrics.csv**

Summary table with metrics at each phase (onset, peak, recovery) for each lead time.

**Columns**:
- `Event_Name`: Beast from the East 2018
- `Stage`: 1 (lead time assessment)
- `Lead_Days`: 1, 7, 14, or 21
- `Phase`: Onset, Peak, or Recovery
- `T2m_Mean_C`: Aurora forecast regional mean T2m (°C)
- `T2m_Min_C`: Aurora forecast regional minimum T2m (°C)
- `T2m_Error_C`: Bias vs ERA5 (Aurora - ERA5)
- `T2m_RMSE_C`: Root mean squared error (°C)
- `T850_Mean_C`: 850 hPa temperature mean (°C)
- `T850_Error_C`: 850 hPa temperature bias (°C)
- `Z500_Mean_m`: 500 hPa geopotential height mean (m)
- `Z500_Error_m`: 500 hPa geopotential height bias (m)
- `MSL_Mean_hPa`: Mean sea level pressure (hPa)
- `MSL_Error_hPa`: MSL bias (hPa)
- `Spatial_Extent_0C_pct`: % of region below 0°C (at peak only)
- `Spatial_IoU_0C`: Intersection over Union for T < 0°C (at peak only)
- `Pattern_Correlation`: Spatial correlation at peak

**Example CSV format**:
```csv
Event_Name,Stage,Lead_Days,Phase,T2m_Mean_C,T2m_Min_C,T2m_Error_C,T2m_RMSE_C,T850_Mean_C,T850_Error_C,Z500_Mean_m,Z500_Error_m,MSL_Mean_hPa,MSL_Error_hPa,Spatial_Extent_0C_pct,Spatial_IoU_0C,Pattern_Correlation
Beast from the East 2018,1,1,Onset,-0.5,-12.3,0.2,1.5,-2.1,0.1,5450,10,1015,2.0,,,
Beast from the East 2018,1,1,Peak,-2.6,-31.5,0.1,1.2,-3.8,-0.2,5440,-5,1018,1.5,65.2,0.85,0.92
Beast from the East 2018,1,1,Recovery,0.3,-10.2,-0.1,1.0,-1.5,0.0,5480,15,1012,-1.0,,,
```

### 2. **beast_stage1_results.json**

Detailed metrics including:
- Timing errors (onset, peak, recovery in hours)
- RMSE at each phase
- Spatial extent and IoU scores
- Duration errors
- Intensity bias
- Pattern correlations

### 3. **Visualization Plots**

**Time Series:**
- `freeze_temporal_evolution.png`: Regional mean T2m for all lead times vs ERA5
- `freeze_lead_time_skill.png`: Skill degradation plots (4 panels)
  - Onset timing error vs lead time
  - Peak timing error vs lead time
  - Peak RMSE vs lead time
  - Duration error vs lead time

**Spatial Field Comparisons** (at peak, for each lead time):

For each lead time (1, 7, 14, 21 days), 4 spatial plots:

1. **`freeze_extent_{lead}day_peak.png`** - 3-panel freeze extent analysis
   - Panel 1: Aurora forecast T2m with freeze contours (0°C, -5°C, -10°C in black/blue/darkblue)
   - Panel 2: ERA5 truth T2m with freeze contours
   - Panel 3: Difference map with overlaid freeze extent comparison (Aurora dashed, ERA5 solid)
   - **Purpose**: Visualize freeze extent accuracy and spatial errors

2. **`t850_{lead}day_peak.png`** - 3-panel 850 hPa temperature comparison
   - Panel 1: Aurora forecast 850T
   - Panel 2: ERA5 truth 850T
   - Panel 3: Difference (Aurora - ERA5)
   - **Purpose**: Cold air mass representation

3. **`z500_{lead}day_peak.png`** - 3-panel 500 hPa geopotential comparison
   - Panel 1: Aurora forecast Z500
   - Panel 2: ERA5 truth Z500
   - Panel 3: Difference (Aurora - ERA5)
   - **Purpose**: Blocking pattern accuracy

4. **`msl_{lead}day_peak.png`** - 3-panel mean sea level pressure comparison
   - Panel 1: Aurora forecast MSL
   - Panel 2: ERA5 truth MSL
   - Panel 3: Difference (Aurora - ERA5)
   - **Purpose**: Surface pressure pattern errors

**Total plots**: 2 time series + 16 spatial comparisons (4 variables × 4 lead times) = **18 plots**

---

## Metrics Computed

### Temporal Metrics
1. **Onset timing error** (hours): When does regional mean first drop below 0°C?
2. **Peak timing error** (hours): When is coldest regional mean?
3. **Recovery timing error** (hours): When does regional mean return above 0°C?
4. **Duration error** (hours): How long is regional mean < 0°C?

### Spatial Metrics (at onset/peak/recovery)
5. **T2m RMSE** (°C): Spatial RMSE over region
6. **T2m bias** (°C): Mean difference (Aurora - ERA5)
7. **Spatial extent** (%): Fraction of region below 0°C, -5°C, -10°C
8. **IoU** (0-1): Intersection over Union for cold areas
9. **Pattern correlation** (0-1): Spatial correlation at peak

### Physical Mechanism Metrics
10. **T850 bias** (°C): Cold air mass representation
11. **Z500 bias** (m): Blocking pattern height error
12. **MSL bias** (hPa): Surface pressure pattern error

---

## Files Created

```
research/Freeze/
├── Freeze_utils.py                    # ✅ Freeze-specific utilities
└── 2018_BeastFromEast/
    ├── beast_stage1_detection.py      # ✅ Stage 1 script
    ├── BEAST_STAGE1_README.md         # ✅ This file
    ├── baseline_analysis/             # ✅ Already complete
    │   ├── beast_temporal_evolution.png
    │   └── beast_spatial_statistics.png
    └── prediction_output/             # Created by script
        ├── beast_stage1_results.json
        ├── beast_stage1_metrics.csv
        ├── freeze_temporal_evolution.png
        └── freeze_lead_time_skill.png
```

---

## Next Steps

1. **Run the script**: `python beast_stage1_detection.py`
2. **Check CSV output**: Verify metrics look reasonable
3. **Review plots**: Check skill degradation patterns
4. **Compare to TC results**: Use CSV for cross-event comparison later
5. **Replicate for Texas 2021**: Copy script, update dates/domain

---

## Key Differences from TC Stage 1

| Aspect | TC (Sandy) | Freeze (Beast) |
|--------|-----------|----------------|
| **Target** | Single landfall point | Three phases (onset/peak/recovery) |
| **Tracking** | Uses Tracker() | No tracking (spatial fields) |
| **Lead times** | 1, 3, 5, 7 days | 1, 7, 14, 21 days |
| **Forecast length** | Variable to landfall | Variable to cover full event |
| **Metrics** | Track error (km) | RMSE (°C), timing (hours) |
| **Verification** | IBTrACS + ERA5 | ERA5 only |
| **CSV columns** | Track/landfall errors | T2m/T850/Z500/MSL errors |

---

**Last Updated**: 2025-11-19
**Status**: Ready to run
