# Aurora vs Pangu: Perturbation Implementation Comparison

## Overview

This document compares the perturbation approaches used in Hurricane Sandy forecasting between two AI weather models: Microsoft's Aurora and Huawei's Pangu-Weather. The analysis is based on implementations in:

- **Aurora**: `sandy_perturb.ipynb` - Single perturbation comparison with two physics methods
- **Pangu**: `sandy_perturb_10-Copy1.py` - 10-member ensemble with enhanced physics coupling

## Key Differences Summary

| Aspect | Aurora | Pangu |
|--------|--------|-------|
| **Data Structure** | Native `Batch` objects with metadata | Raw NumPy arrays for ONNX |
| **Ensemble Strategy** | 2 methods comparison | 10-member operational ensemble |
| **Physics Coupling** | T-only or T+Q | T+Q+Wind with thermal adjustment |
| **Spatial Pattern** | Gaussian (σ=8°) | Circular masks (great circle) |
| **Locations** | Single fixed (30°N, 80°W) | 10 strategic Atlantic locations |
| **Vertical Coupling** | Simple factor-based | Enhanced multi-level |
| **Realism** | Research-focused comparison | Operational-ready implementation |

## Detailed Analysis

### 1. Model Framework & Data Handling

#### Aurora Batch System
```python
batch = Batch(
    surf_vars={
        "2t": torch.tensor(...),
        "10u": torch.tensor(...),
        # ... other surface variables
    },
    atmos_vars={
        "t": torch.tensor(...),  # Temperature
        "q": torch.tensor(...),  # Specific humidity
        # ... other atmospheric variables
    },
    metadata=Metadata(
        lat=torch.tensor(...),
        lon=torch.tensor(...),
        time=(...),
        atmos_levels=(50, 100, 150, ...)
    )
)
```

**Advantages for Perturbation**:
- **Semantic clarity**: Variables have meaningful names (`2t`, `msl`, `q`)
- **Metadata preservation**: Coordinate systems and time information maintained
- **Type safety**: PyTorch tensors with gradient tracking capability
- **Native integration**: Direct compatibility with Aurora model inference

**Role in Perturbation**:
- Perturbations applied by modifying specific variable dictionaries
- Automatic handling of coordinate transformations
- Built-in validation of variable shapes and types

#### Pangu Array System
```python
# Upper atmosphere: [variables, levels, lat, lon]
base_input_upper.shape  # (5, 13, 721, 1440)
# Variables: [Z, Q, T, U, V] at 13 pressure levels

# Surface: [variables, lat, lon] 
base_input_surface.shape  # (4, 721, 1440)
# Variables: [MSLP, U10, V10, T2M]
```

**Advantages for Perturbation**:
- **Direct array access**: Immediate indexing `array[var_idx, level_idx, lat_idx, lon_idx]`
- **Memory efficiency**: Raw NumPy arrays without metadata overhead
- **Computational speed**: Direct numerical operations without tensor abstractions
- **ONNX compatibility**: Native format for inference

**Role in Perturbation**:
- Perturbations applied through direct array indexing
- Manual coordinate grid management required
- Explicit variable mapping (T=index 2, Q=index 1, etc.)

### 2. Perturbation Physics Implementation

#### Aurora: Two-Method Comparison

**Yeongbin Method (Simplified)**:
```python
# Condensation warming only
Lv = 2.5e6       # Latent heat of vaporization
cp = 1005        # Specific heat
delta_q = 0.0010 # Water vapor condensed
delta_T = (Lv * delta_q) / cp  # ≈ 2.49 K

# Apply to temperature only
batch_pert.atmos_vars["t"][0, 0, level_idx] += gaussian_mask_torch
```

**Moyan Method (Realistic)**:
```python
# Energy-balanced ice nucleation
L_f = 334000     # Latent heat of freezing
L_v = 2500000    # Latent heat of vaporization
C_p = 1004       # Specific heat

# Calculate energy balance
delta_E = L_f * q_frozen - (L_v + L_f) * q_fallout
delta_T = delta_E / C_p  # Usually cooling

# Modify both temperature AND humidity
batch_seeded.atmos_vars["t"][0, 1, level_idx] += delta_T
batch_seeded.atmos_vars["q"][0, 1, level_idx] -= q_fallout
```

#### Pangu: Enhanced Physics Coupling

**Enhanced Moyan with Additional Physics**:
```python
# 1. Same energy balance as Aurora Moyan
delta_E = self.L_f * q_frozen - (self.L_v + self.L_f) * q_fallout
delta_T = delta_E / self.C_p

# 2. ADDITIONAL: Geostrophic wind adjustment
dT_dy = np.gradient(delta_T, axis=0)  # Meridional temperature gradient
dT_dx = np.gradient(delta_T, axis=1)  # Zonal temperature gradient

# Apply thermal wind relationship
wind_adjustment_factor = 0.1
perturbed_upper[3, level_idx] -= dT_dy * wind_adjustment_factor  # U wind
perturbed_upper[4, level_idx] += dT_dx * wind_adjustment_factor  # V wind

# 3. Enhanced vertical coupling to adjacent levels
for offset in [-1, 1]:
    adj_level_idx = level_idx + offset
    if 0 <= adj_level_idx < perturbed_upper.shape[1]:
        delta_T_adj = delta_T * self.coupling_factor
        perturbed_upper[2, adj_level_idx] += delta_T_adj
```

### 3. Spatial Pattern Generation

#### Aurora: Gaussian Pattern
```python
# Create coordinate grids
lon_grid, lat_grid = np.meshgrid(lon, lat)
dlon = (lon_grid - center_lon + 180) % 360 - 180
dlat = lat_grid - center_lat

# Gaussian heating pattern
gaussian_mask = amplitude * np.exp(-(dlon**2 + dlat**2) / (2 * sigma**2))
```

#### Pangu: Great Circle Distance
```python
# Haversine formula for realistic distance calculation
lat1 = np.radians(lat_grid)
lat2 = np.radians(center_lat)
lon1 = np.radians(lon_grid)
lon2 = np.radians(center_lon)

dlat = lat2 - lat1
dlon = lon2 - lon1

a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
c = 2 * np.arcsin(np.sqrt(a))
distance_km = R_earth * c

return distance_km <= radius_km  # Circular mask
```

### 4. Ensemble Strategy

#### Aurora: Method Comparison
- **Purpose**: Compare simplified vs realistic perturbation physics
- **Members**: 2 (Yeongbin warming vs Moyan seeding)
- **Location**: Single fixed perturbation site (30°N, 80°W)
- **Analysis**: Track differences between physics approaches

#### Pangu: Operational Ensemble
- **Purpose**: Generate forecast uncertainty estimates
- **Members**: 10 with different perturbation locations
- **Locations**: Strategic sites across Atlantic basin
- **Analysis**: Ensemble mean, spread statistics, probability forecasts

```python
# 10 strategic perturbation locations
base_locations = [
    {'lat': 30.0, 'lon': 280.0, 'radius': 300},  # Main upstream
    {'lat': 35.0, 'lon': 275.0, 'radius': 250},  # Eastern seaboard
    {'lat': 25.0, 'lon': 285.0, 'radius': 200},  # Subtropical Atlantic
    # ... 7 more strategic locations
]
```

## Which Model is Easier for Perturbation?

### Aurora: Easier for Research & Development

**Advantages**:
1. **Semantic variable access**: `batch.atmos_vars["t"]` vs `array[2, level_idx]`
2. **Built-in validation**: Automatic shape and type checking
3. **Metadata handling**: Coordinates and time automatically managed
4. **Documentation**: Clear variable meanings and units
5. **Debugging**: Named variables easier to track and verify

**Best for**:
- Research experiments comparing different physics
- Prototype development of new perturbation methods
- Educational purposes and method validation

### Pangu: Better for Operational Implementation

**Advantages**:
1. **Performance**: Direct array operations are faster
2. **Memory efficiency**: No metadata overhead
3. **Flexibility**: Complete control over array manipulation
4. **Scalability**: Easier to parallelize across ensemble members
5. **Production ready**: ONNX format standard for deployment

**Best for**:
- Operational forecasting systems
- Large ensemble implementations
- Performance-critical applications
- Integration with existing numerical weather systems

## Data Structure Roles in Perturbation

### Aurora Batch: High-Level Abstraction

The Aurora `Batch` object serves as a **scientific data container** that:

- **Preserves context**: Maintains coordinate systems, time information, and variable metadata
- **Ensures consistency**: Automatic validation of data shapes and types across variables
- **Enables traceability**: Clear mapping between physical variables and tensor data
- **Supports experimentation**: Easy swapping of different perturbation methods

**Example of role in perturbation**:
```python
# Clear, self-documenting perturbation
batch_perturbed.atmos_vars["t"][0, 1, level_700_idx] += heating_pattern
batch_perturbed.atmos_vars["q"][0, 1, level_700_idx] -= moisture_loss

# Metadata automatically preserved for downstream analysis
print(f"Perturbed at level: {batch_perturbed.metadata.atmos_levels[level_700_idx]} hPa")
```

### Pangu Arrays: Low-Level Efficiency

Pangu's raw arrays serve as **computational workhorses** that:

- **Maximize performance**: Direct memory access without abstraction overhead
- **Enable batch processing**: Easy to apply perturbations across multiple ensemble members
- **Support complex operations**: Full NumPy ecosystem for mathematical operations
- **Provide deployment flexibility**: Standard format compatible with various inference engines

**Example of role in perturbation**:
```python
# Efficient batch perturbation across ensemble
for member in range(N_ENSEMBLE):
    # Direct array manipulation - very fast
    perturbed_upper[2, level_idx] += delta_T  # Temperature at index 2
    perturbed_upper[1, level_idx] -= q_fallout  # Humidity at index 1
    
    # Easy to parallelize and optimize
    ensemble_upper[member] = perturbed_upper.copy()
```

## Conclusions

1. **Aurora's approach is more accessible** for research and development due to its semantic clarity and built-in safeguards

2. **Pangu's approach is more suitable for operational deployment** due to performance advantages and deployment flexibility

3. **Physics complexity**: Pangu implements more sophisticated physics coupling (thermal wind adjustment) while Aurora focuses on comparing fundamental approaches

4. **Scientific purpose**: Aurora prioritizes method comparison and validation, while Pangu targets operational ensemble forecasting

5. **Development workflow**: Aurora better for prototyping new ideas, Pangu better for scaling proven methods

The choice between approaches depends on the primary goal: scientific research and method development (Aurora) vs operational forecasting and production deployment (Pangu).