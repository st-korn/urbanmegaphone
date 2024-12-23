# ============================================
# Module: Read raster and DEM data and calculate wolrd bounds
# ============================================

# Modules import
# ============================================

# Standart modules
from loguru import logger # Write log
from pathlib import Path # Crossplatform pathing
from modules.geotiff import GeoTiff # GeoTIFF format reader
import numpy as np # Work with DEM matrix
import pandas as pd
import geopandas as gpd

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

    # -------------------------------------------------------------------
    # Read bounds of raster files

    logger.info("Loop through raster files")

    for file in Path('.',folderRaster).glob("*.tif", case_sensitive=False):

        # Open GeoTIFF and conver coordinates to Web-Mercator
        gtf = GeoTiff(file, as_crs=3857)
        
        logger.debug("{file}: ESPG:{proj} {resolution}", file=file.name, proj=gtf.crs_code, resolution=gtf.tif_shape)
        logger.debug("   {box} =>", box=gtf.tif_bBox)
        logger.debug("   => {projected}", projected=gtf.tif_bBox_converted)
        
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

    # -------------------------------------------------------------------
    # Read bounds of DEM files in the intersecting part of rasters

    logger.info("Loop through DEM files")

    for file in Path('.',folderDEM).glob("*.tif", case_sensitive=False):

        # Open GeoTIFF and conver coordinates to Web-Mercator
        gtf = GeoTiff(file, as_crs=3857)
        
        logger.debug("{file}: ESPG:{proj} {resolution}", file=file.name, proj=gtf.crs_code, resolution=gtf.tif_shape)
        logger.debug("   {box} =>", box=gtf.tif_bBox)
        logger.debug("   => {projected}", projected=gtf.tif_bBox_converted)

        # Read intersection DEM and Raster bounds
        boxIntersection = ((boundsMin[0],boundsMax[1]),(boundsMax[0],boundsMin[1]))
        try:
            dem = np.array(gtf.read_box(boxIntersection))
        except Exception as e:
            logger.warning("DEM intersection not found: {}", e)
            continue
        logger.debug("DEM intersection dimensions: {}", dem.shape)
        logger.trace(dem)

        # Find lowrest and highest value of DEM heights
        minZ = np.min(dem).item()
        maxZ = np.max(dem).item()
        if boundsMin[2] is None: boundsMin[2] = minZ
        if minZ < boundsMin[2]: boundsMin[2] = minZ
        if boundsMax[2] is None: boundsMax[2] = maxZ
        if maxZ > boundsMax[2]: boundsMax[2] = maxZ
        logger.debug("Lowrest point: {}m, highest point {}m", minZ, maxZ)

    # -------------------------------------------------------------------
    # Read max floors of vector buildings

    logger.info("Loop through vector buildings files")

    gdfVectors = []
    for file in Path('.',folderBUILDINGS).glob("*.geojson", case_sensitive=False):
        logger.debug("Load vector buildings: {file}", file=file)
        gdfVectors.append(gpd.read_file(file))
    gdfBuildings = gpd.GeoDataFrame(pd.concat(gdfVectors, ignore_index=True, sort=False))
    maxFloors = gdfBuildings['floors'].max()
    logger.debug("Max floor count: {}", maxFloors)

    # -------------------------------------------------------------------
    # Calculate global world's bounds

    if boundsMin[2] is None:
        boundsMin[2] = 0
    if boundsMax[2] is None:
        boundsMax[2] = 0
    boundsMax[2] = boundsMax[2] + (float(maxFloors)*sizeFloor)
    logger.success("Bounds of our world:  {} - {}", boundsMin, boundsMax)

    # Calculate bounds of voxel's world
    for i in [0,1,2]:
        bounds[i] = int(np.ceil((boundsMax[i]  - boundsMin[i]) / sizeVoxel).item())
    
    logger.success("Bounds of voxel's world:  {}", bounds)


# ============================================
# Accept three coordinates in meters [lon, lat, height]
# and return three float coordinates of VTK space without rounding [x_vtk, y_vtk, z_vtk]
# ============================================
def coordM2Float(meters):
    floats = []
    floats.append( (float(meters[0])-boundsMin[0]) )
    floats.append( (float(meters[2])-boundsMin[2]) )
    floats.append( (float(boundsMax[1]-meters[1])) )
    return floats
'''
# ============================================
# Accept three int coordinates in meters [lon, lat, height]
# and return three float coordinates of VTK space without rounding [x_vtk, y_vtk, z_vtk]
# ============================================
def coordM2Float(meters):
    floats = []
    floats.append( (float(meters[0])-boundsMin[0])/sizeVoxel )
    floats.append( (float(meters[2])-boundsMin[2])/sizeVoxel )
    floats.append( (float(boundsMax[1]-meters[1]))/sizeVoxel )
    return floats
'''