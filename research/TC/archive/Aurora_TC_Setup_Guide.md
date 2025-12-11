# Aurora Tropical Cyclone Prediction Setup Guide

This technical guide documents the key code elements and configurations for reproducible tropical cyclone prediction experiments using Aurora models.

## Table of Contents
1. [Model Configurations](#model-configurations)
2. [Data Setup](#data-setup)
3. [Batch Creation](#batch-creation)
4. [Tracker Initialization](#tracker-initialization)
5. [Prediction Rollout](#prediction-rollout)
6. [Key Parameters Summary](#key-parameters-summary)
7. [Troubleshooting](#troubleshooting)

---

## Model Configurations

### Aurora 0.25° Fine-tuned (HRES optimized)
```python
from aurora import Aurora, rollout

# Load fine-tuned model for HRES T0 data
model = Aurora()  # Default uses LoRA
model.load_checkpoint("microsoft/aurora", "aurora-0.25-finetuned.ckpt")
```

### Aurora 0.25° Pretrained (ERA5 compatible)
```python
from aurora import Aurora, rollout

# Load pretrained model for ERA5 data
model = Aurora(use_lora=False)  # Pretrained version does not use LoRA
model.load_checkpoint("microsoft/aurora", "aurora-0.25-pretrained.ckpt")
```

**Key Difference**: Fine-tuned model uses LoRA by default, pretrained model requires `use_lora=False`.

---

## Data Setup

### Data Source Options

#### Option 1: HRES T0 + ERA5 Static (WeatherBench2)
```python
# Surface & atmospheric: WeatherBench2 HRES T0 (2016-2022 only)
url = "gs://weatherbench2/datasets/hres_t0/2016-2022-6h-1440x721.zarr"
ds = xr.open_zarr(fsspec.get_mapper(url), chunks=None)

# Static variables: ERA5 (any date)
c.retrieve("reanalysis-era5-single-levels", {...}, "static.nc")
```

#### Option 2: All ERA5 (Any historical period)
```python
# All variables from ERA5 reanalysis
c.retrieve("reanalysis-era5-single-levels", {...})      # Surface + static
c.retrieve("reanalysis-era5-pressure-levels", {...})    # Atmospheric
```

### Required Variables

#### Surface Variables
```python
surface_vars = [
    "2m_temperature",           # "2t" in Aurora
    "10m_u_component_of_wind",  # "10u" in Aurora  
    "10m_v_component_of_wind",  # "10v" in Aurora
    "mean_sea_level_pressure",  # "msl" in Aurora
]
```

#### Static Variables  
```python
static_vars = [
    "geopotential",    # "z" in Aurora
    "land_sea_mask",   # "lsm" in Aurora
    "soil_type",       # "slt" in Aurora
]
```

#### Atmospheric Variables
```python
atmos_vars = [
    "temperature",              # "t" in Aurora
    "u_component_of_wind",      # "u" in Aurora
    "v_component_of_wind",      # "v" in Aurora
    "specific_humidity",        # "q" in Aurora
    "geopotential",            # "z" in Aurora
]

pressure_levels = ["50", "100", "150", "200", "250", "300", "400", 
                   "500", "600", "700", "850", "925", "1000"]
```

---

## Batch Creation

### Key Principle
Aurora requires **two consecutive time points** for initialization. The second time point becomes the forecast initialization time.

### Initialization Time Configuration

#### For 06:00 UTC Initialization
```python
# Use time indices 0 and 1 (00:00, 06:00)
batch = Batch(
    surf_vars={
        "2t": torch.from_numpy(surf_vars_ds["t2m"].values[:2][None]),
        "10u": torch.from_numpy(surf_vars_ds["u10"].values[:2][None]),
        "10v": torch.from_numpy(surf_vars_ds["v10"].values[:2][None]),
        "msl": torch.from_numpy(surf_vars_ds["msl"].values[:2][None]),
    },
    # ... other variables
    metadata=Metadata(
        # Use element 1 for 06:00 UTC
        time=(surf_vars_ds.valid_time.values.astype("datetime64[s]").tolist()[1],),
        # ... other metadata
    ),
)
```

#### For 12:00 UTC Initialization  
```python
# Use time indices 1 and 2 (06:00, 12:00)
batch = Batch(
    surf_vars={
        "2t": torch.from_numpy(surf_vars_ds["t2m"].values[1:3][None]),
        "10u": torch.from_numpy(surf_vars_ds["u10"].values[1:3][None]),
        "10v": torch.from_numpy(surf_vars_ds["v10"].values[1:3][None]),
        "msl": torch.from_numpy(surf_vars_ds["msl"].values[1:3][None]),
    },
    # ... other variables
    metadata=Metadata(
        # Use element 2 for 12:00 UTC
        time=(surf_vars_ds.valid_time.values.astype("datetime64[s]").tolist()[2],),
        # ... other metadata
    ),
)
```

#### For 18:00 UTC Initialization
```python
# Use time indices 2 and 3 (12:00, 18:00)
batch = Batch(
    surf_vars={
        "2t": torch.from_numpy(surf_vars_ds["t2m"].values[2:4][None]),
        # ... similar for other variables
    },
    metadata=Metadata(
        # Use element 3 for 18:00 UTC
        time=(surf_vars_ds.valid_time.values.astype("datetime64[s]").tolist()[3],),
        # ... other metadata
    ),
)
```

### Data Format Considerations

#### HRES Data (WeatherBench2)
```python
def _prepare(x: np.ndarray) -> torch.Tensor:
    """Prepare HRES variable - requires latitude flipping"""
    return torch.from_numpy(x[[1, 2]][None][..., ::-1, :].copy())
```

#### ERA5 Data (Direct)
```python
# ERA5 data doesn't need latitude flipping
batch = Batch(
    surf_vars={
        "2t": torch.from_numpy(surf_vars_ds["t2m"].values[:2][None]),
        # ... no latitude flipping needed
    },
    # ...
)
```

---

## Tracker Initialization

### Basic Setup
```python
from datetime import datetime
from aurora import Tracker

# Initialize tracker with TC position and time
tracker = Tracker(
    init_lat=latitude,     # Initial latitude (degrees N)
    init_lon=longitude,    # Initial longitude (degrees E)  
    init_time=datetime_obj # Initialization datetime
)
```

### Case-Specific Examples

#### Typhoon Nanmadol 2022
```python
# 06:00 UTC initialization
tracker = Tracker(
    init_lat=26.8, 
    init_lon=133.2, 
    init_time=datetime(2022, 9, 17, 6, 0)
)

# 12:00 UTC initialization  
tracker = Tracker(
    init_lat=27.5,
    init_lon=132.0, 
    init_time=datetime(2022, 9, 17, 12, 0)
)
```

#### Hurricane Sandy 2012
```python

```

### Accessing Tracker Attributes
```python
# Tracker stores data in lists, not individual attributes
print(f"Init time: {tracker.tracked_times[0]}")
print(f"Init position: {tracker.tracked_lats[0]}°N, {tracker.tracked_lons[0]}°E")

# Get results as DataFrame
track_df = tracker.results()
```

---

## Prediction Rollout

### Standard Rollout Setup
```python
# Setup model for inference
model.eval()
model = model.to("cuda")

# Run rollout with tracking
preds = []
with torch.inference_mode():
    for i, pred in enumerate(rollout(model, batch, steps=n_steps)):
        pred = pred.to("cpu")  # Free GPU memory immediately
        preds.append(pred)
        tracker.step(pred)     # Update tracker with new prediction
        print(f"Step {i+1}/{n_steps}: {pred.metadata.time[0]}")

# Clean up
model = model.to("cpu")
```

### Common Rollout Configurations

#### 48-hour forecast - 2 days (8 steps)
```python
steps = 8  # 8 × 6 hours = 48 hours
```

#### 72-hour forecast - 3 days (12 steps)  
```python
steps = 12  # 12 × 6 hours = 72 hours
```

#### 120-hour forecast - 5 days (20 steps)
```python
steps = 20  # 20 × 6 hours = 120 hours = 5 days
```

---

## Key Parameters Summary

### Experiment Configuration Matrix

| Parameter | HRES Fine-tuned | ERA5 Pretrained | Notes |
|-----------|----------------|-----------------|-------|
| **Model** | `Aurora()` | `Aurora(use_lora=False)` | LoRA setting crucial |
| **Checkpoint** | `aurora-0.25-finetuned.ckpt` | `aurora-0.25-pretrained.ckpt` | Different checkpoints |
| **Data Source** | WeatherBench2 + ERA5 static | All ERA5 | Data compatibility |
| **Time Range** | 2016-2022 only | Any historical period | Availability constraint |
| **Lat Flipping** | Required (HRES) | Not needed (ERA5) | Data format difference |
| **Time Step** | 6 hours | 6 hours | Standard Aurora timestep |

### Initialization Time Mapping

| Init Time | Time Indices | Metadata Index | Comments |
|-----------|-------------|----------------|----------|
| 00:00 UTC | `[-1, 0]` (prev day 18:00, current 00:00) | `[0]` | Requires previous day data |
| 06:00 UTC | `[0, 1]` (00:00, 06:00) | `[1]` | Standard morning init |
| 12:00 UTC | `[1, 2]` (06:00, 12:00) | `[2]` | Standard noon init |
| 18:00 UTC | `[2, 3]` (12:00, 18:00) | `[3]` | Standard evening init |

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Tracker AttributeError
```python
# Wrong - Tracker doesn't have these attributes
print(tracker.init_time)  # AttributeError

# Correct - Use list indices  
print(tracker.tracked_times[0])
```

#### 2. Model/Data Mismatch
```python
# Fine-tuned model with ERA5 data - suboptimal
model = Aurora()  # Fine-tuned for HRES
# Use ERA5 data -> poor performance

# Solution: Match model and data
model = Aurora(use_lora=False)  # Pretrained for ERA5
# Use ERA5 data -> optimal performance
```

#### 3. Latitude Orientation Issues
```python
# HRES data needs latitude flipping
hres_data = torch.from_numpy(data[..., ::-1, :].copy())

# ERA5 data doesn't need flipping
era5_data = torch.from_numpy(data)
```

#### 4. Time Index Errors
```python
# Make sure you have enough time points
print(f"Available times: {len(surf_vars_ds.time)}")
# Need at least 2 points for initialization

# Check time alignment
print(surf_vars_ds.time.values)
```

#### 5. GPU Memory Issues
```python
# Always move predictions to CPU immediately
for pred in rollout(model, batch, steps=steps):
    pred = pred.to("cpu")  # Prevent GPU memory accumulation
    preds.append(pred)
```

### Validation Checklist

Before running experiments, verify:

- [ ] Model checkpoint matches data source (fine-tuned→HRES, pretrained→ERA5)
- [ ] Time indices align with desired initialization time
- [ ] Tracker initialization time matches batch metadata time
- [ ] All required variables are present in correct format
- [ ] GPU memory is properly managed during rollout
- [ ] Static variables have correct normalization



---

## File Organization

### updated 10/20/2025
```
research/TC/
├── Aurora_TC_Setup_Guide.md          # This guide
├── finetune_nanmadol_2022_init12.ipynb      # HRES + Fine-tuned example
├── era5_nanmadol_2022_init6.ipynb          # ERA5 + Pretrained (06:00 init)
├── era5_nanmadol_2022_init12.ipynb   # ERA5 + Pretrained (12:00 init)
├── data/
│   ├── hresT0_nanmadol_2022/               # HRES data
│   └── era5_nanmadol_2022/          # ERA5 data
└── ProgressRecord.md                 # Experiment log
```

This guide provides all necessary code patterns and configurations for reproducible Aurora TC prediction experiments across different model versions, data sources, and initialization times.