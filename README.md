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

Example of downloading the latest data of the level 2 AOD product:
```bash
GOES16_download -d 20200117 -r 10 20 -60 -50 -o ./GOES16__{channel}__{N1}N-{N2}N_{E1}E-{E2}E__%Y%m%d_%H%M.nc -t 0 0 -p ABI-L2-AODF -k AOD
```

## AIRS
Example to download AIRS Level3 data:
```bash
AIRS_download -d 20180101-20180102 -r 10 20 -62 -52 -m Temperature_A H2O_MMR_A Temperature_D H2O_MMR_D -u <username> -p <password>
```

## GridsatB1
Example to download GridsatB1 data:
```bash
GridsatB1_download -y 2020 -m 01 02 -r 5 25 -63 -43 -o ./Gridsat-B1__5-25N_-63--43E__%Y%m%d.nc
```
