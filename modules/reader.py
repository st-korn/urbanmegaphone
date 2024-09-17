# ============================================
# Module: Read all data from files to memory
# ============================================

# Modules import
# ============================================

# Standart modules
import logging # Write log
from pathlib import Path # Crossplatform pathing
from geotiff import GeoTiff # GeoTIFF format reader

# Own core modules
from modules.settings import * # Settings defenition
from modules.environment import * # Environment defenition


# ============================================
# Read .tif files of RASTER and DEM models
# Find the dimensions of the world being explored
# ============================================
def ReadWorldBounds():

    # Use global variables
    global boundsMin, boundsMax

    logging.info("Find the dimensions of the world being explored")

    logging.info("Loop through raster files")

    for file in Path('.',folderRaster).glob("*.tif", case_sensitive=False):

        # Open GeoTIFF and conver coordinates to Web-Mercator
        gtf = GeoTiff(file, as_crs=3857)
        
        logging.debug(file.name, "ESPG:", gtf.crs_code, gtf.tif_bBox, " => ", gtf.tif_bBox_converted)
        
        # Find total bounds of all rasters
        box = gtf.tif_bBox_converted
        for i in [0,1]:
            if boundsMin[i] is None: boundsMin[i]=box[0][i]
            if box[0][i] < boundsMin[i]: boundsMin[i] = box[0][i]
            if box[1][i] < boundsMin[i]: boundsMin[i] = box[1][i]
            if boundsMax[i] is None: boundsMax[i]=box[0][i]
            if box[0][i] > boundsMax[i]: boundsMax[i] = box[0][i]
            if box[1][i] > boundsMax[i]: boundsMax[i] = box[1][i]
    
    logging.debug("Bounds of rasters:", boundsMin, boundsMax)

    logging.info("Bounds of our world:", boundsMin, boundsMax)
