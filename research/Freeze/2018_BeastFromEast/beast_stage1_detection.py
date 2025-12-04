#!/usr/bin/env python3
"""
Beast from the East 2018 - Stage 1: Lead Time Assessment

Tests 4 different lead times (1, 7, 14, 21 days) by varying initialization date.
All forecasts target the same critical event: onset (Feb 27), peak (Feb 28), recovery (Mar 2).

This answers: "How far in advance can we predict the Beast from East freeze event?"

Based on baseline analysis results:
- Onset: Feb 27, 2018 00:00 UTC (regional mean < 0°C)
- Peak: Feb 28, 2018 06:00 UTC (coldest regional mean: -2.57°C, min: -31.8°C)
- Recovery: Mar 2, 2018 00:00 UTC (regional mean > 0°C)
- Duration: 60 hours (2.5 days)
"""

import sys
from pathlib import Path
import torch
from datetime import datetime, timedelta
import numpy as np
import xarray as xr
import pandas as pd
import csv
import pickle

# Add research directory to path
research_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(research_dir))

# Import shared utilities
from shared.data_loading import create_aurora_batch
from shared.forecasting import run_forecast, extract_field_from_predictions

# Import Freeze utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from Freeze_utils import (
    extract_regional_subset, compute_regional_statistics,
    compute_freeze_metrics, save_freeze_results
)
# Note: Plotting removed - use regenerate_visualizations.py for publication-quality plots

from aurora import Aurora


def main():
    print("=" * 80)
    print("  Beast from the East 2018 - Stage 1: Lead Time Assessment")
    print("=" * 80)
    print()
    print("Strategy: Variable initialization date, fixed target (Feb 27 onset)")
    print()

    # =========================================================================
    # CONFIGURATION
    # =========================================================================
    CONFIG = {
        'event_name': 'Beast from the East 2018',
        'region': {
            'name': 'UK, Ireland, Western Europe',
            'lat_min': 45.0,
            'lat_max': 62.0,
            'lon_min': -12.0,
            'lon_max': 10.0
        },

        # Event timeline from baseline analysis
        'onset_date': '2018-02-27',      # Regional mean < 0°C
        'peak_date': '2018-02-28',       # Coldest day
        'recovery_date': '2018-03-02',   # Regional mean > 0°C

        'base_data_path': Path(__file__).parent.parent / "data" / "era5_beast_2018",
        'output_dir': Path(__file__).parent / "prediction_output",

        # Combined data files
        'combined_surface_file': 'beast_2018_surface_feb03-mar02.nc',
        'combined_atmos_file': 'beast_2018_atmospheric_feb03-mar02.nc',

        # Stage 1: Test 4 lead times, all targeting Feb 27 onset
        # All initialized at 12:00 UTC
        # Data starts Feb 3, 00:00 UTC (index 0)
        'lead_time_configs': [
            {
                'lead_days': 1,
                'init_date': '2018-02-26',
                'init_hour': '12',
                'time_idx': 94,  # Feb 26, 12 UTC (Feb 3 00:00 = 0, +23.5 days)
                'forecast_days': 5,  # Forecast until Mar 3
                'steps': 19      # 5 days × 4 - 1
            },
            {
                'lead_days': 7,
                'init_date': '2018-02-20',
                'init_hour': '12',
                'time_idx': 70,  # Feb 20, 12 UTC (Feb 3 00:00 = 0, +17.5 days)
                'forecast_days': 10, # Forecast until Mar 2
                'steps': 39      # 10 days × 4 - 1
            },
            {
                'lead_days': 14,
                'init_date': '2018-02-13',
                'init_hour': '12',
                'time_idx': 42,  # Feb 13, 12 UTC (Feb 3 00:00 = 0, +10.5 days)
                'forecast_days': 17, # Forecast until Mar 2
                'steps': 67      # 17 days × 4 - 1
            },
            {
                'lead_days': 21,
                'init_date': '2018-02-06',
                'init_hour': '12',
                'time_idx': 14,  # Feb 6, 12 UTC (Feb 3 00:00 = 0, +3.5 days)
                'forecast_days': 24, # Forecast until Mar 2
                'steps': 95      # 24 days × 4 - 1
            },
        ],

        # Thresholds for spatial extent analysis
        'thresholds': [0, -5, -10],  # °C
    }

    CONFIG['output_dir'].mkdir(exist_ok=True, parents=True)

    print(f"Event: {CONFIG['event_name']}")
    print(f"Region: {CONFIG['region']['name']}")
    print(f"Target timeline:")
    print(f"  Onset: {CONFIG['onset_date']}")
    print(f"  Peak: {CONFIG['peak_date']}")
    print(f"  Recovery: {CONFIG['recovery_date']}")
    print(f"\nTesting {len(CONFIG['lead_time_configs'])} lead times:")
    for cfg in CONFIG['lead_time_configs']:
        print(f"  • {cfg['lead_days']}-day: Initialize {cfg['init_date']} {cfg['init_hour']}:00 UTC")
        print(f"    Forecast {cfg['forecast_days']} days ({cfg['steps']} steps)")
    print()

    # =========================================================================
    # SETUP MODEL
    # =========================================================================
    print("Loading Aurora model...")
    model = Aurora(use_lora=False)
    model.load_checkpoint("microsoft/aurora", "aurora-0.25-pretrained.ckpt")
    model.eval()

    if torch.cuda.is_available():
        try:
            model = model.to("cuda")
            device = "cuda"
            print(f"✓ Model loaded on GPU")
        except torch.cuda.OutOfMemoryError:
            model = model.to("cpu")
            device = "cpu"
            print("⚠ CUDA OOM, using CPU")
    else:
        model = model.to("cpu")
        device = "cpu"
        print("✓ Model loaded on CPU")
    print()

    # =========================================================================
    # LOAD ERA5 DATA
    # =========================================================================
    print("Loading ERA5 data...")
    data_path = CONFIG['base_data_path']

    surf_file = data_path / CONFIG['combined_surface_file']
    atmos_file = data_path / CONFIG['combined_atmos_file']
    static_file = data_path.parent / "static.nc"  # static.nc is one level up

    if not surf_file.exists() or not atmos_file.exists():
        print(f"⚠ ERROR: Combined data files not found!")
        print(f"  Expected: {surf_file}")
        print(f"  Expected: {atmos_file}")
        print(f"  Run combine script first!")
        sys.exit(1)

    if not static_file.exists():
        print(f"⚠ ERROR: Static file not found!")
        print(f"  Expected: {static_file}")
        print(f"  Static file should be at: research/Freeze/data/static.nc")
        sys.exit(1)

    surf_ds = xr.open_dataset(surf_file)
    atmos_ds = xr.open_dataset(atmos_file)
    static_ds = xr.open_dataset(static_file)

    print(f"✓ Loaded ERA5 data: {len(surf_ds.valid_time)} timesteps")
    print(f"  Time range: {surf_ds.valid_time.values[0]} to {surf_ds.valid_time.values[-1]}")
    print()

    # =========================================================================
    # RUN FORECASTS FOR EACH LEAD TIME
    # =========================================================================
    print("=" * 80)
    print("  Stage 1: Running Lead Time Experiments")
    print("=" * 80)
    print()

    results = {}
    csv_records = []

    for config in CONFIG['lead_time_configs']:
        lead_days = config['lead_days']
        init_date = config['init_date']
        init_hour = config['init_hour']
        steps = config['steps']

        print(f"\n{'=' * 80}")
        print(f"  {lead_days}-Day Lead Time")
        print(f"  Initialize: {init_date} {init_hour}:00 UTC")
        print(f"  Forecast: {config['forecast_days']} days ({steps} steps)")
        print(f"{'=' * 80}\n")

        # Check if predictions already exist on disk
        pred_cache_file = CONFIG['output_dir'] / f"predictions_{lead_days}day.pkl"

        if pred_cache_file.exists():
            print(f"✓ Found cached predictions: {pred_cache_file.name}")
            print(f"  Loading from disk (skipping forecast)...")

            with open(pred_cache_file, 'rb') as f:
                cached_data = pickle.load(f)

            preds = cached_data['preds']
            forecast_times = cached_data['forecast_times']
            t2m_fields_celsius = cached_data['t2m_fields_celsius']
            t850_fields_celsius = cached_data['t850_fields_celsius']
            z500_fields_m = cached_data['z500_fields_m']
            msl_fields_hpa = cached_data['msl_fields_hpa']

            print(f"✓ Loaded {len(preds)} timesteps from cache")

        else:
            print(f"No cached predictions found, running forecast...")

            # Create batch
            batch = create_aurora_batch(
                static_ds, surf_ds, atmos_ds,
                time_start_idx=config['time_idx']
            )

            # Get initialization time for forecast times
            init_time = datetime.strptime(f"{init_date} {init_hour}:00", "%Y-%m-%d %H:%M")

            # Run forecast (no tracker for freeze events!)
            print(f"Running {steps}-step forecast...")
            preds = run_forecast(
                model, batch, tracker=None,  # No tracker!
                steps=steps,
                name=f"Beast {lead_days}day",
                device=device,
                verbose=True
            )
            print(f"✓ Forecast complete: {len(preds)} timesteps")

            # Generate forecast times
            forecast_times = [init_time + timedelta(hours=6*(i+1)) for i in range(len(preds))]

            # Extract fields from predictions
            print("Extracting fields from predictions...")
            t2m_fields = extract_field_from_predictions(preds, '2t')  # K
            t2m_fields_celsius = [(t - 273.15) for t in t2m_fields]

            # FIXED: Aurora pressure levels are (1000, 925, 850, 700, 600, 500, ...)
            t850_fields = extract_field_from_predictions(preds, 't', level_idx=2)  # 850 hPa (index 2)
            t850_fields_celsius = [(t - 273.15) for t in t850_fields]

            z500_fields = extract_field_from_predictions(preds, 'z', level_idx=5)   # 500 hPa (index 5)
            z500_fields_m = [(z / 9.81) for z in z500_fields]  # Convert to meters

            msl_fields = extract_field_from_predictions(preds, 'msl')  # Pa
            msl_fields_hpa = [(p / 100) for p in msl_fields]  # Convert to hPa

            print(f"✓ Extracted T2m, T850, Z500, MSL fields")

            # Save predictions to disk for future use
            print(f"Saving predictions to disk...")
            cache_data = {
                'preds': preds,
                'forecast_times': forecast_times,
                't2m_fields_celsius': t2m_fields_celsius,
                't850_fields_celsius': t850_fields_celsius,
                'z500_fields_m': z500_fields_m,
                'msl_fields_hpa': msl_fields_hpa,
                'config': config
            }

            with open(pred_cache_file, 'wb') as f:
                pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)

            file_size_mb = pred_cache_file.stat().st_size / (1024**2)
            print(f"✓ Saved predictions: {pred_cache_file.name} ({file_size_mb:.1f} MB)")

        # Extract ERA5 truth for same region
        print("Extracting ERA5 verification data...")
        region = CONFIG['region']

        # Create a temporary dataset for this forecast period
        # Find time indices in ERA5 that match forecast period
        era5_times = surf_ds.valid_time.values
        forecast_start = forecast_times[0]
        forecast_end = forecast_times[-1]

        # Find matching ERA5 timesteps
        era5_mask = (era5_times >= np.datetime64(forecast_start)) & (era5_times <= np.datetime64(forecast_end))
        era5_subset_indices = np.where(era5_mask)[0]

        if len(era5_subset_indices) == 0:
            print(f"⚠ Warning: No ERA5 data in forecast period!")
            print(f"  Forecast: {forecast_start} to {forecast_end}")
            print(f"  ERA5 range: {era5_times[0]} to {era5_times[-1]}")
            continue

        # Compute metrics using Freeze_utils
        print("Computing freeze metrics...")
        metrics = compute_freeze_metrics(
            t2m_fields_celsius,
            surf_ds,
            forecast_times,
            region,
            CONFIG['onset_date'],
            CONFIG['peak_date'],
            CONFIG['recovery_date'],
            thresholds=CONFIG['thresholds']
        )

        # Compute field statistics for CSV export
        # Regional statistics at key phases
        forecast_stats = compute_regional_statistics(t2m_fields_celsius)

        # Find phase indices in forecast
        phase_indices = {}
        for phase_name, target_date in [('onset', CONFIG['onset_date']),
                                        ('peak', CONFIG['peak_date']),
                                        ('recovery', CONFIG['recovery_date'])]:
            target_dt = pd.Timestamp(target_date)
            diffs = [abs((pd.Timestamp(t) - target_dt).total_seconds()) for t in forecast_times]
            phase_indices[phase_name] = int(np.argmin(diffs))

        # Extract ERA5 regional statistics at same phases
        t2m_era5 = extract_regional_subset(surf_ds, 't2m', region) - 273.15
        t850_era5 = extract_regional_subset(atmos_ds, 't', region, level=850) - 273.15
        z500_era5 = extract_regional_subset(atmos_ds, 'z', region, level=500) / 9.81
        msl_era5 = extract_regional_subset(surf_ds, 'msl', region) / 100

        era5_stats = {}
        for phase_name, idx in phase_indices.items():
            if idx < len(forecast_times):
                forecast_time = forecast_times[idx]
                # Find closest ERA5 time
                time_diffs = np.abs(era5_times - np.datetime64(forecast_time))
                era5_idx = np.argmin(time_diffs)

                era5_stats[phase_name] = {
                    't2m_mean': float(t2m_era5.isel(valid_time=era5_idx).mean()),
                    't2m_min': float(t2m_era5.isel(valid_time=era5_idx).min()),
                    't850_mean': float(t850_era5.isel(valid_time=era5_idx).mean()),
                    'z500_mean': float(z500_era5.isel(valid_time=era5_idx).mean()),
                    'msl_mean': float(msl_era5.isel(valid_time=era5_idx).mean()),
                }

        # Create CSV record
        for phase_name, idx in phase_indices.items():
            if idx < len(t2m_fields_celsius):
                # Compute field statistics at this phase
                t2m_aurora = t2m_fields_celsius[idx]
                t850_aurora = t850_fields_celsius[idx]
                z500_aurora = z500_fields_m[idx]
                msl_aurora = msl_fields_hpa[idx]

                # Compute errors vs ERA5
                t2m_error = np.mean(t2m_aurora) - era5_stats[phase_name]['t2m_mean']
                t850_error = np.mean(t850_aurora) - era5_stats[phase_name]['t850_mean']
                z500_error = np.mean(z500_aurora) - era5_stats[phase_name]['z500_mean']
                msl_error = np.mean(msl_aurora) - era5_stats[phase_name]['msl_mean']

                csv_records.append({
                    'Event_Name': CONFIG['event_name'],
                    'Stage': 1,
                    'Lead_Days': lead_days,
                    'Phase': phase_name.capitalize(),
                    'T2m_Mean_C': np.mean(t2m_aurora),
                    'T2m_Min_C': np.min(t2m_aurora),
                    'T2m_Error_C': t2m_error,
                    'T2m_RMSE_C': metrics['rmse'][phase_name] if phase_name in metrics['rmse'] else None,
                    'T850_Mean_C': np.mean(t850_aurora),
                    'T850_Error_C': t850_error,
                    'Z500_Mean_m': np.mean(z500_aurora),
                    'Z500_Error_m': z500_error,
                    'MSL_Mean_hPa': np.mean(msl_aurora),
                    'MSL_Error_hPa': msl_error,
                    'Spatial_Extent_0C_pct': metrics['spatial_extent']['forecast'][0] * 100 if phase_name == 'peak' else None,
                    'Spatial_IoU_0C': metrics['spatial_extent']['iou_scores'][0] if phase_name == 'peak' else None,
                    'Pattern_Correlation': metrics['pattern_correlation_at_peak'] if phase_name == 'peak' else None,
                })

        # Summary
        print(f"\nMetrics Summary:")
        print(f"  Onset timing error: {metrics['timing']['onset_error_hours']:.1f} hours"
              if metrics['timing']['onset_error_hours'] is not None else "  Onset timing error: N/A")
        print(f"  Peak timing error: {metrics['timing']['peak_error_hours']:.1f} hours"
              if metrics['timing']['peak_error_hours'] is not None else "  Peak timing error: N/A")
        print(f"  Peak RMSE: {metrics['rmse']['peak']:.2f}°C"
              if metrics['rmse']['peak'] is not None else "  Peak RMSE: N/A")
        print(f"  Duration error: {metrics['duration']['error_hours']:.1f} hours")
        print(f"  Intensity bias at peak: {metrics['intensity']['bias']:.2f}°C")

        # Store results
        results[lead_days] = {
            'config': config,
            'predictions': preds,
            'forecast_times': forecast_times,
            'fields': {
                't2m': t2m_fields_celsius,
                't850': t850_fields_celsius,
                'z500': z500_fields_m,
                'msl': msl_fields_hpa
            },
            'forecast_stats': forecast_stats,
            'metrics': metrics
        }

        # Clear GPU memory
        if device == "cuda":
            torch.cuda.empty_cache()

    # =========================================================================
    # SAVE RESULTS
    # =========================================================================
    print("\n" + "=" * 80)
    print("  Saving Results")
    print("=" * 80)

    # Save JSON results
    json_path = CONFIG['output_dir'] / "beast_stage1_results.json"
    save_freeze_results(results, json_path)

    # Save CSV results
    csv_path = CONFIG['output_dir'] / "beast_stage1_metrics.csv"
    if csv_records:
        fieldnames = csv_records[0].keys()
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_records)
        print(f"✓ CSV metrics saved to: {csv_path}")

    # =========================================================================
    # GENERATE VISUALIZATIONS
    # =========================================================================
    print("\n" + "=" * 80)
    print("  Generating Visualizations")
    print("=" * 80)

    # Plotting removed - use regenerate_visualizations.py for publication-quality plots
    print("\nNote: For publication-quality visualizations, run:")
    print("  python regenerate_visualizations.py")


    print("\n" + "=" * 80)
    print("  ✓ Beast Stage 1 Analysis Complete!")
    print("=" * 80)
    print()
    print(f"Results saved to: {CONFIG['output_dir']}")
    print(f"  - predictions_*.pkl (cached forecasts for 1/7/14/21-day leads)")
    print(f"  - beast_stage1_results.json (detailed metrics)")
    print(f"  - beast_stage1_metrics.csv (summary table)")
    print()


if __name__ == "__main__":
    main()
