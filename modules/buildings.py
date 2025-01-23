# ============================================
# Module: Generate voxels for earth ground vector buildings
# ============================================

# Modules import
# ============================================

# Standart modules
from shapely.geometry import Point
import geopandas as gpd # For vector objects
from vtkmodules.vtkCommonCore import vtkPoints # Use points cloud in 3D-world
from vtkmodules.vtkCommonDataModel import vtkPolyData # Use 3D-primitives
from vtkmodules.vtkRenderingCore import (vtkActor, vtkPolyDataMapper, vtkTexture) # Use VTK rendering
import vtk # Use other 3D-visualization features

# Own core modules
import modules.settings as cfg # Settings defenition
import modules.environment as env # Environment defenition


# ============================================
# Process vector buildings and generate voxel's world
# ============================================
def GenerateBuildings():

    env.logger.info("Create grid of squares on voxel's plane...")

    # Generate 2D-GeoPandas GeoDataFrame with centers of voxel's squares on the plane
    centresSquares = []
    xSquares = []
    ySquares = []
    for x in env.tqdm(range(env.bounds[0])):
        for y in range(env.bounds[1]):
            centresSquares.append(Point((x+0.5)*cfg.sizeVoxel, (y+0.5)*cfg.sizeVoxel))
            xSquares.append(x)
            ySquares.append(y)
    env.gdfSquares = gpd.GeoDataFrame({'geometry': centresSquares, 'x': xSquares, 'y': ySquares})
    env.logger.trace(env.gdfSquares)
    env.logger.success("World grid created")

    env.logger.info("Convert vector buildings to our world dimensions")

    # Convert 2D-coordinates of buildings GeoDataFrame from meters (Web-Mercator ESPG:3857) to vtk's float
    env.logger.trace(env.gdfBuildings)
    env.gdfBuildings = env.gdfBuildings.set_crs(None, allow_override=True)
    env.gdfBuildings.geometry = env.gdfBuildings.geometry.scale(xfact=1.0, yfact=-1.0, zfact=1.0, origin=(0,0))
    env.logger.trace(env.gdfBuildings)
    env.gdfBuildings.geometry = env.gdfBuildings.geometry.translate(xoff=-env.boundsMin[0], yoff=env.boundsMax[1], zoff=0.0)
    env.logger.trace(env.gdfBuildings)

    env.logger.info("Split buildings to voxel's grid cells")

    # Join buildings and centers of voxel's squares GeoDataFrames
    env.gdfCells = env.gdfBuildings.sjoin(env.gdfSquares, how='inner', predicate='contains')
    env.logger.trace(env.gdfCells)

    env.logger.info("Generate voxel's of buildings")
    pnts = vtkPoints()
    for cell in env.gdfCells.itertuples():
        for floor in range(int(float(cell.floors))):
            pnts.InsertNextPoint((cell.x+0.5)*cfg.sizeVoxel, (env.squares[cell.x,cell.y]+0.5+floor)*cfg.sizeVoxel, (cell.y+0.5)*cfg.sizeVoxel)

    # Put Voxels on intersection points
    polyDataVoxels = vtkPolyData()
    polyDataVoxels.SetPoints(pnts)
    env.pldtVoxels.append(polyDataVoxels)
    planeVoxel = vtk.vtkCubeSource()
    planeVoxel.SetXLength(cfg.sizeVoxel-0.1)
    planeVoxel.SetYLength(cfg.sizeVoxel-0.1)
    planeVoxel.SetZLength(cfg.sizeVoxel-0.1)
    env.plnVoxels.append(planeVoxel)
    glyphVoxels = vtk.vtkGlyph3D()
    glyphVoxels.SetInputData(polyDataVoxels)
    glyphVoxels.SetSourceConnection(planeVoxel.GetOutputPort())
    glyphVoxels.ScalingOff()
    glyphVoxels.Update()
    env.glphVoxels.append(glyphVoxels)
    pointsMapperVoxels = vtkPolyDataMapper()
    pointsMapperVoxels.SetInputConnection(glyphVoxels.GetOutputPort())
    pointsMapperVoxels.ScalarVisibilityOff()
    env.mapVoxels.append(pointsMapperVoxels)
    pointsActorVoxels = vtkActor()
    pointsActorVoxels.SetMapper(pointsMapperVoxels)
    pointsActorVoxels.GetProperty().SetColor(env.Colors.GetColor3d("Green"))
    pointsActorVoxels.GetProperty().SetOpacity(1)
    env.actVoxels.append(pointsActorVoxels)
