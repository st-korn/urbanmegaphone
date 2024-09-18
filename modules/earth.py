# ============================================
# Module: Read raster and DEM data and generate earth surface
# ============================================

# Modules import
# ============================================

# Standart modules
from loguru import logger # Write log
from pathlib import Path # Crossplatform pathing
from geotiff import GeoTiff # GeoTIFF format reader
import numpy as np # Work with DEM matrix

# Own core modules
from modules.settings import * # Settings defenition
from modules.environment import * # Environment defenition
from modules.bounds import * # Read raster and DEM data and calculate wolrd bounds


# ============================================
# Read .tif files of RASTER and DEM models
# Find the dimensions of the world being explored
# ============================================
def GenerateEarthSurface():

    # Use global variables
    global boundsMin, boundsMax, bounds

    logger.info("Generate earth surface")

    logger.info("Loop through raster files")

    for fileR in Path('.',folderRaster).glob("*.tif", case_sensitive=False):

        # Open GeoTIFF and conver coordinates to Web-Mercator
        gtfR = GeoTiff(fileR, as_crs=3857)
        boxR = gtfR.tif_bBox_converted
        
        logger.debug("{file}: ", file=fileR.name)
        
        for fileD in Path('.',folderDEM).glob("*.tif", case_sensitive=False):

            # Open GeoTIFF and conver coordinates to Web-Mercator
            gtfD = GeoTiff(fileD, as_crs=3857)
        
            # Read intersection DEM and Raster bounds
            dem = np.array(gtfD.read_box(boxR))
            lons, lats = gtfD.get_coord_arrays(boxR)

            logger.debug("{file} intersection: {dim} = ({lon} {lat})", file=fileD.name, dim=dem.shape, lon=lons.shape, lat=lats.shape)
            logger.trace(" ({},{}) = ({})",lons[0][0],lats[0,0],coordM2Int([lons[0][0],lats[0,0]]))

