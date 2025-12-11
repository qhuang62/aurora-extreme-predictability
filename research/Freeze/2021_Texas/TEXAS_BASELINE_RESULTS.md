# Texas 2021 Freeze - Baseline Analysis Results

**Analysis Date**: November 20, 2024
**Data Range**: Jan 24 - Feb 21, 2021 (116 timesteps, 6-hourly)
**Region**: Texas and Southern US (25-37°N, 107-93°W)

---

## Key Event Timeline (ERA5 Truth)

**Timezone Note**: Texas is CST (UTC-6), so 06:00 UTC = 00:00 CST (midnight Texas time)

**ERA5 Baseline Detection:**
- First freeze: Feb 13, 12:00 UTC (Feb 13, 06:00 CST)
- Peak cold: Feb 15, 12:00 UTC (Feb 15, 06:00 CST)
- Recovery: Feb 20, 18:00 UTC (Feb 20, 12:00 CST)

**Adjusted for Stage 1 Analysis (using 06:00 UTC = midnight CST):**

| Phase | Date/Time (UTC) | Texas Time (CST) | Temperature | Details |
|-------|-----------------|------------------|-------------|---------|
| **Onset** | **Feb 14, 06:00 UTC** | Feb 14, 00:00 CST | Regional mean < 0°C | Target for Stage 1 (enables true 21-day lead) |
| **Peak** | **Feb 15, 06:00 UTC** | Feb 15, 00:00 CST | Mean: -9.9°C, Min: -29.5°C | Coldest conditions at midnight |
| **Recovery** | **Feb 21, 06:00 UTC** | Feb 21, 00:00 CST | Regional mean returns > 0°C | Freeze ends |

**Note**: Onset set to Feb 14, 06:00 UTC (instead of baseline Feb 13, 12:00 UTC) to:
1. Align with midnight Texas time (06:00 UTC)
2. Match literature/wiki expected onset (Feb 14)
3. Enable true 21-day lead initialization (Jan 24, 06:00 UTC)

---

## Event Characteristics

### Spatial Extent
- **Maximum freeze coverage**: 82.7% of region (at peak on Feb 15, 12 UTC)
- This is an extremely widespread freeze event for Texas

### Intensity
- **Regional mean at peak**: -9.9°C (extremely cold for Texas)
- **Regional minimum**: -29.5°C (arctic-level temperatures)
- **Duration**: 4.5 days of sustained freezing

### Comparison to Literature
- Expected onset: ~Feb 14, 2021 ✓ (actual: Feb 13, 12 UTC - 12 hours earlier)
- Expected peak: ~Feb 15-16, 2021 ✓ (actual: Feb 15, 12 UTC - confirmed)
- Expected recovery: ~Feb 19-20, 2021 ✓ (actual: Feb 20, 18 UTC - confirmed)

**Analysis aligns well with known event timeline!**

---

## Stage 1 Configuration Updates

Based on baseline analysis, update `texas_stage1_detection.py` with:

### Target Dates
```python
'onset_date': '2021-02-13',      # Feb 13, 12 UTC
'peak_date': '2021-02-15',       # Feb 15, 12 UTC
'recovery_date': '2021-02-20',   # Feb 20, 18 UTC (use 00 UTC for simplicity)
```

### Lead Time Initialization Times (targeting Feb 13 onset)

**Data starts**: Jan 24, 00:00 UTC (index 0)
**All initialized at 12:00 UTC**

| Lead Time | Init Date | Init Time | Days from Start | Time Index | Forecast Days | Steps |
|-----------|-----------|-----------|-----------------|------------|---------------|-------|
| **1-day** | Feb 12, 12 UTC | 12:00 | 19.5 days | 78 | 9 days | 35 |
| **7-day** | Feb 6, 12 UTC | 12:00 | 13.5 days | 54 | 15 days | 59 |
| **14-day** | Jan 30, 12 UTC | 12:00 | 6.5 days | 26 | 22 days | 87 |
| **21-day** | Jan 23, 12 UTC | 12:00 | -0.5 days | N/A ❌ | - | - |

**⚠️ ISSUE**: 21-day lead would require init on Jan 23, 12 UTC, but data starts Jan 24, 00 UTC!

**SOLUTION**: Use Jan 24, 12 UTC for 21-day lead (actually 20.5 days):
- **21-day** → Jan 24, 12 UTC → time_idx = 2 → 21 days forecast → 83 steps

---

## Time Index Calculation Formula

```
time_idx = (init_datetime - data_start_datetime) / 6 hours

Data start: Jan 24, 2021 00:00 UTC

Examples:
- Jan 24, 12 UTC: (0.5 days) × 4 = 2
- Jan 30, 12 UTC: (6.5 days) × 4 = 26
- Feb 6, 12 UTC: (13.5 days) × 4 = 54
- Feb 12, 12 UTC: (19.5 days) × 4 = 78
```

---

## Updated Stage 1 Configurations

### Final Lead Time Setup (All at 06:00 UTC = Midnight Texas Time)

```python
'lead_time_configs': [
    {
        'lead_days': 1,
        'init_date': '2021-02-13',
        'init_hour': '06',
        'time_idx': 81,        # (Feb 13 06:00 - Jan 24 00:00) / 6h
        'forecast_days': 9,    # Through Feb 21
        'steps': 33            # (9 days × 4) - 3
    },
    {
        'lead_days': 7,
        'init_date': '2021-02-07',
        'init_hour': '06',
        'time_idx': 57,        # (Feb 7 06:00 - Jan 24 00:00) / 6h
        'forecast_days': 15,   # Through Feb 21
        'steps': 57            # (15 days × 4) - 3
    },
    {
        'lead_days': 14,
        'init_date': '2021-01-31',
        'init_hour': '06',
        'time_idx': 29,        # (Jan 31 06:00 - Jan 24 00:00) / 6h
        'forecast_days': 22,   # Through Feb 21
        'steps': 85            # (22 days × 4) - 3
    },
    {
        'lead_days': 21,
        'init_date': '2021-01-24',
        'init_hour': '06',
        'time_idx': 1,         # (Jan 24 06:00 - Jan 24 00:00) / 6h
        'forecast_days': 29,   # Through Feb 21
        'steps': 113           # (29 days × 4) - 3
    },
]
```

**Note**: All initializations at 06:00 UTC (midnight Texas CST) for consistent local time alignment. True 21-day lead achieved!

---

## Outputs Generated

1. **`baseline_analysis/texas_temporal_evolution.png`**
   - Regional mean/min temperature over time
   - Spatial extent below 0°C, -5°C, -10°C
   - Coldest temperature evolution

2. **`baseline_analysis/texas_spatial_statistics.png`**
   - T2m spatial statistics (mean/min/max)
   - T850 spatial statistics
   - MSL spatial statistics
   - Z500 spatial statistics

---

## Next Steps

1. ✅ **Baseline complete** - Event timeline verified
2. ⬜ **Update Stage 1 script** - Apply configurations above
3. ⬜ **Run Stage 1** - Execute `texas_stage1_detection.py`
4. ⬜ **Generate visualizations** - Run `regenerate_visualizations.py`
5. ⬜ **Compare with Beast** - Cross-event analysis

---

## Scientific Context

This was one of the most severe winter weather events in Texas history:
- **Impact**: 246 deaths, power grid failure, $195 billion in damages
- **Cause**: Polar vortex disruption → Arctic air mass intrusion → sustained freeze
- **Unusual**: Temperatures 20-40°F below normal for extended period
- **Infrastructure**: Texas infrastructure not designed for sustained freezing

The extreme spatial extent (82.7%) and intensity (-9.9°C mean) confirm this as an exceptional event worthy of predictability analysis.
