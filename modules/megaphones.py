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

# Own core modules
import modules.settings as cfg # Settings defenition
import modules.environment as env # Environment defenition
import modules.earth # Earth surface routines

# ============================================
# Process vector buildings and generate voxel's world
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
    env.logger.trace(env.gdfMegaphones)

    # Join megaphones and cells of buildings GeoDataFrames
    env.gdfMegaphones = env.gdfMegaphones.sjoin_nearest(env.gdfCells, how='left', max_distance=cfg.distanceMegaphoneAndBuilding)
    env.logger.trace(env.gdfMegaphones)

    # Calculate height of megaphones
    for cell in env.gdfMegaphones.itertuples():
        if pd.isna(cell.floors):
            x = int(round(cell.geometry.x/cfg.sizeVoxel))
            y = int(round(cell.geometry.y/cfg.sizeVoxel))
            z = int(modules.earth.getGroundHeight( x, y, None ))
            env.logger.warning("Megaphone too far from the any building: {}. Use {} voxels as ground and {} voxels as height",cell,z,height)
            env.pntsMegaphones_standalone_cones.InsertNextPoint((x+0.5)*cfg.sizeVoxel, (z+0.5)*cfg.sizeVoxel, (y+0.5)*cfg.sizeVoxel)
        else:
            x = cell.x
            y = cell.y
            if cfg.BuildingGroundMode != 'levels':
                z = cell.GP_agg
            else:
                z = cell.GP
            height = int(round( cell.floors * cfg.sizeFloor / cfg.sizeVoxel ))
            env.pntsMegaphones_buildings_cones.InsertNextPoint((x+0.5)*cfg.sizeVoxel, (z+0.5+height)*cfg.sizeVoxel, (y+0.5)*cfg.sizeVoxel)
        env.pntsMegaphones_spheres.InsertNextPoint((x+0.5)*cfg.sizeVoxel, (z+0.5+height+0.5)*cfg.sizeVoxel, (y+0.5)*cfg.sizeVoxel)

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

