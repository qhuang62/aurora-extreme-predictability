# Experimental Strategy: Two-Stage Approach

**Last Updated**: November 10, 2025
**Status**: APPROVED - This is the strategy for the paper

---

## Strategy Overview: Variable Initialization (Strategy B)

**Core Principle**: Target the SAME critical event from different lead times by varying initialization date.

**Why**: Operationally relevant - answers "How far in advance can we predict extreme events?"

---

## Two-Stage Analysis Approach

### **Stage 1: Lead Time Assessment** (Find Best Lead Time)

**Test 4 different initialization dates to target the same event**

**Example: Hurricane Sandy Landfall (Oct 29, 2012)**

| Lead Time | Initialize | Forecast To | Purpose |
|-----------|-----------|-------------|---------|
| **1 day** | Oct 28, 12:00 UTC | Oct 29 landfall | Very short range |
| **3 days** | Oct 26, 12:00 UTC | Oct 29 landfall | Short range |
| **5 days** | Oct 24, 12:00 UTC | Oct 29 landfall | Medium range |
| **7 days** | Oct 22, 12:00 UTC | Oct 29 landfall | Long range |

**Note**: All use 12:00 UTC initialization (standard operational time)

**Deliverable**:
- Identify which lead time has best skill
- Quantify skill degradation with increasing lead time
- Determine practical predictability horizon

### **Stage 2: Initialization Sensitivity** (Test Init Times at Best Lead)

**Use the best-performing lead time from Stage 1, test 4 initialization times**

**Example: If 5-day lead time performed best (Oct 24 init)**

| Init Time | Initialize | Forecast To | Purpose |
|-----------|-----------|-------------|---------|
| **00:00 UTC** | Oct 24, 00:00 | Oct 29 landfall | Early morning init |
| **06:00 UTC** | Oct 24, 06:00 | Oct 29 landfall | Morning init |
| **12:00 UTC** | Oct 24, 12:00 | Oct 29 landfall | Noon init (operational standard) |
| **18:00 UTC** | Oct 24, 18:00 | Oct 29 landfall | Evening init |

**Deliverable**:
- Quantify initialization time sensitivity
- Identify optimal initialization time
- Compute initialization spread (uncertainty)

---

## Complete Sandy Example

### Stage 1: Lead Time Assessment

```python
# sandy_stage1_lead_time.py

lead_time_configs = [
    {'lead_days': 1, 'init_date': '2012-10-28', 'init_hour': '12'},
    {'lead_days': 3, 'init_date': '2012-10-26', 'init_hour': '12'},
    {'lead_days': 5, 'init_date': '2012-10-24', 'init_hour': '12'},
    {'lead_days': 7, 'init_date': '2012-10-22', 'init_hour': '12'},
]

results_stage1 = {}

for config in lead_time_configs:
    # Load ERA5 data for this init date
    data = load_era5_data(data_path, config['init_date'])

    # Create batch
    batch = create_aurora_batch(data, time_idx=2)  # 12 UTC

    # Run forecast (all run same number of steps to reach Oct 29)
    steps = config['lead_days'] * 4  # days × 4 steps/day
    preds = run_forecast(model, batch, tracker, steps=steps)

    # Extract track and compute errors
    track = extract_track_from_tracker(tracker)
    errors = compute_track_error(track, obs_track)

    # Save
    results_stage1[config['lead_days']] = {
        'track': track,
        'errors': errors,
        'landfall_error': compute_landfall_error(track, obs_track)
    }

# Identify best lead time
best_lead_time = min(results_stage1, key=lambda x: results_stage1[x]['landfall_error'])
print(f"Best lead time: {best_lead_time} days")
```

**Expected Output**:
```
Lead Time Analysis Results:
  1-day:  Landfall error = XX km, Mean track error = XX km
  3-days: Landfall error = XX km, Mean track error = XX km
  5-days: Landfall error = XX km, Mean track error = XX km  ← Best!
  7-days: Landfall error = XX km, Mean track error = XX km

Best performing: 5-day lead time (Oct 24 initialization)
```

### Stage 2: Initialization Sensitivity (Using Best Lead Time)

```python
# sandy_stage2_init_sensitivity.py

# Use best init date from Stage 1 (e.g., Oct 24 for 5-day lead)
best_init_date = '2012-10-24'
init_hours = ['00', '06', '12', '18']

results_stage2 = {}

for hour in init_hours:
    # Load ERA5 data (same date, different start time)
    data = load_era5_data(data_path, best_init_date)

    # Create batch for this init time
    time_idx = {'00': 0, '06': 1, '12': 2, '18': 3}[hour]
    batch = create_aurora_batch(data, time_idx=time_idx)

    # Run 5-day forecast
    steps = 20  # 5 days × 4 steps/day
    preds = run_forecast(model, batch, tracker, steps=steps)

    # Compute errors
    track = extract_track_from_tracker(tracker)
    errors = compute_track_error(track, obs_track)

    results_stage2[hour] = {
        'track': track,
        'errors': errors,
        'landfall_error': compute_landfall_error(track, obs_track)
    }

# Compute initialization spread
landfall_errors = [results_stage2[h]['landfall_error'] for h in init_hours]
init_spread = np.std(landfall_errors)
print(f"Initialization spread: {init_spread:.1f} km")
```

**Expected Output**:
```
Initialization Sensitivity Results (5-day lead time, Oct 24):
  00:00 UTC: Landfall error = XX km
  06:00 UTC: Landfall error = XX km
  12:00 UTC: Landfall error = XX km
  18:00 UTC: Landfall error = XX km

Initialization spread: XX km (Low/Moderate/High sensitivity)
```

---

## Data Requirements (Updated for Strategy B)

### Hurricane Sandy Complete Analysis

**Stage 1: Lead Time Assessment**
```
7-day lead:  Oct 22-23 (init) + Oct 29-30 (verify) = 4 days
5-day lead:  Oct 24-25 (init) + Oct 29-30 (verify) = 4 days
3-day lead:  Oct 26-27 (init) + Oct 29-30 (verify) = 4 days
1-day lead:  Oct 28-29 (init) + Oct 29-30 (verify) = 3 days

Total needed: Oct 22 - Oct 30 (~9 days)
```

**Stage 2: Initialization Sensitivity**
```
Best date (e.g., Oct 24): Oct 24-25 (already have from Stage 1)
```

### General Formula for Any Event

**Stage 1 Data Needs:**
```
For each lead time N days:
  - Init: (Event_Date - N days) through (Event_Date - N days + 1)
  - Verify: Event_Date through (Event_Date + 2)

Total: (Event_Date - Max_Lead_Days - 1) through (Event_Date + 2)
```

**Example with 7-day max lead:**
```
Landfall: Oct 29
Min init: Oct 29 - 7 = Oct 22
Max verify: Oct 29 + 2 = Oct 31
Total: Oct 22 - Oct 31 (10 days)
```

---

## Comparison: Strategy A vs Strategy B

### Strategy A: Fixed Init, Variable Forecast Length
```
Initialize: Oct 24
├─ 1-day forecast → Oct 25 (NOT the critical event)
├─ 3-day forecast → Oct 27 (NOT the critical event)
├─ 5-day forecast → Oct 29 (the event!)
└─ 7-day forecast → Oct 31 (after the event)

Problem: Comparing apples and oranges
```

### Strategy B: Variable Init, Fixed Target (OUR APPROACH)
```
Target: Oct 29 landfall

├─ Oct 28 init (1-day) ─→ Oct 29 landfall ✓
├─ Oct 26 init (3-day) ─→ Oct 29 landfall ✓
├─ Oct 24 init (5-day) ─→ Oct 29 landfall ✓
└─ Oct 22 init (7-day) ─→ Oct 29 landfall ✓

Solution: All forecasts target THE critical event
```

---

## Paper Figures Using This Strategy

### Figure 2: TC Predictability (Panel B)
**"Track Error vs Lead Time"**
```
X-axis: Lead time (1, 3, 5, 7 days)
Y-axis: Landfall position error (km)

Shows: How error increases with longer lead time
All points target the SAME landfall event
```

### Figure 6: Cross-Event Comparison (Panel B)
**"Lead Time Degradation Curves"**
```
Multiple lines (TC, Freeze, AR, Precip)
X-axis: Lead time (1, 3, 5, 7 days)
Y-axis: Event prediction error

Shows: Which event types have longer predictability horizons
All forecasts target the peak/critical moment of each event
```

### Figure 6: Cross-Event Comparison (Panel C)
**"Initialization Sensitivity Heatmap"**
```
Rows: Event types
Columns: Lead times
Color: Initialization spread (std dev across 00/06/12/18 UTC)

Shows: Which events/lead times are most sensitive to init time
Only computed for best-performing lead time per event
```

---

## Application to Other Event Types

### Freeze Event (Texas 2021)

**Peak cold**: Feb 15-18, 2021 (use Feb 16 as target)

**Stage 1**: Lead time assessment
```
1-day:  Init Feb 15 → Predict Feb 16
3-days: Init Feb 13 → Predict Feb 16
5-days: Init Feb 11 → Predict Feb 16
7-days: Init Feb 9  → Predict Feb 16
```

**Stage 2**: Init sensitivity (if 5-day best)
```
Init Feb 11 at 00, 06, 12, 18 UTC → All predict Feb 16
```

### Atmospheric River (California 2022-23)

**Peak IVT**: Jan 9, 2023 (example)

**Stage 1**: Lead time assessment
```
1-day:  Init Jan 8  → Predict Jan 9 peak
3-days: Init Jan 6  → Predict Jan 9 peak
5-days: Init Jan 4  → Predict Jan 9 peak
7-days: Init Jan 2  → Predict Jan 9 peak
```

### Precipitation (Spain Oct 2024)

**Extreme rainfall**: Oct 29, 2024

**Stage 1**: Lead time assessment
```
1-day:  Init Oct 28 → Predict Oct 29 peak
3-days: Init Oct 26 → Predict Oct 29 peak
5-days: Init Oct 24 → Predict Oct 29 peak
7-days: Init Oct 22 → Predict Oct 29 peak
```

---

## Workflow Summary

### For Each Event in Your Paper:

1. **Identify critical moment** (landfall, peak cold, max IVT, extreme precip)

2. **Stage 1: Run 4 lead times** (1, 3, 5, 7 days)
   - Each targets the critical moment
   - All use 12:00 UTC initialization
   - Identify best-performing lead time
   - Create lead time degradation plot

3. **Stage 2: Run 4 init times** (00, 06, 12, 18 UTC)
   - Use best lead time from Stage 1
   - All use same initialization date
   - Quantify initialization sensitivity
   - Compute spread statistics

4. **Save all results** using `save_forecast_results()`
   - Avoid re-running expensive forecasts
   - Can regenerate figures anytime

5. **Generate paper figures**
   - Load saved results
   - Create visualizations
   - Iterate on plot style without re-running

---

## Summary Table: What Gets Tested

| Stage | What Varies | What's Fixed | Tests |
|-------|-------------|--------------|-------|
| **Stage 1** | Initialization date (4 dates) | Init time (12 UTC), Target event | Lead time skill degradation |
| **Stage 2** | Initialization time (00/06/12/18 UTC) | Init date (best from Stage 1), Target event | Initialization sensitivity |

**Total forecasts per event**: 4 (Stage 1) + 4 (Stage 2) = **8 forecasts**

**For 12-15 events**: 8 × 15 = **~120 total forecasts**

**With saving**: Run once (~10-15 hours), visualize infinitely!

---

## Action Items

- [x] Update DATA_GUIDE.md with Strategy B data requirements
- [ ] Create `sandy_stage1_lead_time.py` script
- [ ] Create `sandy_stage2_init_sensitivity.py` script
- [ ] Update visualization functions to handle Stage 1 & 2 outputs
- [ ] Create download script for Oct 22-30 Sandy data
- [ ] Test complete workflow on Sandy
- [ ] Replicate for other events

---

**This two-stage approach is scientifically rigorous and operationally meaningful!** 🎯
