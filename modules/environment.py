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
import vtkmodules.vtkRenderingOpenGL2 # Use OpenGL for render

# Own core modules
from modules.settings import * # Settings defenition


# Global variables defenition
# ============================================

# World dimensions (meters, Web-Mercator ESPG:3857)
boundsMin = [None, None, None]
boundsMax = [None, None, None]

# Voxel's world dimensions (integer)
bounds = [None, None, None]


# Single VTK objects
readerFactory = vtkImageReader2Factory()
Renderer = vtkRenderer()
Window = vtkRenderWindow()
Interactor = vtkRenderWindowInteractor()

# Arrays of VTK objects: original raster texture files
imgrdrTextures = [] # vtkImageReader2

# Arrays of VTK objects: intersection raster textures and DEM
pntsTextureDEM = [] # vtkPoints
pldtTextureDEM = [] # vtkPolyData
srfsfltTextureDEM = [] # vtkSurfaceReconstructionFilter
cntrfltTextureDEM = [] # vtkContourFilter
rvrsfltTextureDEM = [] # vtkReverseSense
fltarTextureDEM = [] # vtkFloatArray array of texture coordinates
txtrTextureDEM = [] # vtkTexture
mapTextureDEM = [] # vtkPolyDataMapper
actTextureDEM = [] # vtkActor

# Environment initialization
# ============================================

# Apply selected logging level
logger.remove()
logger.add(sys.stderr, level=logLevel)

# Prepare VTK rendering window
Window.AddRenderer(Renderer)
Interactor.SetRenderWindow(Window)