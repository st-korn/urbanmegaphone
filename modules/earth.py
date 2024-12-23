# ============================================
# Module: Read raster and DEM data and generate earth surface
# ============================================

# Modules import
# ============================================

# Standart modules
from loguru import logger # Write log
from pathlib import Path # Crossplatform pathing
from modules.geotiff import GeoTiff # GeoTIFF format reader
import numpy as np # Work with DEM matrix
from vtkmodules.vtkCommonCore import vtkPoints # Use points cloud in 3D-world
from vtkmodules.vtkCommonDataModel import vtkPolyData # Use 3D-primitives
from vtkmodules.vtkRenderingCore import (vtkActor, vtkPolyDataMapper, vtkTexture) # Use VTK rendering
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

    # Draw the coordinate axes, if necessary
    if flagShowAxis:
        axes = vtk.vtkAxesActor()
        axes.SetTotalLength(100,100,100)
        axes.GetXAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
        axes.GetYAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
        axes.GetZAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
        actAxes.append(axes)
        logger.debug("Axes created")

    logger.info("Loop through raster files")

    for fileR in Path('.',folderRaster).glob("*.tif", case_sensitive=False):

        # Open GeoTIFF and conver coordinates to Web-Mercator
        gtfR = GeoTiff(fileR, as_crs=3857)
        boxR = gtfR.tif_bBox_converted
        boxRLeftTop = coordM2Float([boxR[0][0],boxR[0][1],0])
        boxRRightBottom = coordM2Float([boxR[1][0],boxR[1][1],0])

        # Generate a box cube arround raster
        cube = vtk.vtkCubeSource()
        cube.SetBounds(boxRLeftTop[0],boxRRightBottom[0],-1,boundsMax[2]+1,boxRLeftTop[2],boxRRightBottom[2])
        cube.Update()
        cubeRASTER.append(cube)
        if flagShowEarthPoints:
            # Put raster's box in our world
            cubeMapper = vtkPolyDataMapper()
            cubeMapper.SetInputConnection(cube.GetOutputPort())
            mapCube.append(cubeMapper)
            cubeActor = vtkActor()
            cubeActor.SetMapper(cubeMapper)
            cubeActor.GetProperty().SetRepresentationToWireframe()
            cubeActor.GetProperty().SetOpacity(0.2)
            cubeActor.GetProperty().SetColor(Colors.GetColor3d("red"))
            actCube.append(cubeActor)
            logger.debug("Box of raster created")
        box = vtk.vtkBox()
        box.SetBounds(cube.GetOutput().GetBounds())
        boxRASTER.append(box)

        # Load raster image from file to vtkImageReader2 object
        imageReader = readerFactory.CreateImageReader2(str(fileR))
        imageReader.SetFileName(fileR)
        imageReader.Update()
        imgrdrRASTER.append(imageReader)

        logger.success("Raster {} loaded", fileR.name)
        logger.trace("Raster box: {}",boxR)
        
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
            logger.debug("@ ({src}) = ({dst})", src=[float(lons[0,0]),float(lats[0,0]),float(dem[0,0])], dst=coordM2Float([float(lons[0,0]),float(lats[0,0]),float(dem[0,0])]))
            logger.trace("@ ({src}) = ({dst})", src=[float(lons[dem.shape[0]-1,dem.shape[1]-1]),float(lats[dem.shape[0]-1,dem.shape[1]-1]),float(dem[dem.shape[0]-1,dem.shape[1]-1])], 
                                                dst=coordM2Float([float(lons[dem.shape[0]-1,dem.shape[1]-1]),float(lats[dem.shape[0]-1,dem.shape[1]-1]),float(dem[dem.shape[0]-1,dem.shape[1]-1])]))

            # Collect points of surface
            points = vtkPoints()
            for lon, lat in np.ndindex(dem.shape):
                points.InsertNextPoint(coordM2Float([lons[lon,lat],lats[lon,lat],dem[lon,lat]]))
            pntsDEM.append(points)
            polyDataPoints = vtkPolyData()
            polyDataPoints.SetPoints(points)
            pldtDEM.append(polyDataPoints)
            logger.debug("DEM points converted")

            if flagShowEarthPoints:
                # Generate spheres on original earth DEM points
                sphereDEM = vtk.vtkSphereSource()
                sphereDEM.SetRadius(1)
                sphrDEM.append(sphereDEM)
                glyphDEM = vtk.vtkGlyph3D()
                glyphDEM.SetInputData(polyDataPoints)
                glyphDEM.SetSourceConnection(sphereDEM.GetOutputPort())
                glyphDEM.ScalingOff()
                glyphDEM.Update()
                glphDEM.append(glyphDEM)
                pointsMapperDEM = vtkPolyDataMapper()
                pointsMapperDEM.SetInputConnection(glyphDEM.GetOutputPort())
                mapDEM.append(pointsMapperDEM)
                pointsActorDEM = vtkActor()
                pointsActorDEM.SetMapper(pointsMapperDEM)
                pointsActorDEM.GetProperty().SetColor(Colors.GetColor3d("goldenrod_light"))
                actDEM.append(pointsActorDEM)
                logger.debug("DEM source points spheres created")

            # Create surface from points
            logger.debug("Start DEM surface creation...")
            surface = vtk.vtkSurfaceReconstructionFilter()
            surface.SetNeighborhoodSize(SurfaceNeighbor)
            surface.SetSampleSpacing(SurfaceCells)
            surface.SetInputData(polyDataPoints)
            srfsfltSurface.append(surface)
            cf = vtk.vtkContourFilter()
            cf.SetInputConnection(surface.GetOutputPort())
            cf.SetValue(0, 0.0)
            srfsfltSurface.append(cf)
            reverse = vtk.vtkReverseSense()
            reverse.SetInputConnection(cf.GetOutputPort())
            reverse.ReverseCellsOn()
            reverse.ReverseNormalsOn()
            reverse.Update()
            rvrsfltSurface.append(reverse)
            polyDataSurface = reverse.GetOutput()
            pldtSurface.append(polyDataSurface)
            logger.debug("DEM surface created")
            logger.trace("Sample spacing = {}",surface.GetSampleSpacing())

            if flagShowEarthPoints:
                # Generate spheres on generated earth surfacee vertices
                sphereSurface = vtk.vtkSphereSource()
                sphereSurface.SetRadius(1)
                sphrSurface.append(sphereSurface)
                glyphSurface = vtk.vtkGlyph3D()
                glyphSurface.SetInputData(polyDataSurface)
                glyphSurface.SetSourceConnection(sphereSurface.GetOutputPort())
                glyphSurface.ScalingOff()
                glyphSurface.Update()
                glphSurface.append(glyphSurface)
                pointsMapperSurface = vtkPolyDataMapper()
                pointsMapperSurface.SetInputConnection(glyphSurface.GetOutputPort())
                pointsMapperSurface.ScalarVisibilityOff()
                mapSurface.append(pointsMapperSurface)
                pointsActorSurface = vtkActor()
                pointsActorSurface.SetMapper(pointsMapperSurface)
                pointsActorSurface.GetProperty().SetColor(Colors.GetColor3d("dim_grey"))
                actSurface.append(pointsActorSurface)
                logger.debug("DEM generated surface's points spheres created")

            # Shrink surface to raster bounds to preven the formation of a seam between the stitched surfaces
            clipper = vtk.vtkClipPolyData()
            clipper.SetInputData(polyDataSurface)
            clipper.SetClipFunction(box)
            clipper.InsideOutOn()
            clipper.Update()
            clpprClipped.append(clipper)
            polyDataClipped = clipper.GetOutput()
            pldtClipped.append(polyDataClipped)
            logger.debug("DEM shrinked to RASTER")
            
            # Put texture on surface
            surfacePoints = polyDataClipped.GetPoints()
            pntsClipped.append(surfacePoints)
            texturePoints = vtk.vtkFloatArray()
            texturePoints.SetNumberOfComponents(2)
            for i in range(surfacePoints.GetNumberOfPoints()):
                pnt = surfacePoints.GetPoint(i)
                a = (pnt[0]-boxRLeftTop[0])/(boxRRightBottom[0]-boxRLeftTop[0])
                b = (pnt[2]-boxRLeftTop[2])/(boxRRightBottom[2]-boxRLeftTop[2])
                texturePoints.InsertNextTuple2(a, b)
            polyDataClipped.GetPointData().SetTCoords(texturePoints)
            fltarTexture.append(texturePoints)
            texture = vtkTexture()
            texture.SetInputConnection(imageReader.GetOutputPort())
            texture.InterpolateOn()
            txtrTexture.append(texture)
            logger.debug("DEM texture applied")

            # Prepare surface for view
            mapper = vtkPolyDataMapper()
            mapper.SetInputData(polyDataClipped)
            mapper.ScalarVisibilityOff()
            mapTexture.append(mapper)
            actor = vtkActor()
            actor.SetMapper(mapper)
            actor.SetTexture(texture)
            actTexture.append(actor)
            logger.success("{}: DEM ready for render",fileD.name)