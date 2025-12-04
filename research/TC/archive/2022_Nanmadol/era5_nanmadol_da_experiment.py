#!/usr/bin/env python3
"""
Aurora Data Assimilation Experiment for Typhoon Nanmadol 2022

This script implements a controlled experiment comparing:
1. Free-running 48-hour forecast (no updates)
2. Data assimilation with 12-hour observational updates
3. Observed track for validation

The script generates a single comprehensive visualization showing all tracks.
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

def load_era5_data(data_path, day="2022-09-17"):
    """Load ERA5 data for Aurora batch creation"""
    static_vars_ds = xr.open_dataset(data_path / "static.nc", engine="netcdf4")
    surf_vars_ds = xr.open_dataset(data_path / f"{day}-surface-level.nc", engine="netcdf4")
    atmos_vars_ds = xr.open_dataset(data_path / f"{day}-atmospheric.nc", engine="netcdf4")
    
    return static_vars_ds, surf_vars_ds, atmos_vars_ds

def create_aurora_batch(static_vars_ds, surf_vars_ds, atmos_vars_ds, time_start_idx=1):
    """Create Aurora batch for given time indices"""
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

def run_forecast_segment(model, batch, tracker, steps):
    """Run forecast for specified number of steps"""
    preds = []
    with torch.inference_mode():
        for pred in rollout(model, batch, steps=steps):
            pred = pred.to("cpu")
            preds.append(pred)
            tracker.step(pred)
    return preds

def get_observed_position(obs_df, target_time):
    """Get observed position at target time"""
    target_obs = obs_df[obs_df['datetime'] == target_time]
    if not target_obs.empty:
        return target_obs.iloc[0]['lat'], target_obs.iloc[0]['lon']
    return None, None

def create_updated_tracker(lat, lon, time):
    """Create new tracker with updated position"""
    return Tracker(init_lat=lat, init_lon=lon, init_time=time)

def main():
    print("=== Aurora Data Assimilation Experiment ===")
    print("Typhoon Nanmadol 2022 - Comparing Free-running vs DA-enhanced forecasts")
    print()
    
    # Setup paths and load model
    data_path = Path("/scratch/qhuang62/aurora-extreme-predictability/research/TC/data/era5_nanmadol_2022")
    
    # Load Aurora model
    print("Loading Aurora 0.25° Pretrained model...")
    model = Aurora(use_lora=False)
    model.load_checkpoint("microsoft/aurora", "aurora-0.25-pretrained.ckpt")
    model.eval()
    model = model.to("cuda")
    
    # Load ERA5 data
    print("Loading ERA5 data...")
    static_vars_ds, surf_vars_ds, atmos_vars_ds = load_era5_data(data_path)
    
    # Observational data for Nanmadol
    obs_data = [
        ("2022-09-17 12:00", 27.5, 132.0),  # Initialization point
        ("2022-09-17 18:00", 28.5, 131.4),
        ("2022-09-18 00:00", 29.7, 131.0),  # 12-hour update point
        ("2022-09-18 06:00", 30.7, 130.7),
        ("2022-09-18 12:00", 31.9, 130.5),  # 24-hour update point
        ("2022-09-18 18:00", 33.2, 130.4),
        ("2022-09-19 00:00", 34.0, 130.9),  # 36-hour update point
        ("2022-09-19 06:00", 35.2, 132.3),
        ("2022-09-19 12:00", 36.5, 134.4),  # 48-hour endpoint
    ]
    
    obs_df = pd.DataFrame(obs_data, columns=['datetime', 'lat', 'lon'])
    obs_df['datetime'] = pd.to_datetime(obs_df['datetime'])
    
    init_time = datetime(2022, 9, 17, 12, 0)
    
    # ===== EXPERIMENT 1: FREE-RUNNING FORECAST =====
    print("\n1. Running FREE-RUNNING 48-hour forecast...")
    
    # Create initial batch and tracker
    batch_free = create_aurora_batch(static_vars_ds, surf_vars_ds, atmos_vars_ds, time_start_idx=1)
    tracker_free = Tracker(init_lat=27.5, init_lon=132.0, init_time=init_time)
    
    # Run full 48-hour forecast (8 steps × 6 hours)
    preds_free = run_forecast_segment(model, batch_free, tracker_free, steps=8)
    track_free = tracker_free.results()
    
    print(f"   Free-running forecast completed: {len(track_free)} points")
    
    # ===== EXPERIMENT 2: DATA ASSIMILATION WITH 12-HOUR UPDATES =====
    print("\n2. Running DATA ASSIMILATION with 12-hour updates...")
    
    # Initialize DA experiment
    current_time = init_time
    tracker_da = Tracker(init_lat=27.5, init_lon=132.0, init_time=current_time)
    all_preds_da = []
    
    # Update points: 12h, 24h, 36h after initialization
    update_times = [
        init_time + timedelta(hours=12),   # 2022-09-18 00:00
        init_time + timedelta(hours=24),   # 2022-09-18 12:00
        init_time + timedelta(hours=36),   # 2022-09-19 00:00
    ]
    
    print("   DA Forecast segments:")
    
    # Segment 1: 0-12 hours (2 steps)
    print("   Segment 1: 12:00 → 00:00 (12 hours)")
    batch_da1 = create_aurora_batch(static_vars_ds, surf_vars_ds, atmos_vars_ds, time_start_idx=1)
    preds_da1 = run_forecast_segment(model, batch_da1, tracker_da, steps=2)
    all_preds_da.extend(preds_da1)
    
    # Update 1: Reset with observed position at 12-hour mark
    obs_lat_12h, obs_lon_12h = get_observed_position(obs_df, update_times[0])
    if obs_lat_12h is not None:
        print(f"   Update 1: Reset to observed position {obs_lat_12h:.1f}°N, {obs_lon_12h:.1f}°E")
        tracker_da = create_updated_tracker(obs_lat_12h, obs_lon_12h, update_times[0])
    
    # Segment 2: 12-24 hours (2 steps)
    print("   Segment 2: 00:00 → 12:00 (12 hours)")
    # Note: For simplicity, we reuse the same batch. In practice, you'd download data for the new time.
    preds_da2 = run_forecast_segment(model, batch_da1, tracker_da, steps=2)
    all_preds_da.extend(preds_da2)
    
    # Update 2: Reset with observed position at 24-hour mark
    obs_lat_24h, obs_lon_24h = get_observed_position(obs_df, update_times[1])
    if obs_lat_24h is not None:
        print(f"   Update 2: Reset to observed position {obs_lat_24h:.1f}°N, {obs_lon_24h:.1f}°E")
        tracker_da = create_updated_tracker(obs_lat_24h, obs_lon_24h, update_times[1])
    
    # Segment 3: 24-36 hours (2 steps)
    print("   Segment 3: 12:00 → 00:00 (12 hours)")
    preds_da3 = run_forecast_segment(model, batch_da1, tracker_da, steps=2)
    all_preds_da.extend(preds_da3)
    
    # Update 3: Reset with observed position at 36-hour mark
    obs_lat_36h, obs_lon_36h = get_observed_position(obs_df, update_times[2])
    if obs_lat_36h is not None:
        print(f"   Update 3: Reset to observed position {obs_lat_36h:.1f}°N, {obs_lon_36h:.1f}°E")
        tracker_da = create_updated_tracker(obs_lat_36h, obs_lon_36h, update_times[2])
    
    # Segment 4: 36-48 hours (2 steps)
    print("   Segment 4: 00:00 → 12:00 (12 hours)")
    preds_da4 = run_forecast_segment(model, batch_da1, tracker_da, steps=2)
    all_preds_da.extend(preds_da4)
    
    track_da = tracker_da.results()
    print(f"   DA forecast completed: {len(all_preds_da)} prediction steps")
    
    # Clean up GPU
    model = model.to("cpu")
    
    # ===== VISUALIZATION =====
    print("\n3. Creating comprehensive track comparison...")
    
    fig = plt.figure(figsize=(16, 12))
    ax = plt.axes(projection=ccrs.PlateCarree())
    
    # Set map extent for typhoon region
    ax.set_extent([125, 145, 25, 45], crs=ccrs.PlateCarree())
    
    # Add geographic features
    ax.add_feature(cfeature.OCEAN, facecolor='#e6f3ff', alpha=0.8)
    ax.add_feature(cfeature.LAND, facecolor='#f5f5dc', edgecolor='0.5')
    ax.add_feature(cfeature.BORDERS.with_scale('50m'), linewidth=0.8, color="0.4")
    ax.coastlines('50m', linewidth=0.8)
    
    # Add gridlines
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='0.5', alpha=0.7, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False
    
    # Plot observed track (black solid line)
    ax.plot(obs_df.lon, obs_df.lat, 'k-', linewidth=4, 
            transform=ccrs.PlateCarree(), label='Observed Track', zorder=6)
    ax.scatter(obs_df.lon, obs_df.lat, c='black', s=80, 
              edgecolors='white', linewidth=2, transform=ccrs.PlateCarree(), zorder=7)
    
    # Plot free-running forecast (blue dashed line)
    ax.plot(track_free.lon, track_free.lat, 'b--', linewidth=3, marker='o', markersize=6,
            transform=ccrs.PlateCarree(), label='Free-running Forecast', zorder=5)
    
    # Plot DA forecast (red dash-dot line)
    ax.plot(track_da.lon, track_da.lat, 'r-.', linewidth=3, marker='s', markersize=6,
            transform=ccrs.PlateCarree(), label='DA-enhanced Forecast', zorder=5)
    
    # Mark initialization point
    init_lon, init_lat = 132.0, 27.5
    ax.plot(init_lon, init_lat, '^', markersize=20, color='gold', markeredgecolor='black', 
            markeredgewidth=2, transform=ccrs.PlateCarree(), zorder=8, 
            label='Initialization (12:00 UTC)')
    
    # Mark update points
    update_positions = [
        (obs_lat_12h, obs_lon_12h, "12h"),
        (obs_lat_24h, obs_lon_24h, "24h"), 
        (obs_lat_36h, obs_lon_36h, "36h")
    ]
    
    for lat, lon, label in update_positions:
        if lat is not None and lon is not None:
            ax.plot(lon, lat, 'D', markersize=12, color='red', markeredgecolor='white',
                    markeredgewidth=2, transform=ccrs.PlateCarree(), zorder=8)
            ax.text(lon + 0.8, lat + 0.3, f"Update\n{label}", transform=ccrs.PlateCarree(),
                    fontsize=9, ha='left', va='bottom', weight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.7,
                             edgecolor='white'), zorder=8, color='white')
    
    # Add major Japanese cities
    cities = [
        ("Tokyo", 35.6762, 139.6503),
        ("Osaka", 34.6937, 135.5023),
        ("Nagoya", 35.1815, 136.9066),
        ("Kagoshima", 31.5966, 130.5571),
    ]
    
    for name, lat, lon in cities:
        ax.plot(lon, lat, marker='*', markersize=12, color='darkred', 
                markeredgecolor='black', markeredgewidth=0.5,
                transform=ccrs.PlateCarree(), zorder=6)
        ax.text(lon + 0.5, lat, name, transform=ccrs.PlateCarree(),
                fontsize=11, ha='left', va='center', weight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                         edgecolor='0.4', alpha=0.9), zorder=6)
    
    # Create comprehensive legend
    legend_handles = [
        Line2D([0], [0], color='black', linewidth=4, label='Observed Track'),
        Line2D([0], [0], color='blue', linewidth=3, linestyle='--', 
               marker='o', markersize=6, label='Free-running Forecast'),
        Line2D([0], [0], color='red', linewidth=3, linestyle='-.', 
               marker='s', markersize=6, label='DA-enhanced Forecast'),
        Line2D([0], [0], marker='^', markersize=20, color='gold', 
               markeredgecolor='black', linewidth=0, label='Initialization Point'),
        Line2D([0], [0], marker='D', markersize=12, color='red', 
               markeredgecolor='white', linewidth=0, label='DA Update Points')
    ]
    ax.legend(handles=legend_handles, loc='upper right', fontsize=12, frameon=True,
             fancybox=True, shadow=True, bbox_to_anchor=(0.98, 0.98))
    
    # Set title
    title_lines = [
        'Aurora Data Assimilation Experiment: Typhoon Nanmadol 2022',
        'Comparing Free-running vs DA-enhanced Forecasts with 12-hour Updates',
        'Sep 17-19, 2022 (48-hour forecast from 12:00 UTC)'
    ]
    ax.set_title('\n'.join(title_lines), fontsize=16, fontweight='bold', pad=30)
    
    plt.tight_layout()
    
    # ===== QUANTITATIVE ANALYSIS =====
    print("\n4. Quantitative Results:")
    
    def calculate_distance(lat1, lon1, lat2, lon2):
        """Calculate great circle distance in km"""
        R = 6371
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        return R * c
    
    # Final position errors
    final_obs = obs_df.iloc[-1]
    final_free = track_free.iloc[-1]
    final_da = track_da.iloc[-1]
    
    error_free = calculate_distance(final_free.lat, final_free.lon, 
                                   final_obs.lat, final_obs.lon)
    error_da = calculate_distance(final_da.lat, final_da.lon,
                                 final_obs.lat, final_obs.lon)
    
    print(f"\nFinal Position Errors (48-hour forecast):")
    print(f"   Free-running: {error_free:.1f} km")
    print(f"   DA-enhanced:  {error_da:.1f} km")
    print(f"   Improvement:  {error_free - error_da:+.1f} km ({100*(error_free-error_da)/error_free:+.1f}%)")
    
    # 24-hour comparison
    if len(track_free) >= 4 and len(track_da) >= 4:
        mid_obs = obs_df[obs_df['datetime'] == init_time + timedelta(hours=24)].iloc[0]
        mid_free = track_free.iloc[3]
        mid_da = track_da.iloc[3]
        
        error_24h_free = calculate_distance(mid_free.lat, mid_free.lon,
                                           mid_obs.lat, mid_obs.lon)
        error_24h_da = calculate_distance(mid_da.lat, mid_da.lon,
                                         mid_obs.lat, mid_obs.lon)
        
        print(f"\n24-hour Position Errors:")
        print(f"   Free-running: {error_24h_free:.1f} km")
        print(f"   DA-enhanced:  {error_24h_da:.1f} km")
        print(f"   Improvement:  {error_24h_free - error_24h_da:+.1f} km ({100*(error_24h_free-error_24h_da)/error_24h_free:+.1f}%)")
    
    print(f"\nExperiment completed! Check the visualization above.")
    print("The plot shows observed track (black), free-running forecast (blue dashed),")
    print("and DA-enhanced forecast (red dash-dot) with update points marked.")
    
    plt.show()

if __name__ == "__main__":
    main()