# ============================================
# Module: Read raster and DEM data and generate earth surface
# ============================================

# Modules import
# ============================================

# Standart modules
from pathlib import Path # Crossplatform pathing
from modules.geotiff import GeoTiff # GeoTIFF format reader
import numpy as np # Work with DEM matrix
from vtkmodules.vtkCommonCore import vtkPoints # Use points cloud in 3D-world
from vtkmodules.vtkCommonDataModel import vtkPolyData # Use 3D-primitives
from vtkmodules.vtkRenderingCore import (vtkActor, vtkPolyDataMapper, vtkTexture) # Use VTK rendering
import vtk # Use other 3D-visualization features

# Own core modules
import modules.settings as cfg # Settings defenition
import modules.environment as env # Environment defenition


# ============================================
# Read .tif files of RASTER and DEM models
# Generate 3D-surface with textures
# ============================================
def GenerateEarthSurface():

    env.logger.info("Generate earth surface")

    # Draw the coordinate axes, if necessary
    if cfg.flagShowAxis:
        axes = vtk.vtkAxesActor()
        axes.SetTotalLength(100,100,100)
        axes.GetXAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
        axes.GetYAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
        axes.GetZAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
        env.actAxes.append(axes)
        env.logger.debug("Axes created")

    env.logger.info("Loop through raster files")

    for fileR in Path('.',cfg.folderRaster).glob("*.tif", case_sensitive=False):

        # Open GeoTIFF and convert coordinates to Web-Mercator
        gtfR = GeoTiff(fileR, as_crs=3857)
        boxR = gtfR.tif_bBox_converted
        boxRLeftTop = env.coordM2Float([boxR[0][0],boxR[0][1],0])
        boxRRightBottom = env.coordM2Float([boxR[1][0],boxR[1][1],0])

        # Generate a box cube arround raster
        cube = vtk.vtkCubeSource()
        cube.SetBounds(boxRLeftTop[0],boxRRightBottom[0],-1,env.boundsMax[2]+1,boxRLeftTop[2],boxRRightBottom[2])
        cube.Update()
        env.cubeRASTER.append(cube)
        if cfg.flagShowEarthPoints:
            # Put raster's box in our world
            cubeMapper = vtkPolyDataMapper()
            cubeMapper.SetInputConnection(cube.GetOutputPort())
            env.mapCube.append(cubeMapper)
            cubeActor = vtkActor()
            cubeActor.SetMapper(cubeMapper)
            cubeActor.GetProperty().SetRepresentationToWireframe()
            cubeActor.GetProperty().SetOpacity(0.2)
            cubeActor.GetProperty().SetColor(env.Colors.GetColor3d("red"))
            env.actCube.append(cubeActor)
            env.logger.debug("Box of raster created")
        box = vtk.vtkBox()
        box.SetBounds(cube.GetOutput().GetBounds())
        env.boxRASTER.append(box)

        # Load raster image from file to vtkImageReader2 object
        imageReader = env.readerFactory.CreateImageReader2(str(fileR))
        imageReader.SetFileName(fileR)
        imageReader.Update()
        env.imgrdrRASTER.append(imageReader)

        env.logger.success("Raster {} loaded", fileR.name)
        env.logger.trace("Raster box: {}",boxR)
        
        for fileD in Path('.',cfg.folderDEM).glob("*.tif", case_sensitive=False):

            # Open GeoTIFF and conver coordinates to Web-Mercator
            gtfD = GeoTiff(fileD, as_crs=3857)
        
            # Read intersection DEM and Raster bounds
            try:
                dem = np.array(gtfD.read_box(boxR, outer_points=cfg.SurfaceOutline))
            except:
                env.logger.warning("{}: DEM intersection not found", fileD.name)
                continue
            lons, lats = gtfD.get_coord_arrays(boxR, outer_points=cfg.SurfaceOutline)

            env.logger.debug("{file} intersection: {dim}",file=fileD.name, dim=dem.shape)
            env.logger.debug("@ ({src}) = ({dst})", src=[float(lons[0,0]),float(lats[0,0]),float(dem[0,0])], dst=env.coordM2Float([float(lons[0,0]),float(lats[0,0]),float(dem[0,0])]))
            env.logger.debug("@ ({src}) = ({dst})", src=[float(lons[dem.shape[0]-1,dem.shape[1]-1]),float(lats[dem.shape[0]-1,dem.shape[1]-1]),float(dem[dem.shape[0]-1,dem.shape[1]-1])], 
                                                dst=env.coordM2Float([float(lons[dem.shape[0]-1,dem.shape[1]-1]),float(lats[dem.shape[0]-1,dem.shape[1]-1]),float(dem[dem.shape[0]-1,dem.shape[1]-1])]))

            # Collect points of surface
            points = vtkPoints()
            for lon, lat in np.ndindex(dem.shape):
                points.InsertNextPoint(env.coordM2Float([lons[lon,lat],lats[lon,lat],dem[lon,lat]]))
            env.pntsDEM.append(points)
            polyDataPoints = vtkPolyData()
            polyDataPoints.SetPoints(points)
            env.pldtDEM.append(polyDataPoints)
            env.logger.debug("DEM points converted")

            if cfg.flagShowEarthPoints:
                # Generate spheres on original earth DEM points
                sphereDEM = vtk.vtkSphereSource()
                sphereDEM.SetRadius(1)
                env.sphrDEM.append(sphereDEM)
                glyphDEM = vtk.vtkGlyph3D()
                glyphDEM.SetInputData(polyDataPoints)
                glyphDEM.SetSourceConnection(sphereDEM.GetOutputPort())
                glyphDEM.ScalingOff()
                glyphDEM.Update()
                env.glphDEM.append(glyphDEM)
                pointsMapperDEM = vtkPolyDataMapper()
                pointsMapperDEM.SetInputConnection(glyphDEM.GetOutputPort())
                env.mapDEM.append(pointsMapperDEM)
                pointsActorDEM = vtkActor()
                pointsActorDEM.SetMapper(pointsMapperDEM)
                pointsActorDEM.GetProperty().SetColor(env.Colors.GetColor3d("goldenrod_light"))
                env.actDEM.append(pointsActorDEM)
                env.logger.debug("DEM source points spheres created")

            # Create surface from points
            env.logger.debug("Start DEM surface creation...")
            surface = vtk.vtkSurfaceReconstructionFilter()
            surface.SetNeighborhoodSize(cfg.SurfaceNeighbor)
            surface.SetSampleSpacing(cfg.SurfaceCells)
            surface.SetInputData(polyDataPoints)
            env.srfsfltSurface.append(surface)
            cf = vtk.vtkContourFilter()
            cf.SetInputConnection(surface.GetOutputPort())
            cf.SetValue(0, 0.0)
            env.srfsfltSurface.append(cf)
            reverse = vtk.vtkReverseSense()
            reverse.SetInputConnection(cf.GetOutputPort())
            reverse.ReverseCellsOn()
            reverse.ReverseNormalsOn()
            reverse.Update()
            env.rvrsfltSurface.append(reverse)
            polyDataSurface = reverse.GetOutput()
            env.pldtSurface.append(polyDataSurface)
            env.logger.debug("DEM surface created")
            env.logger.trace("Sample spacing = {}",surface.GetSampleSpacing())

            if cfg.flagShowEarthPoints:
                # Generate spheres on generated earth surfacee vertices
                sphereSurface = vtk.vtkSphereSource()
                sphereSurface.SetRadius(1)
                env.sphrSurface.append(sphereSurface)
                glyphSurface = vtk.vtkGlyph3D()
                glyphSurface.SetInputData(polyDataSurface)
                glyphSurface.SetSourceConnection(sphereSurface.GetOutputPort())
                glyphSurface.ScalingOff()
                glyphSurface.Update()
                env.glphSurface.append(glyphSurface)
                pointsMapperSurface = vtkPolyDataMapper()
                pointsMapperSurface.SetInputConnection(glyphSurface.GetOutputPort())
                pointsMapperSurface.ScalarVisibilityOff()
                env.mapSurface.append(pointsMapperSurface)
                pointsActorSurface = vtkActor()
                pointsActorSurface.SetMapper(pointsMapperSurface)
                pointsActorSurface.GetProperty().SetColor(env.Colors.GetColor3d("dim_grey"))
                env.actSurface.append(pointsActorSurface)
                env.logger.debug("DEM generated surface's points spheres created")

            # Shrink surface to raster bounds to prevent the formation of a seam between the stitched surfaces
            clipper = vtk.vtkClipPolyData()
            clipper.SetInputData(polyDataSurface)
            clipper.SetClipFunction(box)
            clipper.InsideOutOn()
            clipper.Update()
            env.clpprClipped.append(clipper)
            polyDataClipped = clipper.GetOutput()
            env.pldtClipped.append(polyDataClipped)
            env.logger.debug("DEM shrinked to RASTER")
            
            # Put texture on surface
            surfacePoints = polyDataClipped.GetPoints()
            env.pntsClipped.append(surfacePoints)
            texturePoints = vtk.vtkFloatArray()
            texturePoints.SetNumberOfComponents(2)
            for i in range(surfacePoints.GetNumberOfPoints()):
                pnt = surfacePoints.GetPoint(i)
                a = (pnt[0]-boxRLeftTop[0])/(boxRRightBottom[0]-boxRLeftTop[0])
                b = (pnt[2]-boxRLeftTop[2])/(boxRRightBottom[2]-boxRLeftTop[2])
                texturePoints.InsertNextTuple2(a, b)
            polyDataClipped.GetPointData().SetTCoords(texturePoints)
            env.fltarTexture.append(texturePoints)
            texture = vtkTexture()
            texture.SetInputConnection(imageReader.GetOutputPort())
            texture.InterpolateOn()
            env.txtrTexture.append(texture)
            env.logger.debug("DEM texture applied")

            # Prepare surface for view
            mapper = vtkPolyDataMapper()
            mapper.SetInputData(polyDataClipped)
            mapper.ScalarVisibilityOff()
            env.mapTexture.append(mapper)
            actor = vtkActor()
            actor.SetMapper(mapper)
            actor.SetTexture(texture)
            actor.GetProperty().SetOpacity(0.5)
            env.actTexture.append(actor)
            env.logger.success("{}: DEM ready for render",fileD.name)

            if cfg.flagSquares:
                env.logger.info("Calculate earth surface height of each voxel...")
                # Find voxels of this surface
                flBounds = polyDataClipped.GetBounds()
                [x_min, x_max, y_min, y_max] = env.boxM2Int(flBounds[0],flBounds[1],flBounds[4],flBounds[5])
                env.logger.debug("Surface bounds: {} = [{}..{}],[{}..{}]",flBounds,x_min,x_max,y_min,y_max)
                # Create cell locator
                locator = vtk.vtkCellLocator()
                locator.SetDataSet(polyDataClipped)
                locator.BuildLocator()
                pnts = vtkPoints()
                # Loop throght voxels
                for x in env.tqdm(range(x_min,x_max+1)):
                    for y in range (y_min,y_max+1):
                        # Find intersection point of vertical ray from the center of voxel and the surface
                        t = vtk.mutable(0)
                        pos = [0.0, 0.0, 0.0]
                        pcoords = [0.0, 0.0, 0.0]
                        subId = vtk.mutable(0)
                        x_center = (x+0.5)*cfg.sizeVoxel
                        y_center = (y+0.5)*cfg.sizeVoxel
                        intersected = locator.IntersectWithLine([x_center, flBounds[2], y_center], [x_center, flBounds[3], y_center], 
                                                                0.01, t, pos, pcoords, subId)
                        if intersected:
                            # Find vertical z-coordinate of first voxel over earth's surface
                            #z = np.round(pos[1]/cfg.sizeVoxel-0.4999)
                            z = np.ceil(pos[1]/cfg.sizeVoxel)
                            if z<0:
                                z = 0
                            env.squares[x,y] = z
                            # Add point to collection
                            pnts.InsertNextPoint(x_center,z*cfg.sizeVoxel,y_center)
                env.logger.success("Earth surface height calculation done")

                # Put squares on intersection points
                polyDataSquares = vtkPolyData()
                polyDataSquares.SetPoints(pnts)
                env.pldtSquares.append(polyDataSquares)
                planeSquare = vtk.vtkPlaneSource()
                planeSquare.SetOrigin(0, 0, 0)
                planeSquare.SetPoint1(cfg.sizeVoxel, 0, 0)
                planeSquare.SetPoint2(0, 0, cfg.sizeVoxel)
                env.plnSquares.append(planeSquare)
                glyphSquares = vtk.vtkGlyph3D()
                glyphSquares.SetInputData(polyDataSquares)
                glyphSquares.SetSourceConnection(planeSquare.GetOutputPort())
                glyphSquares.ScalingOff()
                glyphSquares.Update()
                env.glphSquares.append(glyphSquares)
                pointsMapperSquares = vtkPolyDataMapper()
                pointsMapperSquares.SetInputConnection(glyphSquares.GetOutputPort())
                pointsMapperSquares.ScalarVisibilityOff()
                env.mapSquares.append(pointsMapperSquares)
                pointsActorSquares = vtkActor()
                pointsActorSquares.SetMapper(pointsMapperSquares)
                pointsActorSquares.GetProperty().SetColor(env.Colors.GetColor3d("Tomato"))
                pointsActorSquares.GetProperty().SetOpacity(0.5)
                env.actSquares.append(pointsActorSquares)
