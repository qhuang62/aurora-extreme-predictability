#!/usr/bin/env python3
"""
Aurora Hurricane Sandy Single Perturbation Forecast
Using Pangu's enhanced physics-based perturbation method with Aurora model setup
Location: 26°N, 70°W (Bahamas region), Radius: 300km
"""

import torch
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.lines import Line2D
from datetime import datetime, timedelta
from pathlib import Path

from aurora import Aurora, Batch, Metadata, Tracker, rollout

print("=== Aurora Sandy One-Shot Perturbation Experiment ===")
print("Enhanced Physics-Based Perturbation (Pangu Method)")
print("Location: 26°N, 70°W (Bahamas region)")
print("Radius: 300km")
print("=" * 60)

class EnhancedPhysicsPerturbation:
    """Enhanced physics-based perturbation using Pangu's method for Aurora"""
    
    def __init__(self):
        # Physical constants (from Pangu/Moyan approach)
        self.L_f = 334000   # J/kg (latent heat of freezing)
        self.L_v = 2500000  # J/kg (latent heat of vaporization)
        self.C_p = 1004     # J/(kg·K) (specific heat of air)
        
        # Enhanced seeding parameters
        self.freeze_efficiency = 0.30         # 30% of moisture freezes
        self.fallout_fraction = 0.70          # 70% of frozen water precipitates
        self.coupling_factor = 0.4            # Vertical coupling strength
        self.wind_adjustment_factor = 0.1     # Thermal wind adjustment
        
        # Target pressure levels for perturbations (500-700 hPa supercooled layer)
        self.target_levels = [500, 600, 700]  # hPa
    
    def create_circular_mask(self, lats, lons, center_lat, center_lon, radius_km):
        """Create circular mask using great circle distance (Pangu method)"""
        R_earth = 6371  # km
        
        # Create 2D grids
        lon_grid, lat_grid = np.meshgrid(lons, lats)
        
        # Convert to radians
        lat1 = np.radians(lat_grid)
        lat2 = np.radians(center_lat)
        lon1 = np.radians(lon_grid)
        lon2 = np.radians(center_lon)
        
        # Haversine formula for great circle distance
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        distance_km = R_earth * c
        
        return distance_km <= radius_km
    
    def apply_enhanced_perturbation(self, batch_orig, center_lat, center_lon, radius_km):
        """Apply enhanced physics perturbation with thermal wind adjustment"""
        
        # Get coordinate arrays from Aurora batch
        lats_np = batch_orig.metadata.lat.numpy()
        lons_np = batch_orig.metadata.lon.numpy()
        
        # Handle longitude format (Aurora uses 0-360° like ERA5)
        if center_lon < 0:
            center_lon = center_lon + 360
        
        # Create spatial perturbation mask using great circle distance
        perturbation_mask = self.create_circular_mask(lats_np, lons_np, center_lat, center_lon, radius_km)
        
        # Clone batch for perturbation (Aurora format)
        batch_perturbed = Batch(
            surf_vars={k: v.clone() for k, v in batch_orig.surf_vars.items()},
            static_vars={k: v.clone() for k, v in batch_orig.static_vars.items()},
            atmos_vars={k: v.clone() for k, v in batch_orig.atmos_vars.items()},
            metadata=batch_orig.metadata,
        )
        
        # Convert mask to torch tensor
        device = batch_orig.atmos_vars["t"].device
        mask_torch = torch.from_numpy(perturbation_mask).float().to(device)
        
        # Track total perturbations for analysis
        total_delta_T = torch.zeros_like(batch_orig.atmos_vars["t"][0, 1]).to(device)
        total_delta_Q = torch.zeros_like(batch_orig.atmos_vars["q"][0, 1]).to(device)
        
        # Apply enhanced perturbations to target pressure levels
        p_levels = torch.tensor(batch_orig.metadata.atmos_levels)
        
        for level_mb in self.target_levels:
            if level_mb in batch_orig.metadata.atmos_levels:
                level_idx = list(batch_orig.metadata.atmos_levels).index(level_mb)
                
                # Get specific humidity at this level (kg/kg)
                q_layer = batch_perturbed.atmos_vars["q"][0, 1, level_idx].clone()
                
                # Add realistic moisture variability (small perturbation)
                torch.manual_seed(42)  # For reproducibility
                moisture_noise = torch.randn_like(q_layer) * 1e-4  # 0.1 g/kg variability
                q_layer_perturbed = q_layer + moisture_noise * mask_torch
                
                # Ensure moisture stays positive and realistic
                q_layer_perturbed = torch.clamp(q_layer_perturbed, min=0.0, max=0.02)  # Cap at 20 g/kg
                
                # Calculate frozen and precipitated moisture using enhanced method
                q_perturbation = (q_layer_perturbed - q_layer) * mask_torch
                q_frozen = torch.abs(q_perturbation) * self.freeze_efficiency
                q_fallout = q_frozen * self.fallout_fraction
                
                # Energy balance: warming from freezing, cooling from precipitation fallout
                delta_E = self.L_f * q_frozen - (self.L_v + self.L_f) * q_fallout
                delta_T = delta_E / self.C_p
                
                # Scale to realistic magnitude (±1 to 5K)
                delta_T = torch.clamp(delta_T, min=-5.0, max=5.0)
                
                # Apply temperature change to both time steps
                batch_perturbed.atmos_vars["t"][0, 0, level_idx] += delta_T
                batch_perturbed.atmos_vars["t"][0, 1, level_idx] += delta_T
                
                # Remove precipitated moisture (realistic moisture loss)
                batch_perturbed.atmos_vars["q"][0, 0, level_idx] -= q_fallout
                batch_perturbed.atmos_vars["q"][0, 1, level_idx] -= q_fallout
                
                # Track perturbations for analysis
                total_delta_T[level_idx] += delta_T
                total_delta_Q[level_idx] -= q_fallout
                
                # Enhanced feature 1: Vertical coupling to adjacent levels
                for offset in [-1, 1]:
                    adj_level_idx = level_idx + offset
                    if 0 <= adj_level_idx < len(batch_orig.metadata.atmos_levels):
                        delta_T_adj = delta_T * self.coupling_factor
                        batch_perturbed.atmos_vars["t"][0, 0, adj_level_idx] += delta_T_adj
                        batch_perturbed.atmos_vars["t"][0, 1, adj_level_idx] += delta_T_adj
                        total_delta_T[adj_level_idx] += delta_T_adj * self.coupling_factor
                
                # Enhanced feature 2: Geostrophic wind adjustment via thermal wind
                if level_mb <= 700:  # Apply to steering flow levels
                    # Calculate temperature gradients using finite differences
                    delta_T_np = delta_T.cpu().numpy()
                    
                    # Compute gradients (approximation for spherical coordinates)
                    dlat = np.abs(lats_np[1] - lats_np[0])  # Latitude spacing
                    dlon = np.abs(lons_np[1] - lons_np[0])  # Longitude spacing
                    
                    # Convert to meters for gradient calculation
                    R_earth = 6371000  # m
                    dy = dlat * np.pi * R_earth / 180  # meters per latitude degree
                    dx = dlon * np.pi * R_earth * np.cos(np.radians(center_lat)) / 180  # meters per longitude degree
                    
                    # Finite difference gradients
                    dT_dy_np = np.gradient(delta_T_np, dy, axis=0)  # Meridional gradient [K/m]
                    dT_dx_np = np.gradient(delta_T_np, dx, axis=1)  # Zonal gradient [K/m]
                    
                    # Convert back to torch tensors
                    dT_dy = torch.from_numpy(dT_dy_np).float().to(device)
                    dT_dx = torch.from_numpy(dT_dx_np).float().to(device)
                    
                    # Apply thermal wind relationship: ∂u/∂z ∝ -∂T/∂y, ∂v/∂z ∝ ∂T/∂x
                    wind_adjustment = self.wind_adjustment_factor * 1e3  # Scale for m/s adjustment
                    
                    # Apply to both time steps
                    batch_perturbed.atmos_vars["u"][0, 0, level_idx] -= dT_dy * wind_adjustment
                    batch_perturbed.atmos_vars["u"][0, 1, level_idx] -= dT_dy * wind_adjustment
                    batch_perturbed.atmos_vars["v"][0, 0, level_idx] += dT_dx * wind_adjustment
                    batch_perturbed.atmos_vars["v"][0, 1, level_idx] += dT_dx * wind_adjustment
        
        return batch_perturbed, total_delta_T, total_delta_Q, perturbation_mask

# Configuration
data_path = Path("../data/era5_sandy_2012")
output_dir = Path("./prediction_output")
output_dir.mkdir(exist_ok=True)

day = "2012-10-24"
perturbation_config = {
    'lat': 26.0,   # °N (Bahamas region)
    'lon': -70.0,  # °W (will be converted to 0-360° format)
    'radius_km': 300,  # km
}

print(f"Perturbation Configuration:")
print(f"  Location: {perturbation_config['lat']}°N, {abs(perturbation_config['lon'])}°W")
print(f"  Radius: {perturbation_config['radius_km']} km")
print(f"  Enhanced physics: T+Q+Wind coupling with thermal adjustment")

# Load Aurora model
print(f"\nLoading Aurora 0.25° Pretrained model...")
if torch.cuda.is_available():
    torch.cuda.empty_cache()
    print(f"CUDA available. GPU memory: {torch.cuda.memory_allocated()/1024**3:.2f} GB")

model = Aurora(use_lora=False)
model.load_checkpoint("microsoft/aurora", "aurora-0.25-pretrained.ckpt")
model.eval()

# Move to GPU if available
try:
    model = model.to("cuda")
    device = "cuda"
    print(f"Model loaded on GPU. Memory usage: {torch.cuda.memory_allocated()/1024**3:.2f} GB")
except torch.cuda.OutOfMemoryError:
    print("CUDA out of memory. Using CPU...")
    model = model.to("cpu")
    device = "cpu"

# Load ERA5 data
print(f"\nLoading ERA5 data for {day}...")
static_vars_ds = xr.open_dataset(data_path / "static.nc", engine="netcdf4")
surf_vars_ds = xr.open_dataset(data_path / f"{day}-surface-level.nc", engine="netcdf4")
atmos_vars_ds = xr.open_dataset(data_path / f"{day}-atmospheric.nc", engine="netcdf4")

print(f"Surface variables: {list(surf_vars_ds.data_vars)}")
print(f"Atmospheric levels: {list(atmos_vars_ds.pressure_level.values)} hPa")

# Create Aurora batch function
def create_aurora_batch(static_vars_ds, surf_vars_ds, atmos_vars_ds, time_start_idx=1):
    """Create Aurora batch for given time indices (12:00 UTC initialization)"""
    batch = Batch(
        surf_vars={
            "2t": torch.from_numpy(surf_vars_ds["t2m"].values[time_start_idx:time_start_idx+2][None]),
            "10u": torch.from_numpy(surf_vars_ds["u10"].values[time_start_idx:time_start_idx+2][None]),
            "10v": torch.from_numpy(surf_vars_ds["v10"].values[time_start_idx:time_start_idx+2][None]),
            "msl": torch.from_numpy(surf_vars_ds["msl"].values[time_start_idx:time_start_idx+2][None]),
        },
        static_vars={
            "z": torch.from_numpy(static_vars_ds["z"].values[0]),
            "slt": torch.from_numpy(static_vars_ds["slt"].values[0]),
            "lsm": torch.from_numpy(static_vars_ds["lsm"].values[0]),
        },
        atmos_vars={
            "t": torch.from_numpy(atmos_vars_ds["t"].values[time_start_idx:time_start_idx+2][None]),
            "u": torch.from_numpy(atmos_vars_ds["u"].values[time_start_idx:time_start_idx+2][None]),
            "v": torch.from_numpy(atmos_vars_ds["v"].values[time_start_idx:time_start_idx+2][None]),
            "q": torch.from_numpy(atmos_vars_ds["q"].values[time_start_idx:time_start_idx+2][None]),
            "z": torch.from_numpy(atmos_vars_ds["z"].values[time_start_idx:time_start_idx+2][None]),
        },
        metadata=Metadata(
            lat=torch.from_numpy(surf_vars_ds.latitude.values),
            lon=torch.from_numpy(surf_vars_ds.longitude.values),
            time=(surf_vars_ds.valid_time.values.astype("datetime64[s]").tolist()[time_start_idx+1],),
            atmos_levels=tuple(int(level) for level in atmos_vars_ds.pressure_level.values),
        ),
    )
    return batch

# Create baseline batch (06:00, 12:00 UTC → 12:00 UTC initialization)
batch_baseline = create_aurora_batch(static_vars_ds, surf_vars_ds, atmos_vars_ds, time_start_idx=1)
print(f"\nBaseline batch created")
print(f"Initialization time: {batch_baseline.metadata.time[0]}")
print(f"Grid shape: {batch_baseline.surf_vars['2t'].shape[-2:]}")

# Apply enhanced perturbation
print(f"\nApplying enhanced physics perturbation...")
perturbation_generator = EnhancedPhysicsPerturbation()

batch_perturbed, delta_T_total, delta_Q_total, perturb_mask = perturbation_generator.apply_enhanced_perturbation(
    batch_baseline,
    perturbation_config['lat'],
    perturbation_config['lon'],
    perturbation_config['radius_km']
)

# Report perturbation statistics
print(f"\nPerturbation Applied:")
print(f"  Affected grid points: {perturb_mask.sum()}")
print(f"  Max temperature change: {delta_T_total.max():.3f} K")
print(f"  Min temperature change: {delta_T_total.min():.3f} K")
print(f"  Total moisture removed: {delta_Q_total.abs().sum():.6f} kg/kg")
print(f"  Expected result: Cooling due to energy balance")

# Run baseline forecast
print(f"\nRunning baseline 7-day forecast...")
tracker_baseline = Tracker(
    init_lat=16.6, 
    init_lon=283.1, 
    init_time=datetime(2012, 10, 24, 12, 0)
)

preds_baseline = []
with torch.inference_mode():
    for i, pred in enumerate(rollout(model, batch_baseline, steps=28)):
        pred = pred.to("cpu")
        preds_baseline.append(pred)
        tracker_baseline.step(pred)
        
        if (i+1) % 4 == 0:  # Print every 24 hours
            hours = (i+1) * 6
            print(f"  Baseline +{hours:3d}h: {pred.metadata.time[0]}")
        
        if device == "cuda" and i % 5 == 0:
            torch.cuda.empty_cache()

track_baseline = tracker_baseline.results()

# Run perturbed forecast
print(f"\nRunning enhanced perturbed forecast...")
tracker_perturbed = Tracker(
    init_lat=16.6, 
    init_lon=283.1, 
    init_time=datetime(2012, 10, 24, 12, 0)
)

preds_perturbed = []
with torch.inference_mode():
    for i, pred in enumerate(rollout(model, batch_perturbed, steps=28)):
        pred = pred.to("cpu")
        preds_perturbed.append(pred)
        tracker_perturbed.step(pred)
        
        if (i+1) % 4 == 0:  # Print every 24 hours
            hours = (i+1) * 6
            print(f"  Perturbed +{hours:3d}h: {pred.metadata.time[0]}")
        
        if device == "cuda" and i % 5 == 0:
            torch.cuda.empty_cache()

track_perturbed = tracker_perturbed.results()

print(f"\nForecasts completed!")
print(f"  Baseline track points: {len(track_baseline)}")
print(f"  Perturbed track points: {len(track_perturbed)}")

# Observational track for comparison
obs_data = [
    ("2012-10-24 12:00", 16.6, 283.1),  # Initialization point  
    ("2012-10-24 18:00", 17.7, 283.3),
    ("2012-10-25 00:00", 18.9, 283.6),
    ("2012-10-25 06:00", 20.1, 284.0),
    ("2012-10-25 12:00", 21.7, 284.5),
    ("2012-10-25 18:00", 23.3, 284.7),
    ("2012-10-26 00:00", 24.8, 284.1),
    ("2012-10-26 06:00", 25.7, 283.6),
    ("2012-10-26 12:00", 26.4, 283.1),
    ("2012-10-26 18:00", 27.0, 282.8),
    ("2012-10-27 00:00", 27.5, 282.9),
    ("2012-10-27 06:00", 28.1, 283.1),
    ("2012-10-27 12:00", 28.8, 283.5),
    ("2012-10-27 18:00", 29.7, 284.4),
    ("2012-10-28 00:00", 30.5, 285.3),
    ("2012-10-28 06:00", 31.3, 286.1),
    ("2012-10-28 12:00", 32.0, 287.0),
    ("2012-10-28 18:00", 32.8, 288.0),
    ("2012-10-29 00:00", 33.9, 289.0),
    ("2012-10-29 06:00", 35.3, 289.5),
    ("2012-10-29 12:00", 36.9, 289.0),
    ("2012-10-29 18:00", 38.3, 286.8),  # Near US landfall
    ("2012-10-30 00:00", 39.5, 285.5),  # US Landfall
    ("2012-10-30 06:00", 39.9, 283.8),
    ("2012-10-30 12:00", 40.1, 282.2),
    ("2012-10-30 18:00", 40.4, 281.1),
    ("2012-10-31 00:00", 40.7, 280.2),
]

obs_df = pd.DataFrame(obs_data, columns=['datetime', 'lat', 'lon'])
obs_df['datetime'] = pd.to_datetime(obs_df['datetime'])

# Create visualization
print(f"\nCreating track comparison visualization...")

fig = plt.figure(figsize=(16, 12))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.set_extent([270, 310, 10, 50], crs=ccrs.PlateCarree())

# Geographic features
ax.add_feature(cfeature.OCEAN, facecolor='#e6f3ff', alpha=0.8)
ax.add_feature(cfeature.LAND, facecolor='#f5f5dc', edgecolor='0.5')
ax.add_feature(cfeature.BORDERS.with_scale('50m'), linewidth=0.8, color="0.4")
ax.coastlines('50m', linewidth=0.8)

# Gridlines
gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='0.5', alpha=0.7, linestyle='--')
gl.top_labels = False
gl.right_labels = False

# Plot observed track (reference)
ax.plot(obs_df.lon, obs_df.lat, 'k-', linewidth=5, 
        transform=ccrs.PlateCarree(), label='Observed Track', zorder=6)
ax.scatter(obs_df.lon, obs_df.lat, c='black', s=35, 
          edgecolors='white', linewidth=1.5, transform=ccrs.PlateCarree(), zorder=7)

# Plot baseline track
if len(track_baseline) > 0:
    ax.plot(track_baseline.lon, track_baseline.lat, 'b-', linewidth=3, 
            transform=ccrs.PlateCarree(), label='Aurora Baseline', zorder=5)
    ax.scatter(track_baseline.lon, track_baseline.lat, c='blue', s=25, 
              marker='o', transform=ccrs.PlateCarree(), zorder=6)

# Plot perturbed track
if len(track_perturbed) > 0:
    ax.plot(track_perturbed.lon, track_perturbed.lat, 'r--', linewidth=3, 
            transform=ccrs.PlateCarree(), label='Enhanced Perturbation', zorder=5)
    ax.scatter(track_perturbed.lon, track_perturbed.lat, c='red', s=25, 
              marker='s', transform=ccrs.PlateCarree(), zorder=6)

# Mark initialization point
ax.plot(283.1, 16.6, '^', markersize=18, color='gold', markeredgecolor='black', 
        markeredgewidth=2, transform=ccrs.PlateCarree(), zorder=8, 
        label='Initialization (Oct 24, 12Z)')

# Mark perturbation center (convert longitude to 0-360° format)
perturb_lon_plot = perturbation_config['lon'] + 360 if perturbation_config['lon'] < 0 else perturbation_config['lon']
ax.plot(perturb_lon_plot, perturbation_config['lat'], '*', 
        markersize=18, color='orange', markeredgecolor='black', markeredgewidth=2,
        transform=ccrs.PlateCarree(), zorder=8, label='Perturbation Center (Bahamas)')

# Add perturbation circle
R_earth = 6371  # km
lat_center_rad = np.radians(perturbation_config['lat'])
radius_deg = perturbation_config['radius_km'] / (R_earth * np.pi / 180)

theta = np.linspace(0, 2*np.pi, 100)
circle_lats = perturbation_config['lat'] + radius_deg * np.cos(theta)
circle_lons = perturb_lon_plot + radius_deg * np.sin(theta) / np.cos(lat_center_rad)

ax.plot(circle_lons, circle_lats, 'orange', linewidth=2, linestyle='--', alpha=0.8,
        transform=ccrs.PlateCarree(), zorder=7, label=f'Perturbation Area (300km)')

# Add major cities
cities = [
    ("Miami", 25.7617, 279.8269),
    ("New York", 40.7128, 286.0060), 
    ("DC", 38.9072, 282.9401),
    ("Boston", 42.3601, 288.9740),
    ("Norfolk", 36.8485, 283.8839),
    ("Charleston", 32.7765, 280.0316),
    ("Bermuda", 32.3078, 295.2361),
    ("Kingston", 17.9712, 283.2064),
    ("Havana", 23.1136, 277.6334),
    ("Nassau", 25.0443, 282.6566),
]

for name, lat, lon in cities:
    ax.plot(lon, lat, marker='*', markersize=8, color='darkred', 
            markeredgecolor='black', markeredgewidth=0.5,
            transform=ccrs.PlateCarree(), zorder=6)
    ax.text(lon + 1, lat, name, transform=ccrs.PlateCarree(),
            fontsize=9, ha='left', va='center', weight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', 
                     edgecolor='0.4', alpha=0.9), zorder=6)

ax.legend(loc='upper left', fontsize=12, frameon=True, fancybox=True, shadow=True)
ax.set_title('Hurricane Sandy: Aurora with Enhanced Physics Perturbation\n'
             'Pangu-Style T+Q+Wind Coupling at Bahamas Region (26°N, 70°W)', 
             fontsize=16, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig(output_dir / 'aurora_enhanced_perturbation_track.png', dpi=300, bbox_inches='tight')
print(f"✅ Track comparison saved: {output_dir / 'aurora_enhanced_perturbation_track.png'}")
plt.show()

# Calculate final position errors
def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate great circle distance in km"""
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

# Final analysis
print(f"\n" + "="*60)
print(f"AURORA ENHANCED PERTURBATION EXPERIMENT SUMMARY")
print(f"="*60)

if len(track_baseline) > 0 and len(track_perturbed) > 0 and len(obs_df) > 0:
    min_len = min(len(track_baseline), len(track_perturbed), len(obs_df))
    
    if min_len > 0:
        final_obs = obs_df.iloc[min_len-1]
        final_baseline = track_baseline.iloc[min_len-1]
        final_perturbed = track_perturbed.iloc[min_len-1]
        
        error_baseline = calculate_distance(
            final_baseline.lat, final_baseline.lon,
            final_obs.lat, final_obs.lon
        )
        
        error_perturbed = calculate_distance(
            final_perturbed.lat, final_perturbed.lon,
            final_obs.lat, final_obs.lon
        )
        
        improvement = error_baseline - error_perturbed
        
        print(f"\nFinal Position Errors (vs Observed):")
        print(f"  Baseline error:       {error_baseline:.1f} km")
        print(f"  Perturbed error:      {error_perturbed:.1f} km")
        print(f"  Improvement:          {improvement:+.1f} km")
        
        if improvement > 0:
            print(f"  ✅ Enhanced perturbation IMPROVED track accuracy")
        else:
            print(f"  ⚠️  Enhanced perturbation affected track accuracy")

print(f"\nPerturbation Method Summary:")
print(f"  • Location: 26°N, 70°W (Bahamas region)")
print(f"  • Radius: 300 km (great circle distance)")
print(f"  • Physics: Enhanced energy balance + thermal wind adjustment")
print(f"  • Variables: Temperature + Humidity + Wind coupling")
print(f"  • Target levels: 500-700 hPa with vertical coupling")
print(f"  • Framework: Pangu physics + Aurora model architecture")

print(f"\nFiles Generated:")
print(f"  • aurora_enhanced_perturbation_track.png")

# Clean up GPU memory
if device == "cuda":
    model = model.to("cpu")
    torch.cuda.empty_cache()
    print(f"\n🧹 GPU memory cleaned: {torch.cuda.memory_allocated()/1024**3:.2f} GB")

print(f"\n🎉 Aurora Enhanced Perturbation Experiment completed successfully!")
print(f"="*60)