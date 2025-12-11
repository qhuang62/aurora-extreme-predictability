# Hurricane Ian 2022 Data Download and Analysis Workflow

**Last Updated**: November 11, 2025
**Status**: ⬜ PENDING - Ready to execute

## Overview

This document describes the complete workflow for downloading ERA5 data and running the two-stage predictability analysis for Hurricane Ian (2022).

**Target Event**: September 28, 2022 20:00 UTC (Florida landfall)

**For experimental design details**, see `IAN_EXPERIMENTAL_DESIGN.md`

---

## Two-Stage Experimental Design

### Stage 1: Lead Time Assessment

**Question:** How far in advance can we predict Ian's Florida landfall (Sep 28, 2022 20:00 UTC)?

**Approach:** Variable initialization date, fixed target

| Lead Time | Init Date & Time | Init Position (IBTrACS) | Forecast Steps | Target Event |
|-----------|------------------|-------------------------|----------------|--------------|
| 1-day     | Sep 27, 18:00 UTC | 23.50°N, 83.30°W | 5 steps (30h) | Sep 28 20:00 UTC landfall |
| 3-day     | Sep 25, 18:00 UTC | 15.80°N, 80.10°W | 13 steps (78h) | Sep 28 20:00 UTC landfall |
| 5-day     | Sep 23, 18:00 UTC | 14.60°N, 70.60°W | 21 steps (126h) | Sep 28 20:00 UTC landfall |
| 6-day     | Sep 22, 18:00 UTC | 12.30°N, 66.30°W | 25 steps (150h) | Sep 28 20:00 UTC landfall |

**Note**: Ian formed on Sep 22, so 7-day lead is not available. Using 6-day instead (genesis).

### Stage 2: Initialization Sensitivity

**Question:** How sensitive is the prediction to initialization time of day?

**Approach:** Fixed lead time (likely 3-day based on Stage 1), variable init time

**Anticipated Configuration (3-day lead, Sep 25 init)**:

| Init Time | Init Date & Time | Init Position (IBTrACS) | Forecast Steps | Target Event |
|-----------|------------------|-------------------------|----------------|--------------|
| 00 UTC    | Sep 25, 00:00 UTC | 14.60°N, 77.20°W | 16 steps (96h) | Sep 28 20:00 UTC landfall |
| 06 UTC    | Sep 25, 06:00 UTC | 14.60°N, 78.30°W | 15 steps (90h) | Sep 28 20:00 UTC landfall |
| 12 UTC    | Sep 25, 12:00 UTC | 15.00°N, 79.40°W | 14 steps (84h) | Sep 28 20:00 UTC landfall |
| 18 UTC    | Sep 25, 18:00 UTC | 15.80°N, 80.10°W | 13 steps (78h) | Sep 28 20:00 UTC landfall |

**Note**: Final Stage 2 configuration determined after Stage 1 analysis.

---

## Data Requirements

### Complete Dataset: Sep 22-29, 2022

- **Sep 22-23**: 6-day and 5-day lead time initialization
- **Sep 24-25**: 3-day lead time initialization (+ Stage 2 init times)
- **Sep 26-27**: 1-day lead time initialization
- **Sep 28**: Landfall day (18:00 and 00:00 bracket 20:00 landfall)
- **Sep 29**: Post-landfall verification (optional)

### Temporal Resolution

- 6-hourly timesteps (00, 06, 12, 18 UTC)
- **Combined file**: Sep 22, 00:00 UTC → Sep 28, 12:00 UTC (initialization periods)
- **Separate verification file**: Sep 28, 18:00 UTC → Sep 29, 06:00 UTC (landfall bracketing)

### Combined File Time Indices

**File**: `ian_2022_combined_sept22-28.nc`

```
Index  0: Sep 22, 00:00 UTC
Index  1: Sep 22, 06:00 UTC
Index  2: Sep 22, 12:00 UTC
Index  3: Sep 22, 18:00 UTC  ← 6-day lead init (18 UTC)
...
Index  7: Sep 23, 18:00 UTC  ← 5-day lead init (18 UTC)
...
Index 13: Sep 25, 00:00 UTC  ← Stage 2: 00 UTC init
Index 14: Sep 25, 06:00 UTC  ← Stage 2: 06 UTC init
Index 15: Sep 25, 12:00 UTC  ← Stage 2: 12 UTC init
Index 16: Sep 25, 18:00 UTC  ← 3-day lead init (18 UTC), Stage 2: 18 UTC init
...
Index 23: Sep 27, 18:00 UTC  ← 1-day lead init (18 UTC)
...
Index 26: Sep 28, 12:00 UTC  ← Last timestep in combined file
```

**Landfall verification file**: `ian_2022_landfall_verification.nc`
```
Sep 28, 18:00 UTC  ← Bracket landfall (before)
Sep 29, 00:00 UTC  ← Bracket landfall (after)
Sep 29, 06:00 UTC  ← Extended verification
```

### Variables Required

**Surface-level** (single-levels):
- `2t`: 2-meter temperature
- `10u`: 10-meter u-component of wind
- `10v`: 10-meter v-component of wind
- `msl`: Mean sea level pressure

**Atmospheric** (pressure-levels):
- `t`: Temperature
- `u`: U-component of wind
- `v`: V-component of wind
- `q`: Specific humidity
- `z`: Geopotential

**Pressure levels**: 50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 850, 925, 1000 hPa (13 levels)

**Static variables** (already available at 0.25° resolution):
- `z`: Geopotential (topography)
- `lsm`: Land-sea mask
- `slt`: Soil type

**Spatial Domain**:
- **Latitude**: 90°N to -90°S (global)
- **Longitude**: 0°E to 360°E (global)
- **Resolution**: 0.25° x 0.25°

---

## Step-by-Step Workflow

### Step 1: Download ERA5 Data via CDS API

**Create download script**: `download_ian_era5.py`

This script will download ERA5 data for the required dates using the Copernicus Climate Data Store (CDS) API.

**Prerequisites**:
- CDS API account and API key configured (`~/.cdsapirc`)
- Python package: `cdsapi` installed

**Date ranges to download**:

1. **All data needed** (Sep 21-28):
   - Dates: 2022-09-21, 2022-09-22, 2022-09-23, 2022-09-24, 2022-09-25, 2022-09-26, 2022-09-27, 2022-09-28
   - Times: 00:00, 06:00, 12:00, 18:00 UTC (all 4 times for each day)
   - Sep 28 includes 18:00 UTC which is used for landfall verification

**Download strategy**:
- Download daily files first: `2022-09-DD-surface-level.nc` and `2022-09-DD-atmospheric.nc`
- Then combine into single files (Step 2)
- Keep individual files as backup

**Expected runtime**: ~45-90 minutes (depends on CDS queue)

**Output structure**:
```
/scratch/qhuang62/aurora-extreme-predictability/research/TC/data/era5_ian_2022/
├── 2022-09-22-surface-level.nc
├── 2022-09-22-atmospheric.nc
├── 2022-09-23-surface-level.nc
├── 2022-09-23-atmospheric.nc
├── 2022-09-24-surface-level.nc
├── 2022-09-24-atmospheric.nc
├── 2022-09-25-surface-level.nc
├── 2022-09-25-atmospheric.nc
├── 2022-09-26-surface-level.nc
├── 2022-09-26-atmospheric.nc
├── 2022-09-27-surface-level.nc
├── 2022-09-27-atmospheric.nc
├── 2022-09-28-surface-level.nc       # Full day (00, 06, 12, 18) - includes landfall 18:00 UTC
└── 2022-09-28-atmospheric.nc         # Full day
```

**Note**: No Sep 29 data needed - last forecast point is Sep 28 18:00 UTC (landfall verification)

### Step 2: Combine Individual Files

**Create combine script**: `combine_ian_data.py`

**What it does**:
1. Reads individual daily files for Sep 21-28
2. Concatenates along time dimension
3. Creates combined files for initialization
4. Creates separate verification file for landfall

**Output files**:
```
ian_2022_surface_combined.nc           # Sep 21 00:00 → Sep 28 12:00 UTC (31 timesteps)
ian_2022_atmospheric_combined.nc       # Sep 21 00:00 → Sep 28 12:00 UTC (31 timesteps)
ian_2022_surface_landfall.nc           # Sep 28 18:00 UTC only (1 timestep)
ian_2022_atmospheric_landfall.nc       # Sep 28 18:00 UTC only (1 timestep)
```

**Verification**:
```python
import xarray as xr

# Check combined file
ds = xr.open_dataset('ian_2022_surface_combined.nc')
print(f"Time range: {ds.valid_time.values[0]} to {ds.valid_time.values[-1]}")
print(f"Number of timesteps: {len(ds.valid_time)}")
# Expected: 31 timesteps (Sep 21 00:00 UTC to Sep 28 12:00 UTC)

# Check landfall file
ds_landfall = xr.open_dataset('ian_2022_surface_landfall.nc')
print(f"Landfall time: {ds_landfall.valid_time.values[0]}")
print(f"Landfall timesteps: {len(ds_landfall.valid_time)}")
# Expected: 1 timestep (Sep 28 18:00 UTC only)
```

### Step 3: Download IBTrACS Observational Data

**Source**: https://ncics.org/ibtracs/index.php?name=v04r01-2022266N12294

**Method 1: Direct download from IBTrACS website**
- Navigate to the IBTrACS storm page
- Download CSV or NetCDF format
- Save as: `ibtracs_ian_2022.csv` or `ibtracs_ian_2022.nc`

**Method 2: Use IBTrACS Python API** (if available):
```python
# Example code to load IBTrACS data
import pandas as pd

# Load from CSV
track_obs = pd.read_csv('ibtracs_ian_2022.csv')

# Or use existing IBTrACS global dataset and filter for Ian
# storm_id: 2022266N12294
```

**Required fields**:
- `time`: UTC timestamps (6-hourly)
- `lat`: Latitude (°N)
- `lon`: Longitude (°E or °W)
- `wind`: Maximum sustained wind (kt or m/s)
- `pres`: Minimum central pressure (mb or hPa)

**Time range needed**: Sep 22, 18:00 UTC → Sep 30, 18:00 UTC (full lifecycle)

### Step 4: Run Stage 1 Analysis

**Script**: `ian_stage1_lead_day.py` (adapted from `sandy_stage1_lead_day.py`)

**Location**: `/scratch/qhuang62/aurora-extreme-predictability/research/TC/2022_Ian/`

**Execution**:
```bash
cd /scratch/qhuang62/aurora-extreme-predictability/research/TC/2022_Ian
python ian_stage1_lead_day.py
```

**What it does**:
- Loads Aurora 0.25° Pretrained model
- Loads combined ERA5 data + landfall verification data
- Loads IBTrACS observational track
- For each lead time (1, 3, 5, 6 days):
  - Initializes Aurora at appropriate time (18:00 UTC)
  - Runs forecast to Sep 28, 20:00 UTC landfall
  - Tracks hurricane using Aurora's built-in tracker
  - Computes track errors vs IBTrACS
  - Compares MSL and wind fields at landfall vs ERA5
  - Computes landfall timing and location errors
- Saves predictions to avoid re-running
- Generates visualizations and summary statistics

**Outputs** (in `prediction_output/`):
```
prediction_output/
├── ian_stage1_tracks.png                  # Track comparison (4 lead times)
├── ian_stage1_errors.png                  # Error evolution over time
├── ian_stage1_lead_time_results.pkl       # Saved predictions (all leads)
├── ian_stage1_lead_time_results.json      # Summary metrics
├── ian_1day_landfall_msl.png              # MSL field at landfall (1-day)
├── ian_1day_landfall_wind.png             # Wind field at landfall (1-day)
├── ian_3day_landfall_msl.png              # MSL field at landfall (3-day)
├── ian_3day_landfall_wind.png             # Wind field at landfall (3-day)
├── ian_5day_landfall_msl.png              # MSL field at landfall (5-day)
├── ian_5day_landfall_wind.png             # Wind field at landfall (5-day)
├── ian_6day_landfall_msl.png              # MSL field at landfall (6-day)
└── ian_6day_landfall_wind.png             # Wind field at landfall (6-day)
```

**Expected runtime**: ~30-60 minutes (depends on GPU availability)

### Step 5: Analyze Stage 1 Results

**Review outputs**:
1. Open `ian_stage1_tracks.png` - Visual assessment of track accuracy
2. Open `ian_stage1_errors.png` - Error growth patterns
3. Read `ian_stage1_lead_time_results.json` - Quantitative metrics
4. Examine landfall field comparisons - MSL and wind structure

**Key questions to answer**:
- Which lead time has best landfall location accuracy?
- How does track error grow with lead time?
- Does Aurora capture rapid intensification (Sep 26-28)?
- Are there systematic biases (MSL too high, winds too weak)?
- Which lead time is optimal for Stage 2 sensitivity testing?

**Decision point**: Select best lead time for Stage 2 (likely 3-day based on Sandy)

### Step 6: Run Stage 2 Analysis

**Script**: `ian_stage2_init_time.py` (adapted from `sandy_stage2_init_time.py`)

**Location**: `/scratch/qhuang62/aurora-extreme-predictability/research/TC/2022_Ian/`

**Execution**:
```bash
cd /scratch/qhuang62/aurora-extreme-predictability/research/TC/2022_Ian
python ian_stage2_init_time.py
```

**What it does**:
- Uses optimal lead time from Stage 1 (e.g., 3-day)
- Runs 4 forecasts with different initialization times (00, 06, 12, 18 UTC on Sep 25)
- All forecasts target same landfall (Sep 28, 20:00 UTC)
- Compares track spread and initialization sensitivity
- Evaluates field-level differences at landfall

**Outputs** (in `prediction_output/`):
```
prediction_output/
├── ian_stage2_init_tracks.png             # Combined track comparison (4 init times)
├── ian_stage2_init_errors.png             # Error comparison by init time
├── ian_stage2_init_time_results.pkl       # Saved predictions (all init times)
├── ian_stage2_init_time_results.json      # Summary metrics
├── ian_init00_landfall_msl.png            # MSL field (00 UTC init)
├── ian_init00_landfall_wind.png           # Wind field (00 UTC init)
├── ian_init06_landfall_msl.png            # MSL field (06 UTC init)
├── ian_init06_landfall_wind.png           # Wind field (06 UTC init)
├── ian_init12_landfall_msl.png            # MSL field (12 UTC init)
├── ian_init12_landfall_wind.png           # Wind field (12 UTC init)
├── ian_init18_landfall_msl.png            # MSL field (18 UTC init)
└── ian_init18_landfall_wind.png           # Wind field (18 UTC init)
```

**Expected runtime**: ~20-40 minutes

### Step 7: Document Complete Results

**Create**: `IAN_RESULTS.md`

**Structure** (following Sandy template):
1. **Executive Summary**
   - Key findings
   - Best performing configurations
   - Systematic biases identified

2. **Stage 1 Results**
   - Lead time performance table
   - Detailed metrics for each lead time
   - Track and intensity verification

3. **Stage 2 Results**
   - Initialization sensitivity table
   - Track spread and uncertainty quantification
   - Field-level comparison at landfall

4. **Key Findings**
   - Aurora's strengths for Ian
   - Identified limitations
   - Comparison with Sandy results

5. **Implications for Paper**
   - Out-of-sample validation success
   - Rapid intensification prediction capability
   - TC predictability insights

---

## File Organization

```
/scratch/qhuang62/aurora-extreme-predictability/research/TC/2022_Ian/
├── IAN_EXPERIMENTAL_DESIGN.md         # ✅ This document (experiment plan)
├── IAN_DATA_WORKFLOW.md               # ✅ This document (workflow guide)
├── IAN_RESULTS.md                     # ⬜ To be created after analysis
├── ian_stage1_lead_day.py             # ⬜ Stage 1 analysis script
├── ian_stage2_init_time.py            # ⬜ Stage 2 analysis script
├── prediction_output/                 # ⬜ Analysis outputs (~20 figures + JSON)
│   ├── ian_stage1_tracks.png
│   ├── ian_stage1_errors.png
│   ├── ian_*day_landfall_*.png
│   ├── ian_stage2_init_tracks.png
│   └── ...
└── data/                              # ⬜ Optional local data symlink
    └── era5_ian_2022/ -> ../../data/era5_ian_2022/
```

**Shared data directory**:
```
/scratch/qhuang62/aurora-extreme-predictability/research/TC/data/era5_ian_2022/
├── 2022-09-22-surface-level.nc
├── 2022-09-22-atmospheric.nc
├── ... (individual daily files)
├── ian_2022_surface_combined.nc
├── ian_2022_atmospheric_combined.nc
├── ian_2022_surface_landfall.nc
├── ian_2022_atmospheric_landfall.nc
└── ibtracs_ian_2022.csv
```

---

## Quality Checks

### Data Verification

**After downloading ERA5 data**:
```python
import xarray as xr

# Check surface variables
ds_surf = xr.open_dataset('ian_2022_surface_combined.nc')
assert '2t' in ds_surf, "Missing 2t"
assert '10u' in ds_surf, "Missing 10u"
assert '10v' in ds_surf, "Missing 10v"
assert 'msl' in ds_surf, "Missing msl"

# Check atmospheric variables
ds_atmos = xr.open_dataset('ian_2022_atmospheric_combined.nc')
assert 't' in ds_atmos, "Missing t"
assert 'u' in ds_atmos, "Missing u"
assert 'v' in ds_atmos, "Missing v"
assert 'q' in ds_atmos, "Missing q"
assert 'z' in ds_atmos, "Missing z"

# Check pressure levels
expected_levels = [50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 850, 925, 1000]
assert len(ds_atmos.level) == 13, f"Expected 13 levels, got {len(ds_atmos.level)}"
print("✅ All variables and levels present")

# Check time continuity
time_diff = ds_surf.time.diff('time')
assert all(time_diff == pd.Timedelta('6h')), "Time steps not uniformly 6-hourly"
print("✅ Time steps are continuous and 6-hourly")
```

### IBTrACS Verification

```python
import pandas as pd

# Load observational track
track = pd.read_csv('ibtracs_ian_2022.csv')

# Check landfall time is present
landfall_time = pd.Timestamp('2022-09-28 20:00:00')
assert landfall_time in track['time'].values, "Landfall time missing in IBTrACS"

# Check coordinate at landfall
landfall_row = track[track['time'] == landfall_time]
print(f"Landfall position: {landfall_row['lat'].values[0]}°N, {landfall_row['lon'].values[0]}°W")
# Expected: ~26.80°N, 82.00°W

print("✅ IBTrACS data verified")
```

---

## Expected Timeline

| Step | Task | Estimated Time | Status |
|------|------|----------------|--------|
| 1 | Download ERA5 data (CDS API) | 1-2 hours | ⬜ |
| 2 | Combine data files | 10-15 minutes | ⬜ |
| 3 | Download IBTrACS data | 5 minutes | ⬜ |
| 4 | Adapt Stage 1 script | 30-45 minutes | ⬜ |
| 5 | Run Stage 1 analysis | 30-60 minutes | ⬜ |
| 6 | Analyze Stage 1 results | 30 minutes | ⬜ |
| 7 | Adapt Stage 2 script | 20-30 minutes | ⬜ |
| 8 | Run Stage 2 analysis | 20-40 minutes | ⬜ |
| 9 | Document results | 1-2 hours | ⬜ |

**Total estimated time**: ~5-8 hours (including data download wait time)

---

## Troubleshooting

### Common Issues

**1. CDS API download fails**
- Check API key in `~/.cdsapirc`
- Verify CDS account is active
- Check API request queue status at https://cds.climate.copernicus.eu/

**2. Time index mismatch**
- Verify combined file starts at Sep 22, 00:00 UTC
- Check that initialization indices match expected positions
- Use `xarray` to print time coordinates: `ds.time.values`

**3. Aurora tracker fails**
- Check if storm is over land (tracker limitation)
- Verify MSL field has realistic values (900-1010 hPa)
- Ensure search box doesn't hit domain boundaries

**4. Missing IBTrACS data**
- Verify storm ID: `2022266N12294`
- Check date range includes full lifecycle
- Ensure 6-hourly resolution (not 3-hourly or interpolated)

---

## Next Steps After Completion

1. ✅ Complete Ian analysis (both stages)
2. ⬜ Update `RESEARCH_PLAN.md` with Ian results
3. ⬜ Compare Ian vs Sandy results (out-of-sample vs in-sample)
4. ⬜ Begin next TC case (e.g., Hinnamnor 2022)
5. ⬜ Draft TC section of paper with multi-event comparison

---

**Status Summary**:
- Folder created: ✅
- Experimental design documented: ✅
- Workflow documented: ✅
- Data download: ⬜ Ready to begin
- Scripts adapted: ⬜ Pending
- Analysis complete: ⬜ Pending
- Results documented: ⬜ Pending
