from pathlib import Path
import json
import geojson
from pyproj import Transformer
from shapely.geometry import shape, Point
from shapely.ops import transform
from shapely import distance
import textdistance
import tqdm

folder = Path.cwd() / 'get-buildings' / 'lipetsk'
src_file = folder / 'lipetsk.osm.geojson'
dst_file = folder / 'lipetsk.pnts.geojson'
transformer = Transformer.from_crs(4326, 3857,always_xy=True)

# Load houses
with open(folder / 'dom.gosuslugi.ru.json', encoding='utf-8') as f:
    houses = json.load(f)
print("DOM.GOSUSLUGI.RU houses loaded.")

# Load GeoJSON
with open(src_file, encoding='utf-8') as f:
    gj = geojson.load(f)
# Loop throught all OSM shapes
for feature in gj['features']:
    polygon = shape(feature['geometry'])
    polygon = transform(transformer.transform,polygon)
    feature['geometry'] = polygon
print("OSM.ORG GeoJSON loaded.")

# Load PKK points
pointsPKK = []
with open(folder / 'pkk.txt', encoding='utf-8') as f:
    for line in f:
        data = line.rstrip().split(',')
        if data[1]:
            # Add point to collection
            geo = geojson.Feature( geometry=geojson.Point((float(data[1]),float(data[2]))) )
            geo.properties['cadastr'] = data[0]
            pointsPKK.append(geo)
print("PKK.ROSREESTR.RU points of cadastre loaded.")

# Load Yandex points
pointsYandex = []
for file in Path('.',folder/'yandex').glob("*.json", case_sensitive=False):
    with open(file, encoding='utf-8') as f:
        yandex = json.load(f)
        fias = Path(file).stem
        # Fix yandex bug: find the result, who is most similar to original request of yandex geocoder
        # This is not always the first result
        request = yandex['response']['GeoObjectCollection']['metaDataProperty']['GeocoderResponseMetaData']['request']
        addresses = []
        for fm in yandex['response']['GeoObjectCollection']['featureMember']:
            addresses.append(fm['GeoObject']['metaDataProperty']['GeocoderMetaData']['Address']['formatted'])
        similarity = []
        for address in addresses:
            similarity.append(textdistance.cosine.normalized_similarity(request,address))
        max_similarity = max(similarity)
        max_index = similarity.index(max_similarity)
        if max_index>0:
            print("Fix: "+request+" | was: "+addresses[0]+" | become: "+addresses[max_index])
        # Get coordinates of best result
        coords = yandex['response']['GeoObjectCollection']['featureMember'][max_index]['GeoObject']['Point']['pos'].split()
        (a,b) = transformer.transform(float(coords[0]),float(coords[1]))
        # Add point to collection
        geo = geojson.Feature( geometry=geojson.Point((a, b)) )
        geo.properties['fias'] = fias
        pointsYandex.append(geo)
print("MAP.YANDEX.RU points of FIAS loaded.")


# Loop throught all OSM shapes
print("--- Starting to analyze polygons\n")
pbar = tqdm.tqdm(total = len(gj['features']))
for feature in gj['features']:
    # Get polygon
    polygon = shape(feature['geometry'])
    description = "Polygon:"
    if 'osm-street' in feature['properties']:
        description = description + " " + feature['properties']['osm-street']
    if 'osm-housenumber' in feature['properties']:
        description = description + " " + feature['properties']['osm-housenumber']
    pbar.write("\n"+description)
    # Loop throught pointsYandex
    found = ''
    for geo_point in pointsYandex:
        point = Point(geo_point['geometry']['coordinates'])
        if polygon.contains(point):
            found = geo_point.properties['fias']
            pbar.write("Point found contains: "+found)
            break
        elif distance(polygon,point) < 5:
            found = geo_point.properties['fias']
            pbar.write("Point found near in "+str(distance(polygon,point))+": "+found)
            break
    if found:
        house = None
        for h in houses:
            if h['fias'] == found:
                house = h
                pbar.write("House found: "+house['address'])
                break
        if house:
            # Add properties to shape
            feature['properties']['cadastre']=house['cadastre']
            feature['properties']['address']=house['address']
            feature['properties']['fias']=house['fias']
            feature['properties']['type']=house['type']
            feature['properties']['floors']=house['floors']
            feature['properties']['flats']=house['flats']
            pbar.update(1)
            continue
    # Loop throught pointsPKK
    found = ''
    for geo_point in pointsPKK:
        point = Point(geo_point['geometry']['coordinates'])
        if polygon.contains(point):
            found = geo_point.properties['cadastr']
            pbar.write("Point found contains: "+found)
            break
        elif distance(polygon,point) < 5:
            found = geo_point.properties['cadastr']
            pbar.write("Point found near in "+str(distance(polygon,point))+": "+found)
            break
    if found:
        house = None
        for h in houses:
            if h['cadastre'] == found:
                house = h
                pbar.write("House found: "+house['address'])
                break
        if house:
            # Add properties to shape
            feature['properties']['cadastre']=house['cadastre']
            feature['properties']['address']=house['address']
            feature['properties']['fias']=house['fias']
            feature['properties']['type']=house['type']
            feature['properties']['floors']=house['floors']
            feature['properties']['flats']=house['flats']
            pbar.update(1)
            continue

    pbar.update(1)

print("--- Polygons analysis completed.\n")


# Save GeoJSON to file
gj['features'] = gj['features'] + pointsPKK + pointsYandex 
gj['crs'] = {"type":"EPSG", "properties":{"code":3857}}
with open(dst_file, 'w', encoding='utf8') as f:
    geojson.dump(gj, f, ensure_ascii=False, indent=4)
print("GeoJSON saved.")
