# ============================================
# Module: Read raster and DEM data and calculate wolrd bounds
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


# ============================================
# Read .tif files of RASTER and DEM models
# Find the dimensions of the world being explored
# ============================================
def ReadWorldBounds():

    # Use global variables
    global boundsMin, boundsMax, bounds

    logger.info("Find the dimensions of the world being explored")

    logger.info("Loop through raster files")

    for file in Path('.',folderRaster).glob("*.tif", case_sensitive=False):

        # Open GeoTIFF and conver coordinates to Web-Mercator
        gtf = GeoTiff(file, as_crs=3857)
        
        logger.debug("{file}: ESPG:{proj} {box} => {projected}", file=file.name, proj=gtf.crs_code, box=gtf.tif_bBox, projected=gtf.tif_bBox_converted)
        
        # Find total bounds of all rasters
        box = gtf.tif_bBox_converted
        for i in [0,1]:
            if boundsMin[i] is None: boundsMin[i] = box[0][i]
            if box[0][i] < boundsMin[i]: boundsMin[i] = box[0][i]
            if box[1][i] < boundsMin[i]: boundsMin[i] = box[1][i]
            if boundsMax[i] is None: boundsMax[i] = box[0][i]
            if box[0][i] > boundsMax[i]: boundsMax[i] = box[0][i]
            if box[1][i] > boundsMax[i]: boundsMax[i] = box[1][i]
    
    logger.success("Bounds of rasters: {} - {}", boundsMin, boundsMax)

    logger.info("Loop through DEM files")

    for file in Path('.',folderDEM).glob("*.tif", case_sensitive=False):

        # Open GeoTIFF and conver coordinates to Web-Mercator
        gtf = GeoTiff(file, as_crs=3857)
        
        logger.debug("{file}: ESPG:{proj} {box} => {projected}", file=file.name, proj=gtf.crs_code, box=gtf.tif_bBox, projected=gtf.tif_bBox_converted)

        # Read intersection DEM and Raster bounds
        dem = np.array(gtf.read_box([( max([boundsMin[0], gtf.tif_bBox_converted[0][0]]), min([boundsMax[1], gtf.tif_bBox_converted[0][1]]) ),
                                     ( min([boundsMax[0], gtf.tif_bBox_converted[1][0]]), max([boundsMin[1], gtf.tif_bBox_converted[1][1]]) ) ]))
        logger.debug("DEM intersection dimensions: {}", dem.shape)
        logger.trace(dem)

        # Find lowrest and highest value of DEM heights
        minZ = np.min(dem).item()
        maxZ = np.max(dem).item()
        if boundsMin[2] is None: boundsMin[2] = minZ
        if minZ < boundsMin[2]: boundsMin[2] = minZ
        if boundsMax[2] is None: boundsMax[2] = maxZ
        if maxZ < boundsMax[2]: boundsMax[2] = maxZ
        logger.debug("Lowrest point: {}m, highest point {}m", minZ, maxZ)

    logger.success("Bounds of our world:  {} - {}", boundsMin, boundsMax)

    # Calculate bounds of voxel's world
    for i in [0,1,2]:
        bounds[i] = int(np.ceil((boundsMax[i] - boundsMin[i]) / sizeVoxel).item())
    
    logger.success("Bounds of voxel's world:  {}", bounds)


# ============================================
# Accept two or three coordinates in meters
# and return two or three integer coordinates
# ============================================
'''
def coordM2Int(meters):
    ints = []
    for i in range(len(meters)):
        ints.append( int(np.round( (meters[i]-boundsMin[i])/sizeVoxel ).item()) )
    return ints
'''

# ============================================
# Accept two or three coordinates in meters
# and return two or three float coordinates of integer space (without rounding)
# ============================================
def coordM2Float(meters):
    floats = []
    for i in range(len(meters)):
        floats.append( float( (meters[i]-boundsMin[i])/sizeVoxel ) )
    return floats