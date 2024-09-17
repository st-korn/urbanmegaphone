# ============================================
# Module: Environment defenition
# ============================================


# Modules import
# ============================================

# Standart modules
import sys # use default outputs
from loguru import logger # Write log

# Own core modules
from modules.settings import * # Settings defenition


# Global variables defenition
# ============================================

# World dimensions (meters, Web-Mercator ESPG:3857)
boundsMin = [None, None, None]
boundsMax = [None, None, None]


# Environment initialization
# ============================================

# Apply selected logging level
logger.remove()
logger.add(sys.stderr, level=logLevel)