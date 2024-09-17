# ============================================
# Module: Environment defenition
# ============================================


# Modules import
# ============================================

# Standart modules
from pyproj import Transformer # Transform cartographic projections and coordinates


# Global variables defenition
# ============================================

# Transformer degrees of WGS84 datum to meters of Web-Mercator projection
# Use: transWgsMeter.transform(40, 50) => (571666.4475041276, 5539109.815175673)
transWgsMeter = Transformer.from_crs(4326, 3857)

