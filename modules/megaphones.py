# ============================================
# Module: Load megaphones data and calculate audibility for buildings and surface
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
def LoadMegaphones():

    env.logger.info("Convert vector buildings to our world dimensions...")

