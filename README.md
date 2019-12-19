# satdownload

Collection of scripts to download satellite data

## Installation

Install package with anaconda

```
conda create -n satdownload
conda activate satdownload
conda install -c observingClouds satdownload
```

## GOES16
Example of downloading the midnight image:
```bash
GOES16_download -d 20191217 -r 10 20 -60 -50 -k 13 -o ./out_%Y%m%d_%H%M.nc -t 24 60
```

## AIRS
Example to download AIRS Level3 data:
```bash
AIRS_download -d 20180101-20180102 -r 10 20 -62 -52 -m Temperature_A H2O_MMR_A Temperature_D H2O_MMR_D -u <username> -p <password>
```
