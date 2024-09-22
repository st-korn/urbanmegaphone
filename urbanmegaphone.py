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

# Prepare VTK-window for view and interact
# ============================================
logger.info("Prepare 3D model in viewer window")
Window.AddRenderer(Renderer)
Interactor.SetRenderWindow(Window)

# Prepare VTK 3D-objects
# ============================================
for actor in actTextureDEM: 
    Renderer.AddActor(actor)

# Run VTK-window
# ============================================
Interactor.Initialize()
Renderer.ResetCamera()
Window.Render()
Interactor.SetInteractorStyle(vtk.vtkInteractorStyleTerrain())
logger.success("Done. Ready for viewing")
Interactor.Start()

