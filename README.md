![Loudspeakers of a city warning system on the roof of a house](/images/logo3.png)

- [How to run it?](#how-to-run-it)
- [How it works?](#how-it-works)
    - [ Files and folders](#1-files-and-folders)
    - [Coordinate system](#1-coordinate-system)
    - [The arrangement of voxels in computer memory](#2-the-arrangement-of-voxels-in-computer-memory)
- [What i need prepare to my own modeling?](#what-i-need-prepare-to-my-own-modeling)
    - [Digital elevation model of earth's surface](#1-digital-elevation-model-of-earths-surface)
    - [Raster map for background](#2-raster-map-for-background)
    - [Vector map of buildings](#3-vector-map-of-buildings)


# How to run it?

1. Please, install `python 3` from https://www.python.org/

2. Install `vtk` library for python https://vtk.org/ and several others via:
    ```
    pip install vtk
    pip install geotiff
    pip install loguru
    pip install imagecodecs
    ```

3. Clone this repository. In any forlder do:
    ```
    git clone https://github.com/st-korn/urbanmegaphone.git
    ```

3. Run our script immediately, because all folders contains sampla data (fake, but it is enough to demonstration):
    ```
    cd urbanmegaphone
    ./urbanmegaphone.py
    ```


# How it works?

## 1. Files and folders

Project folder contains these files and folders:
- `urbanmegaphone.py` - script to generation 3D-model and calculation alarm coverage
- `modules/` - python core modules
- `images/` - images of this documentation
- `DEM/` - digital elevation models
- `RASTER/` - raster background of the map
- `BUILDINGS/` - vector layers of urban buildings
- `MEGAPHONES/` - points locations of loudspeakers
!!! Screen of run every command


## 2. Coordinate system

Project work with three coordinate systems:

- `WGS 84` aka `EPSG:4326` - degrees on WGS'84 datum for [DEM Models](#1-digital-elevation-model-of-earths-surface)

- `ESPG:3857` - Metric Mercator's projection. It has conversion formulas for a sphere, but applies them to WGS'84 datum ellipsoid. [See more](https://en.wikipedia.org/wiki/Web_Mercator_projection). All meridians are vertical, all parallels are horizontal. This projection is used for [raster background](#2-raster-map-for-background).

- Internal integer coordinate system of primitive voxel wolrd. We find lowrest x,y,z coordinates and put then in (0,0,0) of our new world. Then we use an accuracy value (default `3m`) for an voxel edge. The whole world is built from these voxels. All world details smaller than half a voxel edge are considered as an error and are ignored.

![Parallel transfer the world to the new zero point of reference](/images/coordinates.png)\
<sub><sup>3D-city designed by [Freepik](www.freepik.com)</sup></sub>

![Voxel world](/images/voxels-grid5.png)

## 3. The arrangement of voxels in computer memory

We create one big 3D-array of `int32` by `numpy` library:
- first array's dimension is **longitude** of our world
- second array's dimension is **latitude** of our world
- third array's dimension is **height** of our world

Latitude and longitude are calculated from the whole set of tiles [background raster map](#2-raster-map-for-background).
Height calculates from the [digital elevation model of earth's surface](#1-digital-elevation-model-of-earths-surface) and by the height of the tallest building of [vector buildings map](#3-vector-map-of-buildings).

Signed `int32` values of array's cells means:
- **zero** if this cell does not contains anything
- **positive integer number** if this cell belongs to an **important object** (currently these are only **buildings**)
- **-1** if this cell belongs to the earth's surface
- **negative integer number** if this cell is located below earth's surface

![Each voxel contains an integer](/images/voxels5.png)

Positive integer numbers of voxel cells are links to flat array with Voxel class:

If `int32` is not enough to store information about all the important voxels in the world, it can be replaced with `int64`


# What i need prepare to my own modeling?

## 1. Digital elevation model of earth's surface

You need to download ASTER GDEM or SRTM [digital elevation model](https://en.wikipedia.org/wiki/Digital_elevation_model) model. Both of these models are approximately the same accuracy. You can read more about the comparison of these models [here](https://visioterra.fr/telechargement/A003_VISIOTERRA_COMMUNICATION/HYP-082-VtWeb_SRTM_ASTER-GDEM_local_statistics_comparison.pdf) or [here](https://www.e3s-conferences.org/articles/e3sconf/pdf/2020/66/e3sconf_icgec2020_01027.pdf)

### 1.1. ASTER GDEM

Do these steps to download ASTER GDEM for your city:

1.1.1. Go to https://gdemdl.aster.jspacesystems.or.jp/index_en.html

1.1.2. Select rectangle area of required territory

1.1.3. Download one or more DEM fragments

![ASTER GDEM download](/images/astergdem-download.png)

1.1.4. You will download ZIP-archive with two sub-archives. One version 001 and one version 003:

![ASTER GDEM archive](/images/astergdem-archive.png)

1.1.5. We need version 003. Unpack it and put `ASTGTMV003_NxxEyyy_dem.tif` to `DEM/` folder of your project

![ASTER GDEM v003](/images/astergdem-v003.png)

### 1.2. SRTM

Do these steps to download SRTM DEM for your city:

1.2.1. Go to [USGS Earth Explorer](https://earthexplorer.usgs.gov/)

1.2.2. Login or create new NASA account (answer on some questions about your job)

1.2.3. Position the map on your city and click `Use map` button on `Polygon` tab:

![SRTM use map to define rectangly area](/images/srtm-select.png)

1.2.4. Zoom out and drag the four vertices of the polygon to make it better encircle the city. On finish click `Data Sets >>`

![SRTM manaully editing the polygon](/images/srtm-edit.png)

1.2.5. On the left tree, expand leaf `Digital Elevation`, then expand leaf `SRTM` and select `SRTM 1 Arc-Second Global` dataset, then click `Results >>`

![SRTM selecting required dataset of DEM](/images/srtm-search.png)

1.2.6. Earth Explorer will found one or more datasets of selected area. For each dataset you can click `footprint` button to see area of dataset on the map. Then you click `download` button to download dataset file

![SRTM dataset preview](/images/srtm-preview.png)

1.2.7. Next you get a window, which ask of downloaded file format. Select `GeoTIFF` format:

![SRTM download format selection](/images/srtm-download.png)

1.2.8. You will receive file `nXX_eYYY_1arc_v3.tif`. Save it to `DEM/` folder of your project

![SRTM file](/images/srtm-v3.png)

## 2. Raster map for background

You need to have raster tiles of map to put them on background of your city. There are many sources to get these tiles. We recomend you use [OpenStreetMap](osm.org) tiles.

2.1. Go to [SAS Planet site](https://www.sasgis.org/download/) and download the lastes stable version of `SAS Planeta`

2.2. Save archive into any folder, and then unzip it

![SAS Planet archive file](/images/sasplanet-source.png)

2.3. Go to the `Maps \ sas.maps` folder and run `Update.cmd`. It will download settings for all currently aviable maps for SAS Planet

![SAS Planet script for maps update](/images/sasplanet-gotomap.gif)

2.4. You will get this window while `git` working:

![SAS Planet maps updating](/images/sasplanet-mapupdate.png)

2.5. Next you can run `SASPlanet.exe`:

![Run SAS Planet](/images/sasplanet-run.png)

2.6. In the SAS Planet window select menu `Maps -> City -> OSM OpenStreetMap.org - MAPNIK` map

![Change map in SAS Planet](/images/sasplanet-changemap.png)

2.7. Select rectangle area around your city:

![Draw rectangle area around your city](/images/sasplanet-rectangle.png)

2.8. Download all tiles on `18th` zoom `OSM Mapnik` map for your selected rectangle:

![Download tiles](/images/sasplanet-download.png)

2.9. Wait, while tiles are downloading...

![Progress window](/images/sasplanet-downloading.png)

2.10. Resume your last rectangular selection:

![Resume your selection](/images/sasplanet-lastselection.png)

2.11. Stich all tiles in some bitmaps. Select output format `GeoTIFF`. Put bitmaps on `RESULT/` folder with any filename, for example - your city name. Use `18th` zoom. Use `ESPG 3857` projection. Calculate number of tiles to split the resulting image so that each side of bitmap contains less than `10.000 pixels`. Use `TIFF` format without compression: LZW compression by SAS Planet causes an error exception in vtkTIFFReader.

![Stitch bitmaps](/images/sasplanet-stitch.png)

2.12. If you did everything correctly, the following set of files will appear in the `RESULT/` folder:

![Contents of the RESULT folder](/images/sasplanet-result.png)

## 3. Vector map of buildings
