# ============================================
# Module: Generate voxels for earth ground vector buildings
# ============================================

# Modules import
# ============================================

# Standart modules
from loguru import logger # Write log

# Own core modules
from modules.settings import * # Settings defenition
from modules.environment import * # Environment defenition


# ============================================
# Process vector buildings and generate voxel's world
# ============================================
def GenerateBuildings():

    logger.info("Generate buildings")


    for x in range(bounds[0]):
        for y in range(bounds[1]):
            continue