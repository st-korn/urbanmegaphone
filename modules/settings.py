# ============================================
# Module: Settings defenition
# ============================================

# Global program settings
# ============================================

# Path to files and folders
folderRaster = 'RASTER' # Subfolder (in current folder) with raster tiles (.tif)
folderDEM = 'DEM' # Subfolder (in current folder) with DEM tiles (.tif)
folderBUILDINGS = 'BUILDINGS' # Subfolder (in current folder) with vector buildings tiles (.geojson)

# Debug log detail level, from verbose to terse:
# "TRACE" or "DEBUG" or "INFO" or "SUCCESS" or "WARNING" or "ERROR" or "CRITICAL"
logLevel = "DEBUG"


# Quality of world's detail
# ============================================

# Voxel's edge size, meter. Default value is 3 meter - approximately one floor
sizeVoxel = 3

# The gap between voxels, meter. Default value is 0.5 meter
gapVoxel = 0.5

# Floor size, meter.  Default value is 3 meter
sizeFloor = 3

# How many pixeles get out of box border. Increase it to prevent blank lines on raster's or DEMs seams. Default value is 3 px
SurfaceOutline = 3

# Count of neighboring points, used for aproximate surface. Low values lead to a haotic surface. Default value is 20
SurfaceNeighbor = 20

# Count of neighboring points, used for aproximate one cell of surface. Low values lead to long calculation times. Default value is 36
SurfaceCells = 6*6

# Show original DEM earth's point: True or False. Used for debug surface purposes. Default value is False
flagShowEarthPoints = False

# Show axis of ccordinate system. Used for debug surface purposes. Default value is True
flagShowAxis = True

# Show squares and calculate audibility on earth surface:
# 'full' - for all surface
# 'buffer' - for surface around living buildings
# 'none' - do not calculate and show
# Default value is 'buffer'
ShowSquares = 'buffer'

# Radius of buffer zones around buildings. Used with ShowSquares = 'buffer. Meters, default value = 300
BufferRadius = 300

# Select mode for ground point of buildings:
# 'min' - building positioned at the lowerest point on his ground. All voxels of building have same ground level.
# 'max' - building positioned at the highest point on his ground. All voxels of building have same ground level.
# 'mean' - building positioned at the mean point on his ground. All voxels of building have same ground level.
# 'median' - building positioned at the median point on his ground. All voxels of building have same ground level.
# 'levels' - Each voxel of building positioned at its own ground level.
# Default value is 'median'
BuildingGroundMode = 'median'