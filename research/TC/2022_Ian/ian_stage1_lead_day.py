#!/usr/bin/env python3
"""
Hurricane Ian 2022 - Stage 1: Lead Time Assessment

Tests 4 different lead times (1, 3, 5, 7 days) by varying initialization date.
All forecasts target the same critical event: Ian's Florida landfall on Sep 28, 2022.

This answers: "How far in advance can we predict Ian's landfall?"

Note: 7-day lead initializes Sep 21 18:00 UTC (pre-genesis), but uses Sep 22 18:00 UTC
      genesis position (12.30°N, 66.30°W) for tracker initialization.
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
    print("  Hurricane Ian 2022 - Stage 1: Lead Time Assessment")
    print("=" * 75)
    print()
    print("Strategy: Variable initialization date, fixed target (Sep 28 landfall)")
    print()

    # =========================================================================
    # CONFIGURATION
    # =========================================================================
    CONFIG = {
        'event_name': 'Hurricane Ian 2022',
        'storm_name': 'IAN',
        'storm_year': 2022,
        'landfall_date': 'Sep 28, 2022 20:00 UTC',
        'base_data_path': Path("/scratch/qhuang62/aurora-extreme-predictability/research/TC/data"),
        'output_dir': Path(__file__).parent / "prediction_output",

        # Combined data file covering Sep 21-28
        'combined_surface_file': 'ian_2022_surface_combined.nc',
        'combined_atmos_file': 'ian_2022_atmospheric_combined.nc',
        'data_folder': 'era5_ian_2022',

        # Stage 1: Test 4 lead times, all targeting Sep 28 20:00 UTC (landfall)
        # All initialized at 18:00 UTC for exact 1/3/5/7 day leads
        # Coordinates from IBTrACS v04r01 (Storm ID: 2022266N12294)
        'lead_time_configs': [
            {
                'lead_days': 1,
                'init_date': '2022-09-27',
                'init_hour': '18',
                'time_idx': 27,  # Sep 27, 18:00 UTC in combined file (Sep 21 00:00 = 0)
                'init_lat': 23.50,  # IBTrACS: Sep 27 18:00 UTC
                'init_lon': 276.70,  # -83.30°W = 276.70°E
            },
            {
                'lead_days': 3,
                'init_date': '2022-09-25',
                'init_hour': '18',
                'time_idx': 19,  # Sep 25, 18:00 UTC in combined file (FIXED: was 20, off by 1)
                'init_lat': 15.80,  # IBTrACS: Sep 25 18:00 UTC
                'init_lon': 279.90,  # -80.10°W = 279.90°E
            },
            {
                'lead_days': 5,
                'init_date': '2022-09-23',
                'init_hour': '18',
                'time_idx': 11,  # Sep 23, 18:00 UTC in combined file
                'init_lat': 14.60,  # IBTrACS: Sep 23 18:00 UTC
                'init_lon': 289.40,  # -70.60°W = 289.40°E
            },
            {
                'lead_days': 7,
                'init_date': '2022-09-21',
                'init_hour': '18',
                'time_idx': 3,   # Sep 21, 18:00 UTC in combined file
                # Note: Ian formed Sep 22 18:00 UTC, so use genesis position for tracker
                'init_lat': 12.30,  # IBTrACS: Sep 22 18:00 UTC (genesis position)
                'init_lon': 293.70,  # -66.30°W = 293.70°E
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
    print("Note: 7-day lead uses Sep 22 genesis position for tracker initialization")
    print("      (tests Aurora's ability to develop Ian from pre-genesis environment)")
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
        print(f"  Target: Sep 28 20:00 UTC landfall ({lead_days} days ahead)")
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
            print(f"  Run download_ian_complete.py and combine_ian_data.py first")
            continue

        # Load ERA5 data from combined files
        try:
            import xarray as xr
            static_ds, _, _ = load_era5_data(data_path, '2022-09-22')  # Load static vars
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

        # Run forecast (target: Sep 28 18:00 UTC)
        # Target: Sep 28 18:00 UTC (closest 6-hourly time to actual 20:00 UTC landfall)
        # Following Sandy's pattern: steps = lead_days * 4 - 1
        # This makes forecasts end 6h before target (at Sep 28 12:00 UTC)
        # The tracker includes init position (t=0) + forecast steps (t=1 to N)
        #   1-day: 3 steps → 4 track points, ending at Sep 28 12:00 UTC
        #   3-day: 11 steps → 12 track points, ending at Sep 28 12:00 UTC
        #   5-day: 19 steps → 20 track points, ending at Sep 28 12:00 UTC
        #   7-day: 27 steps → 28 track points, ending at Sep 28 12:00 UTC
        steps = lead_days * 4 - 1

        print(f"Running forecast: {lead_days} days = {steps} steps ({steps*6} hours)")

        preds = run_forecast(
            model, batch, tracker,
            steps=steps,
            name=f"Ian {lead_days}day",
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
            landfall_threshold_lon=-82.0  # Florida Gulf Coast
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

        save_path = CONFIG['output_dir'] / "ian_stage1_lead_time_results.pkl"
        save_multi_init_results(
            results,
            save_path,
            metadata={
                'event': CONFIG['event_name'],
                'stage': 1,
                'strategy': 'Variable initialization date',
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
        # Start: Sep 21 18:00 (7-day forecast initialization, earliest)
        # End: Sep 28 18:00 (target time - closest 6-hourly to actual 20:00 landfall)
        earliest_init_time = datetime(2022, 9, 21, 18, 0)  # 7-day lead init
        landfall_time = datetime(2022, 9, 28, 18, 0)  # Target: 18:00 UTC (6-hourly grid)

        # Find indices for time range
        valid_indices = [i for i, t in enumerate(obs_track['time'])
                        if earliest_init_time <= t <= landfall_time]

        obs_track_truncated = {
            'time': [obs_track['time'][i] for i in valid_indices],
            'lat': [obs_track['lat'][i] for i in valid_indices],
            'lon': [obs_track['lon'][i] for i in valid_indices]
        }

        track_plot = CONFIG['output_dir'] / "ian_stage1_tracks.png"
        plot_track_comparison(
            forecast_tracks=forecast_tracks,
            obs_track=obs_track_truncated,  # Use truncated track
            title="Hurricane Ian - Track Comparison (Different Lead Days)",
            save_path=track_plot,
            extent=[-90, -60, 10, 35]  # Gulf/Caribbean/Florida region
        )

        # Error evolution by valid time (not lead time from init)
        errors_dict = {}
        tracks_dict = {}
        for lead in sorted(results.keys()):
            if len(results[lead]['errors_data']['errors']) > 0:
                label = f"{lead}-day lead"
                errors_dict[label] = results[lead]['errors_data']['errors']
                tracks_dict[label] = results[lead]['forecast_track']

        if len(errors_dict) > 0:
            landfall_time = datetime(2022, 9, 28, 18, 0)  # Target: 18:00 UTC (6-hourly grid)

            error_plot = CONFIG['output_dir'] / "ian_stage1_errors.png"
            plot_error_by_valid_time(
                forecast_tracks_dict=tracks_dict,
                errors_dict=errors_dict,
                target_time=landfall_time,
                ylabel="Track Error (km)",
                title="Hurricane Ian - Track Error (Different Lead Days)",
                save_path=error_plot,
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

    # Import field comparison functions
    from TC.TC_utils import compare_fields_at_landfall
    from shared.visualization import plot_field_comparison

    # Landfall parameters (Ian landfall Sep 28, 20:00 UTC)
    # Based on IBTrACS: lat 26.80°N, lon 278.0°E (-82.0°W)
    LANDFALL_LAT = 26.80
    LANDFALL_LON = 278.0  # -82.0°W converted to 0-360°E
    LANDFALL_REGION = [272, 288, 20, 32]  # Gulf Coast/Florida region

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
            # Landfall ~Sep 28, 20:00 UTC
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

                # Load ERA5 verification data at landfall time (Sep 28 18:00 UTC)
                # Use separate Sep 28 landfall file for rigorous verification
                try:
                    import xarray as xr
                    data_path = CONFIG['base_data_path'] / CONFIG['data_folder']
                    surf_file = data_path / "ian_2022_surface_landfall.nc"
                    atmos_file = data_path / "ian_2022_atmospheric_landfall.nc"

                    if surf_file.exists() and atmos_file.exists():
                        era5_surf = xr.open_dataset(surf_file)
                        era5_atmos = xr.open_dataset(atmos_file)
                        print(f"  ✓ Loaded Sep 28 18:00 UTC ERA5 data for landfall verification")

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
                        msl_plot = CONFIG['output_dir'] / f"ian_{lead_days}day_landfall_msl.png"
                        plot_field_comparison(
                            forecast=comparison['msl']['aurora'] / 100,  # Convert to hPa
                            truth=comparison['msl']['era5'] / 100,
                            lat=comparison['lat'],
                            lon=comparison['lon'],
                            variable_name="MSL (hPa)",
                            title=f"Ian {lead_days}-day Lead: MSL at Landfall",
                            save_path=msl_plot,
                            extent=LANDFALL_REGION
                        )

                        # Wind field
                        wind_plot = CONFIG['output_dir'] / f"ian_{lead_days}day_landfall_wind.png"
                        plot_field_comparison(
                            forecast=comparison['wind']['aurora'],
                            truth=comparison['wind']['era5'],
                            lat=comparison['lat'],
                            lon=comparison['lon'],
                            variable_name="10m Wind Speed (m/s)",
                            title=f"Ian {lead_days}-day Lead: Wind at Landfall",
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
                        print(f"  ⚠ Sep 28 landfall ERA5 files not found, skipping field comparison")
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
            tc_name='Ian 2022',
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
