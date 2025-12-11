# 2023 European Heatwave - Complete Analysis Workflow

**Event**: August 2023 Southwest Europe Heatwave
**Region**: France, Northern Spain, Switzerland
**Status**: Data download in progress

---

## Event Overview

### Timeline

| Phase | Date | Description | Key Characteristics |
|-------|------|-------------|---------------------|
| **Onset** | **Aug 20, 2023** | Heat begins (regional mean T2m > 30°C) | Detected from baseline analysis |
| **Peak** | **Aug 23, 2023** | Hottest day (regional mean: 30.6°C) | Lyon: 41.4°C, Bilbao: 44.0°C |
| **Recovery** | **Aug 24, 2023** | Cooling begins (T2m < 30°C) | Regional mean drops below 30°C |

**Note**: Literature reports 17-day heat event in Lyon (Aug 9-25), but regional mean analysis detects later onset (Aug 20) due to cooler northern areas. See `ONSET_DEFINITION_INSIGHTS.md` for details.

### Impact

- **Duration** (baseline detected): 36 hours (1.5 days) - Regional mean > 30°C
- **Duration** (literature): 17+ days in southern areas (Lyon: Aug 9-25)
- **Temperature records**: Multiple cities exceeded 40°C
- **Geographic extent**: Southwestern Europe (France, N. Spain, Switzerland)
- **Peak spatial extent**: 71.2% of region above 30°C (Aug 23)
- **Peak temperatures**:
  - Lyon: 41.4°C (Aug 24)
  - Bilbao: 44.0°C (Aug 23)
  - Toulouse: 42.4°C (Aug 23)

### Physical Mechanisms

- **Heat dome**: Persistent subtropical high at 500 hPa
- **Warm air advection**: Southerly flow bringing Mediterranean/Saharan air
- **Blocking pattern**: Amplified Rossby wave pattern
- **Feedback**: Suppressed precipitation reinforcing surface heating

### Sample Status

**Out-of-sample**: August 2023 is beyond Aurora's training period (1979-2020)
- Provides scientifically valid test of generalization
- No training contamination concerns
- Complements freeze events (both out-of-sample)

---

## Regional Domain

```python
REGION = {
    'name': 'SW Europe (France, N. Spain, Switzerland)',
    'lat_min': 42.0,   # Northern Spain
    'lat_max': 48.0,   # Central France
    'lon_min': -2.0,   # Western France/N. Spain coast
    'lon_max': 8.0     # Switzerland/Eastern France
}
```

**Covers major cities**:
- France: Lyon, Toulouse, Bordeaux, Marseille
- Spain: Bilbao, San Sebastian
- Switzerland: Geneva

---

## Data Requirements

### ERA5 Data Period

**Download range**: July 19 - August 27, 2023 (40 days)
- **Total timesteps**: 160 (40 days × 4 per day at 6-hourly)
- **Size**: ~10 GB total

**Why this range?**
- Initialization dates: Jul 30, Aug 6, 13, 19 (for 21, 14, 7, 1-day leads)
- Verification period: Aug 1-27 (covers onset → peak → recovery)
- Onset date: Aug 20, 2023 (detected from baseline analysis)
- Buffer: Extra days before/after for analysis

### Variables

**Surface-level** (required):
- `2m_temperature` (2t)
- `10m_u_component_of_wind` (10u)
- `10m_v_component_of_wind` (10v)
- `mean_sea_level_pressure` (msl)

**Atmospheric** (pressure levels: 50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 850, 925, 1000 hPa):
- `temperature` (t)
- `u_component_of_wind` (u)
- `v_component_of_wind` (v)
- `specific_humidity` (q)
- `geopotential` (z)

**Static** (shared with Freeze):
- `geopotential` (topography)
- `land_sea_mask`
- `soil_type`

---

## Complete Workflow

### Step 1: Download ERA5 Data ⏳ IN PROGRESS

```bash
cd /scratch/qhuang62/aurora-extreme-predictability/research/Heatwave/data/era5_heatwave_2023/
python download_heatwave_complete.py
```

**What it does**:
- Downloads 40 days of data (Jul 19 - Aug 27, 2023)
- 6-hourly resolution (00, 06, 12, 18 UTC)
- Creates individual files per date:
  - `YYYY-MM-DD-surface-level.nc`
  - `YYYY-MM-DD-atmospheric.nc`
- **Resume capability**: Skips already-downloaded dates

**Expected runtime**: 2-6 hours (depends on CDS queue)

**Progress check**:
```bash
ls -lh *.nc | wc -l  # Should be 80 files when complete (40 days × 2 files)
```

---

### Step 2: Combine Data Files ⏸️ WAITING

```bash
cd /scratch/qhuang62/aurora-extreme-predictability/research/Heatwave/data/era5_heatwave_2023/
python combine_heatwave_data.py
```

**What it does**:
- Concatenates daily files into single continuous timeseries
- Creates two combined files:
  - `heatwave_2023_surface_jul19-aug27.nc` (160 timesteps)
  - `heatwave_2023_atmospheric_jul19-aug27.nc` (160 timesteps)
- Verifies time indices for initialization dates
- Shows key dates (onset, peak, recovery)

**Expected runtime**: 5-10 minutes

**Verification**:
```bash
# Check combined files exist
ls -lh heatwave_2023_*.nc

# Quick check with Python
python -c "import xarray as xr; ds = xr.open_dataset('heatwave_2023_surface_jul19-aug27.nc'); print(f'Timesteps: {len(ds.valid_time)}'); print(f'Range: {ds.valid_time.values[0]} to {ds.valid_time.values[-1]}')"
```

**Expected output**:
```
Timesteps: 160
Range: 2023-07-19T00:00:00 to 2023-08-27T18:00:00
```

---

### Step 3: Baseline Analysis (ERA5 Ground Truth) ⏸️ WAITING

```bash
cd /scratch/qhuang62/aurora-extreme-predictability/research/Heatwave/2023_European_Heatwave/
python heatwave_baseline_analysis.py
```

**Purpose**: Understand the heatwave in ERA5 (ground truth) BEFORE testing Aurora predictions.

**What it does**:
1. Loads combined ERA5 data
2. Extracts regional subset (42-48°N, 2°W-8°E)
3. Computes temporal evolution:
   - Regional mean/max T2m time series
   - Spatial extent above 30/35/40°C thresholds
   - Onset/peak/recovery detection
4. Creates baseline visualizations
5. Saves event statistics

**Outputs** (saved to `baseline_analysis/`):
- `heatwave_temporal_evolution.png` - Time series plots (3 panels)
  - Panel 1: Regional mean/max temperature with onset/peak markers
  - Panel 2: Spatial extent (% area above 30/35/40°C thresholds)
  - Panel 3: Regional maximum temperature
- `heatwave_spatial_statistics.png` - Field variable evolution (4 panels)
  - Panel 1: T2m spatial statistics (mean, min-max range)
  - Panel 2: T850 spatial statistics (850 hPa temperature)
  - Panel 3: MSL spatial statistics (mean sea level pressure)
  - Panel 4: Z500 spatial statistics (500 hPa geopotential height)
- Console output: Event statistics

**Actual results** (from baseline analysis):
- Onset: Aug 20, 2023 12:00 UTC (regional mean > 30°C)
- Peak: Aug 23, 2023 12:00 UTC (hottest regional mean)
- Duration: 36 hours (1.5 days) - Regional mean > 30°C
- Peak regional mean: 30.6°C
- Peak regional max: 42.0°C
- Peak spatial extent: 71.2% of region > 30°C

**Expected runtime**: 2-5 minutes

**Verification**:
```bash
ls -lh baseline_analysis/
# Should contain: heatwave_temporal_evolution.png, heatwave_spatial_statistics.png
```

---

### Step 4: Stage 1 - Lead Time Assessment ⏸️ WAITING

```bash
cd /scratch/qhuang62/aurora-extreme-predictability/research/Heatwave/2023_European_Heatwave/
python heatwave_stage1_detection.py
```

**Purpose**: Test Aurora's heatwave detection skill at 1, 7, 14, 21-day lead times.

**What it does**:
1. Loads Aurora 0.25° Pretrained model
2. Runs 4 forecasts, all targeting Aug 20 onset (detected from baseline):
   - **1-day lead**: Init Aug 19, 12 UTC → Forecast 8 days (31 steps)
   - **7-day lead**: Init Aug 13, 12 UTC → Forecast 14 days (55 steps)
   - **14-day lead**: Init Aug 6, 12 UTC → Forecast 21 days (83 steps)
   - **21-day lead**: Init Jul 30, 12 UTC → Forecast 28 days (111 steps)
3. Extracts fields: T2m, T850, Z500, MSL
4. Computes heatwave metrics using `Heatwave_utils.py`:
   - Onset timing error (hours)
   - Peak timing error (hours)
   - Peak RMSE (°C)
   - Duration prediction (hours)
   - Spatial extent (area above 30/35/40°C)
   - IoU scores
   - Intensity bias at peak
5. Caches predictions to `.pkl` files (avoids re-running)
6. Saves results to JSON and CSV

**Expected runtime**: 1-2 hours total (shorter forecasts due to later onset)
- 1-day lead: ~10 minutes (31 steps)
- 7-day lead: ~15 minutes (55 steps)
- 14-day lead: ~25 minutes (83 steps)
- 21-day lead: ~35 minutes (111 steps)
- (GPU speeds up by ~3-5x)

**Outputs** (saved to `prediction_output/`):
- `predictions_1day.pkl` - Cached 1-day forecast (~60 MB)
- `predictions_7day.pkl` - Cached 7-day forecast (~110 MB)
- `predictions_14day.pkl` - Cached 14-day forecast (~165 MB)
- `predictions_21day.pkl` - Cached 21-day forecast (~220 MB)
- `heatwave_stage1_results.json` - Detailed metrics (all phases)
- `heatwave_stage1_metrics.csv` - Summary table (CSV for analysis)

**Resume capability**:
- If `.pkl` files exist, script loads from cache instead of re-running
- Allows quick re-analysis or metric tweaking without expensive forecasts
- To force re-run: Delete specific `.pkl` file

**GPU vs CPU**:
- Script auto-detects CUDA
- Falls back to CPU if GPU unavailable or OOM
- CPU forecasts are ~3-5x slower but work fine

**Verification**:
```bash
ls -lh prediction_output/
# Should contain: 4 .pkl files + .json + .csv

# Check results
head -20 prediction_output/heatwave_stage1_metrics.csv
```

---

### Step 5: Generate Visualizations (FUTURE)

**Create**: `regenerate_heatwave_visualizations.py` (to be written)

**Purpose**: Create publication-quality figures from cached predictions.

**Planned visualizations**:
1. **Temporal evolution** - All lead times overlaid with ERA5 truth
2. **Spatial comparisons** - Aurora vs ERA5 at onset/peak/recovery
3. **Heat extent maps** - 30/35/40°C contours (red color scheme)
4. **Lead time skill degradation** - RMSE, timing errors, duration
5. **Physical mechanisms** - Z500 blocking, T850 warm air, MSL high

**Advantage**: Can re-run anytime to refine plots without expensive forecasts!

---

## Stage 1 Lead Time Configurations

### All forecasts target Aug 20 onset (detected from baseline analysis)

| Lead | Init Date | Init Hour | Target | Forecast Days | Steps | Time Index |
|------|-----------|-----------|--------|---------------|-------|------------|
| **1-day** | Aug 19, 2023 | 12 UTC | Aug 20 onset | 8 days | 31 | 126 |
| **7-day** | Aug 13, 2023 | 12 UTC | Aug 20 onset | 14 days | 55 | 102 |
| **14-day** | Aug 6, 2023 | 12 UTC | Aug 20 onset | 21 days | 83 | 74 |
| **21-day** | Jul 30, 2023 | 12 UTC | Aug 20 onset | 28 days | 111 | 46 |

**Time index calculation**:
- Data starts: Jul 19, 00:00 UTC (index 0)
- 6-hourly resolution (4 timesteps per day)
- Example: Jul 30, 12 UTC = 11.5 days × 4 = index 46
- Example: Aug 19, 12 UTC = 31.5 days × 4 = index 126

**Forecast through recovery**:
- All forecasts extend through Aug 27 (end of data)
- Covers full event: onset (Aug 20) → peak (Aug 23) → recovery (Aug 24)
- Shorter forecasts due to later onset detection (Aug 20 vs Aug 9)

**Why Aug 20 onset?**
- Baseline analysis detected regional mean > 30°C on Aug 20, 12:00 UTC
- Literature reports Aug 9 onset (Lyon-specific, southern areas)
- Regional mean criterion is stricter (includes cooler northern areas)
- See `ONSET_DEFINITION_INSIGHTS.md` for detailed discussion

---

## Key Metrics

### Detection Metrics (Stage 1)

**Onset timing error** (hours):
- Difference between Aurora's predicted onset vs ERA5 truth
- Onset defined as: First time regional mean T2m > 30°C
- Expected: 1-day lead < 6h, 7-day lead < 24h

**Peak timing error** (hours):
- Difference between Aurora's predicted peak vs ERA5 truth
- Peak defined as: Maximum regional mean T2m
- Expected: 1-day lead < 6h, 7-day lead < 48h

**Duration prediction** (hours):
- Forecast duration of T > 30°C vs ERA5 truth
- Truth: 36 hours (1.5 days) - Regional mean > 30°C
- Note: Literature reports longer duration (17 days in southern areas)

### Intensity Metrics

**Peak RMSE** (°C):
- Spatial RMSE at peak day (Aug 23-24)
- Expected: 1-day < 2°C, 7-day < 4°C, 14-day < 6°C, 21-day < 8°C

**Intensity bias** (°C):
- Aurora peak temp - ERA5 peak temp (regional mean)
- Positive = too warm, Negative = too cold
- Critical: Does Aurora underpredict heat extremes?

### Spatial Metrics

**Spatial extent** (% of region):
- Area above 30°C, 35°C, 40°C thresholds
- Computed at peak day
- Compare Aurora vs ERA5

**IoU scores** (0-1):
- Intersection over Union for hot areas
- IoU(30°C), IoU(35°C), IoU(40°C)
- Expected: 1-day > 0.7, 7-day > 0.5

**Pattern correlation** (0-1):
- Spatial correlation of T2m field at peak
- Expected: 1-day > 0.9, 7-day > 0.7

---

## Expected Challenges & Research Questions

### Challenge 1: Temperature Bias
- **Question**: Does Aurora underpredict heat extremes (like it underpredicts cold)?
- **Test**: Compare intensity bias at different lead times
- **Hypothesis**: Systematic cold bias (Aurora too cool during peak)

### Challenge 2: Heat Dome Persistence
- **Question**: Can Aurora maintain blocking high beyond 7 days?
- **Test**: Z500 geopotential pattern at 14, 21-day leads
- **Hypothesis**: Blocking pattern decays faster than reality

### Challenge 3: Onset Timing
- **Question**: How sensitive is onset to southerly flow errors?
- **Test**: Onset timing error vs lead time
- **Hypothesis**: Small wind errors → large temperature impact

### Challenge 4: Freeze-Heat Symmetry
- **Question**: Symmetric skill for cold vs heat extremes?
- **Test**: Compare RMSE degradation curves (freeze vs heatwave)
- **Hypothesis**: Asymmetric bias (better at one extreme)

### Challenge 5: Subseasonal Skill
- **Question**: Does Aurora have useful skill at 21-day lead?
- **Test**: All metrics at 21-day vs operational threshold
- **Hypothesis**: Detection skill yes, spatial accuracy no

---

## Success Criteria

### Temperature Prediction

| Lead Time | Excellent | Acceptable | Poor |
|-----------|-----------|------------|------|
| 1-day | RMSE < 2°C | RMSE < 3°C | RMSE > 4°C |
| 7-day | RMSE < 4°C | RMSE < 6°C | RMSE > 8°C |
| 14-day | RMSE < 6°C | RMSE < 8°C | RMSE > 10°C |
| 21-day | RMSE < 8°C | RMSE < 10°C | RMSE > 12°C |

### Onset Timing

| Lead Time | Excellent | Acceptable | Poor |
|-----------|-----------|------------|------|
| 1-day | < 6 hours | < 12 hours | > 24 hours |
| 7-day | < 12 hours | < 24 hours | > 48 hours |
| 14-day | < 24 hours | < 48 hours | > 72 hours |
| 21-day | < 48 hours | < 72 hours | > 96 hours |

### Spatial Extent

| Lead Time | Excellent IoU | Acceptable IoU | Poor IoU |
|-----------|---------------|----------------|----------|
| 1-day | > 0.8 | > 0.7 | < 0.6 |
| 7-day | > 0.7 | > 0.5 | < 0.4 |
| 14-day | > 0.6 | > 0.4 | < 0.3 |
| 21-day | > 0.5 | > 0.3 | < 0.2 |

---

## Scientific Significance

### Novel Contributions

1. **First Aurora heatwave assessment** - No published studies exist
2. **Cold-heat symmetry test** - Direct comparison with freeze events
3. **Multi-week sustained event** - Tests 17+ day heat prediction
4. **Subseasonal lead times** - 21-day forecasts rare for extremes
5. **Out-of-sample validation** - 2023 event beyond training data

### Paper Integration

**Complements freeze events for comprehensive temperature extreme evaluation**:

| Aspect | Freeze Events | Heatwave Event |
|--------|---------------|----------------|
| **Physical driver** | Arctic air, blocking high | Mediterranean heat, heat dome |
| **Temperature extreme** | Cold (< 0°C) | Hot (> 30°C) |
| **Scale** | Synoptic (1000s km) | Synoptic (1000s km) |
| **Duration** | ~7-14 days | ~17 days |
| **Evolution** | Slow (days) | Slow (days) |
| **Sample status** | In + out-of-sample | Out-of-sample only |

**Research question**: Does Aurora show symmetric skill or asymmetric bias?

---

## Troubleshooting

### Issue: "Combined files not found"
**Solution**: Complete Step 2 (combine_heatwave_data.py) after download finishes

### Issue: "Static file not found"
**Solution**:
```bash
# Copy from Freeze directory (already exists)
cp /scratch/qhuang62/aurora-extreme-predictability/research/Freeze/data/static.nc \
   /scratch/qhuang62/aurora-extreme-predictability/research/Heatwave/data/
```

### Issue: "CUDA out of memory"
**Expected behavior**: Script auto-falls back to CPU
**Impact**: Forecasts slower but work fine
**Solution**: No action needed, or close other GPU processes

### Issue: "Cached predictions exist, loading from disk"
**This is GOOD**: Saves time by reusing predictions
**To force re-run**: Delete specific `.pkl` file in `prediction_output/`

### Issue: "Missing time indices in verification"
**Check**:
```bash
python -c "import xarray as xr; ds = xr.open_dataset('../data/era5_heatwave_2023/heatwave_2023_surface_jul19-aug27.nc'); print(len(ds.valid_time))"
```
**Expected**: 160 timesteps
**Solution**: Re-run combine script if incorrect

---

## Next Steps After Stage 1

1. **Analyze results**: Compare 1/7/14/21-day lead performance
2. **Cross-event comparison**: Heatwave vs freeze predictability
3. **Stage 2 design**: Plan detailed spatial/physical characterization
4. **Visualizations**: Create publication-quality figures
5. **Paper integration**: Write heatwave section for manuscript

---

## File Checklist

### Data Files (After Download & Combine)
- [ ] 40 daily surface files (`2023-*-surface-level.nc`)
- [ ] 40 daily atmospheric files (`2023-*-atmospheric.nc`)
- [ ] Combined surface file (`heatwave_2023_surface_jul19-aug27.nc`)
- [ ] Combined atmospheric file (`heatwave_2023_atmospheric_jul19-aug27.nc`)
- [ ] Static file (`../static.nc`)

### Analysis Outputs (After Baseline)
- [ ] `baseline_analysis/heatwave_temporal_evolution.png`
- [ ] `baseline_analysis/heatwave_spatial_statistics.png`
- [ ] Console log with onset/peak/recovery dates

### Prediction Outputs (After Stage 1)
- [ ] `prediction_output/predictions_1day.pkl`
- [ ] `prediction_output/predictions_7day.pkl`
- [ ] `prediction_output/predictions_14day.pkl`
- [ ] `prediction_output/predictions_21day.pkl`
- [ ] `prediction_output/heatwave_stage1_results.json`
- [ ] `prediction_output/heatwave_stage1_metrics.csv`

---

**Document Created**: November 23, 2025
**Last Updated**: November 23, 2025
**Status Updates**:
- Data download and combine: ✅ Completed
- Baseline analysis: ✅ Completed (onset: Aug 20, peak: Aug 23, recovery: Aug 24)
- Stage1 script: ✅ Updated to match baseline results
- Field variables: ✅ Added T2m, T850, MSL, Z500 tracking
**Next Action**: Run baseline analysis with updated field variable plotting, then run Stage 1 forecasts
