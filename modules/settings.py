# ============================================
# Module: Settings defenition
# ============================================

# Global program settings
# ============================================

# Path to files and folders
folderRaster = 'RASTER' # Subfolder (in current folder) with raster tiles (.tif)
folderDEM = 'DEM' # Subfolder (in current folder) with DEM tiles (.tif)

# Debug log detail level, from verbose to terse:
# "TRACE" or "DEBUG" or "INFO" or "SUCCESS" or "WARNING" or "ERROR" or "CRITICAL"
logLevel = "DEBUG"


# Quality of world's detail
# ============================================

# Voxel's edge size, meter. Default value is 3 meter - approximately one floor
sizeVoxel = 3

# How many pixeles get out of box border. Increase it to prevent blank lines on raster's seam. Default value is 2 px
SurfaceOutline = 1

# Count of neighboring points, used for aproximate surface. Low values lead to a haotic surface. Default value is 10
SurfaceNeighbor = 10

# Count of neighboring points, used for aproximate one cell of surface. Low values lead to long calculation times. Default value is 5
SurfaceCells = 5

# Show original DEM earth's point: True or False. Used for debug surface purposes
flagShowEarthPoints = True