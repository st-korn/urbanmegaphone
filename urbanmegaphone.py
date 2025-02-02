# ============================================
# Urban megaphone
# 3D-modeling of sound wave coverage among urban buildings and streets
# ============================================

# Modules import
# ============================================
import vtk # Use other 3D-visualization features

# Own core modules
import modules.settings as cfg # Settings defenition
import modules.environment as env # Environment defenition
import modules.bounds # Read raster and DEM data and calculate wolrd bounds
import modules.earth # Read raster and DEM data and generate earth surface
import modules.buildings # Generate voxels for earth ground vector buildings
import modules.megaphones # Load megaphones points and calculate audibility level

# Real work
# ============================================
modules.bounds.ReadWorldBounds() # Read .tif files of RASTER and DEM models, find the dimensions of the world being explored
modules.earth.GenerateEarthSurface() # Read .tif files of RASTER and DEM models, generate 3D-surface with textures
modules.buildings.GenerateBuildings() # Process vector buildings and generate voxel's world
modules.earth.PrepareBufferZones() # Calculate buffer zones around living buildings if ShowSquares mode is 'buffer'
modules.megaphones.LoadMegaphones() # Load megaphones points
env.clearMemory() # Clear memory from unused variables
modules.buildings.VizualizeAllVoxels() # Generate voxels of buildings vizualiztion
modules.earth.VizualizeAllSquares() # Generate squares of earth surface vizualization

# Prepare VTK-window for view and interact
# ============================================
env.logger.info("Prepare 3D model in viewer window...")
env.Window.AddRenderer(env.Renderer)
env.Interactor.SetRenderWindow(env.Window)

# Prepare VTK 3D-objects
# ============================================
for actor in env.actAxes: env.Renderer.AddActor(actor)
for actor in env.actCube: env.Renderer.AddActor(actor)
for actor in env.actDEM: env.Renderer.AddActor(actor)
for actor in env.actSurface: env.Renderer.AddActor(actor)
for actor in env.actTexture: env.Renderer.AddActor(actor)
for actor in env.actSquares: env.Renderer.AddActor(actor)
for actor in env.actVoxels: env.Renderer.AddActor(actor)

# Run VTK-window
# ============================================
env.Interactor.Initialize()
env.Renderer.ResetCamera()
env.Window.Render()
env.Interactor.SetInteractorStyle(vtk.vtkInteractorStyleTerrain())
env.logger.success("Done. Ready for viewing")
env.Interactor.Start()
env.logger.info("Please wait for finishing memory cleanup")