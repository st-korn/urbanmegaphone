from pathlib import Path
import json
import geojson
import pandas as pd
import geopandas as gpd

folder = Path.cwd() / 'get-buildings' / 'lipetsk'
src_file = folder / 'lipetsk.osm.geojson'
dst_file = folder / 'lipetsk.pnts.geojson'

# Load DOM.GOSUSLUGI.RU houses data
with open(folder / 'houses.dom.gosuslugi.ru.json', encoding='utf-8') as f:
    houses = json.load(f)
dfHouses = pd.DataFrame.from_dict(houses) 
print(dfHouses)
print("DOM.GOSUSLUGI.RU houses loaded.")

# Load GeoJSON
with open(src_file, encoding='utf-8') as f:
    gjOSM = geojson.load(f)
gdfOSM = gpd.read_file(gjOSM, driver='GeoJSON')
print(gdfOSM)
print("OSM.ORG GeoJSON loaded.")

# Load PKK points
pointsPKK = []
with open(folder / 'pkk.txt', encoding='utf-8') as f:
    for line in f:
        data = line.rstrip().split(',')
        if data[1]:
            # Add point to collection
            geo = geojson.Feature( geometry=geojson.Point((float(data[1]),float(data[2]))) )
            geo.properties['cadastre'] = data[0]
            pointsPKK.append(geo)
gjPKK = geojson.FeatureCollection(pointsPKK)
gjPKK['crs'] = {"type":"EPSG", "properties":{"code":3857}}
gdfPKK = gpd.read_file(gjPKK, driver='GeoJSON')
print(gdfPKK)
print("PKK.ROSREESTR.RU points of cadastre loaded.")

# Load Yandex points
pointsYandex = []
with open(folder / 'yandex.json', encoding='utf-8') as f:
    yandex = json.load(f)
    for fias in yandex:
        geo = geojson.Feature( geometry=geojson.Point((yandex[fias][0], yandex[fias][1])) )
        geo.properties['fias'] = fias
        pointsYandex.append(geo)
gjYandex = geojson.FeatureCollection(pointsYandex)
gjYandex['crs'] = {"type":"EPSG", "properties":{"code":3857}}
gdfYandex = gpd.read_file(gjYandex, driver='GeoJSON')
print(gdfYandex)
print("MAP.YANDEX.RU points of FIAS loaded.")

'''
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
'''

# Save GeoJSON to file
gjOSM['features'] = gjOSM['features'] + gjPKK['features'] + gjYandex['features']
with open(dst_file, 'w', encoding='utf8') as f:
    geojson.dump(gjOSM, f, ensure_ascii=False, indent=4)
print("GeoJSON saved.")
