# ============================================
# Module: Load megaphones data and calculate audibility for buildings and surface
# ============================================

# Modules import
# ============================================

# Standart modules
from pathlib import Path # Crossplatform pathing
import pandas as pd # For tables of data
import geopandas as gpd # For vector objects

# Own core modules
import modules.settings as cfg # Settings defenition
import modules.environment as env # Environment defenition

# ============================================
# Process vector buildings and generate voxel's world
# ============================================
def LoadMegaphones():

    env.logger.info("Convert vector buildings to our world dimensions...")
    gdfPoints = []
    for file in Path('.',cfg.folderMEGAPHONES).glob("*.geojson", case_sensitive=False):
        env.logger.debug("Load points of megaphones: {file}", file=file)
        gdfPoints.append(gpd.read_file(file))
    env.gdfMegaphones = gpd.GeoDataFrame(pd.concat(gdfPoints, ignore_index=True, sort=False))
    env.logger.success("{} megaphones loaded.", len(env.gdfMegaphones.index))

