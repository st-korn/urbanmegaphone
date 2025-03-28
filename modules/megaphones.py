# ============================================
# Module: Load megaphones data and calculate audibility for buildings and surface
# ============================================

# Modules import
# ============================================

# Standart modules
import multiprocessing as mp # Use multiprocessing
import ctypes # Use primitive datatypes for multiprocessing data exchange
from pathlib import Path # Crossplatform pathing
import numpy as np # For arrays of numbers
import pandas as pd # For tables of data
import geopandas as gpd # For vector objects
from vtkmodules.vtkCommonDataModel import vtkPolyData # Use 3D-primitives
from vtkmodules.vtkRenderingCore import (vtkActor, vtkPolyDataMapper) # Use VTK rendering
import vtk # Use other 3D-visualization features
from shapely.ops import unary_union # For combine vector objects 
import gc # For garbage collectors

# Own core modules
import modules.settings as cfg # Settings defenition
import modules.environment as env # Environment defenition
import modules.earth # The earth's surface routines

# ============================================
# Load vector points of megaphones
# ============================================
def LoadMegaphones():

    env.logger.info("Load points of megaphones")
    gdfPoints = []
    for file in Path('.',cfg.folderMEGAPHONES).glob("*.geojson", case_sensitive=False):
        env.logger.debug("Load points of megaphones: {file}", file=file)
        gdfPoints.append(gpd.read_file(file))
    env.gdfMegaphones = gpd.GeoDataFrame(pd.concat(gdfPoints, ignore_index=True, sort=False))
    env.logger.success("{} megaphones loaded", len(env.gdfMegaphones.index))
    env.logger.trace(env.gdfMegaphones)

    # Convert 2D-coordinates of megaphones GeoDataFrame from meters (Web-Mercator ESPG:3857) to vtk's float
    env.gdfMegaphones = env.gdfMegaphones.set_crs(None, allow_override=True)
    env.gdfMegaphones.geometry = env.gdfMegaphones.geometry.scale(xfact=1.0, yfact=-1.0, zfact=1.0, origin=(0,0))
    env.gdfMegaphones.geometry = env.gdfMegaphones.geometry.translate(xoff=-env.boundsMin[0], yoff=env.boundsMax[1], zoff=0.0)
    env.logger.trace(env.gdfMegaphones)

    # Remove megaphones outside of currend world
    env.gdfMegaphones = env.gdfMegaphones.loc[env.gdfMegaphones.within(env.plgnBounds)]
    # Add unique identificator of megaphone (UIM)
    env.gdfMegaphones['UIM'] = np.arange(len(env.gdfMegaphones.index))
    env.logger.success("{} megaphones left after removing megaphones outside of current world area", len(env.gdfMegaphones.index))
    env.logger.trace(env.gdfMegaphones)

    # Join megaphones and cells of buildings GeoDataFrames
    env.gdfCellsMegaphones = env.gdfMegaphones.sjoin_nearest(env.gdfCellsBuildings, how='left', max_distance=cfg.distanceMegaphoneAndBuilding)
    env.logger.success("{} from {} cells are under megaphones", 
                       env.printLong(len(env.gdfCellsMegaphones.index)), env.printLong(len(env.gdfCells.index)))
    env.logger.trace(env.gdfCellsMegaphones)

    # Calculate height of stanalone megaphones (tqdm is not needed)
    env.gdfCellsMegaphones['x'] = env.gdfCellsMegaphones['x'].fillna(env.gdfCellsMegaphones['geometry'].apply(lambda g : int(round(g.x/cfg.sizeVoxel))))
    env.gdfCellsMegaphones['y'] = env.gdfCellsMegaphones['y'].fillna(env.gdfCellsMegaphones['geometry'].apply(lambda g : int(round(g.y/cfg.sizeVoxel))))
    env.logger.trace(env.gdfCellsMegaphones)

    # Generate VTK's objects for megaphones
    for cell in env.gdfCellsMegaphones.itertuples(): # (tqdm is not needed)
        if pd.isna(cell.floors):
            z = int(modules.earth.getGroundHeight( int(cell.x), int(cell.y), None ))
            height = cfg.heightStansaloneMegaphone / cfg.sizeVoxel
            env.pntsMegaphones_standalone_cones.InsertNextPoint((cell.x+0.5)*cfg.sizeVoxel, (z-0.5)*cfg.sizeVoxel+cfg.heightStansaloneMegaphone/2, (cell.y+0.5)*cfg.sizeVoxel)
            env.pntsMegaphones_spheres.InsertNextPoint((cell.x+0.5)*cfg.sizeVoxel, (z-0.5)*cfg.sizeVoxel+cfg.heightStansaloneMegaphone, (cell.y+0.5)*cfg.sizeVoxel)
            env.logger.warning("Megaphone too far from any building: {}. Use {} voxels ground and {} voxels height",
                               cell.geometry, z, f'{height:.1f}')
        else:
            if cfg.BuildingGroundMode != 'levels':
                z = cell.GP_agg
            else:
                z = cell.GP
            height = int(round( cell.floors * cfg.sizeFloor / cfg.sizeVoxel ))
            env.pntsMegaphones_buildings_cones.InsertNextPoint((cell.x+0.5)*cfg.sizeVoxel, (z+0.5+height)*cfg.sizeVoxel, (cell.y+0.5)*cfg.sizeVoxel)
            env.pntsMegaphones_spheres.InsertNextPoint((cell.x+0.5)*cfg.sizeVoxel, (z+0.5+height+0.5)*cfg.sizeVoxel, (cell.y+0.5)*cfg.sizeVoxel)

    # Echo distance of maxium possible audibility
    env.logger.success("Maximum distance of possible audibility is {} meter in the buildings and {} meter on the streets", 
                       f'{cfg.distancePossibleAudibilityInt:.1f}', f'{cfg.distancePossibleAudibilityExt:.1f}' )
    if cfg.distancePossibleAudibilityInt > cfg.distancePossibleAudibilityExt:
        env.logger.error("Audibility on the streets is less than in the buildings. It's impossible")

    # Prepare for genetaion of zones of possible audibility

    # Join megaphones and buildings GeoDataFrames
    env.gdfMegaphones = env.gdfMegaphones.sjoin_nearest(env.gdfBuildings, how='left', max_distance=cfg.distanceMegaphoneAndBuilding)
    env.logger.trace(env.gdfMegaphones)
    
    # Add buildings polygones to each cell-megaphone row
    env.gdfMegaphones = env.gdfMegaphones.merge(right=env.gdfBuildings, how='left', left_on="UIB", right_on="UIB", suffixes=[None, '_buildings'])
    env.gdfMegaphones['geometry_buildings'] = env.gdfMegaphones['geometry_buildings'].fillna(env.gdfMegaphones['geometry'])
    env.gdfMegaphones = env.gdfMegaphones.set_geometry(col='geometry_buildings').drop(columns='geometry').rename_geometry('geometry')
    env.logger.trace(env.gdfMegaphones)

    # Generate zones of possible audibility in the buildings
    env.logger.info("Locate zones of possible audibility in the buildings...")

    # Calculate buffer around all megaphones
    env.gdfBuffersMegaphonesInt = env.gdfMegaphones.copy()
    env.gdfBuffersMegaphonesInt = env.gdfBuffersMegaphonesInt.drop(labels='index_right', axis='columns')
    env.gdfBuffersMegaphonesInt['geometry'] = env.gdfBuffersMegaphonesInt['geometry'].buffer(distance=cfg.distancePossibleAudibilityInt)
    env.logger.trace(env.gdfBuffersMegaphonesInt)

    # Join buffer zones and centers of voxel's squares GeoDataFrames
    env.gdfBuffersMegaphonesInt = env.gdfCells.sjoin(env.gdfBuffersMegaphonesInt, how='inner',predicate='within')
    env.logger.trace(env.gdfBuffersMegaphonesInt)
    env.logger.trace(env.gdfBuffersMegaphonesInt.dtypes)

    # Calculate count of unique cells
    gdfBuffersMegaphonesInt = env.gdfBuffersMegaphonesInt.groupby(['x','y']).size().reset_index()
    env.logger.success("{} from {} unique cells in zones of possible audibility", 
                       env.printLong(len(gdfBuffersMegaphonesInt.index)), env.printLong(len(env.gdfCells.index)))
    env.logger.success("{} cell-megaphone combinations", env.printLong(len(env.gdfBuffersMegaphonesInt.index)))

    # Generate zones of possible audibility at the streets
    env.logger.info("Locate zones of possible audibility at the streets...")

    # Calculate buffer around all megaphones
    env.gdfBuffersMegaphonesExt = env.gdfMegaphones.copy()
    env.gdfBuffersMegaphonesExt = env.gdfBuffersMegaphonesExt.drop(labels='index_right', axis='columns')
    env.gdfBuffersMegaphonesExt['geometry'] = env.gdfBuffersMegaphonesExt['geometry'].buffer(distance=cfg.distancePossibleAudibilityExt)
    env.logger.trace(env.gdfBuffersMegaphonesExt)

    # Join buffer zones and centers of voxel's squares GeoDataFrames
    env.gdfBuffersMegaphonesExt = env.gdfCells.sjoin(env.gdfBuffersMegaphonesExt, how='inner',predicate='within')
    env.logger.trace(env.gdfBuffersMegaphonesExt)
    env.logger.trace(env.gdfBuffersMegaphonesExt.dtypes)

    # Calculate count of unique cells
    gdfBuffersMegaphonesExt = env.gdfBuffersMegaphonesExt.groupby(['x','y']).size().reset_index()
    env.logger.success("{} from {} unique cells in zones of possible audibility", 
                       env.printLong(len(gdfBuffersMegaphonesExt.index)), env.printLong(len(env.gdfCells.index)))
    env.logger.success("{} cell-megaphone combinations", env.printLong(len(env.gdfBuffersMegaphonesExt.index)))

    # Allocate memory and store megaphones and their zones
    env.logger.info("Allocate memory and store megaphones and their zones...")
    env.countMegaphones = len(env.gdfMegaphones.index)
    env.leftMegaphones = mp.RawArray(ctypes.c_ubyte, env.countMegaphones)
    env.countMegaphonesCells = len(env.gdfCellsMegaphones.index)
    env.MegaphonesCells = mp.RawArray(ctypes.c_long, env.countMegaphonesCells*env.sizeCell)
    env.MegaphonesCells_count = mp.RawArray(ctypes.c_long, env.countMegaphones)
    env.MegaphonesCells_index = mp.RawArray(ctypes.c_long, env.countMegaphones)
    env.countMegaphonesBuffersInt = len(env.gdfBuffersMegaphonesInt.index)
    env.MegaphonesBuffersInt = mp.RawArray(ctypes.c_long, env.countMegaphonesBuffersInt*env.sizeCell)
    env.MegaphonesBuffersInt_count = mp.RawArray(ctypes.c_long, env.countMegaphones)
    env.MegaphonesBuffersInt_index = mp.RawArray(ctypes.c_long, env.countMegaphones)
    env.countMegaphonesBuffersExt = len(env.gdfBuffersMegaphonesExt.index)
    env.MegaphonesBuffersExt = mp.RawArray(ctypes.c_long, env.countMegaphonesBuffersExt*env.sizeCell)
    env.MegaphonesBuffersExt_count = mp.RawArray(ctypes.c_long, env.countMegaphones)
    env.MegaphonesBuffersExt_index = mp.RawArray(ctypes.c_long, env.countMegaphones)
    env.countChecks = mp.RawArray(ctypes.c_ulonglong, env.countMegaphones)
    env.madeChecks = mp.RawArray(ctypes.c_ulonglong, env.countMegaphones)
    env.totalChecks = 0
    indexCells = 0
    indexBuffersInt = 0
    indexBuffersExt = 0
    for uim in env.tqdm(range(env.countMegaphones)):
        env.leftMegaphones[uim] = 1
        megaphoneCells = env.gdfCellsMegaphones.loc[env.gdfCellsMegaphones['UIM'] == uim]
        env.MegaphonesCells_count[uim] = len(megaphoneCells.index)
        env.MegaphonesCells_index[uim] = indexCells
        for cell in megaphoneCells.itertuples():
            env.MegaphonesCells[indexCells] = int(cell.x)
            env.MegaphonesCells[indexCells+1] = int(cell.y)
            indexCells = indexCells + env.sizeCell
            modules.earth.getGroundHeight(int(cell.x), int(cell.y), None)
        megaphoneBuffersInt = env.gdfBuffersMegaphonesInt.loc[env.gdfBuffersMegaphonesInt['UIM'] == uim]
        env.MegaphonesBuffersInt_count[uim] = len(megaphoneBuffersInt.index)
        env.MegaphonesBuffersInt_index[uim] = indexBuffersInt
        for cell in megaphoneBuffersInt.itertuples():
            env.MegaphonesBuffersInt[indexBuffersInt] = int(cell.x)
            env.MegaphonesBuffersInt[indexBuffersInt+1] = int(cell.y)
            indexBuffersInt = indexBuffersInt + env.sizeCell
            modules.earth.getGroundHeight(int(cell.x), int(cell.y), None)
        megaphoneBuffersExt = env.gdfBuffersMegaphonesExt.loc[env.gdfBuffersMegaphonesExt['UIM'] == uim]
        env.MegaphonesBuffersExt_count[uim] = len(megaphoneBuffersExt.index)
        env.MegaphonesBuffersExt_index[uim] = indexBuffersExt
        for cell in megaphoneBuffersExt.itertuples():
            env.MegaphonesBuffersExt[indexBuffersExt] = int(cell.x)
            env.MegaphonesBuffersExt[indexBuffersExt+1] = int(cell.y)
            indexBuffersExt = indexBuffersExt + env.sizeCell
            modules.earth.getGroundHeight(int(cell.x), int(cell.y), None)
        env.countChecks[uim] = (env.MegaphonesCells_count[uim] * env.MegaphonesBuffersInt_count[uim]) + \
                               (env.MegaphonesCells_count[uim] * env.MegaphonesBuffersExt_count[uim])
        env.totalChecks = env.totalChecks + env.countChecks[uim]
        del megaphoneCells
        del megaphoneBuffersInt
        del megaphoneBuffersExt
    env.logger.success('{} megaphones, {} cells under megaphones stored', 
                       env.printLong(env.countMegaphones), env.printLong(env.countMegaphonesCells) )
    env.logger.success('{} cells under buildings, {} cells at the streets in megaphones zones  of possible audibility stored',  
                       env.printLong(env.countMegaphonesBuffersInt), env.printLong(env.countMegaphonesBuffersExt) )
    env.logger.success('{} total checks will be performed', env.printLong(env.totalChecks))

    # Select livings buffer zone, excluded megaphones potential audibility zone
    if cfg.ShowSquares == 'buffer':
        env.logger.info("Exclude living zones without possible audibility...")
        gdfLivingWithoutAudibility = env.gdfBuffersLiving.merge(gdfBuffersMegaphonesExt, how='left', on=['x','y'], indicator=True)
        gdfLivingWithoutAudibility = gdfLivingWithoutAudibility.loc[gdfLivingWithoutAudibility['_merge'] == 'left_only']
        for cell in env.tqdm(gdfLivingWithoutAudibility.itertuples(), total=len(gdfLivingWithoutAudibility.index)):
            env.audibility2D[cell.x*env.bounds[1]+cell.y] = -1
        env.logger.success('{} from {} living cells excluded', 
                           env.printLong(len(gdfLivingWithoutAudibility.index)), env.printLong(len(env.gdfBuffersLiving.index)) )
        del gdfLivingWithoutAudibility

    # Clear temporary variables
    del gdfBuffersMegaphonesInt
    del gdfBuffersMegaphonesExt
    gc.collect()

# ============================================
# Generate necessary VTK objects of megaphones from vtkPoints
# with the specified color and opacity to vizualization
# IN: 
# points - vtkPoints collection
# glyph - vtkObject object's glyph
# color - tuple of three float number 0..1 for R,G,B values of color (0% .. 100%)
# opacity - float number 0..1 for opacity value (0% .. 100%)
# OUT:
# No return values. Modify variables of environment.py in which VTK objects for further vizualization
# ============================================
def VizualizePartOfMegaphones(points, glyph, color, opacity):
    # Put Voxels on intersection points
    polyDataMegaphones = vtkPolyData()
    polyDataMegaphones.SetPoints(points)
    env.pldtMegaphones.append(polyDataMegaphones)
    glyphMegaphone = vtk.vtkGlyph3D()
    glyphMegaphone.SetInputData(polyDataMegaphones)
    glyphMegaphone.SetSourceConnection(glyph.GetOutputPort())
    glyphMegaphone.ScalingOff()
    glyphMegaphone.Update()
    env.glphMegaphones.append(glyphMegaphone)
    pointsMapperMegaphones = vtkPolyDataMapper()
    pointsMapperMegaphones.SetInputConnection(glyphMegaphone.GetOutputPort())
    pointsMapperMegaphones.ScalarVisibilityOff()
    env.mapMegaphones.append(pointsMapperMegaphones)
    pointsActorMegaphones = vtkActor()
    pointsActorMegaphones.SetMapper(pointsMapperMegaphones)
    pointsActorMegaphones.GetProperty().SetColor(color)
    pointsActorMegaphones.GetProperty().SetOpacity(opacity)
    env.actMegaphones.append(pointsActorMegaphones)

# ============================================
# Generate voxels of building vizualization
# from previously calculated and classified points
# ============================================
def VizualizeAllMegaphones():
    env.logger.info("Build megaphones...")

    # Build body of buildings megaphones
    coneMegaphone = vtk.vtkConeSource()
    coneMegaphone.SetDirection(0, 1, 0)
    coneMegaphone.SetHeight(cfg.sizeVoxel)
    coneMegaphone.SetRadius(cfg.sizeVoxel/4)
    env.cnMegaphones.append(coneMegaphone)
    VizualizePartOfMegaphones(env.pntsMegaphones_buildings_cones, coneMegaphone, env.Colors.GetColor3d("GreenYellow"), 1.0)

    # Build body of standalone megaphones
    coneMegaphone = vtk.vtkConeSource()
    coneMegaphone.SetDirection(0, 1, 0)
    coneMegaphone.SetHeight(cfg.heightStansaloneMegaphone)
    coneMegaphone.SetRadius(cfg.sizeVoxel)
    env.cnMegaphones.append(coneMegaphone)
    VizualizePartOfMegaphones(env.pntsMegaphones_standalone_cones, coneMegaphone, env.Colors.GetColor3d("GreenYellow"), 1.0)

    # Build head of megaphones
    sphereMegaphone = vtk.vtkSphereSource()
    sphereMegaphone.SetRadius(cfg.sizeVoxel/4)
    env.sphMegaphones.append(sphereMegaphone)
    VizualizePartOfMegaphones(env.pntsMegaphones_spheres, sphereMegaphone, env.Colors.GetColor3d("GreenYellow"), 1.0)

    # Export megaphones to CSV
    env.vtkPoints2CSV('mgphn_buildings.csv', env.pntsMegaphones_buildings_cones)
    env.vtkPoints2CSV('mgphn_standalone.csv', env.pntsMegaphones_standalone_cones)
    env.vtkPoints2CSV('mgphn_spehres.csv', env.pntsMegaphones_spheres)
    env.logger.success("Megaphones exported")

    env.writeStat("{} megaphones on {} buildings, {} standalone megaphones".format(
                  env.printLong(env.pntsMegaphones_buildings_cones.GetNumberOfPoints()),
                  env.countMegaphones - env.pntsMegaphones_standalone_cones.GetNumberOfPoints(),
                  env.printLong(env.pntsMegaphones_standalone_cones.GetNumberOfPoints())) )