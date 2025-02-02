# ============================================
# Module: Generate voxels for earth ground vector buildings
# ============================================

# Modules import
# ============================================

# Standart modules
import numpy as np # For arrays of numbers
import pandas as pd # For tables of data
import geopandas as gpd # For vector objects
from vtkmodules.vtkCommonDataModel import vtkPolyData # Use 3D-primitives
from vtkmodules.vtkRenderingCore import (vtkActor, vtkPolyDataMapper) # Use VTK rendering
import vtk # Use other 3D-visualization features

# Own core modules
import modules.settings as cfg # Settings defenition
import modules.environment as env # Environment defenition
import modules.earth # Earth surface routines


# ============================================
# Process vector buildings and generate voxel's world
# ============================================
def GenerateBuildings():

    env.logger.info("Convert vector buildings to our world dimensions...")

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
    env.logger.success("{} vector buildings found", f'{len(env.gdfBuildings.index):_}')

    env.logger.info("Split buildings to voxel's grid cells...")

    # Join buildings and centers of voxel's squares GeoDataFrames
    env.gdfCells = env.gdfBuildings.sjoin(env.gdfSquares, how='inner', predicate='contains')
    env.logger.trace(env.gdfCells)
    env.logger.success("{} from {} cells are under buildings", f'{len(env.gdfCells.index):_}', f'{len(env.gdfSquares.index):_}')

    # Find ground points for each cell
    env.logger.info("Looking for ground points of each building")
    env.gdfCells['GP'] = env.gdfCells.apply(lambda x : modules.earth.getGroundHeight(x['x'],x['y'],None), axis='columns')
    env.logger.trace(env.gdfCells)

    # Find common ground point for each buildnig
    if cfg.BuildingGroundMode != 'levels':
        pdMinGroundPoints = pd.pivot_table(data = env.gdfCells, index=['UIB'], values=['GP'], aggfunc={'GP':cfg.BuildingGroundMode})
        env.logger.trace(pdMinGroundPoints)
        env.gdfCells = env.gdfCells.merge(right=pdMinGroundPoints, how='left', left_on='UIB', right_on='UIB', suffixes=[None, '_agg'])
        env.gdfCells = env.gdfCells.drop(labels='index_right', axis='columns')
        env.logger.trace(env.gdfCells)
        del pdMinGroundPoints

    # Generate voxels of buildings
    env.logger.info("Calculate squares's of buildings")
    for cell in env.tqdm(env.gdfCells.itertuples(), total=len(env.gdfCells.index)):
        env.UIB[cell.x,cell.y] = cell.UIB
        if cfg.BuildingGroundMode != 'levels':
            if np.isnan(cell.GP_agg):
                continue
            env.bottomfloor[cell.x,cell.y] = cell.GP_agg
        else:
            if np.isnan(cell.GP):
                continue
            env.bottomfloor[cell.x,cell.y] = cell.GP
        env.topfloor[cell.x,cell.y] = env.bottomfloor[cell.x,cell.y] + int(round( cell.floors * cfg.sizeFloor / cfg.sizeVoxel )) -1


# ============================================
# Generate necessary voxel VTK objects from vtkPoints 
# with the specified color and opacity to buildings vizualization
# IN: 
# points - vtkPoints collection
# color - tuple of three float number 0..1 for R,G,B values of color (0% .. 100%)
# opacity - float number 0..1 for opacity value (0% .. 100%)
# OUT:
# No return values. Modify variables of environment.py in which VTK objects for further vizualization
# ============================================
def VizualizePartOfVoxels(points, color, opacity):
    # Put Voxels on intersection points
    polyDataVoxels = vtkPolyData()
    polyDataVoxels.SetPoints(points)
    env.pldtVoxels.append(polyDataVoxels)
    planeVoxel = vtk.vtkCubeSource()
    planeVoxel.SetXLength(cfg.sizeVoxel-cfg.gapVoxel)
    planeVoxel.SetYLength(cfg.sizeVoxel-cfg.gapVoxel)
    planeVoxel.SetZLength(cfg.sizeVoxel-cfg.gapVoxel)
    env.cbVoxels.append(planeVoxel)
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
    pointsActorVoxels.GetProperty().SetColor(color)
    pointsActorVoxels.GetProperty().SetOpacity(opacity)
    env.actVoxels.append(pointsActorVoxels)

# ============================================
# Generate voxels of building vizualization
# from previously calculated and classified points
# ============================================
def VizualizeAllVoxels():
    env.logger.info("Build voxels of buildings")
    VizualizePartOfVoxels(env.pntsVoxels_yes, env.Colors.GetColor3d("Green"), 1)
    VizualizePartOfVoxels(env.pntsVoxels_no, env.Colors.GetColor3d("Tomato"), 1)
    VizualizePartOfVoxels(env.pntsVoxels_living, env.Colors.GetColor3d("Gold"), 1)
    VizualizePartOfVoxels(env.pntsVoxels_industrial, env.Colors.GetColor3d("Gray"), 1)

'''
    # Generate voxels of buildings
    env.logger.info("Generate voxel's of buildings...")
    for cell in env.tqdm(env.gdfCells.itertuples(), total=len(env.gdfCells.index)):
        if cfg.BuildingGroundMode != 'levels':
            z = cell.GP_agg
        else:
            z = cell.GP
        if z is not None:
            height = int(round( cell.floors * cfg.sizeFloor / cfg.sizeVoxel ))
            for floor in range(height):
                if cell.flats>0:
                    env.pntsVoxels_living.InsertNextPoint((cell.x+0.5)*cfg.sizeVoxel, (z+0.5+floor)*cfg.sizeVoxel, (cell.y+0.5)*cfg.sizeVoxel)
                else:
                    env.pntsVoxels_industrial.InsertNextPoint((cell.x+0.5)*cfg.sizeVoxel, (z+0.5+floor)*cfg.sizeVoxel, (cell.y+0.5)*cfg.sizeVoxel)
    env.logger.success("{} living and {} industial voxels created", f'{env.pntsVoxels_living.GetNumberOfPoints():_}', f'{env.pntsVoxels_industrial.GetNumberOfPoints():_}')
'''