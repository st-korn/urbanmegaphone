# ============================================
# Module: Environment defenition
# ============================================


# Modules import
# ============================================

# Standart modules
import logging # Write log

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
logging.basicConfig(level=logLevel)