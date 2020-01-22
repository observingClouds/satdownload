"""
Script to download subsections of AIRS data
"""

import xarray as xr
from pydap.cas.urs import setup_session
from collections import namedtuple
import re
import numpy as np
import requests
import pandas as pd
import datetime as dt
import tqdm
import argparse


def get_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-o', '--outputfile', metavar="/path/to/outputfile_{channel}_%Y%m%d_%H%M.nc",
                        required=False, help='Provide filename of output. If several timestamps are selected, it is'
                                             'recommended to provide a filename format, otherwise the file is over'
                                             'written each time. Valid formaters are %Y, %m, %d, {N1}, {N2}, {E1},'
                                             '{E2}, {channel}.')

    parser.add_argument('-d', '--date', metavar="YYYYMMDD-YYYYMMDD", help='Provide the desired date range to be processed. '
                                                                 'Format: YYYYMMDD-YYYYMMDD',
                        required=True, default=None)

    parser.add_argument('-r', '--region', nargs='+', metavar="lat0 lat1 lon0 lon1",
                        help='Provide the region for the output', required=True, type=int)

    parser.add_argument('-m', '--measurements', nargs='+', metavar="variable of dataset",
                        help='Provide the measurements that shall be downloaded', required=True)

    parser.add_argument('-u', '--username', metavar="username",
                        help='Provide your EOSDIS username', required=True)

    parser.add_argument('-p', '--password', metavar="password",
                        help='Provide your EOSDIS password', required=True)

    args = vars(parser.parse_args())

    return args

def download_all_available_URLS():
    """
    Crawls the opendap server to find
    all data urls

    Note: It would be nicer to create the
    urls directly, but the last sequence of
    digits is (to my knowledge) hard to know
    beforehand.
    """
    urls = []
    baseurl = 'https://acdisc.gesdisc.eosdis.nasa.gov/opendap/'
    subfolder = 'Aqua_AIRS_Level3/AIRS3STD.006/{year}/'

    for year in np.arange(2002, dt.datetime.now().year):
        # Get webpage content
        r = requests.get(baseurl + subfolder.format(year=year))
        filenames = np.unique(re.findall('AIRS.{51}hdf', r.text))  # 51 letters between 'AIRS' and 'hdf'
        for filename in filenames:
            urls.append(baseurl + subfolder.format(year=year) + filename)
    return urls


def create_url_lookup(urls):
    """
    Create look-up table for urls
    """
    lookup_dict = {}

    for url in urls:
        year = int(url[87:91])
        month = int(url[92:94])
        day = int(url[95:97])
        lookup_dict[dt.datetime(year, month, day)] = url
    return lookup_dict


def subset_dataset(ds_in, variables, sat_region):
    """
    Subset dataset and select only specific
    variables

    Returns:
    ds_out : xr.Dataset
        Subset of original dataset
    """
    # Create empty dataset
    ds_out = xr.Dataset()

    # Check if variable du exist in dataset
    for var in variables:
        assert var in ds_in.data_vars, f'Choose only variables from {ds_in.data_vars}'

    for var in variables:
        ds_out[var] = ds_in[var].sel(
            {'Longitude': slice(sat_region.lon0, sat_region.lon1), 'Latitude': slice(sat_region.lat1, sat_region.lat0)})

    return ds_out


def compress_dataset(ds, compression=4):
    """
    Compress dataset by using the
    internal compression of netCDF
    """
    for var in ds.data_vars:
        ds[var].encoding = {'zlib':True, 'compression':compression}
    return ds


def add_time_dimension(ds, times):
    """
    Time dimension is added to the dataset

    Input
    -----
    ds : xr.Dataset
        Dataset with missing time dimension
    times : datetime
        Times that will span the time dimension

    Returns
    -------
    ds_out : xr.Dataset
        Dataset with time dimension
    """
    ds_out = ds

    for var in ds.data_vars:
        ds_out[var] = ds[var].expand_dims({'time':[times]})

    return ds_out


def add_metadata(ds, url):
    """
    Add metadata to dataset
    """
    ds.attrs['title'] = 'Subset of AIRS Level3 data'
    ds.attrs['created_with'] = __file__
    ds.attrs['created_on'] = dt.datetime.now().strftime('%Y%m%d %H%M')
    ds.attrs['source'] = url

    return ds


def get_data_from_url(url, date, settings):
    """
    Worker function that
        - accesses url
        - subset data
        - download data
        - write compressed output to disk
    """
    # Create session
    with setup_session(settings["eosdis_username"],
                       settings["eosdis_password"],
                       check_url=url) as session:
        # Open remote dataset
        store = xr.backends.PydapDataStore.open(url, session=session)
        ds_in = xr.open_dataset(store)

        # Subset dataset
        ds_subset = subset_dataset(ds_in,
                                   settings["vars_of_interest"],
                                   settings["sat_region"])

        # Add time dimension
        ds_subset = add_time_dimension(ds_subset, date)

        # Compress dataset
        ds_subset = compress_dataset(ds_subset)

        # Add metainformation
        ds_subset = add_metadata(ds_subset, url)

        # Write dataset to disk
        ds_subset.to_netcdf("AIRS__{time}.nc".format(time=date.strftime('%Y%m%d')), unlimited_dims=['time'])


def main():
    args = get_args()

    settings = {}
    settings["eosdis_username"] = args["username"]
    settings["eosdis_password"] = args["password"]
    settings["vars_of_interest"] = args["measurements"]

    #lat0, lat1, lon0, lon1 = (10, 20, -62, -52)
    region = namedtuple('region', ["lat0", "lat1", "lon0", "lon1"])
    settings["sat_region"] = region(int(args["region"][0]),
                                    int(args["region"][1]),
                                    int(args["region"][2]),
                                    int(args["region"][3]))

    start_date = dt.datetime.strptime(args["date"].split("-")[0], "%Y%m%d")
    stop_date = dt.datetime.strptime(args["date"].split("-")[1], "%Y%m%d")
    dates = pd.date_range(start_date, stop_date)

    print('Gathering data urls')
    urls = download_all_available_URLS()
    url_lookup = create_url_lookup(urls)

    print('Start downloading data')
    for d, date in enumerate(tqdm.tqdm(dates)):
        # Get data url for date
        try:
            url = url_lookup[date]
        except KeyError:
            print(f'No url could be found for date {date}')
            continue
        get_data_from_url(url, date, settings)

if __name__ == "__main__":
    main()
