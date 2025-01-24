# ============================================
# Module: Generate voxels for earth ground vector buildings
# ============================================

# Modules import
# ============================================

# Standart modules
import numpy as np # For arrays of numbers
import pandas as pd # For tables of data
import geopandas as gpd # For vector objects
from vtkmodules.vtkCommonCore import vtkPoints # Use points cloud in 3D-world
from vtkmodules.vtkCommonDataModel import vtkPolyData # Use 3D-primitives
from vtkmodules.vtkRenderingCore import (vtkActor, vtkPolyDataMapper, vtkTexture) # Use VTK rendering
import vtk # Use other 3D-visualization features
import gc # For garbage collectors

# Own core modules
import modules.settings as cfg # Settings defenition
import modules.environment as env # Environment defenition
import modules.earth # Earth surface routines 


# ============================================
# Process vector buildings and generate voxel's world
# ============================================
def GenerateBuildings():

    env.logger.info("Create grid of squares on voxel's plane...")

    # Generate 2D-GeoPandas GeoDataFrame with centers of voxel's squares on the plane
    arr = np.mgrid[0:env.bounds[0], 0:env.bounds[1]]
    arr_x = np.ravel(arr[0])
    arr_y = np.ravel(arr[1])
    gdfSquares = gpd.GeoDataFrame({'x' : arr_x, 'y' : arr_y,
            'geometry' : gpd.points_from_xy((arr_x+0.5)*cfg.sizeVoxel, (arr_y+0.5)*cfg.sizeVoxel)})
    env.logger.trace(gdfSquares)
    env.logger.success("World grid created")

    env.logger.info("Convert vector buildings to our world dimensions")

    # Convert 2D-coordinates of buildings GeoDataFrame from meters (Web-Mercator ESPG:3857) to vtk's float
    env.logger.trace(env.gdfBuildings)
    env.gdfBuildings = env.gdfBuildings.set_crs(None, allow_override=True)
    env.gdfBuildings.geometry = env.gdfBuildings.geometry.scale(xfact=1.0, yfact=-1.0, zfact=1.0, origin=(0,0))
    env.logger.trace(env.gdfBuildings)
    env.gdfBuildings.geometry = env.gdfBuildings.geometry.translate(xoff=-env.boundsMin[0], yoff=env.boundsMax[1], zoff=0.0)
    env.logger.trace(env.gdfBuildings)

    # Add unique identificator of building (UIB)
    env.gdfBuildings['UIB'] = np.arange(len(env.gdfBuildings))
    env.logger.trace(env.gdfBuildings)

    env.logger.info("Split buildings to voxel's grid cells")

    # Join buildings and centers of voxel's squares GeoDataFrames
    env.gdfCells = env.gdfBuildings.sjoin(gdfSquares, how='inner', predicate='contains')
    env.logger.trace(env.gdfCells)
    del gdfSquares
    gc.collect()

    # Find ground points for each cell
    env.logger.info("Find ground points for each cell")
    env.gdfCells['GP'] = env.gdfCells.apply(lambda x : modules.earth.getGroundHeight(x['x'],x['y'],None), axis='columns')
    env.logger.trace(env.gdfCells)

    # Find nearest ground point for each buildnig
    if cfg.BuildingGroundMode != 'levels':
        pdMinGroundPoints = pd.pivot_table(data = env.gdfCells, index=['UIB'], values=['GP'], aggfunc={'GP':cfg.BuildingGroundMode})
        env.logger.trace(pdMinGroundPoints)
        env.gdfCells = env.gdfCells.merge(right=pdMinGroundPoints, how='left', left_on='UIB', right_on='UIB', suffixes=[None, '_agg'])
        env.logger.trace(env.gdfCells)

    env.logger.info("Generate voxel's of buildings")
    pnts = vtkPoints()
    for cell in env.gdfCells.itertuples():
        if cfg.BuildingGroundMode != 'levels':
            z = cell.GP_agg
        else:
            z = cell.GP
        if z is not None:
            for floor in range(int(float(cell.floors))):
                pnts.InsertNextPoint((cell.x+0.5)*cfg.sizeVoxel, (z+0.5+floor)*cfg.sizeVoxel, (cell.y+0.5)*cfg.sizeVoxel)

    # Put Voxels on intersection points
    polyDataVoxels = vtkPolyData()
    polyDataVoxels.SetPoints(pnts)
    env.pldtVoxels.append(polyDataVoxels)
    planeVoxel = vtk.vtkCubeSource()
    planeVoxel.SetXLength(cfg.sizeVoxel-0.5)
    planeVoxel.SetYLength(cfg.sizeVoxel-0.5)
    planeVoxel.SetZLength(cfg.sizeVoxel-0.5)
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
