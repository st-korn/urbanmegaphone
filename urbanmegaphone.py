# ============================================
# Urban megaphone
# 3D-modeling of sound wave coverage among urban buildings and streets
# ============================================

# Modules import
# ============================================

# Own core modules
from modules.bounds import * # Read raster and DEM data and calculate wolrd bounds
from modules.earth import * # Read raster and DEM data and generate earth surface

# Real work
# ============================================
ReadWorldBounds()
GenerateEarthSurface()