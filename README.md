# Urban megaphone
3D-modeling of sound wave coverage among urban houses

![Loudspeakers of a city warning system on the roof of a house](https://github.com/st-korn/urbanmegaphone/blob/main/images/photo.jpg?raw=true)\
<sub><sup>Photo by Petr Kovalev, TASS</sup></sub>

## How it works?


## What i need to use this product?

1. Please, install `python 3` from https://www.python.org/

2. Install `vtk` library for python https://vtk.org/ via:
    ```
    pip install vtk
    ```

3. Clone this repository. In any forlder do:
    ```
    git clone https://github.com/st-korn/urbanmegaphone.git
    ```

    This action will create folder `urbanmegaphone` with two !!!files:
- `prepare.py` - script to preparation and generation 3D-model
- `show.py` - script for displaying the prepared model

    and folders:
- `images/` - for images of this documentation
- `DEM/` - for digital elevation models
- `RASTER/` - for the raster background of the map
- `HOUSES/` - for vector layers of urban houses
- `MEGAPHONES/` - for points locations of loudspeakers

4. You can run our scripts immediately, because all folders contains sampla data (fake, but it is enough to demonstration).

!!! Screen of run every command


## What i need prepare to modeling?

### 1. Digital elevation model of earth's surface

You need to download ASTER GDEM or SRTM [digital elevation model](https://en.wikipedia.org/wiki/Digital_elevation_model) model. Both of these models are approximately the same accuracy. You can read more about the comparison of these models [here](https://visioterra.fr/telechargement/A003_VISIOTERRA_COMMUNICATION/HYP-082-VtWeb_SRTM_ASTER-GDEM_local_statistics_comparison.pdf) or [here](https://www.e3s-conferences.org/articles/e3sconf/pdf/2020/66/e3sconf_icgec2020_01027.pdf)

#### 1.1. ASTER GDEM

Do these steps to download ASTER GDEM for your city:

1.1.1. Go to https://gdemdl.aster.jspacesystems.or.jp/index_en.html

1.1.2. Select rectangle area of required territory

1.1.3. Download one or more DEM fragments

![ASTER GDEM download](https://github.com/st-korn/urbanmegaphone/blob/main/images/astergdem-download.png?raw=true)

1.1.4. You will download ZIP-archive with two sub-archives. One version 001 and one version 003:

![ASTER GDEM archive](https://github.com/st-korn/urbanmegaphone/blob/main/images/astergdem-archive.png?raw=true)

1.1.5. We need version 003. Unpack it and put `ASTGTMV003_NxxEyyy_dem.tif` to `DEM/` folder of your project

![ASTER GDEM v003](https://github.com/st-korn/urbanmegaphone/blob/main/images/astergdem-v003.png?raw=true)

#### 1.2. SRTM

Do these steps to download SRTM DEM for your city:

1.2.1. Go to [USGS Earth Explorer](https://earthexplorer.usgs.gov/)

1.2.2. Login or create new NASA account (answer on some questions about your job)

1.2.3. Position the map on your city and click `Use map` button on `Polygon` tab:

![SRTM use map to define rectangly area](https://github.com/st-korn/urbanmegaphone/blob/main/images/srtm-select.png?raw=true)

1.2.4. Zoom out and drag the four vertices of the polygon to make it better encircle the city. On finish click `Data Sets >>`

![SRTM manaully editing the polygon](https://github.com/st-korn/urbanmegaphone/blob/main/images/srtm-edit.png?raw=true)

1.2.5. On the left tree, expand leaf `Digital Elevation`, then expand leaf `SRTM` and select `SRTM 1 Arc-Second Global` dataset, then click `Results >>`

![SRTM selecting required dataset of DEM](https://github.com/st-korn/urbanmegaphone/blob/main/images/srtm-edit.png?raw=true)

1.2.6. Earth Explorer will found one or more datasets of selected area. For each dataset you can click `footprint` button to see area of dataset on the map. Then you click `download` button to download dataset file

![SRTM dataset preview](https://github.com/st-korn/urbanmegaphone/blob/main/images/srtm-preview.png?raw=true)

1.2.7. Next you get a window, which ask of downloaded file format. Select `GeoTIFF` format:

![SRTM download format selection](https://github.com/st-korn/urbanmegaphone/blob/main/images/srtm-download.png?raw=true)

1.2.8. You will receive file `nXX_eYYY_1arc_v3.tif`. Save it to `DEM/` folder of your project

![SRTM file](https://github.com/st-korn/urbanmegaphone/blob/main/images/srtm-v3.png?raw=true)

### 2. Raster map for background

You need to have raster tiles of map to put them on background of your city. There are many sources to get these tiles. We recomend you use [OpenStreetMap](osm.org) tiles.

2.1 Go to [SAS Planet site](https://www.sasgis.org/download/) and download the lastes stable version of `SAS Planeta`

2.2 Save archive into any folder, and then unzip it

![SAS Planet archive file](https://github.com/st-korn/urbanmegaphone/blob/main/images/sasplanet-source.png?raw=true)

2.3 Go to the `Maps \ sas.maps` folder and run `Update.cmd`. It will download settings for all currently aviable maps for SAS Planet

![SAS Planet script for maps update](https://github.com/st-korn/urbanmegaphone/blob/main/images/sasplanet-gotomap.gif?raw=true)

2.4 You will get this window while `git` working:

![SAS Planet maps updating](https://github.com/st-korn/urbanmegaphone/blob/main/images/sasplanet-mapupdate.png?raw=true)

2.5 Next you can run `SASPlanet.exe`:

![Run SAS Planet](https://github.com/st-korn/urbanmegaphone/blob/main/images/sasplanet-rum.png?raw=true)
