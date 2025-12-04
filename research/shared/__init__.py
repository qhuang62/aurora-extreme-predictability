"""
Shared utilities for Aurora extreme weather predictability research.

This package contains common functions used across all event types (TC, Freeze, AR, Precipitation).
"""

from .data_loading import load_era5_data, create_aurora_batch
from .forecasting import run_forecast, run_multi_init_forecast
from .metrics import compute_rmse, compute_acc, compute_bias, compute_spatial_correlation
from .visualization import plot_track_comparison, plot_error_evolution, plot_spatial_field

__all__ = [
    'load_era5_data',
    'create_aurora_batch',
    'run_forecast',
    'run_multi_init_forecast',
    'compute_rmse',
    'compute_acc',
    'compute_bias',
    'compute_spatial_correlation',
    'plot_track_comparison',
    'plot_error_evolution',
    'plot_spatial_field',
]

__version__ = '0.1.0'
