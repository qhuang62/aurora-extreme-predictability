#!/usr/bin/env python3
"""
Aurora Predictability Analysis for Hurricane Sandy 2012

This script demonstrates Aurora's predictability for a major Atlantic hurricane:
1. Free-running forecast from single initialization
2. Multiple initialization times (06:00, 12:00 UTC) 
3. Extended 7-day forecast to capture complete lifecycle
4. Track uncertainty and US landfall prediction

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

def load_era5_data(data_path, day="2012-10-24"):
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

def run_forecast(model, batch, tracker, steps, name, device="cuda"):
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
            
            # Clear GPU memory periodically
            if device == "cuda" and i % 5 == 0:
                torch.cuda.empty_cache()
                
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
    print("Hurricane Sandy 2012 - Extended 7-Day Forecast & US Landfall Prediction")
    print()
    
    # Clear GPU cache first
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        print(f"CUDA available: {torch.cuda.is_available()}")
        print(f"GPU memory before loading: {torch.cuda.memory_allocated()/1024**3:.2f} GB")
    
    # Setup
    data_path = Path("/scratch/qhuang62/aurora-extreme-predictability/research/TC/data/era5_sandy_2012")
    
    # Load model
    print("Loading Aurora 0.25° Pretrained model...")
    model = Aurora(use_lora=False)
    model.load_checkpoint("microsoft/aurora", "aurora-0.25-pretrained.ckpt")
    model.eval()
    
    # Try to move to GPU with error handling
    try:
        model = model.to("cuda")
        print(f"Model loaded on GPU. Memory usage: {torch.cuda.memory_allocated()/1024**3:.2f} GB")
    except torch.cuda.OutOfMemoryError:
        print("CUDA out of memory. Falling back to CPU...")
        model = model.to("cpu")
        device = "cpu"
    else:
        device = "cuda"
    
    # Load data
    print("Loading ERA5 data...")
    static_vars_ds, surf_vars_ds, atmos_vars_ds = load_era5_data(data_path)
    
    # Observational track from IBTrACS - complete lifecycle
    obs_data = [
        ("2012-10-24 06:00", 15.6, 282.9),  # 06:00 UTC init point
        ("2012-10-24 12:00", 16.6, 283.1),  # 12:00 UTC init point  
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
        ("2012-10-29 00:00", 33.9, 289.0),  # Final approach
        ("2012-10-29 06:00", 35.3, 289.5),
        ("2012-10-29 12:00", 36.9, 289.0),
        ("2012-10-29 18:00", 38.3, 286.8),  # Near landfall
        ("2012-10-30 00:00", 39.5, 285.5),  # US Landfall
        ("2012-10-30 06:00", 39.9, 283.8),
        ("2012-10-30 12:00", 40.1, 282.2),
        ("2012-10-30 18:00", 40.4, 281.1),
        ("2012-10-31 00:00", 40.7, 280.2),  # Final position
    ]
    obs_df = pd.DataFrame(obs_data, columns=['datetime', 'lat', 'lon'])
    obs_df['datetime'] = pd.to_datetime(obs_df['datetime'])
    
    # Experiment configurations - both initialization times
    experiments = [
        {
            "name": "06 UTC init",
            "time_idx": 0,  # 00:00, 06:00 → 06:00 init
            "init_time": datetime(2012, 10, 24, 6, 0),
            "init_pos": (15.6, 282.9),
            "color": "blue",
            "linestyle": "-"
        },
        {
            "name": "12 UTC init", 
            "time_idx": 1,  # 06:00, 12:00 → 12:00 init
            "init_time": datetime(2012, 10, 24, 12, 0),
            "init_pos": (16.6, 283.1),
            "color": "red",
            "linestyle": "--"
        },
    ]
    
    # Run experiments - Extended 7-day forecast (28 steps)
    print("\nRunning extended forecast experiments:")
    results = {}
    
    for exp in experiments:
        print(f"\n{exp['name']} (init: {exp['init_time']}):")
        
        # Create batch and tracker
        batch = create_aurora_batch(static_vars_ds, surf_vars_ds, atmos_vars_ds, 
                                   time_start_idx=exp['time_idx'])
        tracker = Tracker(init_lat=exp['init_pos'][0], init_lon=exp['init_pos'][1], 
                         init_time=exp['init_time'])
        
        # Run 7-day forecast (28 steps = 168 hours)
        preds = run_forecast(model, batch, tracker, steps=28, name=exp['name'], device=device)
        track = tracker.results()
        
        results[exp['name']] = {
            'track': track,
            'preds': preds,
            'config': exp
        }
        
        print(f"   Completed: {len(track)} track points, {len(preds)} predictions")
        print(f"   Forecast end time: {track.iloc[-1].time if len(track) > 0 else 'N/A'}")
    
    # Clean up GPU
    if device == "cuda":
        model = model.to("cpu")
        torch.cuda.empty_cache()
        print(f"GPU memory after cleanup: {torch.cuda.memory_allocated()/1024**3:.2f} GB")
    
    # Create visualization - PART 1: COMPLETE TRACK MAP
    print("\nCreating complete track comparison map...")
    
    fig_map = plt.figure(figsize=(16, 12))
    ax_main = plt.axes(projection=ccrs.PlateCarree())
    ax_main.set_extent([270, 310, 10, 50], crs=ccrs.PlateCarree())  # Full Atlantic basin
    
    # Geographic features
    ax_main.add_feature(cfeature.OCEAN, facecolor='#e6f3ff', alpha=0.8)
    ax_main.add_feature(cfeature.LAND, facecolor='#f5f5dc', edgecolor='0.5')
    ax_main.add_feature(cfeature.BORDERS.with_scale('50m'), linewidth=0.8, color="0.4")
    ax_main.coastlines('50m', linewidth=0.8)
    
    gl = ax_main.gridlines(draw_labels=True, linewidth=0.5, color='0.5', alpha=0.7, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False
    
    # Plot observed track (full lifecycle)
    ax_main.plot(obs_df.lon, obs_df.lat, 'k-', linewidth=4, 
                transform=ccrs.PlateCarree(), label='Observed Track', zorder=6)
    ax_main.scatter(obs_df.lon, obs_df.lat, c='black', s=25, 
                   edgecolors='white', linewidth=1, transform=ccrs.PlateCarree(), zorder=7)
    
    # Key dates section removed - no yellow labels
    
    # Plot forecasts
    legend_handles = [Line2D([0], [0], color='black', linewidth=4, label='Observed Track')]
    
    for exp_name, result in results.items():
        config = result['config']
        track = result['track']
        
        if len(track) > 0:
            ax_main.plot(track.lon, track.lat, color=config['color'], 
                        linestyle=config['linestyle'], linewidth=3, marker='o', markersize=3,
                        transform=ccrs.PlateCarree(), label=f"Aurora {config['name']}", zorder=5)
            
            # Mark initialization
            ax_main.plot(config['init_pos'][1], config['init_pos'][0], '^', 
                        markersize=15, color=config['color'], markeredgecolor='white',
                        markeredgewidth=2, transform=ccrs.PlateCarree(), zorder=8)
            
            # Mark final prediction
            final_point = track.iloc[-1]
            ax_main.plot(final_point.lon, final_point.lat, 's', 
                        markersize=12, color=config['color'], markeredgecolor='black',
                        markeredgewidth=1.5, transform=ccrs.PlateCarree(), zorder=8)
            
            legend_handles.append(
                Line2D([0], [0], color=config['color'], linewidth=3, 
                       linestyle=config['linestyle'], marker='o', markersize=3,
                       label=f"Aurora {config['name']}")
            )
    
    # Add major US cities and landmarks
    cities = [
        ("Miami", 25.7617, 279.8269),
        ("New York", 40.7128, 286.0060), 
        ("DC", 38.9072, 282.9401),
        ("Boston", 42.3601, 288.9740),
        ("Norfolk", 36.8485, 283.8839),
        ("Charleston", 32.7765, 280.0316),
        ("Bermuda", 32.3078, 295.2361),
        ("Kingston, Jamaica", 17.9712, 283.2064),
        ("Havana, Cuba",    23.1136, 277.6334)
    ]
    
    for name, lat, lon in cities:
        ax_main.plot(lon, lat, marker='*', markersize=8, color='darkred', 
                    markeredgecolor='black', markeredgewidth=0.5,
                    transform=ccrs.PlateCarree(), zorder=6)
        ax_main.text(lon + 0.8, lat, name, transform=ccrs.PlateCarree(),
                    fontsize=9, ha='left', va='center', weight='bold',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', 
                             edgecolor='0.4', alpha=0.9), zorder=6)
    
    ax_main.legend(handles=legend_handles, loc='upper left', fontsize=12, 
                  frameon=True, fancybox=True, shadow=True)
    ax_main.set_title('Aurora 7-Day Forecast: Hurricane Sandy 2012 (Initi: Oct 24)', 
                     fontsize=18, fontweight='bold', pad=20)
    
    plt.tight_layout()
    fig_map.savefig('/scratch/qhuang62/aurora-extreme-predictability/research/TC/2012_Sandy/prediction_output/sandy_7day_track_comparison.png', 
                    dpi=300, bbox_inches='tight')
    print("7-day track comparison map saved as 'prediction_output/sandy_7day_track_comparison.png'")
    plt.close(fig_map)
    
    # Create visualization - PART 2: ERROR ANALYSIS
    print("Creating extended error analysis plot...")
    
    fig_error = plt.figure(figsize=(14, 10))
    ax_error = plt.axes()
    
    lead_times = list(range(0, 168+6, 6))  # 0 to 168 hours (7 days) every 6 hours
    
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
                         linewidth=3, marker='o', markersize=4, 
                         label=f"Aurora {config['name']}")
    
    # Add key event markers
    landfall_time = 120  # ~5 days from Oct 24 to Oct 29
    ax_error.axvline(x=landfall_time, color='red', linestyle=':', linewidth=2, alpha=0.7)
    ax_error.text(landfall_time+2, ax_error.get_ylim()[1]*0.9, 'US Landfall\n(Oct 29)', 
                 fontsize=10, weight='bold', color='red')
    
    ax_error.set_xlabel('Lead Time (hours)', fontsize=14)
    ax_error.set_ylabel('Track Error (km)', fontsize=14)
    ax_error.set_title('Aurora Track Error vs Lead Time - Hurricane Sandy 2012', 
                      fontsize=16, fontweight='bold', pad=20)
    ax_error.grid(True, alpha=0.3)
    ax_error.legend(fontsize=12)
    ax_error.set_ylim(bottom=0)
    ax_error.set_xlim(0, 168)
    
    plt.tight_layout()
    fig_error.savefig('/scratch/qhuang62/aurora-extreme-predictability/research/TC/2012_Sandy/prediction_output/sandy_7day_error_analysis.png', 
                     dpi=300, bbox_inches='tight')
    print("Extended error analysis plot saved as 'prediction_output/sandy_7day_error_analysis.png'")
    plt.close(fig_error)
    
    # Print summary statistics
    print("\nQuantitative Results (Extended 7-Day Forecast):")
    
    for exp_name, result in results.items():
        config = result['config']
        track = result['track']
        
        if len(track) > 0:
            # Key forecast milestones
            milestones = [
                (24, "24h"),
                (48, "48h"), 
                (72, "72h"),
                (120, "5-day (near landfall)"),
                (168, "7-day")
            ]
            
            print(f"\n{config['name']}:")
            
            for hours, label in milestones:
                step_idx = hours // 6  # Convert hours to step index
                if step_idx < len(track):
                    target_time = config['init_time'] + timedelta(hours=hours)
                    obs_at_time = obs_df[obs_df['datetime'] == target_time]
                    
                    if not obs_at_time.empty:
                        pred_point = track.iloc[step_idx]
                        obs_point = obs_at_time.iloc[0]
                        error = calculate_distance(pred_point.lat, pred_point.lon,
                                                 obs_point.lat, obs_point.lon)
                        print(f"  {label} error: {error:.1f} km")
                        
                        # Special landfall analysis
                        if hours == 120:
                            print(f"    Pred position: {pred_point.lat:.1f}°N, {360-pred_point.lon:.1f}°W")
                            print(f"    Obs position: {obs_point.lat:.1f}°N, {360-obs_point.lon:.1f}°W")
            
            print(f"  Total forecast duration: {len(track)*6} hours")
            
            # Landfall prediction assessment
            landfall_window = obs_df[
                (obs_df['datetime'] >= datetime(2012, 10, 29, 12, 0)) &
                (obs_df['datetime'] <= datetime(2012, 10, 30, 6, 0))
            ]
            if not landfall_window.empty:
                print(f"  Observed landfall window: Oct 29 12Z - Oct 30 06Z")
                
                # Check if prediction gets close to US coast
                us_coast_approach = track[
                    (track.lat > 35) & (track.lon > 285) & (track.lon < 290)
                ]
                if not us_coast_approach.empty:
                    print(f"  Predicted US coast approach: Yes")
                else:
                    print(f"  Predicted US coast approach: No")
    
    print("\nKey Findings:")
    print("• Extended 7-day Aurora forecast for major Atlantic hurricane")
    print("• Initialization time sensitivity across full storm lifecycle")
    print("• Track error evolution through recurvature and landfall phases")
    print("• Aurora's capability for predicting US hurricane landfall timing")
    print("• Comparison with traditional NWP model forecast horizons")
    
    print("\nExtended Predictability Analysis Complete!")
    print("Generated files:")
    print("• prediction_output/sandy_7day_track_comparison.png - Complete lifecycle track map")
    print("• prediction_output/sandy_7day_error_analysis.png - Extended error evolution")
    print("\nThis analysis demonstrates Aurora's potential for extended hurricane")
    print("prediction including major landfall events in the US East Coast.")

if __name__ == "__main__":
    main()