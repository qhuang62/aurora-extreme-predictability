#!/usr/bin/env python3
"""
Hurricane Ian 2022 - Stage 2: Initialization Sensitivity Analysis

Tests all 4 initialization times (00, 06, 12, 18 UTC) on Sep 25, 2022
using the best-performing lead time from Stage 1 (anticipated: 3-day lead).

This demonstrates:
1. How forecast skill varies with initialization time of day
2. Initialization-dependent uncertainty quantification
3. Optimal initialization time identification

Uses 3-day lead time (72 hours) to provide sufficient forecast length for
initialization sensitivity to manifest while maintaining reasonable forecast skill.
"""

import sys
from pathlib import Path
import torch
from datetime import datetime

# Add research directory to path
research_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(research_dir))

# Import shared utilities
from shared.data_loading import load_era5_data, create_aurora_batch
from shared.forecasting import run_forecast
from shared.visualization import plot_track_comparison, plot_error_evolution

# Import TC-specific utilities
from TC.TC_utils import (load_ibtracs_track, extract_track_from_tracker,
                         compute_track_error, summarize_track_performance,
                         export_results_to_csv)

# Import Aurora
from aurora import Aurora, Tracker


def main():
    print("=" * 75)
    print("  Hurricane Ian 2022 - Stage 2: Initialization Sensitivity")
    print("=" * 75)
    print()
    print("Strategy: Fixed lead time (best from Stage 1), variable init time")
    print()

    # =========================================================================
    # CONFIGURATION
    # =========================================================================
    CONFIG = {
        'event_name': 'Hurricane Ian 2022',
        'storm_name': 'IAN',
        'storm_year': 2022,
        'base_data_path': Path("/scratch/qhuang62/aurora-extreme-predictability/research/TC/data"),
        'output_dir': Path(__file__).parent / "prediction_output",

        # Combined data file covering Sep 21-28
        'combined_surface_file': 'ian_2022_surface_combined.nc',
        'combined_atmos_file': 'ian_2022_atmospheric_combined.nc',
        'data_folder': 'era5_ian_2022',

        # Stage 2: Use 3-day lead time (provides sufficient forecast length)
        # Test 4 initialization times: 00, 06, 12, 18 UTC on Sep 25
        # All initialized on Sep 25, 2022 (3 days before landfall)
        # Following Sandy's pattern: steps = (total_hours / 6) - 1
        # All forecasts end at Sep 28 12:00 UTC (6h before 18:00 UTC target)
        # Target marker shown at 18:00 UTC (closest 6-hourly to actual 20:00 UTC landfall)
        # Coordinates from IBTrACS v04r01 (Storm ID: 2022266N12294)
        'lead_days': 3,
        'init_date': '2022-09-25',
        'landfall_date': 'Sep 28, 2022 18:00 UTC',  # Target marker (6h after last forecast)
        'init_times': [
            {'hour': '00', 'time_idx': 16, 'init_lat': 14.60, 'init_lon': 282.80, 'steps': 14},  # Sep 25 00:00 (FIXED: was 17)
            {'hour': '06', 'time_idx': 17, 'init_lat': 14.60, 'init_lon': 281.70, 'steps': 13},  # Sep 25 06:00 (FIXED: was 18)
            {'hour': '12', 'time_idx': 18, 'init_lat': 15.00, 'init_lon': 280.60, 'steps': 12},  # Sep 25 12:00 (FIXED: was 19)
            {'hour': '18', 'time_idx': 19, 'init_lat': 15.80, 'init_lon': 279.90, 'steps': 11},  # Sep 25 18:00 (FIXED: was 20)
        ],
    }

    CONFIG['output_dir'].mkdir(exist_ok=True)

    print(f"Event: {CONFIG['event_name']}")
    print(f"Target: {CONFIG['landfall_date']}")
    print(f"Lead time from Stage 1: {CONFIG['lead_days']}-day ({CONFIG['init_date']})")
    print(f"\nTesting {len(CONFIG['init_times'])} initialization times:")
    for init in CONFIG['init_times']:
        print(f"  • {CONFIG['init_date']} {init['hour']}:00 UTC → {init['steps']} steps ({init['steps']*6}h)")
    print(f"All forecasts target: {CONFIG['landfall_date']}")
    print()

    # =========================================================================
    # SETUP
    # =========================================================================
    print("Loading Aurora model...")
    model = Aurora(use_lora=False)
    model.load_checkpoint("microsoft/aurora", "aurora-0.25-pretrained.ckpt")
    model.eval()

    # GPU handling
    if torch.cuda.is_available():
        try:
            model = model.to("cuda")
            device = "cuda"
            print(f"✓ Model loaded on GPU")
            print(f"  GPU memory: {torch.cuda.memory_allocated()/1024**3:.2f} GB")
        except torch.cuda.OutOfMemoryError:
            print("⚠ CUDA out of memory, falling back to CPU")
            model = model.to("cpu")
            device = "cpu"
    else:
        model = model.to("cpu")
        device = "cpu"
        print("✓ Model loaded on CPU")

    print()

    # =========================================================================
    # LOAD DATA
    # =========================================================================
    print("Loading ERA5 data...")
    data_path = CONFIG['base_data_path'] / CONFIG['data_folder']
    surf_file = data_path / CONFIG['combined_surface_file']
    atmos_file = data_path / CONFIG['combined_atmos_file']

    if not surf_file.exists() or not atmos_file.exists():
        print(f"⚠ Combined data files not found:")
        print(f"  {surf_file}")
        print(f"  {atmos_file}")
        print("  Run download_ian_complete.py and combine_ian_data.py first")
        return

    import xarray as xr
    static_ds, _, _ = load_era5_data(data_path, '2022-09-22')  # Load static vars
    surf_ds = xr.open_dataset(surf_file)
    atmos_ds = xr.open_dataset(atmos_file)
    print(f"✓ Loaded combined ERA5 data ({len(surf_ds.valid_time)} timesteps)")
    print()

    # =========================================================================
    # LOAD OBSERVED TRACK
    # =========================================================================
    print("Loading observed track...")
    obs_track = load_ibtracs_track(CONFIG['storm_name'], CONFIG['storm_year'])
    print(f"✓ Observed track: {len(obs_track['time'])} positions")
    print()

    # =========================================================================
    # RUN FORECASTS FOR ALL INITIALIZATION TIMES
    # =========================================================================
    print("=" * 75)
    print("  Stage 2: Running Initialization Time Experiments")
    print("=" * 75)
    print()

    results = {}

    for init_config in CONFIG['init_times']:
        hour = init_config['hour']
        time_idx = init_config['time_idx']
        init_lat = init_config['init_lat']
        init_lon = init_config['init_lon']
        steps = init_config['steps']

        print(f"\n{'='*75}")
        print(f"  Initialization: {CONFIG['init_date']} {hour}:00 UTC")
        print(f"  Initial position: {init_lat}°N, {init_lon}°E")
        print(f"  Forecast: {steps} steps ({steps*6}h) to landfall")
        print(f"{'='*75}\n")

        # Create batch
        batch = create_aurora_batch(
            static_ds, surf_ds, atmos_ds,
            time_start_idx=time_idx
        )

        # Initialize tracker
        init_time = datetime.strptime(f"{CONFIG['init_date']} {hour}:00", "%Y-%m-%d %H:%M")
        tracker = Tracker(init_lat=init_lat, init_lon=init_lon, init_time=init_time)

        # Run forecast
        preds = run_forecast(
            model, batch, tracker,
            steps=steps,
            name=f"Ian {hour}UTC",
            device=device,
            verbose=True
        )

        # Extract track
        forecast_track = extract_track_from_tracker(tracker, init_time)
        print(f"✓ Forecast track: {len(forecast_track['time'])} positions")

        # Compute errors
        errors_data = compute_track_error(forecast_track, obs_track)
        print(f"✓ Computed {len(errors_data['errors'])} error values")

        # Summary
        summary = summarize_track_performance(
            forecast_track, obs_track, init_time, CONFIG['event_name']
        )

        if summary:
            print(f"\nTrack Performance:")
            print(f"  Mean error: {summary['mean_error']:.1f} km")
            if summary['error_24h']:
                print(f"  24h error:  {summary['error_24h']:.1f} km")
            if summary['error_48h']:
                print(f"  48h error:  {summary['error_48h']:.1f} km")
            if summary['error_72h']:
                print(f"  72h error:  {summary['error_72h']:.1f} km")

        # Store results
        results[hour] = {
            'forecast_track': forecast_track,
            'errors_data': errors_data,
            'summary': summary,
            'preds': preds,
            'tracker': tracker
        }

    # =========================================================================
    # VISUALIZE RESULTS
    # =========================================================================
    print("\n" + "=" * 75)
    print("Creating visualizations...")
    print("=" * 75)
    print()

    # 1. Track comparison - all 4 initializations
    forecast_tracks = {
        f"{hour}:00 UTC": results[hour]['forecast_track']
        for hour in ['00', '06', '12', '18']
    }

    # Truncate observed track to match forecast period (Sep 25 - Sep 28)
    earliest_init_time = datetime(2022, 9, 25, 0, 0)  # Stage 2 earliest init
    landfall_time = datetime(2022, 9, 28, 18, 0)      # Target: 18:00 UTC (6-hourly grid)

    # Historical track segment (Sep 21 - Sep 25) to show as dashed line
    stage1_start_time = datetime(2022, 9, 21, 18, 0)  # Stage 1 earliest init

    # Find indices for forecast period (Sep 25 - Sep 28)
    valid_indices = [i for i, t in enumerate(obs_track['time'])
                    if earliest_init_time <= t <= landfall_time]

    obs_track_truncated = {
        'time': [obs_track['time'][i] for i in valid_indices],
        'lat': [obs_track['lat'][i] for i in valid_indices],
        'lon': [obs_track['lon'][i] for i in valid_indices]
    }

    # Find indices for historical segment (Sep 21 - Sep 25)
    historical_indices = [i for i, t in enumerate(obs_track['time'])
                         if stage1_start_time <= t <= earliest_init_time]

    obs_track_historical = {
        'time': [obs_track['time'][i] for i in historical_indices],
        'lat': [obs_track['lat'][i] for i in historical_indices],
        'lon': [obs_track['lon'][i] for i in historical_indices]
    }

    track_plot_path = CONFIG['output_dir'] / "ian_stage2_init_tracks.png"
    plot_track_comparison(
        forecast_tracks=forecast_tracks,
        obs_track=obs_track_truncated,  # Use truncated track (solid red)
        title=f"Hurricane Ian - Track Comparison (Different Initialization Time) ({CONFIG['lead_days']}-Day Lead)",
        save_path=track_plot_path,
        extent=[-90, -60, 10, 35],  # Gulf/Caribbean/Florida region
        obs_track_historical=obs_track_historical  # Historical segment (dashed red)
    )

    # 2. Error evolution by valid time (converging to landfall)
    from shared.visualization import plot_error_by_valid_time

    errors_dict = {
        f"{hour}:00 UTC": results[hour]['errors_data']['errors']
        for hour in ['00', '06', '12', '18']
        if len(results[hour]['errors_data']['errors']) > 0
    }

    tracks_dict = {
        f"{hour}:00 UTC": results[hour]['forecast_track']
        for hour in ['00', '06', '12', '18']
    }

    landfall_time = datetime(2022, 9, 28, 18, 0)  # Target: 18:00 UTC (6-hourly grid)

    error_plot_path = CONFIG['output_dir'] / "ian_stage2_init_errors.png"
    plot_error_by_valid_time(
        forecast_tracks_dict=tracks_dict,
        errors_dict=errors_dict,
        target_time=landfall_time,
        ylabel="Track Error (km)",
        title=f"Hurricane Ian - Track Error (Different Initialization Time) ({CONFIG['lead_days']}-Day Lead)",
        save_path=error_plot_path,
        xaxis_hours=[6, 18]  # Ian uses 06 UTC and 18 UTC
    )

    # =========================================================================
    # LANDFALL FIELD COMPARISON
    # =========================================================================
    print("\n" + "=" * 75)
    print("  Landfall Field Comparison (Direct Verification)")
    print("=" * 75)
    print()
    print("Comparing Aurora vs ERA5 meteorological fields at landfall time...")
    print("This addresses tracker limitation near coastlines.")
    print()

    # Import required modules
    import numpy as np
    import xarray as xr
    from TC.TC_utils import compare_fields_at_landfall
    from shared.visualization import plot_multi_init_field_comparison
    from shared.metrics import calculate_distance

    # Landfall parameters (Ian landfall Sep 28, 20:00 UTC)
    # Based on IBTrACS: lat 26.80°N, lon 278.0°E (-82.0°W)
    LANDFALL_LAT = 26.80
    LANDFALL_LON = 278.0  # -82.0°W converted to 0-360°E
    LANDFALL_REGION = [272, 288, 20, 32]  # Gulf Coast/Florida region

    # Initialize ERA5 dataset variables
    era5_surf = None
    era5_atmos = None

    for hour in ['00', '06', '12', '18']:
        print(f"\n{hour}:00 UTC initialization:")

        # Get predictions
        preds = results[hour]['preds']
        forecast_track = results[hour]['forecast_track']

        # Find timestep closest to landfall based on track
        distances = []
        for i, (lat, lon) in enumerate(zip(forecast_track['lat'], forecast_track['lon'])):
            dist = calculate_distance(lat, lon, LANDFALL_LAT, LANDFALL_LON)
            distances.append(dist)

        if len(distances) > 0:
            track_idx = np.argmin(distances)
            # Track includes initial condition at index 0, but predictions list doesn't
            # So prediction index = track idx - 1
            landfall_idx = max(0, track_idx - 1)
            print(f"  Using track position {track_idx} → prediction timestep {landfall_idx} (closest to landfall)")

            # Load ERA5 verification data at landfall time (only need to do this once)
            if hour == '00':
                try:
                    data_path = CONFIG['base_data_path'] / CONFIG['data_folder']
                    surf_file = data_path / "ian_2022_surface_landfall.nc"
                    atmos_file = data_path / "ian_2022_atmospheric_landfall.nc"

                    if surf_file.exists() and atmos_file.exists():
                        era5_surf = xr.open_dataset(surf_file)
                        era5_atmos = xr.open_dataset(atmos_file)
                        print(f"  ✓ Loaded ERA5 verification data (Sep 28 18:00 UTC)")
                    else:
                        print(f"  ⚠ Landfall ERA5 files not found, skipping field comparison")
                        era5_surf = None
                        era5_atmos = None
                except Exception as e:
                    print(f"  ⚠ Error loading ERA5 data: {e}")
                    era5_surf = None
                    era5_atmos = None

            # Compare fields
            if era5_surf is not None and era5_atmos is not None:
                try:
                    comparison = compare_fields_at_landfall(
                        preds,
                        era5_surf,
                        era5_atmos,
                        landfall_time_idx=landfall_idx,
                        landfall_lat=LANDFALL_LAT,
                        landfall_lon=LANDFALL_LON,
                        region_extent=LANDFALL_REGION
                    )

                    # Print metrics
                    print(f"  MSL minimum: Aurora {comparison['msl']['aurora_min']/100:.1f} hPa, "
                          f"ERA5 {comparison['msl']['era5_min']/100:.1f} hPa "
                          f"(error: {(comparison['msl']['aurora_min'] - comparison['msl']['era5_min'])/100:.1f} hPa)")
                    print(f"  Wind maximum: Aurora {comparison['wind']['aurora_max']:.1f} m/s, "
                          f"ERA5 {comparison['wind']['era5_max']:.1f} m/s "
                          f"(error: {comparison['wind']['aurora_max'] - comparison['wind']['era5_max']:.1f} m/s)")
                    print(f"  Center position error: {comparison['msl']['center_diff_km']:.1f} km")

                    # Store in results
                    results[hour]['landfall_field_comparison'] = comparison

                except Exception as e:
                    print(f"  ⚠ Error in field comparison: {e}")
                    import traceback
                    traceback.print_exc()
        else:
            print(f"  ⚠ No forecast track positions available")

    # Create individual field comparison plots for each initialization time
    print("\nCreating individual initialization field comparison plots...")
    from shared.visualization import plot_field_comparison

    for hour in ['00', '06', '12', '18']:
        if 'landfall_field_comparison' in results[hour]:
            print(f"\nPlotting {hour}:00 UTC initialization...")
            comparison = results[hour]['landfall_field_comparison']

            # MSL field comparison
            msl_plot = CONFIG['output_dir'] / f"ian_init{hour}_landfall_msl.png"
            plot_field_comparison(
                forecast=comparison['msl']['aurora'] / 100,  # Convert to hPa
                truth=comparison['msl']['era5'] / 100,
                lat=comparison['lat'],
                lon=comparison['lon'],
                variable_name="MSL (hPa)",
                title=f"Ian {hour} UTC Init (3-day Lead): MSL at Landfall",
                save_path=msl_plot,
                extent=LANDFALL_REGION
            )

            # Wind field comparison
            wind_plot = CONFIG['output_dir'] / f"ian_init{hour}_landfall_wind.png"
            plot_field_comparison(
                forecast=comparison['wind']['aurora'],
                truth=comparison['wind']['era5'],
                lat=comparison['lat'],
                lon=comparison['lon'],
                variable_name="10m Wind Speed (m/s)",
                title=f"Ian {hour} UTC Init (3-day Lead): Wind at Landfall",
                save_path=wind_plot,
                extent=LANDFALL_REGION,
                cmap='YlOrRd'
            )

    # Close landfall files
    if era5_surf is not None:
        era5_surf.close()
    if era5_atmos is not None:
        era5_atmos.close()

    print()

    # =========================================================================
    # SUMMARY TABLE
    # =========================================================================
    print("\n" + "=" * 75)
    print("  Stage 2 Summary: Initialization Sensitivity Analysis")
    print("=" * 75)
    print()
    print(f"{'Init':<9} {'24hr Track':<15} {'48hr Track':<15} {'72hr Track':<15} {'MSL Error':<13} {'Wind Error':<13} {'Position Error':<15}")
    print(f"{'Time':<9} {'Error (km)':<15} {'Error (km)':<15} {'Error (km)':<15} {'(hPa)':<13} {'(m/s)':<13} {'at Landfall (km)':<15}")
    print("-" * 110)

    for hour in ['00', '06', '12', '18']:
        summary = results[hour]['summary']
        field_comp = results[hour].get('landfall_field_comparison', None)

        if summary:
            # Track errors
            track_24h = f"{summary['error_24h']:.1f}" if summary['error_24h'] else "N/A"
            track_48h = f"{summary['error_48h']:.1f}" if summary['error_48h'] else "N/A"
            track_72h = f"{summary['error_72h']:.1f}" if summary['error_72h'] else "N/A"

            # Field comparison errors
            if field_comp:
                msl_err = f"{(field_comp['msl']['aurora_min'] - field_comp['msl']['era5_min'])/100:.1f}"
                wind_err = f"{field_comp['wind']['aurora_max'] - field_comp['wind']['era5_max']:.1f}"
                pos_err = f"{field_comp['msl']['center_diff_km']:.1f}"
            else:
                msl_err = "N/A"
                wind_err = "N/A"
                pos_err = "N/A"

            print(f"{hour} UTC   {track_24h:<15} {track_48h:<15} {track_72h:<15} {msl_err:<13} {wind_err:<13} {pos_err:<15}")

    print()

    # Compute initialization spread statistics
    import numpy as np
    mean_errors = [results[h]['summary']['mean_error'] for h in ['00', '06', '12', '18']]
    final_errors = [results[h]['summary']['final_error'] for h in ['00', '06', '12', '18']
                    if results[h]['summary']['final_error'] is not None]

    mean_of_means = np.mean(mean_errors)
    std_of_means = np.std(mean_errors)

    if final_errors:
        mean_of_finals = np.mean(final_errors)
        std_of_finals = np.std(final_errors)

    print(f"Initialization Spread Statistics:")
    print(f"  Mean track error (all inits): {mean_of_means:.1f} ± {std_of_means:.1f} km")
    if final_errors:
        print(f"  Final error (all inits):      {mean_of_finals:.1f} ± {std_of_finals:.1f} km")
    print(f"  Range:                        {np.min(mean_errors):.1f} - {np.max(mean_errors):.1f} km")
    print()

    if std_of_means < 50:
        print("✓ Low initialization sensitivity (< 50 km spread)")
        print("  Forecast skill is relatively insensitive to time-of-day initialization")
    elif std_of_means < 100:
        print("⚠ Moderate initialization sensitivity (50-100 km spread)")
        print("  Time-of-day initialization has moderate impact on forecast skill")
    else:
        print("⚠ High initialization sensitivity (> 100 km spread)")
        print("  Time-of-day initialization significantly impacts forecast skill")

    # Identify best initialization time
    best_hour = min(['00', '06', '12', '18'], key=lambda h: results[h]['summary']['mean_error'])
    print(f"\n✓ Best initialization time: {best_hour}:00 UTC")
    print(f"  Mean error: {results[best_hour]['summary']['mean_error']:.1f} km")

    # =========================================================================
    # EXPORT TO CSV
    # =========================================================================
    print("\n" + "=" * 75)
    print("  Exporting Results to CSV")
    print("=" * 75)
    print()

    csv_path = CONFIG['output_dir'].parent.parent / 'TC_result_metrics.csv'
    export_results_to_csv(
        tc_name='Ian 2022',
        stage=2,
        results=results,
        csv_path=csv_path,
        stage_type='stage2'
    )
    print()

    print("=" * 75)
    print("  ✓ Stage 2 Complete!")
    print("=" * 75)
    print()
    print("Output files:")
    print(f"  • {track_plot_path}")
    print(f"  • {error_plot_path}")
    print()
    print("Key Finding:")
    print(f"  Using {CONFIG['lead_days']}-day lead time (best from Stage 1)")
    print(f"  Initialization time sensitivity: {std_of_means:.1f} km std dev")
    print()


if __name__ == "__main__":
    main()
