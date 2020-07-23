"""
Script to download SST observations captured by GOES16

The script downloads each timestep indivually to
avoid having connection timeouts to the THREDDS server.
"""
import xarray as xr
from tqdm import trange

print(xr.__version__)

filename_out_zarr = '/scratch/local1/m300408/GOES16_SST_10-24N_-61--40E.zarr'

ds = xr.open_dataset('https://thredds.jpl.nasa.gov/thredds/dodsC/OceanTemperature/ABI_G16-STAR-L3C-v2.70.nc#fillmismatch')

ds_sel = ds.sel(lat=slice(24,10),lon=slice(-61,-40), time=slice('2018-01-01','2020-04-01'))

del ds_sel['or_number_of_pixels']
del ds_sel['sses_bias']
del ds_sel['sses_standard_deviation']
del ds_sel['wind_speed']
del ds_sel['dt_analysis']
del ds_sel['satellite_zenith_angle']

del ds_sel.l2p_flags.attrs['coordinates']
del ds_sel.sea_surface_temperature.attrs['coordinates']
del ds_sel.sst_dtime.attrs['coordinates']

for t in trange(len(ds_sel.time)):
    if t == 0:
        ds_sel.isel(time=slice(t,t+1)).to_zarr(filename_out_zarr)
    else:
        ds_sel.isel(time=slice(t,t+1)).to_zarr(filename_out_zarr, append_dim='time', mode='a')

