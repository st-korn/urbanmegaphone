# ============================================
# Module: Read raster and DEM data and generate the earth's surface
# ============================================

# Modules import
# ============================================

# Standart modules
from pathlib import Path # Crossplatform pathing
from modules.geotiff import GeoTiff # GeoTIFF format reader
import numpy as np # Work with DEM matrix
from vtkmodules.vtkCommonCore import vtkPoints # Use points clouds in 3D-world
from vtkmodules.vtkCommonDataModel import vtkPolyData # Use 3D-primitives
from vtkmodules.vtkRenderingCore import (vtkActor, vtkPolyDataMapper, vtkTexture) # Use VTK rendering
import vtk # Use other 3D-visualization features
import geopandas as gpd # For vector objects
from shapely.ops import unary_union # For combine vector objects 
import gc # For garbage collectors
from vtkmodules.vtkIOXML import vtkXMLPolyDataWriter # For export VTK objects to files

# Own core modules
import modules.settings as cfg # Settings defenition
import modules.environment as env # Environment defenition


# ============================================
# Read .tif files of RASTER and DEM models
# Generate 3D-surface with textures
# ============================================
def GenerateEarthSurface():

    env.logger.info("Generating the earth's surface:")

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

    for fileR in Path('.',cfg.folderRASTER).glob("*.tif", case_sensitive=False):

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

        env.logger.info("Raster {} loading...", fileR.name)
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
            env.logger.debug("@ ({src}) = ({dst})", src=[float(lons[0,0]),float(lats[0,0]),float(dem[0,0])], 
                                                    dst=env.coordM2Float([float(lons[0,0]),float(lats[0,0]),float(dem[0,0])]))
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
            actor.GetProperty().SetOpacity(1) #(1 if cfg.ShowSquares=='none' else 0.5)
            env.actTexture.append(actor)
            env.strTextureFileName.append(fileR.name)
            env.logger.success("{}: DEM ready for render",fileD.name)

            # Export surface to ParaView-compatible format
            fileV = Path('.',cfg.folderOUTPUT, f"{len(env.mapTexture)}_{fileR.name}.vtp")
            exporter = vtk.vtkXMLPolyDataWriter()
            exporter.SetInputData(mapper.GetInput())
            exporter.SetFileName(fileV)
            exporter.Write()
            env.logger.success("Surface exported to {}",fileV)

            # Create cell locator
            locator = vtk.vtkCellLocator()
            locator.SetDataSet(polyDataClipped)
            locator.BuildLocator()
            env.lctrClipped.append(locator)

            # Prepare squares of the whole earth's surface
            if cfg.ShowSquares == 'full':
                env.logger.info("Calculate the earth's surface height of each square...")
                # Find voxels of this surface
                flBounds = polyDataClipped.GetBounds()
                [x_min, x_max, y_min, y_max] = env.boxM2Int(flBounds[0],flBounds[1],flBounds[4],flBounds[5])
                env.logger.debug("Surface bounds: {} = [{}..{}],[{}..{}]",flBounds,x_min,x_max,y_min,y_max)
                # Loop throght voxels
                for x in env.tqdm(range(x_min,x_max+1)):
                    for y in range (y_min,y_max+1):
                        # Find intersection point of vertical ray from the center of voxel and the surface
                        getGroundHeight(x,y,locator)

# ============================================
# Calculate buffer zones around living buildings if ShowSquares mode is 'buffer'
# IN: no arguments
# OUT: no return values. Modify pntsSquares_unassigned vtkPoints collection of environment.py
# ============================================
def PrepareLivingBuffer():
    if cfg.ShowSquares == 'buffer':
        # Make buffer zones around buildings
        env.logger.info("Locate buffer zones around living buildings...")
        gsBuffer = env.gdfBuildings[ env.gdfBuildings['flats']>0 ].geometry.buffer(cfg.BufferRadius)
        env.logger.trace(gsBuffer)

        # Join buffer zones and centers of voxel's squares GeoDataFrames
        boundary = gpd.GeoSeries(unary_union(gsBuffer))
        gdfBuffer = gpd.GeoDataFrame(geometry=boundary)
        env.logger.trace(boundary)
        env.logger.trace(gdfBuffer)
        env.gdfBuffersLiving = env.gdfCells.sjoin(gdfBuffer, how='inner',predicate='within')
        env.logger.trace(env.gdfBuffersLiving)
        env.logger.success("{} from {} cells are in buffer zones", 
                           env.printLong(len(env.gdfBuffersLiving.index)), env.printLong(len(env.gdfCells.index)))

        # Generate squares of buffer zones
        env.logger.info("Calculate ground height for each cell in buffer zone around living buildings...")
        for cell in env.tqdm(env.gdfBuffersLiving.itertuples(), total=len(env.gdfBuffersLiving.index)):
            getGroundHeight(cell.x,cell.y,None)

        # Clear memory
        del gsBuffer
        del gdfBuffer
        gc.collect()

# ============================================
# Find int Z vertical coordiate of intersection 
# the vertical ray from the center of voxel (x, y) and the earth's surface on VTK space
# Can search on specifec surface (using locator) or on all surfaces in VTK space
# Store found coordinate in env.ground array
# IN:
# x : int X horizontal coordinate of desired voxel
# y : int Y horizontal coordinate of desired voxel
# locator: vtkCellLocator if we need to search on one specific surface
#          or None if we need to search on all surfaces
# OUT:
# integer Z vertical coordinate of first voxel over earth's surface
#         or None if no intersection found
# ============================================
def getGroundHeight(x, y, locator):
    # Fail if (x,y) is out of bounds voxel's world
    if (x<0) or (x>=env.bounds[0]) or (y<0) or (y>=env.bounds[1]):
        return None
    # Is current ground position just calculated and stored?
    z = env.ground[x*env.bounds[1]+y]
    if z >= 0:
        return z # Yes, it was stored
    # No, we need to calculate them
    # Find center of voxel
    x_center = (x+0.5)*cfg.sizeVoxel
    y_center = (y+0.5)*cfg.sizeVoxel
    # Prepare search engine using localor
    t = vtk.mutable(0)
    pos = [0.0, 0.0, 0.0]
    pcoords = [0.0, 0.0, 0.0]
    subId = vtk.mutable(0)
    # How many surfaces we need to search
    if locator is not None:
        locators = [locator] # One surface
    else:
        locators = env.lctrClipped # All surfaces
    # Loop through surfaces and search intersection on each
    for lctr in locators:
        intersected = lctr.IntersectWithLine([x_center, (-1)*cfg.sizeVoxel, y_center], 
                                        [x_center, (env.bounds[2]+1)*cfg.sizeVoxel, y_center], 
                                            0.01, t, pos, pcoords, subId)
        # if intersection found - use first one
        if intersected:
            z = np.ceil(pos[1]/cfg.sizeVoxel)
            if z<0:
                z = 0
            env.ground[x*env.bounds[1]+y] = int(z)
            return z
    return None

# ============================================
# Generate necessary square VTK objects from vtkPoints 
# with the specified color and opacity to the earth's surface vizualization
# IN: 
# points - vtkPoints collection
# color - tuple of three float number 0..1 for R,G,B values of color (0% .. 100%)
# opacity - float number 0..1 for opacity value (0% .. 100%)
# OUT:
# No return values. Modify variables of environment.py in which VTK objects for further vizualization
# ============================================
def VizualizePartOfSquares(points, color, opacity):
    # Put squares on points of the earth's surface
    polyDataSquares = vtkPolyData()
    polyDataSquares.SetPoints(points)
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
    pointsActorSquares.GetProperty().SetColor(color)
    pointsActorSquares.GetProperty().SetOpacity(opacity)
    env.actSquares.append(pointsActorSquares)

# ============================================
# Generate squares of the earth's surface vizualization
# from previously calculated and classified points
# ============================================
def VizualizeAllSquares():
    env.logger.info("Build squares of the earth's surface...")
    
    # Loop throught grid of the earth's surface cells audibility
    idx2D = 0
    for x in env.tqdm(range(env.bounds[0])):
        for y in range(env.bounds[1]):
            z = env.ground[idx2D]
            uib = env.uib[idx2D]
            # Fix the earth's surface height if it is under the building
            if uib >= 0:
                if cfg.BuildingGroundMode != 'levels':
                    z = min(z, env.buildings[uib*env.sizeBuilding+1]) # Use building's ground level
            # Create points for squares of the earth's surface
            if env.audibility2D[idx2D]>1:
                env.pntsSquares_full.InsertNextPoint((x+0.5)*cfg.sizeVoxel, (z+0.1)*cfg.sizeVoxel, (y+0.5)*cfg.sizeVoxel)
            elif env.audibility2D[idx2D]>0:
                env.pntsSquares_only.InsertNextPoint((x+0.5)*cfg.sizeVoxel, (z+0.1)*cfg.sizeVoxel, (y+0.5)*cfg.sizeVoxel)
            elif env.audibility2D[idx2D]<0:
                env.pntsSquares_no.InsertNextPoint((x+0.5)*cfg.sizeVoxel, (z+0.1)*cfg.sizeVoxel, (y+0.5)*cfg.sizeVoxel)
            elif (env.audibility2D[idx2D]==0) and (cfg.ShowSquares == 'full'):
                env.pntsSquares_no.InsertNextPoint((x+0.5)*cfg.sizeVoxel, (z+0.1)*cfg.sizeVoxel, (y+0.5)*cfg.sizeVoxel) # not env.pntsSquares_unassigned
            idx2D = idx2D + 1

    VizualizePartOfSquares(env.pntsSquares_full, env.Colors.GetColor3d("Green"), 0.5)
    VizualizePartOfSquares(env.pntsSquares_only, env.Colors.GetColor3d("Gold"), 0.5)
    VizualizePartOfSquares(env.pntsSquares_no, env.Colors.GetColor3d("Tomato"), 0.5)

    env.vtkPoints2CSV('sq_full.csv', env.pntsSquares_full)
    env.vtkPoints2CSV('sq_only.csv', env.pntsSquares_only)
    env.vtkPoints2CSV('sq_no.csv', env.pntsSquares_no)
    env.logger.success("Squares exported")

    totalSquaresCount = env.pntsSquares_full.GetNumberOfPoints() + env.pntsSquares_only.GetNumberOfPoints() \
                      + env.pntsSquares_no.GetNumberOfPoints()
    audibilitySquaresCount = env.pntsSquares_full.GetNumberOfPoints() + env.pntsSquares_only.GetNumberOfPoints()
    env.writeStat("=========================================================================================================")
    env.writeStat("|| URBAN ENVIRONMENT STATISTIC:")
    env.writeStat("|| {} ({}) audibility squares, {} ({}) non-audibility squares".format(
                       env.printLong(audibilitySquaresCount), 
                       f'{audibilitySquaresCount/totalSquaresCount:.0%}',
                       env.printLong(env.pntsSquares_no.GetNumberOfPoints()), 
                       f'{env.pntsSquares_no.GetNumberOfPoints()/totalSquaresCount:.0%}' ) )
    env.writeStat("|| {} ({}) of {} squares analyzed".format(
                       env.printLong(totalSquaresCount), f'{totalSquaresCount/(env.bounds[0]*env.bounds[1]):.0%}', env.printLong(env.bounds[0]*env.bounds[1]) ), "info")
    env.writeStat("=========================================================================================================")
