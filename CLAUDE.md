# Aurora Extreme Predictability Project Guide

This guide helps Claude Code understand the "Aurora Predictability for Weather Extremes" project.

## Project Structure

```
aurora-extreme-predictability/
├── CLAUDE.md                    # This guide (project context for Claude)
├── research/                    # Research work
│   ├── paper-outline.md        # Paper structure and methodology
│   ├── notebooks/              # Jupyter notebooks for analysis
│   └── scripts/                # Python scripts for data/evaluation
└── upstream-aurora/            # Original Microsoft Aurora codebase
    ├── aurora/                 # Core Aurora package
    ├── docs/                   # Aurora documentation and examples
    ├── tests/                  # Aurora tests
    ├── finetuning/            # Aurora finetuning utilities
    ├── README.md              # Original Aurora README
    └── pyproject.toml         # Aurora dependencies
```

**Key Principles:**
- `research/` - Your analysis, experiments, and paper development
- `upstream-aurora/` - Original Microsoft Aurora code (unchanged)
- Start minimal, add folders as needed

## Project Overview

This project evaluates Microsoft's Aurora AI model for predicting extreme weather events (tropical cyclones, freezes, atmospheric rivers, precipitation extremes) and will result in a research paper.

**Paper Objective**: Evaluate how well Aurora predicts specific classes of extreme events spanning different spatiotemporal scales, mechanisms, and predictability regimes.

## Aurora Model Details

### What is Aurora?
- **Foundation Model**: Machine learning model for Earth system forecasting
- **Training Data**: Trained directly on ERA5 reanalysis data without explicit physics equations
- **Approach**: Learns spatiotemporal relationships directly from data
- **Advantages**: Faster inference, higher spatial resolution than traditional NWP models

### Available Model Versions

1. **Aurora 0.25° Pretrained** (`AuroraPretrained`)
   - General purpose, trained on wide variety of data
   - Use for ERA5 at 0.25° resolution or as base for fine-tuning
   - Resolution: 721 x 1440 grid points

2. **Aurora 0.25° Fine-Tuned** (`Aurora`) 
   - Default model, fine-tuned on IFS HRES T0
   - Best performing at 0.25° resolution
   - **Important**: Only optimal for IFS HRES T0 data

3. **Aurora 0.25° Small Pretrained** (`AuroraSmallPretrained`)
   - Smaller version for debugging
   - Not recommended for production use

4. **Aurora 0.1° Fine-Tuned** (`AuroraHighRes`)
   - High-resolution version for IFS HRES analysis
   - Resolution: 1801 x 3600 grid points
   - **Important**: Only optimal for IFS HRES analysis data

5. **Aurora 0.25° 12-Hour Pretrained** (`Aurora12hPretrained`)
   - 12-hour lead time version

6. **Aurora 0.4° Air Pollution** (`AuroraAirPollution`)
   - Fine-tuned for CAMS analysis air pollution forecasts
   - Resolution: 451 x 900 grid points

7. **Aurora 0.25° Wave** (`AuroraWave`)
   - Fine-tuned for HRES-WAM ocean wave forecasts

### Required Input Variables

**Surface-level variables (required for all models)**:
- `2t`: 2m temperature
- `10u`: 10m u-component of wind  
- `10v`: 10m v-component of wind
- `msl`: Mean sea level pressure

**Static variables (required for all models)**:
- `lsm`: Land-sea mask
- `slt`: Soil type
- `z`: Geopotential (topography)

**Atmospheric variables (required for all models)**:
- `t`: Temperature
- `u`: U-component of wind
- `v`: V-component of wind  
- `q`: Specific humidity
- `z`: Geopotential

**Pressure levels (hPa)**: 50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 850, 925, 1000

### Data Format
- Uses `aurora.Batch` class containing:
  - `surf_vars`: Surface variables dict
  - `static_vars`: Static variables dict  
  - `atmos_vars`: Atmospheric variables dict
  - `metadata`: `Metadata` object with lat, lon, time, pressure levels

## Extreme Weather Case Studies

The project focuses on four types of extreme events:

1. **Tropical Cyclones** (Sandy 2012, Earl 2010)
   - Mechanisms: Warm SSTs, moist convection, Coriolis force
   - Metrics: Track error, landfall timing, position uncertainty

2. **Freeze/Cold Snaps** (2021 Texas Freeze)
   - Mechanisms: Arctic air mass intrusion, jet stream meandering
   - Metrics: Temperature anomaly RMSE, onset timing, spatial extent

3. **Atmospheric Rivers** (Winter 2022 West Coast)
   - Mechanisms: Long narrow corridors of water vapor transport
   - Metrics: IVT RMSE, AR position/timing, precipitation skill

4. **Precipitation Extremes** (Multiple events 2020-2025)
   - Various flood events across global regions
   - Focus on timing, intensity, and spatial patterns

## Key Project Files

- `paper-outline.md`: Detailed paper structure and methodology
- `aurora/model/aurora.py`: Main Aurora model implementation  
- `docs/models.md`: Complete model specifications and usage
- `docs/example_era5.ipynb`: ERA5 data processing example
- `aurora/batch.py`: Data batch handling and metadata

## Development Notes

- **Checkpoints**: Downloaded from HuggingFace `microsoft/aurora`
- **Static Variables**: Available pre-computed for each model resolution
- **LoRA**: Can be disabled for more realistic predictions (slight MSE trade-off)
- **Lead Times**: Standard 6-hour steps, with 12-hour option available
- **GPU**: CUDA support for inference acceleration

## Important Considerations

- Model-specific data requirements (don't mix data types)
- Proper normalization statistics for custom static variables
- ERA5 vs IFS HRES T0 vs IFS HRES analysis distinctions
- Performance varies by event type, scale, and initialization sensitivity