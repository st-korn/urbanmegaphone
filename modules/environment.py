# ============================================
# Module: Environment defenition
# ============================================


# Modules import
# ============================================

# Standart modules
from loguru import logger # Write log
from tqdm import tqdm # Write log
from vtkmodules.vtkIOImage import vtkImageReader2Factory # Read raster images from files
from vtkmodules.vtkRenderingCore import ( vtkRenderer, vtkRenderWindow, vtkRenderWindowInteractor ) # All for render 3D-models
from vtkmodules.vtkCommonColor import vtkNamedColors # Use colors
import vtkmodules.vtkRenderingOpenGL2 # Use OpenGL for render
import math

# Own core modules
import modules.settings as cfg # Settings defenition


# Global variables defenition
# ============================================

# World dimensions (float, meters, Web-Mercator ESPG:3857)
boundsMin = [None, None, None] #lon, lat, height
boundsMax = [None, None, None] #lon, lat, height

# Voxel's world dimensions (integer)
bounds = [None, None, None] #x_lon, y_lat, z_height

# Voxel's world matrix: NumPy 3D-array of int32
voxels = None

# Squares matrix: NumPy 2D-array of int32 with 
# integer vertical z-coordinate of first voxel over earth's surface in current point.
# At first initialized by Nan values
squares = None

# GeoPandas GeoDataFrames
gdfBuildings = None
gdfMegaphones = None

# Buildings statistic:
maxFloors = None 
sumFlats = None

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

# Arrays of VTK objects: polygonal squares of DEM's surface
pntsSquares = [] # vtkPoints
pldtSquares = [] # vtkPolyData
plnSquares = [] # vtkSphereSource
glphSquares = [] # vtkGlyph3D
mapSquares = [] # vtkPolyDataMapper
actSquares = [] # vtkActor


# Environment initialization
# ============================================

# Apply selected logging level
logger.remove()
#logger.add(sys.stderr, level=logLevel)
logger.add(lambda msg: tqdm.write(msg, end=""), level=cfg.logLevel, colorize=True)

# Prepare VTK rendering window
Window.AddRenderer(Renderer)
Renderer.SetBackground(Colors.GetColor3d("ivory_black"))
Interactor.SetRenderWindow(Window)

# ============================================
# Accept three coordinates in meters [lon, lat, height]
# and return three float coordinates of VTK space without rounding [x_vtk, y_vtk, z_vtk]
# ============================================
def coordM2Float(meters):
    floats = []
    floats.append( (float(meters[0])-boundsMin[0]) )
    floats.append( (float(meters[2])-boundsMin[2]) )
    floats.append( (float(boundsMax[1]-meters[1])) )
    return floats

# ============================================
# Accept two pairs of two coordinates in meters (bounding box): lon_min, lon_max, lat_min, lat_max]
# and return two pairs int coordinates of woxel world (bounding box) [x_min, x_max, y_min. y_max]
# ============================================
def boxM2Int(lon_min, lon_max, lat_min, lat_max):
    x_min = math.floor(lon_min/cfg.sizeVoxel)
    x_max = math.ceil(lon_max/cfg.sizeVoxel)
    y_min =math.floor(lat_min/cfg.sizeVoxel)
    y_max = math.ceil(lat_max/cfg.sizeVoxel)
    if ( ( (x_min<0) and (x_max<0) ) or
         ( (x_min>bounds[0]) and (x_max>bounds[0]) ) or
         ( (y_min<0) and (y_max<0) ) or
         ( (y_min>bounds[1]) and (y_max>bounds[1]) ) ):
        return [None, None, None, None]
    if x_min<0:
        x_min = 0
    if x_max>bounds[0]:
        x_max = bounds[0]
    if y_min<0:
        y_min = 0
    if y_max>bounds[1]:
        y_max = bounds[1]
    return [x_min, x_max, y_min, y_max]


