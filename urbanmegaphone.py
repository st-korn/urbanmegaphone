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
ReadWorldBounds() # Read .tif files of RASTER and DEM models, find the dimensions of the world being explored
GenerateEarthSurface() # Read .tif files of RASTER and DEM models, generate 3D-surface with textures

# Prepare VTK 3D-objects
# ============================================
for actor in actTextureDEM: Renderer.AddActor(actor)

# Prepare VTK-window for view and interact
# ============================================
Interactor.Initialize()
Window.Render()
Interactor.SetInteractorStyle(vtk.vtkInteractorStyleTerrain())
Interactor.Start()