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
- `images\` - for images of this documentation
- `DEM\` - for digital elevation models
- `RASTER\` - for the raster background of the map
- `HOUSES\` - for vector layers of urban houses
- `MEGAPHONES\` - for points locations of loudspeakers

4. You can run our scripts immediately, because all folders contains sampla data (fake, but it is enough to demonstration).



## What i need prepare to modeling?

### Digital elevation model of earth's surface

1. You need to download ASTER GDEM or SRTM [digital elevation model](https://en.wikipedia.org/wiki/Digital_elevation_model) model. Both of these models are approximately the same accuracy. You can read more about the comparison of these models [here](https://visioterra.fr/telechargement/A003_VISIOTERRA_COMMUNICATION/HYP-082-VtWeb_SRTM_ASTER-GDEM_local_statistics_comparison.pdf) or [here](https://www.e3s-conferences.org/articles/e3sconf/pdf/2020/66/e3sconf_icgec2020_01027.pdf)

    #### 1.1. ASTER GDEM

    Do these steps to download ASTER GDEM for your city:

    1.1.1. Go to https://gdemdl.aster.jspacesystems.or.jp/index_en.html

    1.1.2. Select rectangle area of required territory

    1.1.3. Download one or more DEM fragments
    
    ![ASTER GDEM download](https://github.com/st-korn/urbanmegaphone/blob/main/images/astergdem-download.png?raw=true)

    1.1.4. You will download ZIP-archive with two sub-archives. One version 001 and one version 003:

    ![ASTER GDEM archive](https://github.com/st-korn/urbanmegaphone/blob/main/images/astergdem-archive.png?raw=true)

    1.1.5. We need version 003. Unpack it and put `ASTGTMV003_NxxEyyy_dem.tif` to `DEM\` folder of your project.
    
    ![ASTER GDEM v003](https://github.com/st-korn/urbanmegaphone/blob/main/images/astergdem-v003.png?raw=true)
