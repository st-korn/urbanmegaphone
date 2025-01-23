# ============================================
# Module: Generate voxels for earth ground vector buildings
# ============================================

# Modules import
# ============================================

# Standart modules
import geojson
import geopandas as gpd # For vector objects

# Own core modules
import modules.settings as cfg # Settings defenition
import modules.environment as env # Environment defenition


# ============================================
# Process vector buildings and generate voxel's world
# ============================================
def GenerateBuildings():

    env.logger.info("Create buildings...")

    # Generate 2D-GeoPandas GeoDataFrame with centers of voxel's squares on the plane
    centresSquares = []
    for x in env.tqdm(range(env.bounds[0])):
        for y in range(env.bounds[1]):
            geo = geojson.Feature( geometry=geojson.Point(((x+0.5)*cfg.sizeVoxel, (y+0.5)*cfg.sizeVoxel)) )
            geo.properties['x'] = x
            geo.properties['y'] = y
            centresSquares.append(geo)
    gjSquares = geojson.FeatureCollection(centresSquares)
    gdfSquares = gpd.read_file(gjSquares)
    env.logger.debug(gdfSquares)

    # Convert 2D-coordinates of buildings GeoDataFrame from meters (Web-Mercator ESPG:3857) to vtk's float
    env.logger.debug(env.gdfBuildings)
    env.gdfBuildings['geometry'] = env.gdfBuildings['geometry'].scale(1, -1)
    env.gdfBuildings['geometry'] = env.gdfBuildings['geometry'].transform(-env.boundsMin[0],env.boundsMax[1])
    env.logger.debug(env.gdfBuildings)
    '''
    for house in env.gdfBuildings.itertuples():
        [lon_min, lat_min, lon_max, lat_max] = house.geometry.bounds
        [x_vtk_min, y_vtk_min, z_vtk_min] = env.coordM2Float([lon_min, lat_max, 0])
        [x_vtk_max, y_vtk_max, z_vtk_max] = env.coordM2Float([lon_max, lat_min, 0])
        [x_min, x_max, y_min, y_max] = env.boxM2Int(x_vtk_min,x_vtk_max,z_vtk_min,z_vtk_max)
        if x_min is None: # Skip building, if it is out of voxel's world
            continue
        env.logger.trace("{} => {} => {}", house.geometry.bounds, [x_vtk_min, z_vtk_min, x_vtk_max, z_vtk_max], [x_min, x_max, y_min, y_max])
        break



        #env.logger.debug(house)
        continue

    for x in range(env.bounds[0]):
        for y in range(env.bounds[1]):
            continue
    '''