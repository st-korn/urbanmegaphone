# ============================================
# Module: Read raster and DEM data and generate earth surface
# ============================================

# Modules import
# ============================================

# Standart modules
from loguru import logger # Write log
from pathlib import Path # Crossplatform pathing
from geotiff import GeoTiff # GeoTIFF format reader
import numpy as np # Work with DEM matrix
from vtkmodules.vtkCommonCore import vtkPoints # Use points cloud in 3D-world
from vtkmodules.vtkCommonDataModel import vtkPolyData # Use 3D-primitives
import vtk # Use other 3D-visualization features

# Own core modules
from modules.settings import * # Settings defenition
from modules.environment import * # Environment defenition
from modules.bounds import * # Read raster and DEM data and calculate wolrd bounds


# ============================================
# Read .tif files of RASTER and DEM models
# Find the dimensions of the world being explored
# ============================================
def GenerateEarthSurface():

    # Use global variables
    global boundsMin, boundsMax, bounds

    logger.info("Generate earth surface")

    logger.info("Loop through raster files")

    for fileR in Path('.',folderRaster).glob("*.tif", case_sensitive=False):

        # Open GeoTIFF and conver coordinates to Web-Mercator
        gtfR = GeoTiff(fileR, as_crs=3857)
        boxR = gtfR.tif_bBox_converted

        # Load raster image from file to vtkImageReader2 object
        imageReader = readerFactory.CreateImageReader2(str(fileR))
        imageReader.SetFileName(fileR)
        imageReader.Update()
        imgrdrTextures.append(imageReader)

        logger.success("Raster {} loaded", fileR.name)
        
        for fileD in Path('.',folderDEM).glob("*.tif", case_sensitive=False):

            # Open GeoTIFF and conver coordinates to Web-Mercator
            gtfD = GeoTiff(fileD, as_crs=3857)
        
            # Read intersection DEM and Raster bounds
            dem = np.array(gtfD.read_box(boxR))
            lons, lats = gtfD.get_coord_arrays(boxR)

            logger.debug("{file} intersection: {dim} @ ({src}) = ({dst})", file=fileD.name, dim=dem.shape, src=[float(lons[0,0]),float(lats[0,0]),float(dem[0,0])], dst=coordM2Float([lons[0,0],lats[0,0],dem[0,0]]))

            # Collect points of surface
            points = vtkPoints()
            for lon, lat in np.ndindex(dem.shape):
                points.InsertNextPoint(coordM2Float([lons[lon,lat],lats[lon,lat],dem[lon,lat]]))
            pntsTextureDEM.append(points)

            # Create surface from points
            polyData = vtkPolyData()
            polyData.SetPoints(points)
            surface = vtk.vtkSurfaceReconstructionFilter()
            surface.SetNeighborhoodSize(2)
            surface.SetInputData(polyData)
            cf = vtk.vtkContourFilter()
            cf.SetInputConnection(surface.GetOutputPort())
            cf.SetValue(0, 0.0)
            reverse = vtk.vtkReverseSense()
            reverse.SetInputConnection(cf.GetOutputPort())
            reverse.ReverseCellsOn()
            reverse.ReverseNormalsOn()
            reverse.Update()
            polyData = reverse.GetOutput()
            pldtTextureDEM.append(polyData)

