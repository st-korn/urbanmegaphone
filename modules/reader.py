# ============================================
# Module: Read all data from files to memory
# ============================================

# Modules import
# ============================================

# Standart modules
from pathlib import Path # Crossplatform pathing
from geotiff import GeoTiff # GeoTIFF format reader

# Own core modules
from modules.settings import * # Settings defenition


# ============================================
# Read .tif files of RASTER and DEM models
# Find the dimensions of the world being explored
# ============================================
def ReadWorldParameters():

    if logLevel>=logTerse: print("Find the dimensions of the world being explored")

    # Loop through raster files
    if logLevel>=logNormal: print("Loop through raster files")

    for file in Path('.',folderRaster).glob("*.tif", case_sensitive=False):
        if logLevel>=logAll: print(file.name,end=" ")
        gtf = GeoTiff(file, as_crs=3857)
        if logLevel>=logAll: print("ESPG:",gtf.crs_code, gtf.tif_bBox_converted)
        
    
