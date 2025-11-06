# Aurora Hurricane Perturbation Methods Documentation

## Overview
This document compares two different atmospheric perturbation approaches used with Aurora for studying hurricane track sensitivity: Yeongbin's condensation warming method and Moyan's realistic cloud seeding approach.

---

## Method 1: Condensation Warming (Yeongbin's Approach)

### Physical Basis
**Mechanism**: Simulates localized convective heating from water vapor condensation
**Assumption**: Enhanced convection releases latent heat without considering precipitation fallout

### Mathematical Framework
```python
# Physical constants
Lv = 2.5e6       # Latent heat of vaporization [J/kg]
cp = 1005        # Specific heat at constant pressure [J/kg·K]
delta_q = 0.0010 # Water vapor condensed [kg/kg]

# Temperature increase
delta_T = (Lv * delta_q) / cp  # ≈ 2.49 K
```

### Spatial Configuration
- **Pattern**: Gaussian spatial distribution
- **Formula**: `amplitude * exp(-(dlon² + dlat²) / (2 * σ²))`
- **Sigma**: 8.0° (spatial spread)
- **Target Variable**: Atmospheric temperature only

### Vertical Configuration
- **Pressure Levels**: 700-925 hPa (mid-to-lower troposphere)
- **Application**: Same heating applied to all target levels
- **Vertical Coupling**: None

### Implementation Details
```python
def make_perturbed_batch_yeongbin(center_lat, center_lon):
    # Constants
    Lv, cp = 2.5e6, 1005
    delta_q = 0.0010
    delta_T = (Lv * delta_q) / cp  # ≈ 2.49 K
    sigma = 8.0
    amplitude = delta_T
    
    # Gaussian mask
    gaussian_mask = amplitude * np.exp(-(dlon**2 + dlat**2) / (2 * sigma**2))
    
    # Apply to temperature at 700-925 hPa levels
    t_pert = batch_orig.atmos_vars["t"].clone()
    p_levels = torch.tensor(batch_orig.metadata.atmos_levels)
    plev_idx = torch.where((p_levels >= 700) & (p_levels <= 925))[0]
    
    for i in plev_idx:
        t_pert[0, :, i] += gaussian_mask_torch
```

### Advantages
- Simple implementation
- Clear physical interpretation (convective heating)
- Suitable for studying steering flow sensitivity

### Limitations
- Unrealistic (ignores precipitation energy loss)
- Violates energy conservation
- Only considers warming phase of convection

---

## Method 2: Realistic Cloud Seeding (Moyan's Approach)

### Physical Basis
**Mechanism**: Ice nucleation seeding with full energy balance
**Process**: 
1. Supercooled water freezes (releases L_f)
2. Precipitation falls out (removes L_v + L_f)
3. Net effect usually cooling

### Mathematical Framework
```python
# Physical constants
L_f = 334000     # Latent heat of freezing [J/kg]
L_v = 2500000    # Latent heat of vaporization [J/kg]
C_p = 1004       # Specific heat of air [J/kg·K]

# Energy balance calculation
freeze_efficiency = 0.30      # 30% of moisture freezes
fallout_fraction = 0.70       # 70% of frozen water precipitates

q_frozen = q_layer * freeze_efficiency
q_fallout = q_frozen * fallout_fraction

# Net energy change
delta_E = L_f * q_frozen - (L_v + L_f) * q_fallout
delta_T = delta_E / C_p
# Typically negative (cooling) if fallout_fraction > 0.12
```

### Spatial Configuration
- **Pattern**: Circular mask (geodesic distance)
- **Radius**: 75 km (realistic seeding range)
- **Target Variables**: Temperature AND specific humidity

### Vertical Configuration
- **Pressure Levels**: 500-700 hPa (supercooled layer)
- **Vertical Coupling**: Yes (spreads to adjacent levels)
- **Coupling Factor**: 0.3-0.5 (fraction spread to neighbors)

### Implementation Details
```python
def apply_realistic_cloud_seeding(batch, seeding_mask_spatial, seeding_params):
    # Energy balance options
    if method == 'net_realistic':
        # Account for precipitation fallout
        delta_E = L_f * q_frozen - (L_v + L_f) * q_fallout
        delta_T = delta_E / C_p
        q_removed = q_fallout
    
    # Apply temperature change
    batch.atmos_vars["t"][0, :, level_idx] += delta_T
    
    # Remove precipitated moisture
    batch.atmos_vars["q"][0, :, level_idx] -= q_removed
    
    # Vertical coupling
    if vertical_coupling:
        for adj_idx in adjacent_levels:
            delta_T_adj = delta_T * coupling_factor
            batch.atmos_vars["t"][0, :, adj_idx] += delta_T_adj
```

### Advantages
- Physically realistic energy balance
- Modifies both temperature and humidity
- Includes vertical coupling effects
- Multiple energy balance options

### Limitations
- More complex implementation
- Requires careful parameter tuning
- May produce smaller perturbations

---

## Method 3: Hybrid Cloud Seeding (Our Implementation)

### Physical Basis
**Mechanism**: Energy-balanced ice nucleation with circular spatial pattern optimized for hurricane perturbation studies
**Innovation**: Combines Moyan's realistic physics with Yeongbin's spatial scale for hurricane steering flow modification

### Mathematical Framework
```python
# Physical constants (same as Moyan)
L_f = 334000   # J/kg (latent heat of freezing)
L_v = 2500000  # J/kg (latent heat of vaporization)
C_p = 1004     # J/(kg·K) (specific heat of air)

# Hybrid seeding parameters
target_levels = [500, 600, 700]  # hPa (broader supercooled layer)
freeze_efficiency = 0.30         # 30% of moisture freezes
fallout_fraction = 0.70          # 70% of frozen water precipitates
coupling_factor = 0.4            # Vertical coupling strength

# Energy balance (realistic physics)
q_frozen = q_layer * freeze_efficiency * spatial_mask
q_fallout = q_frozen * fallout_fraction
delta_E = L_f * q_frozen - (L_v + L_f) * q_fallout
delta_T = delta_E / C_p  # Usually cooling (-1 to -3 K)
```

### Spatial Configuration
- **Pattern**: Circular mask using great circle distance
- **Radius**: 300 km (≈ Gaussian σ=8° for comparison with Yeongbin)
- **Formula**: `create_circular_mask(lats, lons, center_lat, center_lon, radius_km)`
- **Target Variables**: Temperature AND specific humidity (like Moyan)

### Vertical Configuration
- **Pressure Levels**: 500-700 hPa (extended supercooled layer)
- **Vertical Coupling**: Yes, spreads to ±1 adjacent levels
- **Coupling Factor**: 0.4 (40% strength propagation)

### Implementation Details
```python
def apply_realistic_cloud_seeding(batch_orig, center_lat, center_lon, radius_km=300):
    # Physical constants
    L_f, L_v, C_p = 334000, 2500000, 1004
    target_levels = [500, 600, 700]
    freeze_efficiency, fallout_fraction = 0.30, 0.70
    coupling_factor = 0.4
    
    # Create spatial mask using great circle distance
    seeding_mask = create_circular_mask(lats_np, lons_np, 
                                       center_lat, center_lon, radius_km)
    
    # Apply to target levels with energy balance
    for level_mb in target_levels:
        level_idx = list(batch_orig.metadata.atmos_levels).index(level_mb)
        q_layer = batch_seeded.atmos_vars["q"][0, 1, level_idx].clone()
        
        # Calculate frozen and precipitated moisture
        q_frozen = q_layer * freeze_efficiency * mask_torch
        q_fallout = q_frozen * fallout_fraction
        
        # Energy balance: warming from freezing, cooling from precipitation
        delta_E = L_f * q_frozen - (L_v + L_f) * q_fallout
        delta_T = delta_E / C_p
        
        # Apply changes to both time steps
        batch_seeded.atmos_vars["t"][0, :, level_idx] += delta_T
        batch_seeded.atmos_vars["q"][0, :, level_idx] -= q_fallout
        
        # Vertical coupling to adjacent levels
        for offset in [-1, 1]:
            adj_idx = level_idx + offset
            if 0 <= adj_idx < len(batch_orig.metadata.atmos_levels):
                delta_T_adj = delta_T * coupling_factor
                batch_seeded.atmos_vars["t"][0, :, adj_idx] += delta_T_adj
```

### Unique Features
1. **Optimized Spatial Scale**: 300 km radius matches Yeongbin's σ=8° influence area
2. **Hurricane-Focused Levels**: 500-700 hPa targets steering flow and convective layers
3. **Realistic Cooling**: Energy balance typically produces -1 to -3 K cooling
4. **Broader Vertical Coverage**: Targets 3 levels instead of Moyan's specific layer focus
5. **Enhanced Coupling**: 40% vertical propagation for better atmospheric response

### Advantages
- **Physically realistic** energy balance (like Moyan)
- **Hurricane-optimized** spatial scale (like Yeongbin)
- **Broader vertical influence** for steering flow modification
- **Measurable perturbations** with realistic physics
- **Flexible parameterization** for sensitivity studies

### Limitations
- **Complex implementation** requires careful coordinate handling
- **Parameter dependent** results sensitive to efficiency values
- **Usually cooling** may not test warming scenarios
- **Computational overhead** from energy balance calculations

---

## Comparison Summary

| Aspect | Yeongbin (Condensation) | Moyan (Cloud Seeding) | Our Hybrid Implementation |
|--------|-------------------------|------------------------|---------------------------|
| **Physics** | Simplified warming | Realistic energy balance | Realistic energy balance |
| **Energy Conservation** | Violated | Conserved | Conserved |
| **Temperature Change** | +2.49 K | Usually -1 to -2 K | Usually -1 to -3 K |
| **Variables Modified** | Temperature only | Temperature + Humidity | Temperature + Humidity |
| **Spatial Pattern** | Gaussian (σ=8°) | Circular (75 km) | Circular (300 km) |
| **Vertical Levels** | 700-925 hPa | 500-700 hPa | 500-700 hPa |
| **Vertical Coupling** | None | Yes (±1 level) | Yes (±1 level, 40%) |
| **Spatial Scale** | Hurricane-optimal | Small/localized | Hurricane-optimal |
| **Realism** | Low | High | High |
| **Implementation** | Simple | Complex | Complex |
| **Use Case** | Sensitivity testing | Realistic intervention | Hurricane perturbation |

---

## Recommended Applications

### Yeongbin's Method
- **Best for**: Studying hurricane track sensitivity to environmental heating
- **Use when**: Testing idealized perturbations for chaos/predictability studies
- **Hurricane context**: Investigating steering flow modification with simplified physics

### Moyan's Method  
- **Best for**: Realistic cloud seeding impact assessment for atmospheric rivers
- **Use when**: Physical realism is important for small-scale interventions
- **Hurricane context**: Studying localized weather modification effects

### Our Hybrid Method
- **Best for**: Hurricane track perturbation studies with realistic physics
- **Use when**: Need both physical realism and hurricane-scale spatial influence
- **Hurricane context**: Testing realistic cloud seeding effects on TC steering flow
- **Scientific advantage**: Optimal for Aurora TC perturbation experiments

---

## Implementation Notes

### Key Code Differences
1. **Perturbation magnitude**: Yeongbin uses fixed ΔT, Moyan calculates from energy balance
2. **Variable scope**: Yeongbin affects temperature only, Moyan affects temperature + humidity
3. **Spatial pattern**: Yeongbin uses mathematical Gaussian, Moyan uses geodesic circular mask
4. **Vertical structure**: Yeongbin applies uniformly, Moyan includes coupling between levels

### Parameter Sensitivity
- **Yeongbin**: Main parameters are σ (spatial spread) and δq (condensation amount)
- **Moyan**: Main parameters are freeze_efficiency, fallout_fraction, and coupling_factor

### Computational Considerations
- **Yeongbin**: Faster, simpler tensor operations
- **Moyan**: More complex, requires moisture field modifications and energy calculations

---

## References
- Yeongbin's hurricane perturbation experiments (Aurora + Sandy 2012)
- Moyan's atmospheric river cloud seeding experiments (Aurora + AR events)
- Aurora model documentation for perturbation best practices
- **Our implementation**: Hurricane Sandy 2012 perturbation experiments (November 3, 2025)
  - `sandy_perturb.ipynb`: Complete implementation of all three methods
  - `Perturbation_Methods_Documentation.md`: This comparative analysis
  - Physical validation using ERA5 + Aurora 0.25° Pretrained model