# ============================================
# Module: Load megaphones data and calculate audibility for buildings and surface
# ============================================

# Modules import
# ============================================

# Standart modules
from pathlib import Path # Crossplatform pathing
import pandas as pd # For tables of data
import geopandas as gpd # For vector objects
from vtkmodules.vtkCommonDataModel import vtkPolyData # Use 3D-primitives
from vtkmodules.vtkRenderingCore import (vtkActor, vtkPolyDataMapper) # Use VTK rendering
import vtk # Use other 3D-visualization features
from shapely.ops import unary_union # For combine vector objects 
import gc # For garbage collectors
import math 

# Own core modules
import modules.settings as cfg # Settings defenition
import modules.environment as env # Environment defenition
import modules.earth # Earth surface routines

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
    env.logger.success("{} megaphones loaded.", len(env.gdfMegaphones.index))
    env.logger.trace(env.gdfMegaphones)

    # Convert 2D-coordinates of megaphones GeoDataFrame from meters (Web-Mercator ESPG:3857) to vtk's float
    env.gdfMegaphones = env.gdfMegaphones.set_crs(None, allow_override=True)
    env.gdfMegaphones.geometry = env.gdfMegaphones.geometry.scale(xfact=1.0, yfact=-1.0, zfact=1.0, origin=(0,0))
    env.gdfMegaphones.geometry = env.gdfMegaphones.geometry.translate(xoff=-env.boundsMin[0], yoff=env.boundsMax[1], zoff=0.0)
    env.logger.trace(env.gdfMegaphones)

    # Remove megaphones outside of currend world
    env.gdfMegaphones = env.gdfMegaphones.loc[env.gdfMegaphones.within(env.plgnBounds)]
    env.logger.info("{} megaphones left after removing megaphones outside of current area", len(env.gdfMegaphones.index))
    env.logger.trace(env.gdfMegaphones)

    # Join megaphones and cells of buildings GeoDataFrames
    env.gdfMegaphonesCells = env.gdfMegaphones.sjoin_nearest(env.gdfCells, how='left', max_distance=cfg.distanceMegaphoneAndBuilding)
    env.logger.info("{} from {} cells are under megaphones", f'{len(env.gdfMegaphonesCells.index):_}', f'{len(env.gdfSquares.index):_}')
    env.logger.trace(env.gdfMegaphonesCells)

    # Calculate height of stanalone megaphones
    env.gdfMegaphonesCells['x'] = env.gdfMegaphonesCells['x'].fillna(env.gdfMegaphonesCells['geometry'].apply(lambda g : int(round(g.x/cfg.sizeVoxel))))
    env.gdfMegaphonesCells['y'] = env.gdfMegaphonesCells['y'].fillna(env.gdfMegaphonesCells['geometry'].apply(lambda g : int(round(g.y/cfg.sizeVoxel))))
    env.logger.trace(env.gdfMegaphonesCells)

    # Generate VTK's objects for megaphones
    for cell in env.gdfMegaphonesCells.itertuples():
        if pd.isna(cell.floors):
            env.logger.warning("Megaphone too far from the any building: {}. Use {} voxels as ground and {} voxels as height",cell,z,height)
            z = int(modules.earth.getGroundHeight( int(cell.x), int(cell.y), None ))
            env.pntsMegaphones_standalone_cones.InsertNextPoint((cell.x+0.5)*cfg.sizeVoxel, (z-0.5)*cfg.sizeVoxel+cfg.heightStansaloneMegaphone/2, (cell.y+0.5)*cfg.sizeVoxel)
            env.pntsMegaphones_spheres.InsertNextPoint((cell.x+0.5)*cfg.sizeVoxel, (z-0.5)*cfg.sizeVoxel+cfg.heightStansaloneMegaphone, (cell.y+0.5)*cfg.sizeVoxel)
        else:
            if cfg.BuildingGroundMode != 'levels':
                z = cell.GP_agg
            else:
                z = cell.GP
            height = int(round( cell.floors * cfg.sizeFloor / cfg.sizeVoxel ))
            env.pntsMegaphones_buildings_cones.InsertNextPoint((cell.x+0.5)*cfg.sizeVoxel, (z+0.5+height)*cfg.sizeVoxel, (cell.y+0.5)*cfg.sizeVoxel)
            env.pntsMegaphones_spheres.InsertNextPoint((cell.x+0.5)*cfg.sizeVoxel, (z+0.5+height+0.5)*cfg.sizeVoxel, (cell.y+0.5)*cfg.sizeVoxel)


# ============================================
# Calculate audibility of squares and voxels
# ============================================
def CalculateAudibility():

    # Generate zones of possible audibility
    env.logger.info("Generate zones of possible audibility")

    # Join megaphones and buildings GeoDataFrames
    env.gdfMegaphones = env.gdfMegaphones.sjoin_nearest(env.gdfBuildings, how='left', max_distance=cfg.distanceMegaphoneAndBuilding)
    env.logger.debug(env.gdfMegaphones)
    
    # Add buildings polygones to each cell-megaphone row
    env.gdfMegaphones = env.gdfMegaphones.merge(right=env.gdfBuildings, how='left', left_on="UIB", right_on="UIB", suffixes=[None, '_buildings'])
    env.gdfMegaphones['geometry_buildings'] = env.gdfMegaphones['geometry_buildings'].fillna(env.gdfMegaphones['geometry'])
    env.gdfMegaphones = env.gdfMegaphones.set_geometry(col='geometry_buildings').drop(columns='geometry').rename_geometry('geometry')
    #env.gdfMegaphones = env.gdfMegaphones.rename(columns={'x':'x_megaphone', 'y':'y_megaphone', 'UIB':'UIB_megaphone'})[
    #                                    ['x_megaphone', 'y_megaphone', 'UIB_megaphone', 'geometry']]
    #env.gdfMegaphones['x_megaphone'] = env.gdfMegaphones['x_megaphone'].astype(int)
    #env.gdfMegaphones['y_megaphone'] = env.gdfMegaphones['y_megaphone'].astype(int)
    env.logger.debug(env.gdfMegaphones)
    
    # Calculate buffer around all megaphones
    env.gdfBuffersMegaphones = env.gdfMegaphones.copy()
    env.gdfBuffersMegaphones = env.gdfBuffersMegaphones.drop(labels='index_right', axis='columns')
    env.gdfBuffersMegaphones['geometry'] = env.gdfBuffersMegaphones['geometry'].buffer(distance=cfg.distancePossibleAudibility)    
    env.logger.debug(env.gdfBuffersMegaphones)

    #gsBuffer = env.gdfMegaphones.geometry
    #env.logger.trace(gsBuffer)

    # Join buffer zones and centers of voxel's squares GeoDataFrames
    env.logger.info("Find cells in buffer zones of possible audibility")
    #boundary = gpd.GeoSeries(unary_union(gsBuffer))
    #gdfBuffer = gpd.GeoDataFrame(geometry=boundary)
    #env.logger.trace(boundary)
    #env.logger.trace(gdfBuffer)
    env.gdfBuffersMegaphones = env.gdfSquares.sjoin(env.gdfBuffersMegaphones, how='inner',predicate='within')
    env.logger.debug(env.gdfBuffersMegaphones)
    env.logger.debug(env.gdfBuffersMegaphones.dtypes)

    # Loop through squares of buffer zones
    env.logger.info("Loop through squares of buffer zones...")
    a = 0
    for cell in env.tqdm(env.gdfBuffersMegaphones.itertuples(), total=len(env.gdfBuffersMegaphones.index)):
        # Find megaphones of possible audibility on current cell
        #gdfFoundMegaphones = env.gdfMegaphones.contains(cell.geometry)
        #env.logger.debug("{} = {}",cell,gdfFoundMegaphones)
        #for m in env.gdfMegaphones.itertuples():
        a = a+1
            #math.sqrt( (m.x_megaphone-cell.x)**2 + (m.y_megaphone-cell.y)**2 )
        # Create a square
        z = modules.earth.getGroundHeight(cell.x,cell.y,None)
        if z is not None:
            env.pntsSquares_yes.InsertNextPoint((cell.x+0.5)*cfg.sizeVoxel, (z+0.5)*cfg.sizeVoxel, (cell.y+0.5)*cfg.sizeVoxel)
    env.logger.debug(a)
    env.logger.success("{} from {} cells are in buffer zones of possible audibility", f'{len(env.gdfBuffersMegaphones.index):_}', f'{len(env.gdfSquares.index):_}')

    # Clear memory
    #del gsBuffer
    #del gdfBuffer
    #gc.collect()


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
    env.logger.info("Build megaphones")

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

