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
logLevel = "INFO"


# Quality of world's detail
# ============================================

# Voxel's edge size, meter. Default value is 3 meter - approximately one floor
sizeVoxel = 3

# Build earth surface like a grid (best view, but 50x more runtime): True or False
# Not recomended if you have less than 64Gb RAM
flagSurfaceAsGrid = False

# Permissible error in constructing surfaces by points, voxels. Default value is 3 voxel
SurfaceDelta = 3

# How many pixeles get out of box border. Increase it to prevent blank lines on raster's seam. Default value is 2 px
SurfaceOutline = 2

# Show original DEM earth's point: True or False
flagShowEarthPoints = True