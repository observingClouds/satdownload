"""
Download GridSatB1 satellite data and save subset

Author: Hauke Schulz
"""

import os
import sys
import time
import argparse
import logging
import numpy as np
from datetime import datetime
from siphon.catalog import TDSCatalog
from siphon.ncss import NCSS
import xarray as xr
from tqdm import trange


def get_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-o', '--outputfile', metavar="/path/to/outputfile_%Y%m%d_%H%M.nc",
                        required=False, help='Provide filename of output. If several timestamps are selected, it is'
                                             'recommended to provide a filename format, otherwise the file is over'
                                             'written each time. Valid formaters are %Y, %m, %d, {N1}, {N2}, {E1},'
                                             '{E2}.')

    parser.add_argument('-y', '--years', metavar="YYYY YYYY", help='Provide the years of interest'
                                                                   'Format: YYYY YYYY',
                        required=True, default=None, nargs='+', type=int)

    parser.add_argument('-m', '--months', metavar="MM MM", help='Provide the months of interest'
                                                                   'Format: MM MM',
                        required=True, default=None, nargs='+', type=int)

    parser.add_argument('-r', '--region', nargs='+', metavar="lat0 lat1 lon0 lon1",
                        help='Provide the region for the output', required=False, type=int, default=None)

    parser.add_argument('-v', '--verbose', metavar="DEBUG",
                       help='Set the level of verbosity [DEBUG, INFO, WARNING, ERROR]',
                       required=False, default="INFO")

    args = vars(parser.parse_args())

    return args


def setup_logging(verbose):
    assert verbose in ["DEBUG", "INFO", "WARNING", "ERROR"]
    logging.basicConfig(
        level=logging.getLevelName(verbose),
        format="%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
        handlers=[
            logging.FileHandler(f"{__file__}.log"),
            logging.StreamHandler()
        ])


# Settings


# define subset like [lat0, lat1, lon0, lon1] or
# None if the complete globe should be saved
# e.g. [-10, 65, -85, 10] for the North Atlantic
 # [-10, 65, -85, 10]

# define years if interst as array or list
# e.g. np.arange(2012, 2019)


CATALOG_URL_FMT = 'https://www.ncei.noaa.gov/thredds/catalog/cdr/gridsat/{}/catalog.xml'

# Module import



def compress_all_variables(dataset, compression=4):
    """
    Compress all variables and dimensions of dataset

    Input
    -----
    dataset : xr.dataset

    Return
    ------
    dataset : xr.dataset
        Dataset containing compressed variables and dimensions
        or more precisely the meta-information such that
        xr.to_netcdf will write a compressed file
    """
    for var in dataset.variables:
        dataset[var].encoding = {'zlib': True, 'complevel': compression}
    return dataset



def retrieve_general_metadata():
    """
    Get generally available metadata
    """
    metadata = {}
    created_with_fmt = '{} with its last modification on {}'
    metadata['created_with'] = created_with_fmt.format(os.path.basename(__file__),
                                     time.ctime(os.path.getmtime(os.path.realpath(__file__))))
    metadata['created_on'] = time.asctime()
    metadata['python_version'] = "{}".format(sys.version)
    return metadata


def add_metadata(ds, metadata={}):
    """
    Add additional metadata to netCDF output

    Input
    -----
    ds : xr.Dataset
        Dataset
    metadata : dict
        Metainformation to be added

    Return
    ------
    ds : xr.Dataset
        Dataset with additional metadata
    """

    for key, value in metadata.items():
        ds.attrs[key] = value

    return ds


def main():
    args = get_args()

    subset = args['region']
    years_of_interest = args['years']
    months_of_interest = args['months']
    if args['outputfile'] is None:
        outputpath = './GRIDSAT-B1_{lat0}-{lat1}N_{lon0}-{lon1}E_{time}.nc'
    else:
        outputpath = args['outputfile']

    setup_logging(args['verbose'])

    urls = []
    for year in years_of_interest:
        logging.info('Read catalog for year {}'.format(year))
        catalog = TDSCatalog(CATALOG_URL_FMT.format(year))
        logging.info("Catalog read.")
        for i in trange(len(catalog.datasets)):
            dataset = catalog.datasets[i]
            # Check if file has been downloaded already
            if ~np.in1d(dataset.url_path, urls):
                urls.append(dataset.url_path)
                if np.in1d(np.int(dataset.name.split(".")[2]), months_of_interest):
                    logging.info("Using dataset {}".format(dataset.name))
                    try:
                        ncss = dataset.subset()
                    except:
                        logging.warning('Query not successful for {}'.format(dataset.name))
                    try:
                        query = ncss.query().variables('irwin_cdr')
                    except:
                        logging.warning('Query not successful for {}'.format(dataset.name))
                    try:
                        nc = ncss.get_data(query)
                    except:
                        logging.warning('Runtime issue probably, skipping current date')
                        continue
                    data_xr = xr.open_dataset(xr.backends.NetCDF4DataStore(nc))

                    if subset is not None:
                        dataset_sel = data_xr.sel(
                            {
                                'lat': slice(subset[0], subset[1]),
                                'lon': slice(subset[2], subset[3])
                                })
                    else:
                        dataset_sel = data_xr
                        subset = [int(data_xr.lat.min().values),
                                  int(data_xr.lat.max().values),
                                  int(data_xr.lon.min().values),
                                  int(data_xr.lon.max().values)
                                  ]

                    t = dataset_sel.time.values[0]
                    t_str = datetime.utcfromtimestamp(t.astype('O')/1e9).strftime('%Y%m%d%H')

                    metadata = retrieve_general_metadata()
                    add_metadata(dataset_sel, metadata)
                    dataset_sel = compress_all_variables(dataset_sel, compression=6)
                    dataset_sel.to_netcdf(outputpath.format(time=t_str,
                                                                 lat0=subset[0],
                                                                 lat1=subset[1],
                                                                 lon0=subset[2],
                                                                 lon1=subset[3]))

if __name__ == "__main__":
    main()