"""
Regenerate Texas 2021 Freeze Stage 1 visualizations.

This version properly handles Aurora 0.25° grid coordinates.
Adapted from Beast from East visualization script.
"""

import sys
from pathlib import Path
import pickle
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

sys.path.insert(0, str(Path(__file__).parent.parent))
from Freeze_utils import extract_regional_subset

# Configuration
CONFIG = {
    'prediction_dir': Path(__file__).parent / 'prediction_output',
    'output_dir': Path(__file__).parent / 'prediction_output',
    'data_dir': Path(__file__).parent.parent / 'data/era5_texas_2021',

    # Texas-specific regions for visualizations
    # Use larger region for temperature fields to show broader context
    # Use focused region for synoptic patterns
    'region_temp': {
        'name': 'Texas and Southern Plains',
        'lat_min': 22.0,
        'lat_max': 40.0,
        'lon_min': -110.0,
        'lon_max': -88.0
    },
    'region_synoptic': {
        'name': 'Central and Eastern US',
        'lat_min': 20.0,
        'lat_max': 50.0,
        'lon_min': -120.0,
        'lon_max': -75.0
    },

    # Target dates - UPDATED from baseline analysis (Nov 20, 2024)
    # All at 06:00 UTC (midnight Texas CST)
    'target_dates': {
        'onset': '2021-02-14 06:00',
        'peak': '2021-02-15 06:00',
        'recovery': '2021-02-21 06:00'
    },

    'lead_time_configs': [
        {'lead_days': 1},
        {'lead_days': 7},
        {'lead_days': 14},
        {'lead_days': 21},
    ]
}


def subset_aurora_field_to_region(global_field, region):
    """
    Subset Aurora global field (720x1440 at 0.25° resolution) to region.

    Returns
    -------
    tuple
        (regional_field, lats, lons) where lats/lons are actual 0.25° grid coordinates
    """
    # Aurora 0.25° grid (matching Beast implementation)
    # 720 latitudes: 90, 89.75, ..., -89.75
    # 1440 longitudes: 0, 0.25, ..., 359.75
    global_lats = np.arange(90, -90, -0.25)  # 720 points
    global_lons = np.arange(0, 360, 0.25)     # 1440 points

    # Create DataArray
    global_da = xr.DataArray(
        global_field,
        dims=['latitude', 'longitude'],
        coords={'latitude': global_lats, 'longitude': global_lons}
    )

    # Convert lon bounds to 0-360
    lon_min = region['lon_min'] if region['lon_min'] >= 0 else region['lon_min'] + 360
    lon_max = region['lon_max'] if region['lon_max'] >= 0 else region['lon_max'] + 360

    # Subset
    if lon_min > lon_max:
        # Crosses prime meridian
        subset1 = global_da.sel(
            latitude=slice(region['lat_max'], region['lat_min']),
            longitude=slice(lon_min, 360)
        )
        subset2 = global_da.sel(
            latitude=slice(region['lat_max'], region['lat_min']),
            longitude=slice(0, lon_max)
        )
        subset = xr.concat([subset1, subset2], dim='longitude')
    else:
        subset = global_da.sel(
            latitude=slice(region['lat_max'], region['lat_min']),
            longitude=slice(lon_min, lon_max)
        )

    # Get actual coordinates
    lats = subset.latitude.values
    lons = subset.longitude.values

    # Convert lons to -180 to 180 for plotting
    lons_plot = np.where(lons > 180, lons - 360, lons)

    return subset.values, lats, lons_plot


def plot_elegant_comparison(forecast, truth, lat, lon, variable_name, title,
                           save_path, vmin=None, vmax=None, cmap='RdBu_r', extent=None, diff_cmap=None):
    """
    Create elegant publication-quality comparison plot with US state borders.

    Parameters:
    -----------
    diff_cmap : str, optional
        Colormap for difference plot. If None, uses 'RdBu_r' for temperature, same as cmap for others.
    """
    from matplotlib.colors import TwoSlopeNorm

    # Determine difference colormap
    if diff_cmap is None:
        # For temperature fields, always use diverging RdBu_r
        if 'Temperature' in variable_name or 'T2m' in variable_name or 'T850' in variable_name:
            diff_cmap = 'RdBu_r'
        else:
            # For non-temperature fields, use same colormap as forecast/truth
            diff_cmap = cmap

    fig = plt.figure(figsize=(20, 6), dpi=300)

    # Calculate difference
    diff = forecast - truth

    # Auto-scale if not provided
    if vmin is None or vmax is None:
        combined = np.concatenate([forecast.flatten(), truth.flatten()])
        vmin = np.nanpercentile(combined, 2)
        vmax = np.nanpercentile(combined, 98)

    diff_max = max(np.nanpercentile(np.abs(diff), 95), 0.5)

    # Panel 1: Aurora Forecast
    ax1 = plt.subplot(1, 3, 1, projection=ccrs.PlateCarree())
    ax1.set_extent(extent, crs=ccrs.PlateCarree())

    # Add elegant geographic features
    ax1.add_feature(cfeature.OCEAN, facecolor='lightblue', alpha=0.3, zorder=0)
    ax1.add_feature(cfeature.LAND, facecolor='wheat', alpha=0.2, zorder=0)
    ax1.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor='black', zorder=3)
    ax1.add_feature(cfeature.BORDERS, linewidth=0.5, edgecolor='gray', linestyle=':', zorder=3)

    # Add US state borders (higher resolution)
    ax1.add_feature(cfeature.STATES.with_scale('50m'), linewidth=0.6,
                    edgecolor='darkgray', linestyle='-', alpha=0.7, zorder=3)

    # Plot data
    mesh1 = ax1.pcolormesh(lon, lat, forecast, transform=ccrs.PlateCarree(),
                           cmap=cmap, vmin=vmin, vmax=vmax, zorder=1)

    # Add 0°C contour for temperature fields
    if 'Temperature' in variable_name or 'T2m' in variable_name or 'T850' in variable_name:
        cs1 = ax1.contour(lon, lat, forecast, levels=[0], colors='black',
                          linewidths=2.5, linestyles='--', transform=ccrs.PlateCarree(), zorder=4)
        ax1.clabel(cs1, inline=True, fontsize=9, fmt='0°C')

    ax1.set_title(f'Aurora Forecast - {variable_name}', fontsize=13, fontweight='bold', pad=10)
    gl1 = ax1.gridlines(draw_labels=True, linewidth=0.5, alpha=0.3, linestyle='--')
    gl1.top_labels = False
    gl1.right_labels = False

    cbar1 = plt.colorbar(mesh1, ax=ax1, orientation='horizontal', pad=0.05, shrink=0.85)

    # Panel 2: ERA5 Truth
    ax2 = plt.subplot(1, 3, 2, projection=ccrs.PlateCarree())
    ax2.set_extent(extent, crs=ccrs.PlateCarree())

    ax2.add_feature(cfeature.OCEAN, facecolor='lightblue', alpha=0.3, zorder=0)
    ax2.add_feature(cfeature.LAND, facecolor='wheat', alpha=0.2, zorder=0)
    ax2.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor='black', zorder=3)
    ax2.add_feature(cfeature.STATES.with_scale('50m'), linewidth=0.6,
                    edgecolor='darkgray', linestyle='-', alpha=0.7, zorder=3)

    mesh2 = ax2.pcolormesh(lon, lat, truth, transform=ccrs.PlateCarree(),
                           cmap=cmap, vmin=vmin, vmax=vmax, zorder=1)

    if 'Temperature' in variable_name or 'T2m' in variable_name or 'T850' in variable_name:
        cs2 = ax2.contour(lon, lat, truth, levels=[0], colors='black',
                          linewidths=2.5, linestyles='--', transform=ccrs.PlateCarree(), zorder=4)
        ax2.clabel(cs2, inline=True, fontsize=9, fmt='0°C')

    ax2.set_title(f'ERA5 - {variable_name}', fontsize=13, fontweight='bold', pad=10)
    gl2 = ax2.gridlines(draw_labels=True, linewidth=0.5, alpha=0.3, linestyle='--')
    gl2.top_labels = False
    gl2.right_labels = False
    gl2.left_labels = False  # Hide left labels on middle panel

    cbar2 = plt.colorbar(mesh2, ax=ax2, orientation='horizontal', pad=0.05, shrink=0.85)

    # Panel 3: Difference
    ax3 = plt.subplot(1, 3, 3, projection=ccrs.PlateCarree())
    ax3.set_extent(extent, crs=ccrs.PlateCarree())

    ax3.add_feature(cfeature.OCEAN, facecolor='lightblue', alpha=0.3, zorder=0)
    ax3.add_feature(cfeature.LAND, facecolor='wheat', alpha=0.2, zorder=0)
    ax3.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor='black', zorder=3)
    ax3.add_feature(cfeature.STATES.with_scale('50m'), linewidth=0.6,
                    edgecolor='darkgray', linestyle='-', alpha=0.7, zorder=3)

    # Colormap for difference (diverging for temp, sequential for others)
    if diff_cmap in ['RdBu_r', 'RdBu', 'bwr', 'seismic', 'coolwarm']:  # Diverging colormaps
        norm = TwoSlopeNorm(vmin=-diff_max, vcenter=0, vmax=diff_max)
    else:  # Sequential colormaps (viridis, plasma, etc.)
        norm = None
        diff_vmin = np.nanpercentile(diff, 2)
        diff_vmax = np.nanpercentile(diff, 98)

    if norm is not None:
        mesh3 = ax3.pcolormesh(lon, lat, diff, transform=ccrs.PlateCarree(),
                               cmap=diff_cmap, norm=norm, zorder=1)
    else:
        mesh3 = ax3.pcolormesh(lon, lat, diff, transform=ccrs.PlateCarree(),
                               cmap=diff_cmap, vmin=diff_vmin, vmax=diff_vmax, zorder=1)

    # Zero contour for difference
    cs3 = ax3.contour(lon, lat, diff, levels=[0], colors='black',
                      linewidths=1.5, linestyles='--', transform=ccrs.PlateCarree(), zorder=4)

    ax3.set_title(f'Difference (Aurora - ERA5)', fontsize=13, fontweight='bold', pad=10)
    gl3 = ax3.gridlines(draw_labels=True, linewidth=0.5, alpha=0.3, linestyle='--')
    gl3.top_labels = False
    gl3.right_labels = False
    gl3.left_labels = False  # Hide left labels on right panel

    cbar3 = plt.colorbar(mesh3, ax=ax3, orientation='horizontal', pad=0.05, shrink=0.85, extend='both')

    # Super title
    fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"Saved: {save_path.name}")


def load_era5_data():
    """Load ERA5 truth data."""
    print("\n1. Loading ERA5 truth data...")

    data_dir = CONFIG['data_dir']
    surf_ds = xr.open_dataset(data_dir / 'texas_2021_surface_jan24-feb21.nc')
    atmos_ds = xr.open_dataset(data_dir / 'texas_2021_atmospheric_jan24-feb21.nc')
    truth_ds = xr.merge([surf_ds, atmos_ds])

    print(f"   ✓ Loaded ERA5 data")
    return truth_ds


def regenerate_for_lead_time(lead_days, truth_ds):
    """Regenerate visualizations for one lead time."""
    print(f"\n2. Processing {lead_days}-day lead time...")

    pred_cache_file = CONFIG['prediction_dir'] / f"predictions_{lead_days}day.pkl"

    if not pred_cache_file.exists():
        print(f"   ✗ No cached predictions: {pred_cache_file}")
        return

    print(f"   Loading cached predictions...")
    with open(pred_cache_file, 'rb') as f:
        cached_data = pickle.load(f)

    forecast_times = cached_data['forecast_times']
    t2m_global = cached_data['t2m_fields_celsius']
    t850_global = cached_data['t850_fields_celsius']
    z500_global = cached_data['z500_fields_m']
    msl_global = cached_data['msl_fields_hpa']

    print(f"   ✓ Loaded {len(forecast_times)} timesteps")

    # Find phase indices
    phases = {}
    for phase_name, target_str in CONFIG['target_dates'].items():
        target_dt = pd.Timestamp(target_str)
        diffs = [abs((pd.Timestamp(t) - target_dt).total_seconds()) for t in forecast_times]
        idx = int(np.argmin(diffs))
        phases[phase_name] = {'index': idx, 'time': forecast_times[idx]}
        print(f"   {phase_name.capitalize()}: idx={idx}, time={forecast_times[idx]}")

    # Generate visualizations
    region_temp = CONFIG['region_temp']  # Focused on Texas
    region_synoptic = CONFIG['region_synoptic']  # Broader US
    output_dir = CONFIG['output_dir']

    print(f"\n3. Generating visualizations...")

    for phase_name, phase_info in phases.items():
        idx = phase_info['index']
        valid_time = phase_info['time']

        print(f"\n   {phase_name.upper()} Phase:")

        # --- T2m (use temp region) ---
        forecast_t2m_regional, lats, lons = subset_aurora_field_to_region(t2m_global[idx], region_temp)
        # CRITICAL: Extract ERA5 at target TIME, not forecast index
        truth_t2m_da = extract_regional_subset(truth_ds, 't2m', region_temp).sel(valid_time=valid_time, method='nearest')
        truth_t2m = truth_t2m_da.values - 273.15
        truth_lats = truth_t2m_da.latitude.values
        truth_lons = truth_t2m_da.longitude.values
        truth_lons_plot = np.where(truth_lons > 180, truth_lons - 360, truth_lons)

        # Use elegant visualization
        extent = [region_temp['lon_min'], region_temp['lon_max'], region_temp['lat_min'], region_temp['lat_max']]
        output_path = output_dir / f"texas_{lead_days}day_{phase_name}_t2m.png"

        plot_elegant_comparison(
            forecast=forecast_t2m_regional,
            truth=truth_t2m,
            lat=lats,
            lon=lons,
            variable_name='2m Temperature (°C)',
            title=f'Texas 2021 Freeze - {lead_days}-day lead | Valid: {pd.Timestamp(valid_time).strftime("%Y-%m-%d %H:%M UTC")}',
            save_path=output_path,
            vmin=-25, vmax=20,  # Adjusted for Texas climate
            cmap='RdBu_r',
            extent=extent
        )

        # --- T850 (use temp region) ---
        forecast_t850_regional, lats, lons = subset_aurora_field_to_region(t850_global[idx], region_temp)
        truth_t850 = extract_regional_subset(truth_ds, 't', region_temp, level=850).sel(valid_time=valid_time, method='nearest').values - 273.15

        output_path = output_dir / f"texas_{lead_days}day_{phase_name}_t850.png"
        plot_elegant_comparison(
            forecast=forecast_t850_regional,
            truth=truth_t850,
            lat=lats,
            lon=lons,
            variable_name='850 hPa Temperature (°C)',
            title=f'Texas 2021 Freeze - {lead_days}-day lead | Valid: {pd.Timestamp(valid_time).strftime("%Y-%m-%d %H:%M UTC")}',
            save_path=output_path,
            vmin=-20, vmax=15,  # Adjusted for 850 hPa range
            cmap='RdBu_r',
            extent=extent
        )

        # --- Z500 (use synoptic region for larger-scale patterns) ---
        extent_synoptic = [region_synoptic['lon_min'], region_synoptic['lon_max'], region_synoptic['lat_min'], region_synoptic['lat_max']]
        forecast_z500_regional, lats_syn, lons_syn = subset_aurora_field_to_region(z500_global[idx], region_synoptic)
        truth_z500 = extract_regional_subset(truth_ds, 'z', region_synoptic, level=500).sel(valid_time=valid_time, method='nearest').values / 9.81

        output_path = output_dir / f"texas_{lead_days}day_{phase_name}_z500.png"
        plot_elegant_comparison(
            forecast=forecast_z500_regional,
            truth=truth_z500,
            lat=lats_syn,
            lon=lons_syn,
            variable_name='500 hPa Geopotential Height (m)',
            title=f'Texas 2021 Freeze - {lead_days}-day lead | Valid: {pd.Timestamp(valid_time).strftime("%Y-%m-%d %H:%M UTC")}',
            save_path=output_path,
            cmap='viridis',
            extent=extent_synoptic
        )

        # --- MSL (use synoptic region) ---
        forecast_msl_regional, lats_syn, lons_syn = subset_aurora_field_to_region(msl_global[idx], region_synoptic)
        truth_msl = extract_regional_subset(truth_ds, 'msl', region_synoptic).sel(valid_time=valid_time, method='nearest').values / 100.0

        output_path = output_dir / f"texas_{lead_days}day_{phase_name}_msl.png"
        plot_elegant_comparison(
            forecast=forecast_msl_regional,
            truth=truth_msl,
            lat=lats_syn,
            lon=lons_syn,
            variable_name='Mean Sea Level Pressure (hPa)',
            title=f'Texas 2021 Freeze - {lead_days}-day lead | Valid: {pd.Timestamp(valid_time).strftime("%Y-%m-%d %H:%M UTC")}',
            save_path=output_path,
            cmap='plasma',
            extent=extent_synoptic
        )


def main():
    """Main routine."""
    print("="*80)
    print("Texas 2021 Freeze Stage 1 - Visualization Regeneration")
    print("="*80)

    truth_ds = load_era5_data()

    for config in CONFIG['lead_time_configs']:
        regenerate_for_lead_time(config['lead_days'], truth_ds)

    print("\n" + "="*80)
    print("✓ All visualizations regenerated!")
    print("="*80)
    print()
    print(f"Output directory: {CONFIG['output_dir']}")
    print("Files created: texas_*day_*_*.png (48 plots total)")
    print()


if __name__ == '__main__':
    main()
