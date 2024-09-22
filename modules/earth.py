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
from vtkmodules.vtkRenderingCore import (vtkActor, vtkPolyDataMapper) # Use VTK rendering
import vtk # Use other 3D-visualization features

# Own core modules
from modules.settings import * # Settings defenition
from modules.environment import * # Environment defenition
from modules.bounds import * # Read raster and DEM data and calculate wolrd bounds


# ============================================
# Read .tif files of RASTER and DEM models
# Generate 3D-surface with textures
# ============================================
def GenerateEarthSurface():

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
            try:
                dem = np.array(gtfD.read_box(boxR, outer_points=SurfaceOutline))
            except:
                logger.warning("{}: DEM intersection not found", fileD.name)
                continue
            lons, lats = gtfD.get_coord_arrays(boxR, outer_points=SurfaceOutline)

            logger.debug("{file} intersection: {dim}",file=fileD.name, dim=dem.shape)
            logger.debug("@ ({src}) = ({dst})", src=[float(lons[0,0]),float(lats[0,0]),float(dem[0,0])], dst=coordM2Float([lons[0,0],lats[0,0],dem[0,0]]))
            logger.trace("@ ({src}) = ({dst})", src=[float(lons[0,dem.shape[1]-1]),float(lats[0,dem.shape[1]-1]),float(dem[0,dem.shape[1]-1])], 
                                                dst=coordM2Float([lons[0,dem.shape[1]-1],lats[0,dem.shape[1]-1],dem[0,dem.shape[1]-1]]))
            logger.trace("@ ({src}) = ({dst})", src=[float(lons[dem.shape[0]-1,0]),float(lats[dem.shape[0]-1,0]),float(dem[dem.shape[0]-1,0])], 
                                                dst=coordM2Float([lons[dem.shape[0]-1,0],lats[dem.shape[0]-1,0],dem[dem.shape[0]-1,0]]))
            logger.trace("@ ({src}) = ({dst})", src=[float(lons[dem.shape[0]-1,dem.shape[1]-1]),float(lats[dem.shape[0]-1,dem.shape[1]-1]),float(dem[dem.shape[0]-1,dem.shape[1]-1])], 
                                                dst=coordM2Float([lons[dem.shape[0]-1,dem.shape[1]-1],lats[dem.shape[0]-1,dem.shape[1]-1],dem[dem.shape[0]-1,dem.shape[1]-1]]))

            # Collect points of surface
            points = vtkPoints()
            for lon, lat in np.ndindex(dem.shape):
                points.InsertNextPoint(coordM2Float([lons[lon,lat],lats[lon,lat],dem[lon,lat]]))
            pntsTextureDEM.append(points)

            # Create surface from points
            polyDataPoints = vtkPolyData()
            polyDataPoints.SetPoints(points)
            surface = vtk.vtkSurfaceReconstructionFilter()
            surface.SetNeighborhoodSize(SurfaceNeighbor)
            surface.SetSampleSpacing(SurfaceCells)
            surface.SetInputData(polyDataPoints)
            srfsfltTextureDEM.append(surface)
            cf = vtk.vtkContourFilter()
            cf.SetInputConnection(surface.GetOutputPort())
            cf.SetValue(0, 0.0)
            cntrfltTextureDEM.append(cf)
            reverse = vtk.vtkReverseSense()
            reverse.SetInputConnection(cf.GetOutputPort())
            reverse.ReverseCellsOn()
            reverse.ReverseNormalsOn()
            reverse.Update()
            rvrsfltTextureDEM.append(reverse)
            polyData = reverse.GetOutput()
            logger.trace("Sample spacing = {}",surface.GetSampleSpacing())

            if flagShowEarthPoints:
                # Generate spheres on original earth DEM points
                sphere = vtk.vtkSphereSource()
                sphere.SetRadius(1)
                glyph = vtk.vtkGlyph3D()
                glyph.SetInputData(polyDataPoints)
                glyph.SetSourceConnection(sphere.GetOutputPort())
                glyph.ScalingOff()
                glyph.Update()
                pointsMapper = vtkPolyDataMapper()
                pointsMapper.SetInputConnection(glyph.GetOutputPort())
                pointsActor = vtkActor()
                pointsActor.SetMapper(pointsMapper)
                pointsActor.GetProperty().SetColor(Colors.GetColor3d("goldenrod_light"))
                actTextureDEM.append(pointsActor)

                # Generate spheres on generated earth surfacee vertices
                glyph = vtk.vtkGlyph3D()
                glyph.SetInputData(polyData)
                glyph.SetSourceConnection(sphere.GetOutputPort())
                glyph.ScalingOff()
                glyph.Update()
                pointsMapper = vtkPolyDataMapper()
                pointsMapper.SetInputConnection(glyph.GetOutputPort())
                pointsMapper.ScalarVisibilityOff()
                pointsActor = vtkActor()
                pointsActor.SetMapper(pointsMapper)
                pointsActor.GetProperty().SetColor(Colors.GetColor3d("dim_grey"))
                actTextureDEM.append(pointsActor)
                

            # Store generated surface in memory
            pldtTextureDEM.append(polyData)
            # Prepare surface for view
            mapper = vtkPolyDataMapper()
            mapper.SetInputData(polyData)
            mapper.ScalarVisibilityOff()
            mapTextureDEM.append(mapper)
            actor = vtkActor()
            actor.SetMapper(mapper)
            #actor.SetTexture(atext)
            actTextureDEM.append(actor)
