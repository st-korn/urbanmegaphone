# ============================================
# Module: Read raster and DEM data and calculate wolrd bounds
# ============================================

# Modules import
# ============================================

# Standart modules
import multiprocessing as mp # Use multiprocessing
from multiprocessing.shared_memory import SharedMemory # Use shared memory
import ctypes # Use primitive datatypes for multiprocessing data exchange
from pathlib import Path # Crossplatform pathing
from modules.geotiff import GeoTiff # GeoTIFF format reader
import numpy as np # Work with DEM matrix
import pandas as pd # For tables of data
import geopandas as gpd # For vector objects
from shapely.geometry import Polygon

# Own core modules
import modules.settings as cfg # Settings defenition
import modules.environment as env # Environment defenition


# ============================================
# Read .tif files of RASTER and DEM models
# Find the dimensions of the world being explored
# ============================================
def ReadWorldBounds():

    env.logger.info("Find the dimensions of the world being explored")

    # -------------------------------------------------------------------
    # Read bounds of raster files

    env.logger.info("Loop through raster files")

    for file in Path('.',cfg.folderRaster).glob("*.tif", case_sensitive=False):

        # Open GeoTIFF and conver coordinates to Web-Mercator
        gtf = GeoTiff(file, as_crs=3857)
        
        env.logger.debug("{file}: ESPG:{proj} {resolution}", file=file.name, proj=gtf.crs_code, resolution=gtf.tif_shape)
        env.logger.debug("   {box} =>", box=gtf.tif_bBox)
        env.logger.debug("   => {projected}", projected=gtf.tif_bBox_converted)
        
        # Find total bounds of all rasters
        box = gtf.tif_bBox_converted
        for i in [0,1]:
            if env.boundsMin[i] is None: env.boundsMin[i] = box[0][i]
            if box[0][i] < env.boundsMin[i]: env.boundsMin[i] = box[0][i]
            if box[1][i] < env.boundsMin[i]: env.boundsMin[i] = box[1][i]
            if env.boundsMax[i] is None: env.boundsMax[i] = box[0][i]
            if box[0][i] > env.boundsMax[i]: env.boundsMax[i] = box[0][i]
            if box[1][i] > env.boundsMax[i]: env.boundsMax[i] = box[1][i]
    
    env.logger.success("Bounds of rasters: {} - {}", env.boundsMin, env.boundsMax)

    # -------------------------------------------------------------------
    # Read bounds of DEM files in the intersecting part of rasters

    env.logger.info("Loop through DEM files")

    for file in Path('.',cfg.folderDEM).glob("*.tif", case_sensitive=False):

        # Open GeoTIFF and conver coordinates to Web-Mercator
        gtf = GeoTiff(file, as_crs=3857)
        
        env.logger.debug("{file}: ESPG:{proj} {resolution}", file=file.name, proj=gtf.crs_code, resolution=gtf.tif_shape)
        env.logger.debug("   {box} =>", box=gtf.tif_bBox)
        env.logger.debug("   => {projected}", projected=gtf.tif_bBox_converted)

        # Read intersection DEM and Raster bounds
        boxIntersection = ((env.boundsMin[0],env.boundsMax[1]),(env.boundsMax[0],env.boundsMin[1]))
        try:
            dem = np.array(gtf.read_box(boxIntersection))
        except Exception as e:
            env.logger.warning("DEM intersection not found: {}", e)
            continue
        env.logger.debug("DEM intersection dimensions: {}", dem.shape)
        env.logger.trace(dem)

        # Find lowrest and highest value of DEM heights
        minZ = np.min(dem).item()
        maxZ = np.max(dem).item()
        if env.boundsMin[2] is None: env.boundsMin[2] = minZ
        if minZ < env.boundsMin[2]: env.boundsMin[2] = minZ
        if env.boundsMax[2] is None: env.boundsMax[2] = maxZ
        if maxZ > env.boundsMax[2]: env.boundsMax[2] = maxZ
        env.logger.debug("Lowrest point: {}m, highest point {}m", minZ, maxZ)

    # -------------------------------------------------------------------
    # Read max floors of vector buildings

    env.logger.info("Loop through vector buildings files...")

    gdfVectors = []
    for file in Path('.',cfg.folderBUILDINGS).glob("*.geojson", case_sensitive=False):
        env.logger.debug("Load vector buildings: {file}", file=file)
        gdfVectors.append(gpd.read_file(file))
    env.gdfBuildings = gpd.GeoDataFrame(pd.concat(gdfVectors, ignore_index=True, sort=False))
    env.maxFloors = env.gdfBuildings['floors'].max()
    env.sumFlats = env.gdfBuildings['flats'].sum()
    env.logger.success("{} vector buildings loaded. Max floor: {}, Total flats: {}", len(env.gdfBuildings.index), env.maxFloors, env.sumFlats)

    # -------------------------------------------------------------------
    # Calculate global world's bounds

    if env.boundsMin[2] is None:
        env.boundsMin[2] = 0
    if env.boundsMax[2] is None:
        env.boundsMax[2] = 0
    env.boundsMax[2] = env.boundsMax[2] + (float(env.maxFloors)*cfg.sizeFloor)
    env.logger.success("Bounds of our world:  {} - {}", env.boundsMin, env.boundsMax)

    # Calculate bounds of voxel's world
    for i in [0,1,2]:
        env.bounds[i] = int(np.ceil((env.boundsMax[i]  - env.boundsMin[i]) / cfg.sizeVoxel).item())
    
    env.logger.success("Bounds of voxel's world:  {}", env.bounds)

    # Create 2D polygon of VTK area
    env.plgnBounds = Polygon ( [ (0,0), ((env.bounds[0]+0.5)*cfg.sizeVoxel,0), 
                                 ((env.bounds[0]+0.5)*cfg.sizeVoxel,(env.bounds[1]+0.5)*cfg.sizeVoxel), 
                                 (0,(env.bounds[1]+0.5)*cfg.sizeVoxel) ] )

    # Allocate memory for voxel's world
    env.logger.info("Allocate memory for voxel's world...")
    env.ground = mp.RawArray(ctypes.c_short,env.bounds[0]*env.bounds[1])
    
    env.shmemAudibility2D = SharedMemory(create=True, size=ctypes.sizeof(ctypes.c_byte)*env.bounds[0]*env.bounds[1])
    env.audibility2D = (ctypes.c_byte * (env.bounds[0]*env.bounds[1])).from_buffer(env.shmemAudibility2D.buf)
    ctypes.memset(ctypes.addressof(env.audibility2D), 0, ctypes.sizeof(env.audibility2D))

    env.uib = mp.RawArray(ctypes.c_long,env.bounds[0]*env.bounds[1])
    env.VoxelIndex = mp.RawArray(ctypes.c_ulong,env.bounds[0]*env.bounds[1])
    for i in range(env.bounds[0]*env.bounds[1]):
        env.ground[i] = -1
        env.uib[i] = -1
    env.logger.success("Memory allocated")

    # Generate 2D-GeoPandas GeoDataFrame with centers of voxel's squares on the plane
    env.logger.info("Create grid of squares on voxel's plane...")
    arr = np.mgrid[0:env.bounds[0], 0:env.bounds[1]]
    arr_x = np.ravel(arr[0])
    arr_y = np.ravel(arr[1])
    env.gdfCells = gpd.GeoDataFrame({'x' : arr_x, 'y' : arr_y,
            'geometry' : gpd.points_from_xy((arr_x+0.5)*cfg.sizeVoxel, (arr_y+0.5)*cfg.sizeVoxel)})
    env.logger.trace(env.gdfCells)
    env.logger.success("World grid created: {} cells", f'{len(env.gdfCells.index):_}')
