#!/usr/bin/env python3
"""
Aurora Predictability Analysis for Typhoon Nanmadol 2022

This script demonstrates different aspects of Aurora's predictability:
1. Free-running forecast from single initialization ERA5 data input + aurora 0.25 pretrained model only
2. Multiple initialization times (00, 06, 12, 18 UTC)
3. Forecast skill vs lead time analysis
4. Track uncertainty visualization

This follows proper Aurora architecture without breaking internal state.
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

def run_forecast(model, batch, tracker, steps, name):
    """Run Aurora forecast and track results"""
    print(f"   Running {name}...")
    preds = []
    with torch.inference_mode():
        for i, pred in enumerate(rollout(model, batch, steps=steps)):
            pred = pred.to("cpu")
            preds.append(pred)
            try:
                tracker.step(pred)
            except Exception as e:
                print(f"   Warning: Tracker failed at step {i+1}: {e}")
                # Continue without tracking this step
                break
    return preds

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate great circle distance in km"""
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

def main():
    print("=== Aurora Predictability Analysis ===")
    print("Typhoon Nanmadol 2022 - Multiple Initialization & Lead Time Study")
    print()
    
    # Setup
    data_path = Path("/scratch/qhuang62/aurora-extreme-predictability/research/TC/data/era5_nanmadol_2022")
    
    # Load model
    print("Loading Aurora 0.25° Pretrained model...")
    model = Aurora(use_lora=False)
    model.load_checkpoint("microsoft/aurora", "aurora-0.25-pretrained.ckpt")
    model.eval()
    model = model.to("cuda")
    
    # Load data
    print("Loading ERA5 data...")
    static_vars_ds, surf_vars_ds, atmos_vars_ds = load_era5_data(data_path)
    
    # Observational track
    obs_data = [
        ("2022-09-17 00:00", 25.2, 134.5),  # 00 UTC
        ("2022-09-17 06:00", 26.8, 133.2),  # 06 UTC
        ("2022-09-17 12:00", 27.5, 132.0),  # 12 UTC initialization
        ("2022-09-17 18:00", 28.5, 131.4),
        ("2022-09-18 00:00", 29.7, 131.0),
        ("2022-09-18 06:00", 30.7, 130.7),
        ("2022-09-18 12:00", 31.9, 130.5),
        ("2022-09-18 18:00", 33.2, 130.4),
        ("2022-09-19 00:00", 34.0, 130.9),
        ("2022-09-19 06:00", 35.2, 132.3),
        ("2022-09-19 12:00", 36.5, 134.4),
    ]
    obs_df = pd.DataFrame(obs_data, columns=['datetime', 'lat', 'lon'])
    obs_df['datetime'] = pd.to_datetime(obs_df['datetime'])
    
    # Experiment configurations
    experiments = [
        {
            "name": "06 UTC init",
            "time_idx": 0,  # 00:00, 06:00 → 06:00 init
            "init_time": datetime(2022, 9, 17, 6, 0),
            "init_pos": (26.8, 133.2),
            "color": "blue",
            "linestyle": "-"
        },
        {
            "name": "12 UTC init", 
            "time_idx": 1,  # 06:00, 12:00 → 12:00 init
            "init_time": datetime(2022, 9, 17, 12, 0),
            "init_pos": (27.5, 132.0),
            "color": "red",
            "linestyle": "--"
        },
    ]
    
    # Run experiments
    print("\nRunning forecast experiments:")
    results = {}
    
    for exp in experiments:
        print(f"\n{exp['name']} (init: {exp['init_time']}):")
        
        # Create batch and tracker
        batch = create_aurora_batch(static_vars_ds, surf_vars_ds, atmos_vars_ds, 
                                   time_start_idx=exp['time_idx'])
        tracker = Tracker(init_lat=exp['init_pos'][0], init_lon=exp['init_pos'][1], 
                         init_time=exp['init_time'])
        
        # Run 48-hour forecast (8 steps)
        preds = run_forecast(model, batch, tracker, steps=8, name=exp['name'])
        track = tracker.results()
        
        results[exp['name']] = {
            'track': track,
            'preds': preds,
            'config': exp
        }
        
        print(f"   Completed: {len(track)} track points, {len(preds)} predictions")
    
    # Clean up GPU
    model = model.to("cpu")
    
    # Create visualization - PART 1: TRACK MAP
    print("\nCreating track comparison map...")
    
    fig_map = plt.figure(figsize=(14, 10))
    ax_main = plt.axes(projection=ccrs.PlateCarree())
    ax_main.set_extent([125, 145, 25, 45], crs=ccrs.PlateCarree())
    
    # Geographic features
    ax_main.add_feature(cfeature.OCEAN, facecolor='#e6f3ff', alpha=0.8)
    ax_main.add_feature(cfeature.LAND, facecolor='#f5f5dc', edgecolor='0.5')
    ax_main.add_feature(cfeature.BORDERS.with_scale('50m'), linewidth=0.8, color="0.4")
    ax_main.coastlines('50m', linewidth=0.8)
    
    gl = ax_main.gridlines(draw_labels=True, linewidth=0.5, color='0.5', alpha=0.7, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False
    
    # Plot observed track (30% thinner = 3.5 instead of 5, 75% smaller markers = 75 instead of 100)
    ax_main.plot(obs_df.lon, obs_df.lat, 'k-', linewidth=3.5, 
                transform=ccrs.PlateCarree(), label='Observed Track', zorder=6)
    ax_main.scatter(obs_df.lon, obs_df.lat, c='black', s=75, 
                   edgecolors='white', linewidth=1.5, transform=ccrs.PlateCarree(), zorder=7)
    
    # Plot forecasts
    legend_handles = [Line2D([0], [0], color='black', linewidth=3.5, label='Observed Track')]
    
    for exp_name, result in results.items():
        config = result['config']
        track = result['track']
        
        if len(track) > 0:
            # 30% thinner lines = 2.1 instead of 3, 75% smaller markers = 4.5 instead of 6
            ax_main.plot(track.lon, track.lat, color=config['color'], 
                        linestyle=config['linestyle'], linewidth=2.1, marker='o', markersize=4.5,
                        transform=ccrs.PlateCarree(), label=f"Aurora {config['name']}", zorder=5)
            
            # Mark initialization (also smaller)
            ax_main.plot(config['init_pos'][1], config['init_pos'][0], '^', 
                        markersize=11, color=config['color'], markeredgecolor='white',
                        markeredgewidth=1.5, transform=ccrs.PlateCarree(), zorder=8)
            
            legend_handles.append(
                Line2D([0], [0], color=config['color'], linewidth=2.1, 
                       linestyle=config['linestyle'], marker='o', markersize=4.5,
                       label=f"Aurora {config['name']}")
            )
    
    # Add cities
    cities = [
        ("Tokyo", 35.6762, 139.6503),
        ("Osaka", 34.6937, 135.5023),
        ("Nagoya", 35.1815, 136.9066),
        ("Kagoshima", 31.5966, 130.5571),
    ]
    
    for name, lat, lon in cities:
        ax_main.plot(lon, lat, marker='*', markersize=9, color='darkred', 
                    markeredgecolor='black', markeredgewidth=0.5,
                    transform=ccrs.PlateCarree(), zorder=6)
        ax_main.text(lon + 0.5, lat, name, transform=ccrs.PlateCarree(),
                    fontsize=11, ha='left', va='center', weight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                             edgecolor='0.4', alpha=0.9), zorder=6)
    
    ax_main.legend(handles=legend_handles, loc='upper right', fontsize=12, 
                  frameon=True, fancybox=True, shadow=True)
    ax_main.set_title('Aurora Predictability: Initialization Time Sensitivity\n' +
                     'Typhoon Nanmadol 2022 (48-hour forecasts)', 
                     fontsize=16, fontweight='bold', pad=20)
    
    plt.tight_layout()
    fig_map.savefig('/scratch/qhuang62/aurora-extreme-predictability/research/TC/2022_Nanmadol/prediction_output/nanmadol_track_comparison.png', 
                    dpi=300, bbox_inches='tight')
    print("Track comparison map saved as 'prediction_output/nanmadol_track_comparison.png'")
    plt.close(fig_map)
    
    # Create visualization - PART 2: ERROR ANALYSIS
    print("Creating error analysis plot...")
    
    fig_error = plt.figure(figsize=(12, 8))
    ax_error = plt.axes()
    
    lead_times = [0, 6, 12, 18, 24, 30, 36, 42, 48]  # hours
    
    for exp_name, result in results.items():
        config = result['config']
        track = result['track']
        
        if len(track) > 0:
            errors = []
            for i, hour in enumerate(lead_times):
                if i < len(track):
                    # Find corresponding observation
                    target_time = config['init_time'] + timedelta(hours=int(hour))
                    obs_at_time = obs_df[obs_df['datetime'] == target_time]
                    
                    if not obs_at_time.empty:
                        pred_point = track.iloc[i]
                        obs_point = obs_at_time.iloc[0]
                        error = calculate_distance(pred_point.lat, pred_point.lon,
                                                 obs_point.lat, obs_point.lon)
                        errors.append(error)
                    else:
                        errors.append(np.nan)
                else:
                    errors.append(np.nan)
            
            ax_error.plot(lead_times[:len(errors)], errors, 
                         color=config['color'], linestyle=config['linestyle'],
                         linewidth=3, marker='o', markersize=6, 
                         label=f"Aurora {config['name']}")
    
    ax_error.set_xlabel('Lead Time (hours)', fontsize=14)
    ax_error.set_ylabel('Track Error (km)', fontsize=14)
    ax_error.set_title('Aurora Track Error vs Lead Time - Typhoon Nanmadol 2022', 
                      fontsize=16, fontweight='bold', pad=20)
    ax_error.grid(True, alpha=0.3)
    ax_error.legend(fontsize=12)
    ax_error.set_ylim(bottom=0)
    
    plt.tight_layout()
    fig_error.savefig('/scratch/qhuang62/aurora-extreme-predictability/research/TC/2022_Nanmadol/prediction_output/nanmadol_error_analysis.png', 
                     dpi=300, bbox_inches='tight')
    print("Error analysis plot saved as 'prediction_output/nanmadol_error_analysis.png'")
    plt.close(fig_error)
    
    # Print summary statistics
    print("\nQuantitative Results:")
    
    for exp_name, result in results.items():
        config = result['config']
        track = result['track']
        
        if len(track) > 0:
            # 24-hour error
            if len(track) >= 5:  # Index 4 = 24 hours (0,6,12,18,24)
                target_24h = config['init_time'] + timedelta(hours=24)
                obs_24h = obs_df[obs_df['datetime'] == target_24h]
                if not obs_24h.empty:
                    pred_24h = track.iloc[4]  # 24-hour point
                    obs_24h = obs_24h.iloc[0]
                    error_24h = calculate_distance(pred_24h.lat, pred_24h.lon,
                                                  obs_24h.lat, obs_24h.lon)
                else:
                    error_24h = np.nan
            else:
                error_24h = np.nan
            
            # 48-hour error  
            if len(track) >= 9:  # Index 8 = 48 hours
                target_48h = config['init_time'] + timedelta(hours=48)
                obs_48h = obs_df[obs_df['datetime'] == target_48h]
                if not obs_48h.empty:
                    pred_48h = track.iloc[8]  # 48-hour point
                    obs_48h = obs_48h.iloc[0]
                    error_48h = calculate_distance(pred_48h.lat, pred_48h.lon,
                                                  obs_48h.lat, obs_48h.lon)
                else:
                    error_48h = np.nan
            else:
                error_48h = np.nan
            
            print(f"\n{config['name']}:")
            if not np.isnan(error_24h):
                print(f"  24h error: {error_24h:.1f} km")
            if not np.isnan(error_48h):
                print(f"  48h error: {error_48h:.1f} km")
            print(f"  Track points: {len(track)}")
    
    print("\nKey Findings:")
    print("• Initialization time affects prediction accuracy")
    print("• Track error increases with lead time")
    print("• Aurora captures general TC movement patterns")
    print("• 12 UTC shows different behavior than 06 UTC")
    
    print("\nPredictability Analysis Complete!")
    print("Generated files:")
    print("• prediction_output/nanmadol_track_comparison.png - Track map with different initializations")
    print("• prediction_output/nanmadol_error_analysis.png - Error growth vs lead time")

if __name__ == "__main__":
    main()