#!/usr/bin/env python3
"""
Hurricane Sandy 2012 - Stage 1: Lead Time Assessment

Tests 4 different lead times (1, 3, 5, 7 days) by varying initialization date.
All forecasts target the same critical event: Sandy's US landfall on Oct 29-30, 2012.

This answers: "How far in advance can we predict Sandy's landfall?"
"""

import sys
from pathlib import Path
import torch
from datetime import datetime
import numpy as np

# Add research directory to path
research_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(research_dir))

# Import utilities
from shared.data_loading import load_era5_data, create_aurora_batch
from shared.forecasting import run_forecast
from shared.visualization import plot_track_comparison, plot_error_evolution, plot_error_by_valid_time
from shared.save_load import save_multi_init_results

from TC.TC_utils import (load_ibtracs_track, extract_track_from_tracker,
                         compute_track_error, compute_landfall_error,
                         summarize_track_performance, compare_fields_at_landfall,
                         summarize_stage1_results, export_results_to_csv)

from aurora import Aurora, Tracker


def main():
    print("=" * 75)
    print("  Hurricane Sandy 2012 - Stage 1: Lead Time Assessment")
    print("=" * 75)
    print()
    print("Strategy: Variable initialization date, fixed target (Oct 29 landfall)")
    print()

    # =========================================================================
    # CONFIGURATION
    # =========================================================================
    CONFIG = {
        'event_name': 'Hurricane Sandy 2012',
        'storm_name': 'SANDY',
        'storm_year': 2012,
        'landfall_date': 'Oct 30, 2012 00:00 UTC',
        'base_data_path': Path("/scratch/qhuang62/aurora-extreme-predictability/research/TC/data"),
        'output_dir': Path(__file__).parent / "prediction_output",

        # Combined data file covering Oct 22-29
        'combined_surface_file': 'sandy_2012_surface_oct22-29.nc',
        'combined_atmos_file': 'sandy_2012_atmospheric_oct22-29.nc',
        'data_folder': 'era5_sandy_2012',

        # Stage 1: Test 4 lead times, all targeting Oct 30 00:00 UTC (landfall)
        # All initialized at 00:00 UTC for exact 1/3/5/7 day leads
        # Coordinates from IBTrACS v04r01 (Storm ID: 2012296N14283)
        'lead_time_configs': [
            {
                'lead_days': 1,
                'init_date': '2012-10-29',
                'init_hour': '00',
                'time_idx': 28,  # Oct 29, 00 UTC in combined file (Oct 22 00:00 = 0)
                'init_lat': 33.9,  # IBTrACS: Oct 29 00:00 UTC
                'init_lon': 289.0,  # -71.0°W = 289.0°E
            },
            {
                'lead_days': 3,
                'init_date': '2012-10-27',
                'init_hour': '00',
                'time_idx': 20,  # Oct 27, 00 UTC in combined file
                'init_lat': 27.5,  # IBTrACS: Oct 27 00:00 UTC
                'init_lon': 282.9,  # -77.1°W = 282.9°E
            },
            {
                'lead_days': 5,
                'init_date': '2012-10-25',
                'init_hour': '00',
                'time_idx': 12,  # Oct 25, 00 UTC in combined file
                'init_lat': 18.9,  # IBTrACS: Oct 25 00:00 UTC
                'init_lon': 283.6,  # -76.4°W = 283.6°E
            },
            {
                'lead_days': 7,
                'init_date': '2012-10-23',
                'init_hour': '00',
                'time_idx': 4,   # Oct 23, 00 UTC in combined file
                'init_lat': 12.6,  # IBTrACS: Oct 23 00:00 UTC
                'init_lon': 281.6,  # -78.4°W = 281.6°E
            },
        ],
    }

    CONFIG['output_dir'].mkdir(exist_ok=True)

    print(f"Event: {CONFIG['event_name']}")
    print(f"Target: {CONFIG['landfall_date']}")
    print(f"\nTesting {len(CONFIG['lead_time_configs'])} lead times:")
    for cfg in CONFIG['lead_time_configs']:
        print(f"  • {cfg['lead_days']}-day: Initialize {cfg['init_date']} {cfg['init_hour']}:00 UTC")
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
    # LOAD OBSERVED TRACK
    # =========================================================================
    print("Loading observed track...")
    obs_track = load_ibtracs_track(CONFIG['storm_name'], CONFIG['storm_year'])
    print(f"✓ Observed track: {len(obs_track['time'])} positions")
    print()

    # =========================================================================
    # RUN FORECASTS FOR EACH LEAD TIME
    # =========================================================================
    print("=" * 75)
    print("  Stage 1: Running Lead Day Experiments")
    print("=" * 75)
    print()

    results = {}

    for config in CONFIG['lead_time_configs']:
        lead_days = config['lead_days']
        init_date = config['init_date']
        init_hour = config['init_hour']

        print(f"\n{'=' * 75}")
        print(f"  {lead_days}-Day Lead Time")
        print(f"  Initialize: {init_date} {init_hour}:00 UTC")
        print(f"  Target: Oct 29-30 landfall ({lead_days} days ahead)")
        print(f"{'=' * 75}\n")

        # Check if combined data files exist
        data_path = CONFIG['base_data_path'] / CONFIG['data_folder']
        surf_file = data_path / CONFIG['combined_surface_file']
        atmos_file = data_path / CONFIG['combined_atmos_file']

        if not surf_file.exists() or not atmos_file.exists():
            print(f"⚠ Combined data files not found:")
            print(f"  {surf_file}")
            print(f"  {atmos_file}")
            print(f"  Skipping {lead_days}-day lead time")
            print(f"  Run download_sandy_complete.py and combine_data.py first")
            continue

        # Load ERA5 data from combined files
        try:
            import xarray as xr
            static_ds, _, _ = load_era5_data(data_path, '2012-10-24')  # Load static vars
            surf_ds = xr.open_dataset(surf_file)
            atmos_ds = xr.open_dataset(atmos_file)
            print(f"✓ Loaded combined ERA5 data ({len(surf_ds.valid_time)} timesteps)")
        except Exception as e:
            print(f"⚠ Error loading data: {e}")
            print(f"  Skipping {lead_days}-day lead time")
            continue

        # Create batch
        batch = create_aurora_batch(
            static_ds, surf_ds, atmos_ds,
            time_start_idx=config['time_idx']
        )

        # Initialize tracker
        init_time = datetime.strptime(f"{init_date} {init_hour}:00", "%Y-%m-%d %H:%M")
        tracker = Tracker(
            init_lat=config['init_lat'],
            init_lon=config['init_lon'],
            init_time=init_time
        )

        # Run forecast (steps to reach Oct 30)
        # Each step = 6 hours, so lead_days * 4 steps/day
        steps = lead_days * 4 - 1

        print(f"Running forecast: {lead_days} days = {steps} steps ({steps*6} hours)")

        preds = run_forecast(
            model, batch, tracker,
            steps=steps,
            name=f"Sandy {lead_days}day",
            device=device,
            verbose=True
        )

        # Extract track
        forecast_track = extract_track_from_tracker(tracker, init_time)
        print(f"✓ Forecast track: {len(forecast_track['time'])} positions")

        # Compute errors
        errors_data = compute_track_error(forecast_track, obs_track)
        print(f"✓ Computed {len(errors_data['errors'])} error values")

        # Compute landfall error
        landfall_error_data = compute_landfall_error(
            forecast_track, obs_track,
            landfall_threshold_lon=-75.0  # US East Coast
        )

        # Summary
        summary = summarize_track_performance(
            forecast_track, obs_track, init_time, CONFIG['event_name']
        )

        if summary:
            print(f"\nPerformance:")
            print(f"  Mean track error: {summary['mean_error']:.1f} km")
            print(f"  Max track error:  {summary['max_error']:.1f} km")
            print(f"  Final error:      {summary['final_error']:.1f} km")

        if landfall_error_data['timing_error_hours'] is not None:
            print(f"  Landfall timing error: {landfall_error_data['timing_error_hours']:.1f} hours")
            print(f"  Landfall location error: {landfall_error_data['location_error_km']:.1f} km")

        # Store results (including predictions for field analysis)
        results[lead_days] = {
            'forecast_track': forecast_track,
            'predictions': preds,  # ← SAVE FULL PREDICTIONS
            'errors_data': errors_data,
            'landfall_error': landfall_error_data,
            'summary': summary,
            'config': config
        }

        print(f"✓ Stored results with {len(preds)} prediction timesteps")

    # =========================================================================
    # SAVE RESULTS
    # =========================================================================
    if len(results) > 0:
        print("\n" + "=" * 75)
        print("Saving results...")
        print("=" * 75)
        print()

        save_path = CONFIG['output_dir'] / "sandy_stage1_lead_time_results.pkl"
        save_multi_init_results(
            results,
            save_path,
            metadata={
                'event': CONFIG['event_name'],
                'stage': 1,
                'strategy': 'Variable initialization date (Strategy B)',
                'target': CONFIG['landfall_date']
            },
            save_predictions=True  # Save full Aurora prediction fields
        )

        print(f"  Results include full prediction fields for landfall analysis")

    # =========================================================================
    # VISUALIZATIONS
    # =========================================================================
    if len(results) > 0:
        print("\n" + "=" * 75)
        print("Creating visualizations...")
        print("=" * 75)
        print()

        # Track comparison
        forecast_tracks = {
            f"{lead}-day lead": results[lead]['forecast_track']
            for lead in sorted(results.keys())
        }

        # Truncate observed track to match forecast period
        # Start: Oct 23 00:00 (7-day forecast initialization, earliest)
        # End: Oct 30 00:00 (landfall, all forecasts end here)
        # This ensures observed track aligns with all forecast tracks:
        # - First point matches 7-day forecast start
        # - Last point matches landfall (all forecasts end)
        earliest_init_time = datetime(2012, 10, 23, 0, 0)  # 7-day lead init
        landfall_time = datetime(2012, 10, 30, 0, 0)

        # Find indices for time range
        valid_indices = [i for i, t in enumerate(obs_track['time'])
                        if earliest_init_time <= t <= landfall_time]

        obs_track_truncated = {
            'time': [obs_track['time'][i] for i in valid_indices],
            'lat': [obs_track['lat'][i] for i in valid_indices],
            'lon': [obs_track['lon'][i] for i in valid_indices]
        }

        track_plot = CONFIG['output_dir'] / "sandy_stage1_tracks.png"
        plot_track_comparison(
            forecast_tracks=forecast_tracks,
            obs_track=obs_track_truncated,  # Use truncated track
            title="Hurricane Sandy - Track Comparison (Different Lead Days)",
            save_path=track_plot,
            extent=[-90, -65, 10, 45]
        )

        # Error evolution by valid time (not lead time from init)
        # This shows all forecasts converging at the same target (landfall)
        errors_dict = {}
        tracks_dict = {}
        for lead in sorted(results.keys()):
            if len(results[lead]['errors_data']['errors']) > 0:
                label = f"{lead}-day lead"
                errors_dict[label] = results[lead]['errors_data']['errors']
                tracks_dict[label] = results[lead]['forecast_track']

        if len(errors_dict) > 0:
            landfall_time = datetime(2012, 10, 30, 0, 0)  # Landfall target

            error_plot = CONFIG['output_dir'] / "sandy_stage1_errors.png"
            plot_error_by_valid_time(
                forecast_tracks_dict=tracks_dict,
                errors_dict=errors_dict,
                target_time=landfall_time,
                ylabel="Track Error (km)",
                title="Hurricane Sandy - Track Error (Different Lead Days)",
                save_path=error_plot,
                xaxis_hours=[0, 12]  # Sandy uses 00 UTC and 12 UTC
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

    # Import field comparison functions
    from TC.TC_utils import compare_fields_at_landfall
    from shared.visualization import plot_field_comparison

    # Landfall parameters (Sandy landfall Oct 30, 00:00 UTC)
    # Based on IBTrACS: lat 39.5°N, lon 285.5°E (-74.5°W)
    LANDFALL_LAT = 39.5
    LANDFALL_LON = 285.5
    LANDFALL_REGION = [280, 295, 30, 45]  # US East Coast region

    # Store landfall comparisons for summary table
    landfall_comparisons = {}

    # For each lead time, compare fields at landfall
    if len(results) > 0:
        for lead_days in sorted(results.keys()):
            print(f"\n{lead_days}-day lead time:")

            # Get predictions
            preds = results[lead_days]['predictions']
            config = results[lead_days]['config']

            # Calculate which prediction timestep corresponds to landfall
            # Landfall ~Oct 29, 18:00
            # Need to figure out the index based on initialization time
            init_date = config['init_date']
            init_hour = config['init_hour']

            # Each step = 6 hours, landfall is Oct 29, 18:00
            # Will vary by lead time, but for now use the last few timesteps
            # The tracker should give us the approximate landfall time

            # Use the timestep closest to landfall based on track
            forecast_track = results[lead_days]['forecast_track']

            # Find timestep closest to landfall position
            from shared.metrics import calculate_distance
            distances = []
            for i, (lat, lon) in enumerate(zip(forecast_track['lat'], forecast_track['lon'])):
                dist = calculate_distance(lat, lon, LANDFALL_LAT, LANDFALL_LON)
                distances.append(dist)

            if len(distances) > 0:
                track_idx = np.argmin(distances)
                # Track includes initial condition at index 0, but predictions list doesn't
                # So prediction index = track index - 1
                landfall_idx = max(0, track_idx - 1)
                print(f"  Using track position {track_idx} → prediction timestep {landfall_idx} (closest to landfall)")

                # Load ERA5 verification data at landfall time (Oct 30 00:00 UTC)
                # Use separate Oct 30 file for rigorous verification
                try:
                    import xarray as xr
                    data_path = CONFIG['base_data_path'] / CONFIG['data_folder']
                    surf_file = data_path / "2012-10-30-surface-level.nc"
                    atmos_file = data_path / "2012-10-30-atmospheric.nc"

                    if surf_file.exists() and atmos_file.exists():
                        era5_surf = xr.open_dataset(surf_file)
                        era5_atmos = xr.open_dataset(atmos_file)
                        print(f"  ✓ Loaded Oct 30 ERA5 data for landfall verification")

                        # Compare fields
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

                        # Plot field comparisons
                        # MSL field
                        msl_plot = CONFIG['output_dir'] / f"sandy_{lead_days}day_landfall_msl.png"
                        plot_field_comparison(
                            forecast=comparison['msl']['aurora'] / 100,  # Convert to hPa
                            truth=comparison['msl']['era5'] / 100,
                            lat=comparison['lat'],
                            lon=comparison['lon'],
                            variable_name="MSL (hPa)",
                            title=f"Sandy {lead_days}-day Lead: MSL at Landfall",
                            save_path=msl_plot,
                            extent=LANDFALL_REGION
                        )

                        # Wind field
                        wind_plot = CONFIG['output_dir'] / f"sandy_{lead_days}day_landfall_wind.png"
                        plot_field_comparison(
                            forecast=comparison['wind']['aurora'],
                            truth=comparison['wind']['era5'],
                            lat=comparison['lat'],
                            lon=comparison['lon'],
                            variable_name="10m Wind Speed (m/s)",
                            title=f"Sandy {lead_days}-day Lead: Wind at Landfall",
                            save_path=wind_plot,
                            extent=LANDFALL_REGION,
                            cmap='YlOrRd'
                        )

                        # Store comparison in results
                        results[lead_days]['landfall_field_comparison'] = comparison

                        # Store for summary table
                        landfall_comparisons[f'{lead_days}-day lead'] = comparison

                        era5_surf.close()
                        era5_atmos.close()
                    else:
                        print(f"  ⚠ Oct 30 ERA5 files not found, skipping field comparison")
                        print(f"      Missing: {surf_file.name} or {atmos_file.name}")

                except Exception as e:
                    print(f"  ⚠ Error in field comparison: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"  ⚠ No forecast track positions available")

    print()

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 75)
    print("  Stage 1 Summary: Lead Time Assessment")
    print("=" * 75)
    print()

    if len(results) > 0:
        # Generate comprehensive summary using landfall field comparisons
        comprehensive_summary = summarize_stage1_results(results, landfall_comparisons)

        # Print header
        print(f"{'Lead':<8} {'24hr Track':<15} {'48hr Track':<15} {'72hr Track':<15} {'MSL Error':<13} {'Wind Error':<13} {'Position Error':<15}")
        print(f"{'Time':<8} {'Error (km)':<15} {'Error (km)':<15} {'Error (km)':<15} {'(hPa)':<13} {'(m/s)':<13} {'at Landfall (km)':<15}")
        print("-" * 110)

        for lead in sorted(results.keys()):
            metrics = comprehensive_summary[lead]

            # Format values with N/A for None
            track_24h = f"{metrics['track_error_24h']:.1f}" if metrics['track_error_24h'] is not None else "N/A"
            track_48h = f"{metrics['track_error_48h']:.1f}" if metrics['track_error_48h'] is not None else "N/A"
            track_72h = f"{metrics['track_error_72h']:.1f}" if metrics['track_error_72h'] is not None else "N/A"
            msl_err = f"{metrics['msl_min_error']:.1f}" if metrics['msl_min_error'] is not None else "N/A"
            wind_err = f"{metrics['wind_max_error']:.1f}" if metrics['wind_max_error'] is not None else "N/A"
            pos_err = f"{metrics['center_position_error']:.1f}" if metrics['center_position_error'] is not None else "N/A"

            print(f"{lead}-day   {track_24h:<15} {track_48h:<15} {track_72h:<15} {msl_err:<13} {wind_err:<13} {pos_err:<15}")

        print()

        # Identify best lead time based on landfall position error
        valid_leads = [
            lead for lead in results.keys()
            if comprehensive_summary[lead]['center_position_error'] is not None
        ]

        if valid_leads:
            best_lead = min(valid_leads,
                          key=lambda x: comprehensive_summary[x]['center_position_error'])
            print(f"✓ Best performing: {best_lead}-day lead time")
            print(f"  (Based on TC center position error at landfall: {comprehensive_summary[best_lead]['center_position_error']:.1f} km)")
            print(f"  Use this for Stage 2 initialization sensitivity testing!")
        print()

    # =========================================================================
    # EXPORT TO CSV
    # =========================================================================
    if len(results) > 0:
        print("\n" + "=" * 75)
        print("  Exporting Results to CSV")
        print("=" * 75)
        print()

        csv_path = CONFIG['output_dir'].parent.parent / 'TC_result_metrics.csv'
        export_results_to_csv(
            tc_name='Sandy 2012',
            stage=1,
            results=results,
            landfall_comparisons=landfall_comparisons,
            csv_path=csv_path,
            stage_type='stage1'
        )
        print()

    print("=" * 75)
    print("  ✓ Stage 1 Complete!")
    print("=" * 75)
    print()
    print("Next: Run Stage 2 with best lead time to test initialization sensitivity")
    print()


if __name__ == "__main__":
    main()
