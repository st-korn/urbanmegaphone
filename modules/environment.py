# ============================================
# Module: Environment defenition
# ============================================


# Modules import
# ============================================

# Standart modules
import sys # use default outputs
from loguru import logger # Write log
from vtkmodules.vtkIOImage import vtkImageReader2Factory # Read raster images from files
from vtkmodules.vtkRenderingCore import ( vtkRenderer, vtkRenderWindow, vtkRenderWindowInteractor ) # All for render 3D-models
from vtkmodules.vtkCommonColor import vtkNamedColors # Use colors
import vtkmodules.vtkRenderingOpenGL2 # Use OpenGL for render
import geopandas as gpd

# Own core modules
from modules.settings import * # Settings defenition


# Global variables defenition
# ============================================

# World dimensions (meters, Web-Mercator ESPG:3857)
boundsMin = [None, None, None] #lon, lat, height
boundsMax = [None, None, None] #lon, lat, height

# Voxel's world dimensions (integer)
bounds = [None, None, None] #x_lon, y_lat, z_height

# GeoPandas objects
gdfBuildings = gpd.GeoDataFrame()
gdfMegaphones = gpd.GeoDataFrame()

# Single VTK objects
readerFactory = vtkImageReader2Factory()
Colors = vtkNamedColors()
Renderer = vtkRenderer()
Window = vtkRenderWindow()
Interactor = vtkRenderWindowInteractor()

# Arrays of VTK objects: axis of coordinate system
actAxes = [] # vtkAxesActor

# Arrays of VTK objects: original raster texture files
cubeRASTER = [] # vtkCudeSource
mapCube = [] # vtkPolyDataMapper
actCube = [] # vtkActor
boxRASTER = [] # vtkBox
imgrdrRASTER = [] # vtkImageReader2

# Arrays of VTK objects: points of DEM
pntsDEM = [] # vtkPoints
pldtDEM = [] # vtkPolyData
sphrDEM = [] # vtkSphereSource
glphDEM = [] # vtkGlyph3D
mapDEM = [] # vtkPolyDataMapper
actDEM = [] # vtkActor

# Arrays of VTK objects: generated surface of DEM
srfsfltSurface = [] # vtkSurfaceReconstructionFilter
cntrfltSurface = [] # vtkContourFilter
rvrsfltSurface = [] # vtkReverseSense
pldtSurface = [] # vtkPolyData
sphrSurface = [] # vtkSphereSource
glphSurface = [] # vtkGlyph3D
mapSurface = [] # vtkPolyDataMapper
actSurface = [] # vtkActor

# Arrays of VTK objects: clipped surface of DEM
clpprClipped = [] # vtkClipPolyData
pldtClipped = [] # vtkPolyData
pntsClipped = [] # vtkPoints

# Arrays of VTK objects: raster texture on DEM's surface
fltarTexture = [] # vtkFloatArray array of texture coordinates
txtrTexture = [] # vtkTexture
mapTexture = [] # vtkPolyDataMapper
actTexture = [] # vtkActor

# Environment initialization
# ============================================

# Apply selected logging level
logger.remove()
logger.add(sys.stderr, level=logLevel)

# Prepare VTK rendering window
Window.AddRenderer(Renderer)
Renderer.SetBackground(Colors.GetColor3d("ivory_black"))
Interactor.SetRenderWindow(Window)