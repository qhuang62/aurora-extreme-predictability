# Hurricane Sandy Data Download and Analysis Workflow

**Last Updated**: November 11, 2025
**Status**: ✅ COMPLETE - Analysis finished, results documented

## Overview

This document describes the complete workflow for downloading ERA5 data and running the two-stage predictability analysis for Hurricane Sandy (2012).

**For complete results**, see `SANDY_RESULTS.md`

## Two-Stage Experimental Design

### Stage 1: Lead Time Assessment
**Question:** How far in advance can we predict Sandy's US landfall (Oct 30, 2012 00:00 UTC)?

**Approach:** Variable initialization date, fixed target (Strategy B)
- All forecasts target the same critical event (Oct 30 00:00 UTC landfall)
- Test 4 lead times: 1, 3, 5, 7 days
- All use 00:00 UTC initialization

| Lead Time | Init Date & Time  | Target Event         | Steps |
|-----------|-------------------|----------------------|-------|
| 1-day     | Oct 29, 00:00 UTC | Oct 30 00 UTC landfall | 3     |
| 3-day     | Oct 27, 00:00 UTC | Oct 30 00 UTC landfall | 11    |
| 5-day     | Oct 25, 00:00 UTC | Oct 30 00 UTC landfall | 19    |
| 7-day     | Oct 23, 00:00 UTC | Oct 30 00 UTC landfall | 27    |

### Stage 2: Initialization Sensitivity
**Question:** How sensitive is the prediction to initialization time of day?

**Approach:** Fixed lead time (3-day), variable init time
- Use 3-day lead time (sufficient forecast length for sensitivity to manifest)
- Test 4 initialization times: 00, 06, 12, 18 UTC on Oct 27

| Init Time | Init Date & Time  | Forecast Length | Target Event         |
|-----------|-------------------|-----------------|----------------------|
| 00 UTC    | Oct 27, 00:00 UTC | 11 steps (66h)  | Oct 30 00 UTC landfall |
| 06 UTC    | Oct 27, 06:00 UTC | 10 steps (60h)  | Oct 30 00 UTC landfall |
| 12 UTC    | Oct 27, 12:00 UTC | 9 steps (54h)   | Oct 30 00 UTC landfall |
| 18 UTC    | Oct 27, 18:00 UTC | 8 steps (48h)   | Oct 30 00 UTC landfall |

## Data Requirements

### Complete Dataset: Oct 22-30, 2012
- **Oct 22-23**: 7-day lead time initialization
- **Oct 24-25**: 5-day lead time initialization
- **Oct 26-27**: 3-day lead time initialization
- **Oct 28-29**: 1-day lead time initialization
- **Oct 30**: Landfall verification (00:00 UTC)

### Temporal Resolution
- 6-hourly timesteps (00, 06, 12, 18 UTC)
- **Combined files**: Oct 22-29 (32 timesteps)
- **Separate file**: Oct 30 (4 timesteps) for landfall verification

### Variables Required

**Surface-level** (single-levels):
- `2t`: 2m temperature
- `10u`: 10m u-component of wind
- `10v`: 10m v-component of wind
- `msl`: Mean sea level pressure

**Atmospheric** (pressure-levels):
- `t`: Temperature
- `u`: U-component of wind
- `v`: V-component of wind
- `q`: Specific humidity
- `z`: Geopotential

**Pressure levels**: 50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 850, 925, 1000 hPa

**Static variables** (already available):
- `z`: Geopotential (topography)
- `lsm`: Land-sea mask
- `slt`: Soil type

## Step-by-Step Workflow

### Step 1: Download Complete Dataset

Navigate to the data directory:
```bash
cd /scratch/qhuang62/aurora-extreme-predictability/research/TC/data/era5_sandy_2012
```

Run the download script:
```bash
python download_sandy_complete.py
```

**What it does:**
- Downloads Oct 22-23, 25-31 (we already have Oct 24)
- For each date: downloads surface and atmospheric variables
- Each download includes all 4 6-hourly timesteps (00, 06, 12, 18 UTC)
- Creates individual files: `2012-10-DD-surface-level.nc` and `2012-10-DD-atmospheric.nc`

**Expected runtime:** ~30-60 minutes (depends on CDS API queue)

**Output files:**
```
2012-10-22-surface-level.nc
2012-10-22-atmospheric.nc
2012-10-23-surface-level.nc
2012-10-23-atmospheric.nc
2012-10-24-surface-level.nc (already exists)
2012-10-24-atmospheric.nc (already exists)
2012-10-25-surface-level.nc
2012-10-25-atmospheric.nc
...
2012-10-31-surface-level.nc
2012-10-31-atmospheric.nc
```

### Step 2: Combine Individual Files

Run the combine script:
```bash
python combine_data.py
```

**What it does:**
- Reads all individual daily files (Oct 22-31)
- Concatenates them along the time dimension
- Creates two combined files with continuous timesteps
- Preserves original individual files (doesn't delete them)

**Output files:**
```
sandy_2012_surface_oct22-29.nc      (32 timesteps)
sandy_2012_atmospheric_oct22-29.nc  (32 timesteps)
```

**Note**: Oct 30 data kept separate (`2012-10-30-surface-level.nc`, `2012-10-30-atmospheric.nc`) for rigorous landfall verification at 00:00 UTC.

**Timestep indices in combined files:**
```
Index  0: Oct 22, 00:00 UTC  ← 7-day lead init (00 UTC)
Index  1: Oct 22, 06:00 UTC
Index  2: Oct 22, 12:00 UTC
Index  3: Oct 22, 18:00 UTC
...
Index  8: Oct 24, 00:00 UTC
Index  9: Oct 24, 06:00 UTC
Index 10: Oct 24, 12:00 UTC
Index 11: Oct 24, 18:00 UTC
...
Index 12: Oct 25, 00:00 UTC  ← 5-day lead init (00 UTC)
...
Index 20: Oct 27, 00:00 UTC  ← 3-day lead init (00 UTC)
Index 21: Oct 27, 06:00 UTC  ← 3-day lead init (06 UTC)
Index 22: Oct 27, 12:00 UTC  ← 3-day lead init (12 UTC)
Index 23: Oct 27, 18:00 UTC  ← 3-day lead init (18 UTC)
...
Index 28: Oct 29, 00:00 UTC  ← 1-day lead init (00 UTC)
Index 29: Oct 29, 06:00 UTC
Index 30: Oct 29, 12:00 UTC
Index 31: Oct 29, 18:00 UTC  ← Last timestep in combined file

Oct 30, 00:00 UTC ← Landfall (in separate file for verification)
```

### Step 3: Run Stage 1 Analysis

Run the Stage 1 script:
```bash
cd /scratch/qhuang62/aurora-extreme-predictability/research/TC/2012_Sandy
python sandy_stage1_lead_day.py
```

**What it does:**
- Loads Aurora 0.25° Pretrained model
- Loads combined ERA5 data files + Oct 30 verification data
- For each lead time (1, 3, 5, 7 days):
  - Initializes at the appropriate date (00:00 UTC)
  - Runs Aurora forecast to target Oct 30 00:00 UTC landfall
  - Tracks the hurricane using Aurora's Tracker
  - Computes track errors vs IBTrACS observations
  - Compares meteorological fields (MSL, wind) at landfall vs ERA5
  - Computes landfall timing and location errors
- Saves all predictions to avoid re-running
- Generates visualizations and summary statistics

**Outputs:**
```
prediction_output/
├── sandy_stage1_tracks.png              # All 4 lead time tracks vs observations
├── sandy_stage1_errors.png              # Track error evolution by valid time
├── sandy_stage1_lead_time_results.pkl   # All predictions saved
├── sandy_stage1_lead_time_results.json  # Summary metrics
├── sandy_1day_landfall_msl.png          # MSL field comparison
├── sandy_1day_landfall_wind.png         # Wind field comparison
├── sandy_3day_landfall_msl.png
├── sandy_3day_landfall_wind.png
├── sandy_5day_landfall_msl.png
├── sandy_5day_landfall_wind.png
├── sandy_7day_landfall_msl.png
└── sandy_7day_landfall_wind.png
```

### Step 4: Analyze Stage 1 Results

**Results** (see `SANDY_RESULTS.md` for full details):
- ✅ **Best lead time**: 1-day (21.5 km landfall error)
- ✅ **7-day surprising**: Good track (22.2 km at 24h) but poor intensity (14.2 hPa MSL error)
- ✅ **Systematic bias**: All forecasts underpredict intensity and wind speed
- ✅ **For Stage 2**: Use 3-day lead (sufficient length to observe initialization sensitivity)

### Step 5: Run Stage 2 Analysis

Run the Stage 2 script:

```bash
python sandy_stage2_init_time.py
```

**What it does:**
- Uses 3-day lead time (Oct 27 initialization)
- Tests 4 initialization times (00, 06, 12, 18 UTC)
- All forecasts target Oct 30 00:00 UTC landfall
- Each init time has different forecast lengths (8-11 steps) to reach same target
- Compares meteorological fields at landfall for each init time
- Assesses sensitivity to time-of-day initialization
- Answers: "Does initialization time matter for 3-day forecasts?"

**Outputs:**
```
prediction_output/
├── sandy_stage2_init_tracks.png         # All 4 init time tracks (with historical track)
├── sandy_stage2_init_errors.png         # Error evolution converging to landfall
├── sandy_init00_landfall_msl.png        # 00 UTC MSL field comparison
├── sandy_init00_landfall_wind.png       # 00 UTC wind field comparison
├── sandy_init06_landfall_msl.png        # 06 UTC MSL field comparison
├── sandy_init06_landfall_wind.png       # 06 UTC wind field comparison
├── sandy_init12_landfall_msl.png        # 12 UTC MSL field comparison
├── sandy_init12_landfall_wind.png       # 12 UTC wind field comparison
├── sandy_init18_landfall_msl.png        # 18 UTC MSL field comparison
└── sandy_init18_landfall_wind.png       # 18 UTC wind field comparison
```

**Results** (see `SANDY_RESULTS.md` for full details):
- ✅ **Low initialization sensitivity**: 18.9 km std dev across init times
- ✅ **Best init time**: 18 UTC (56.6 km mean, 5.6 km at 24h, 113.3 km landfall error)
- ✅ **Variable error growth**: 18 UTC best early, 00 UTC best at 48h
- ✅ **Consistent bias**: All init times underpredict intensity

## File Locations

### Data Files
```
/scratch/qhuang62/aurora-extreme-predictability/research/TC/data/era5_sandy_2012/
├── download_sandy_complete.py          # Download script
├── combine_data.py                     # Combine script
├── 2012-10-22-surface-level.nc        # Individual daily files
├── 2012-10-22-atmospheric.nc
├── ...
├── 2012-10-31-surface-level.nc
├── 2012-10-31-atmospheric.nc
├── sandy_2012_surface_oct22-29.nc     # Combined surface file (32 timesteps)
├── sandy_2012_atmospheric_oct22-29.nc # Combined atmospheric file (32 timesteps)
├── 2012-10-30-surface-level.nc       # Landfall verification (separate)
└── 2012-10-30-atmospheric.nc         # Landfall verification (separate)
```

### Analysis Scripts
```
/scratch/qhuang62/aurora-extreme-predictability/research/TC/2012_Sandy/
├── sandy_stage1_lead_day.py           # Stage 1: Lead time assessment ✅ Complete
├── sandy_stage2_init_time.py          # Stage 2: Init time sensitivity ✅ Complete
├── prediction_output/                  # Results and visualizations (20 figures)
├── SANDY_DATA_WORKFLOW.md             # This file (workflow guide)
└── SANDY_RESULTS.md                   # Complete analysis results ✅ NEW
```

## Key Decisions Made

1. **Strategy B over Strategy A**: Variable initialization dates targeting the same critical event, rather than fixed initialization with variable forecast lengths. This is more operationally meaningful.

2. **Two-stage approach**: First assess lead time capability, then initialization sensitivity. This is more efficient than testing all combinations at once.

3. **Combined data files**: Single files with all timesteps rather than loading individual daily files. This simplifies the analysis scripts and reduces I/O overhead.

4. **Prediction saving**: Save all forecast outputs to enable iteration on visualizations and metrics without re-running expensive forecasts.

## Next Steps After Sandy

Once the Sandy analysis is complete, replicate this workflow for other TC events:
- Hurricane Ian (2022)
- Hurricane Hinnamnor (2022)
- Cyclone Amphan (2020)

Each event will follow the same two-stage structure, allowing for systematic comparison across different storms.

## Troubleshooting

### CDS API Issues
If downloads fail:
1. Check `~/.cdsapirc` contains valid credentials
2. Verify CDS API is operational: https://cds.climate.copernicus.eu
3. Check queue status - may need to wait if busy

### Memory Issues
If Aurora model runs out of memory:
1. Model will automatically fall back to CPU
2. For very long forecasts, may need to run in segments

### Time Index Issues
If you get index out of bounds errors:
1. Verify combined files were created successfully
2. Check timestep indices in config match the combined file structure
3. Use `xarray.open_dataset()` to inspect the `valid_time` dimension

## References

- **EXPERIMENTAL_STRATEGY.md**: Detailed explanation of Strategy A vs B
- **RESEARCH_PLAN.md**: Overall project plan and timeline
- **TC_utils.py**: TC-specific utility functions
- **shared/**: Shared utilities used across all extreme types
