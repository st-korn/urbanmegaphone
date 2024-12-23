# ============================================
# Urban megaphone
# 3D-modeling of sound wave coverage among urban buildings and streets
# ============================================

# Modules import
# ============================================

# Own core modules
from modules.bounds import * # Read raster and DEM data and calculate wolrd bounds
from modules.earth import * # Read raster and DEM data and generate earth surface
from modules.buildings import * # Generate voxels for earth ground vector buildings

# Real work
# ============================================
ReadWorldBounds() # Read .tif files of RASTER and DEM models, find the dimensions of the world being explored
GenerateEarthSurface() # Read .tif files of RASTER and DEM models, generate 3D-surface with textures
GenerateBuildings() # Process vector buildings and generate voxel's world

# Prepare VTK-window for view and interact
# ============================================
logger.info("Prepare 3D model in viewer window")
Window.AddRenderer(Renderer)
Interactor.SetRenderWindow(Window)

# Prepare VTK 3D-objects
# ============================================
for actor in actAxes: Renderer.AddActor(actor)
for actor in actCube: Renderer.AddActor(actor)
for actor in actDEM: Renderer.AddActor(actor)
for actor in actSurface: Renderer.AddActor(actor)
for actor in actTexture: Renderer.AddActor(actor)

# Run VTK-window
# ============================================
Interactor.Initialize()
Renderer.ResetCamera()
Window.Render()
Interactor.SetInteractorStyle(vtk.vtkInteractorStyleTerrain())
logger.success("Done. Ready for viewing")
Interactor.Start()

