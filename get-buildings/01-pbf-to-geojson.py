import sys
sys.path.insert(0, '.')
import osmium
from pathlib import Path
from modules.geotiff import GeoTiff # GeoTIFF format reader
from modules.settings import * # Settings defenition
from loguru import logger
import geojson

pbf_file = Path.cwd() / 'get-buildings' / 'lipetsk' / 'central-fed-district-latest.osm.pbf'
json_file = Path.cwd() / 'get-buildings' / 'lipetsk' / 'lipetsk.osm.geojson'

# ------------------------------------------------------------------------------------------
# Read raster's bounds

boundsMin = [None, None] # lon, lat
boundsMax = [None, None] # lon, lat

logger.info("Find the dimensions of the world being explored")
logger.info("Loop through raster files")

for file in Path('.',folderRaster).glob("*.tif", case_sensitive=False):

    # Open GeoTIFF and conver coordinates to WGS84 degrees
    gtf = GeoTiff(file, as_crs=4326)
    
    logger.debug("{file}: ESPG:{proj} {resolution}", file=file.name, proj=gtf.crs_code, resolution=gtf.tif_shape)
    logger.debug("   {box} =>", box=gtf.tif_bBox)
    logger.debug("   => {projected}", projected=gtf.tif_bBox_converted)
    
    # Find total bounds of all rasters
    box = gtf.tif_bBox_converted
    for i in [0,1]:
        if boundsMin[i] is None: boundsMin[i] = box[0][i]
        if box[0][i] < boundsMin[i]: boundsMin[i] = box[0][i]
        if box[1][i] < boundsMin[i]: boundsMin[i] = box[1][i]
        if boundsMax[i] is None: boundsMax[i] = box[0][i]
        if box[0][i] > boundsMax[i]: boundsMax[i] = box[0][i]
        if box[1][i] > boundsMax[i]: boundsMax[i] = box[1][i]

logger.success("Bounds of rasters: {} - {}", boundsMin, boundsMax)

# ------------------------------------------------------------------------------------------
# Parse OSM export file and generate GeoJSON
Buildings = []

for o in osmium.FileProcessor(pbf_file).with_areas().with_filter(osmium.filter.KeyFilter('building')):
    if o.is_area():
        polygons = []
        inside = False
        for outer in o.outer_rings():
            rings = []
            # Make outer ring
            ring = []
            for n in outer:
                if n.location.valid():
                    ring.append((n.lon, n.lat))
                    if (n.lon>=boundsMin[0]) and (n.lon<=boundsMax[0]) and (n.lat>=boundsMin[1]) and (n.lat<=boundsMax[1]):
                        inside=True
            rings.append(ring)
            # Make inner rings
            for inner in o.inner_rings(outer):
                ring = []
                for n in inner:
                    if n.location.valid():
                        ring.append((n.lon, n.lat))
                rings.append(ring)
            # Save polygon
            polygons.append(rings)
        if inside:
            if o.is_multipolygon():
                geo = geojson.Feature( geometry=geojson.MultiPolygon(polygons) )
            else:
                geo = geojson.Feature( geometry=geojson.Polygon(polygons[0]) )
            geo.properties['building'] = o.tags['building']
            if 'addr:street' in o.tags:
                geo.properties['osm-street'] = o.tags['addr:street']
            if 'addr:housenumber' in o.tags:
                geo.properties['osm-housenumber'] = o.tags['addr:housenumber']
            if 'building:levels' in o.tags:
                geo.properties['osm-levels'] = o.tags['building:levels']
            Buildings.append(geo)
            logger.debug(geo)
            #if len(Buildings) > 100:
            #    break

feature_collection = geojson.FeatureCollection(Buildings)

with open(json_file, 'w', encoding='utf8') as f:
    geojson.dump(feature_collection, f, ensure_ascii=False, indent=4)

