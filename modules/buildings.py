# ============================================
# Module: Generate voxels for earth ground vector buildings
# ============================================

# Modules import
# ============================================

# Standart modules

# Own core modules
import modules.settings as cfg # Settings defenition
import modules.environment as env # Environment defenition


# ============================================
# Process vector buildings and generate voxel's world
# ============================================
def GenerateBuildings():

    env.logger.info("Create buildings")
    for house in env.gdfBuildings.itertuples():
        #env.logger.debug(house.geometry.bounds)




        #env.logger.debug(house)
        continue

    for x in range(env.bounds[0]):
        for y in range(env.bounds[1]):
            continue