"""
Data loading utilities for Aurora forecasts.

This module contains functions for loading ERA5 data and creating Aurora batches.
These functions are used across all event types (TC, Freeze, AR, Precipitation).
"""

import torch
import xarray as xr
from pathlib import Path
from aurora import Batch, Metadata


def load_era5_data(data_path, day):
    """
    Load ERA5 data for Aurora batch creation.

    Parameters
    ----------
    data_path : Path or str
        Path to directory containing ERA5 NetCDF files
    day : str
        Date string in format 'YYYY-MM-DD'

    Returns
    -------
    tuple of xarray.Dataset
        (static_vars_ds, surf_vars_ds, atmos_vars_ds)

    Notes
    -----
    Expected file structure:
        data_path/
            static.nc
            {day}-surface-level.nc
            {day}-atmospheric.nc
    """
    data_path = Path(data_path)

    static_vars_ds = xr.open_dataset(data_path / "static.nc", engine="netcdf4")
    surf_vars_ds = xr.open_dataset(data_path / f"{day}-surface-level.nc", engine="netcdf4")
    atmos_vars_ds = xr.open_dataset(data_path / f"{day}-atmospheric.nc", engine="netcdf4")

    return static_vars_ds, surf_vars_ds, atmos_vars_ds


def create_aurora_batch(static_vars_ds, surf_vars_ds, atmos_vars_ds, time_start_idx=1):
    """
    Create Aurora batch from ERA5 datasets.

    Parameters
    ----------
    static_vars_ds : xarray.Dataset
        Static variables (z, slt, lsm)
    surf_vars_ds : xarray.Dataset
        Surface variables (t2m, u10, v10, msl)
    atmos_vars_ds : xarray.Dataset
        Atmospheric variables (t, u, v, q, z at pressure levels)
    time_start_idx : int, optional
        Starting time index in the datasets (default: 1)
        Aurora needs 2 consecutive timesteps, so will use [time_start_idx:time_start_idx+2]

    Returns
    -------
    aurora.Batch
        Batch object ready for Aurora model input

    Notes
    -----
    Aurora requires:
    - Surface: 2t, 10u, 10v, msl
    - Static: z, slt, lsm
    - Atmospheric: t, u, v, q, z at 13 pressure levels
    - Two consecutive timesteps for initialization
    """
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


def get_time_indices_from_hour(surf_vars_ds, target_hours):
    """
    Get time indices corresponding to specific hours of day.

    Parameters
    ----------
    surf_vars_ds : xarray.Dataset
        Surface variables dataset with 'valid_time' coordinate
    target_hours : list of int
        Hours to find (e.g., [0, 6, 12, 18] for 00, 06, 12, 18 UTC)

    Returns
    -------
    dict
        Mapping from hour to time index, e.g., {0: 1, 6: 2, 12: 3, 18: 4}

    Example
    -------
    >>> indices = get_time_indices_from_hour(surf_vars_ds, [6, 12])
    >>> # Use for initialization
    >>> batch_06 = create_aurora_batch(static_ds, surf_ds, atmos_ds, indices[6])
    >>> batch_12 = create_aurora_batch(static_ds, surf_ds, atmos_ds, indices[12])
    """
    time_indices = {}
    times = surf_vars_ds.valid_time.values

    for i, time in enumerate(times):
        hour = time.astype('datetime64[h]').astype(int) % 24
        if hour in target_hours:
            time_indices[hour] = i

    return time_indices
