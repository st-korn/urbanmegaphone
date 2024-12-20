![Loudspeakers of a city warning system on the roof of a house](/images/logo3.png)

- [How to run it?](#how-to-run-it)
- [How it works?](#how-it-works)
    - [1. Files and folders](#1-files-and-folders)
    - [2. Coordinate system](#2-coordinate-system)
    - [3. The arrangement of voxels in computer memory](#3-the-arrangement-of-voxels-in-computer-memory)
    - [4. Building the Earth's surface](#4-building-the-earths-surface)
    - [5. Stretching the texture onto the earth's surface](#5-stretching-the-texture-onto-the-earths-surface)
- [What i need prepare to my own modeling?](#what-i-need-prepare-to-my-own-modeling)
    - [1. Digital elevation model of earth's surface](#1-digital-elevation-model-of-earths-surface)
        - [1.1. ASTER GDEM](#11-aster-gdem)
        - [1.2. SRTM](#12-srtm)
        - [1.3. Comparison of ASTER GDEM and SRTM models](#13-comparison-of-aster-gdem-and-srtm-models)
    - [2. Raster map for background](#2-raster-map-for-background)
    - [3. Vector map of buildings](#3-vector-map-of-buildings)
        - [3.1. OpenStreetMap (osm.org)](#31-openstreetmap-osmorg)
        - [3.2. dom.gosuslugi.ru](#32-domgosuslugiru)
        - [3.3. pkk.rosreestr.ru](#33-pkkrosreestrru)
        - [3.4. geocode-maps.yandex.ru](#34-geocode-mapsyandexru)
        - [3.5. Combine received information](#35-сombine-received-information)

# How to run it?

1. Please, install `python 3` from https://www.python.org/

2. Install `vtk` library for python https://vtk.org/ and several others via:
    ```console
    pip install vtk
    pip install tifffile
    pip install pyproj
    pip install zarr
    pip install loguru
    pip install imagecodecs
    ```
    For getting vector map of buildings you need also:
    ```console
    pip install httpx
    pip install osmium
    pip install geojson
    pip install textdistance
    pip install pandas
    pip install geopandas
    pip install tqdm
    ```
    We use own copy in `modules` folder of python [`geotiff`](https://github.com/KipCrossing/geotiff.git) library, because our [pull request](https://github.com/KipCrossing/geotiff/pull/74) has not been processed yet. If you already have this library installed, please uninstall it.

3. Clone this repository. In any folder run:
    ```console
    git clone https://github.com/st-korn/urbanmegaphone.git
    ```

3. Run our script immediately, because all folders contains sampla data (fake, but it is enough to demonstration):
    ```console
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

- `WGS 84` aka `EPSG:4326` - degrees on WGS'84 datum for [DEM Models](#1-digital-elevation-model-of-earths-surface) This projection is automatically converted to `ESPG:3857` when DEM's images opening. \
\
![WGS 84 projection](/images/coord1.png)

- `ESPG:3857` - Metric Web-Mercator's projection. It has conversion formulas for a sphere, but applies them to WGS'84 datum ellipsoid. [See more](https://en.wikipedia.org/wiki/Web_Mercator_projection). All meridians are vertical, all parallels are horizontal. This projection is used for [raster background](#2-raster-map-for-background).
These two projections have a very distant coordinate center located in the Atlantic Ocean. 
Note that northern points have a higher `latitude` coordinate value than southern points.\
\
![Web-Mercator's projection](/images/coord2.png)

- When we work with raster image, we operate local coordinat system of pixels. They have two dimensions `x,y`. Coordinate center is left-top pixel of raster image. Here northern points have a lower `y` coordinate value than southern points.\
\
![Raster's pixel coordinate system](/images/coord3.png)

- Internal integer coordinate system of primitive voxel wolrd. We find lowrest `x,y,z` coordinates and put then in `(0,0,0)` of our new world. Then we use an accuracy value (default `3m`) for an voxel edge. The whole world is built from these voxels. All world details smaller than half a voxel edge are considered as an inaccuracy and are ignored.\
\
![Voxel's world coordinate system](/images/coord4.png)

- Render window of **Visualization ToolKit** library has its own coordinate system. `y`-axis is directed upwards. Horizontal `z`-axis is directed right at us. Coordinate values in VTK's coordinate system equals internal integer coordiates. But they don't have to be integers. They can take real values if needed. For example, to more accurately display the relief of the earth's surface.\
\
![VTK's 3D rendering coordinate system](/images/coord5.png)
<sub><sup>3D-city designed by [Freepik](www.freepik.com)</sup></sub>

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

## 4. Building the Earth's surface

First, we loop through the [raster files](#2-raster-map-for-background) in the `RASTER` directory. We get bounds if `ESPG:3857` of each file, and calculate boundaries `[lon,lat]` of our world. Raster files are the main thing that the program starts from when building the world.

![Earth ground from raster tiles](/images/screen1.png)

Next loop through [Digital elevation model files](#1-digital-elevation-model-of-earths-surface) in `DEM` directory. For each file calculate the intersection between raster and DEM files. We collect all DEM points of intersection to VTK point cloud. Next we use these point to buld surface with the help of PhD work [Hugues Hoppe](https://hhoppe.com/)

![DEM of Caucasus](/images/screen2.png)

Light spheres on the image means source points of DEM raster data. Dark spheres means points of generated aproximated surface. If you want, you can turn on the display of those points using a setting `flagShowEarthPoints` in the module `settings.py`

![DEM of Caucasus with points of surfaces](/images/screen3.png)

## 5. Stretching the texture onto the earth's surface

Next step, we put raster tiles map on the earth surface. For each point of the generated surface we determine the plane coordinates of the corresponding raster map image. Thus, we stretch the raster to the elevation differences of the terrain.

![Put texture on earth surface](/images/texture3.png)

As result we got an earth surface with raster map above it

![Caucasus relief](/images/gunib.gif)


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

### 1.3. Comparison of ASTER GDEM and SRTM models

ASTER GDEM is more granular than the SRTM model. SRTM is more smoothed than ASTER GDEM model. However, there are no crucial differences between this models. I like to use in my project SRTM models, because they are a little more beautiful.

![ASTER GDEM vs SRTM](/images/ASTERvsSRTM.png)

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

You need a GeoJSON with all buildings of your city. It is based on international [OpenStreetMap](https://osm.org/) data. But OpenStreetMap contains insufficient information of building's floors and no information about count of flats. Still 2024 year most buildings in OpenStreetMap have tag `building=yes` without defenition of building's type (residential or commercial).

We download OpenStreetMap data, and than complementing it with number of floors and count of flats of each building.

### 3.1. OpenStreetMap (osm.org)

Original [OpenStreetMap site](https://osm.org) can export only 50.000 objects at once. You need to go on [download.geofabrik.de](https://download.geofabrik.de/), select your continent, country and region and download `.osm.pbf` file for it.

Create in `get-buildings/` sub-folder with your city name. For example `get-builings/lipetsk/`. Put downloaded `.osm.pbf` file in this created folder.

Edit `get-buildings/01-pbf-to-geojson.py` script for paths for source `.osm.pbf` file and destination `.osm.geojson` file:

```python
pbf_file = Path.cwd() / 'get-buildings' / 'gunib' / 'north-caucasus-fed-district-latest.osm.pbf'
json_file = Path.cwd() / 'get-buildings' / 'gunib' / 'gunib.osm.geojson'
```

Run `get-buildings/01-pbf-to-geojson.py` script from root folder of a project to generate `.osm.geojson` file with OSM's buildings of your raster area. All other buildings, not included in these areas, will be discarded.

![Convert pbf to GeoJSON](/images/pbf-to-geojson2.png)

You can load `.osm.geojson` file in [QGIS](https://qgis.org/) desctop application for see its geometry and properties:

![See .osm.geojson in QGIS](/images/qgis2.png)

Vector building features of `.osm.geojson` file may have the following properties:
- `building` (string) - type of building by [OSM building's codification](https://wiki.openstreetmap.org/wiki/Key:building)
- `osm-street` (string) - street name, if exist
- `osm-housenumber` (string) - house number name, if exist
- `osm-levels` (integer) - count of building's levels, if exist

### 3.2. dom.gosuslugi.ru

In Russia Federation you can start at [ГИС ЖКХ](dom.gosuslugi.ru) - public information system about housing and communal services. If there are no such service in your county, you can add this information manual later.

Run `get-buildings/11-get-regions.py` script to collect UUIDs of Russia regions:

![Regions of Russia Federation](/images/get-regions.png)

Paste this UUID into first line of `get-buildings/12-get-region-cities.py` script:

```python
region = '0bb7fa19-736d-49cf-ad0e-9774c4dae09b'
```

and run it:

![List of cities and villages](/images/get-cities2.png)

First you got UUIDs of central cities, next - UUIDs of area's cities, than - UUIDs of area's other settlements. Find line you need.

Next go to `get-buildings/13-get-buildings.py` and change its first lines:

```python
region = '0bb7fa19-736d-49cf-ad0e-9774c4dae09b'
area = '47e1fc4c-4ad1-4d03-91f7-981184adcbe7'
city = None
settlement = '36022007-8503-4d34-92d9-cc82dfb7a496'
resultdir = Path.cwd() / 'get-buildings' / 'gunib'
```

Change here `region` code.
For central city write `city` code and write `None` to `area` and `settlement`.
For area's cities write `area` and `city` codes, and put `None` to the `settlement`.
For other settlements write `area` and `settlement` code and put `None` to the `city`.

| Category | region | area | city | settlement |
| -------- | ------ | ---- | ---- | ---------- |
| Central city | &check; | None | &check; | None |
| Area's city | &check; | &check; | &check; | None |
| Other settlement | &check; | &check; |  None | &check; |

Be sure to write correct name of folder to download building information in `resultdir` variable.

The script will get territories and streets of the city and than loop throgh them and fetch buildings for each.

![Getting buildings](/images/get-buildings.png)

If you are unexpectedly blocked, you got `403 error`. Than remove last incorrect `.json` files 871 bytes length. Wait few minutes and just restart script. It will be continued.

![403 blocked](/images/get-buildings2.png)

This script create in your forlder these files:

![Files of buildings](/images/get-buildings3.png)

- `territories.json` and `streets.json` - list of territories and streets
- `UUID-1.json` - first 100 (or less) buildings of the territory or street
- `UUID-2.json`, `UUID-3.json` and more - next 100 (or less) buildings

After this step, run `get-buildings/14-collect-buildings.py` to collect all buildings from JSON files to one `houses.dom.gosuslugi.ru.json` file.

Edit folder path at the beginning of the script:

```python
folder = Path.cwd() / 'get-buildings' / 'lipetsk'
```

Than run it. Script will print names of found JSON files. At the end of work script print total count of buildings, which are collected.

![Collect buildings](/images/collect-buildings.png)

`houses.dom.gosuslugi.ru.json` file contains list of the buildings:

```json
[
    {
        "fias": "0014d723-fc40-4de4-8084-b328af4e1e8d",
        "address": "398902, обл Липецкая, г Липецк, ул Металлистов, д. 1",
        "cadastre": "48:20:0011206:64",
        "type": "Многоквартирный",
        "floors": 2,
        "flats": 8
    },
    {
        "fias": "0014d723-fc40-4de4-8084-b328af4e1e8d",
        "address": "398902, обл Липецкая, г Липецк, ул Металлистов, д. 2",
        "cadastre": null,
        "type": "Жилой",
        "floors": 1,
        "flats": 1
    },
```
Buildings have the following properties:
- `fias` - unique ID of address
- `address` - full address of building as string
- `cadastre` - unique goverment ID of building (if exist)
- `type` - type of building
- `floors` - count of floors of building
- `flats` - count of flats in the building (`null` if all building is one flat)

### 3.3. pkk.rosreestr.ru

Next source, who can get geographic coordinates by unique goverment cadastreID of building in Russia Federation is the online [Public Cadastral Map](https://pkk.rosreestr.ru/).

First open `get-buildings/21-ask-coordinates.py` and edit workfolder path:

```python
folder = Path.cwd() / 'get-buildings' / 'lipetsk'
```

Next run the script. It read houses from `houses.dom.gosuslugi.ru.json`, and than make HTTP-reuest to `pkk.rosreestr.ru` for each house with cadastre ID. If `pkk.rosreestr.ru` known geographic coordinates of building - they are stored in `pkk.txt` file. If geographic coordinates are unknown - in `pkk.txt` stored blank line.

![Ask pkk.rosreestr.ru](/images/ask-pkk.png)

The file `pkk.txt`is needed to continue fetch coordinates if `pkk.rosreestr.ru` is banned your requests. It is 1 secopnd pause after each request to to prevent the ban.

### 3.4. geocode-maps.yandex.ru

Next source popular in Russia is Yandex maps service. There are commercial geocoder API of this service. You can read API documentation [here](https://yandex.ru/dev/geocode/doc/ru/)

You need to register at [Yandex developer cabinet](https://developer.tech.yandex.ru/), add service `JavaScript API and HTTP Geocoder`, create your personal API key for it. You can make 1000 free requests. Next you must pay $160 per month (1000 requests/day) and $3 per 1000 additional requests.

Put your API key and your folder path on the head of `get-buildings/31-ask-coordinates.py` script:

```python
folder = Path.cwd() / 'get-buildings' / 'lipetsk'
APIkey = '12345678-1234-1234-1234-1234567890ab'
```
Then run `get-buildings/31-ask-coordinates.py` script. It will create subfolder `yandex` and put them files like `00b11c4a-0730-4336-97a1-e94a4afd3c08.json` with UUID of building in name and JSON geocoder response in content. Buildings with coordinates from `pkk.rosreestr.ru` are skiped.

![Ask geocode-maps.yandex.ru](/images/ask-yandex.png)

Example of geocoder response:
```json
    "name": "улица Пожарского, 57",
    "description": "Липецк, Россия",
    "boundedBy": {
        "Envelope": {
            "lowerCorner": "39.655077 52.642789",
            "upperCorner": "39.663288 52.647783"
        }
    },
    "uri": "ymapsbm1://geo?data=Cgg1NjUxMDU4ORI_0KDQvtGB0YHQuNGPLCDQm9C40L_QtdGG0LosINGD0LvQuNGG0LAg0J_QvtC20LDRgNGB0LrQvtCz0L4sIDU3IgoNAKMeQhXHlFJC",
    "Point": {
        "pos": "39.659182 52.645286"
    }
```

Then open `32-fix-and-collect.py` and edit your folder path on its head:

```python
folder = Path.cwd() / 'get-buildings' / 'lipetsk'
```

Run it to make two things. First this script loop throught yandex's json responses and select from each the most relevated address point. We can not use the first address point as the most relevanted, because yandex has now a bug in an algorithm estimation of similarity of text phrases. For example:

We ask yandex to geocode string:
`398916, обл Липецкая, г Липецк, ул Ленина (Желтые Пески), д. 9`

Probably yandex use an edit-based [Levenshtein distance](https://en.wikipedia.org/wiki/Levenshtein_distance) algorithm to find point on map, whose address has minimum edit steps to to be transformed to request's address:

| Suggested address | Levenshtein distance |
| ------------------| -------------------- |
| `Россия, Липецк, улица Ленина, 9` | `0.3548387096774194` |
| `Россия, Липецк, микрорайон Жёлтые Пески, улица Ленина, 9` | `0.29032258064516125` |
| `Россия, Липецк, микрорайон Ссёлки, улица Ленина, 9` | `0.29032258064516125` |
| `Россия, Липецк` | `0.17741935483870963` |

By the Levenshtein distance, the most relevated address to `398916, обл Липецкая, г Липецк, ул Ленина (Желтые Пески), д. 9` is `Россия, Липецк, улица Ленина, 9`. And the address `Россия, Липецк, микрорайон Жёлтые Пески, улица Ленина, 9` is less relevant than that one.

We test all distance functions of the python [`textdistance` library](https://pypi.org/project/textdistance/). An token-based [Cosine similarity](https://en.wikipedia.org/wiki/Cosine_similarity) get the best result for the task of finding the most relevated address:

| Suggested address | Levenshtein distance |
| ------------------| -------------------- |
| `Россия, Липецк, улица Ленина` | `0.6614869888519316` |
| `Россия, Липецк, микрорайон Жёлтые Пески, улица Ленина, 9` | `0.7127864449672372` |
| `Россия, Липецк, микрорайон Ссёлки, улица Ленина, 9` | `0.6286185570937122` |
| `Россия, Липецк` | `0.4073065399812784` |

Resume: Cosine similarity works better for evaluation address similarity, than Levenshtein distance.

Second thing, this script does is transformation coordinated from degrees `WGS-84` to meters `Web-Mercator projection` and collecting coordinates in file `yandex.json` as one big dictionary. Keys are FIAS-codes of houses and values are arrays of two coordinates:

```json
    "0002c3ad-a714-4a81-a4a1-915ca8e124fe": [
        4404403.965894873,
        6905315.453945883
    ],
    "000e9f09-5403-46a4-85c5-1da806a1fbbc": [
        4414974.976060093,
        6918007.910298051
    ],
```

### 3.5. Combine received information

Next step we combine all recieved information into one big GeoJSON file. Run `get-buildings/41-add-points-to-geojson.py` script.

It collect cadastre building dinates