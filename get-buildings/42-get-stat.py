from pathlib import Path
import json
import geojson
import tqdm

folder = Path.cwd() / 'get-buildings' / 'lipetsk'
src_file = folder / 'lipetsk.pnts.geojson'

# Load houses
flats = 0
with open(folder / 'houses.dom.gosuslugi.ru.json', encoding='utf-8') as f:
    houses = json.load(f)
for house in houses:
    flats = flats + house['flats']
print("DOM.GOSUSLUGI.RU houses loaded.")
print("Total living houses found: ",len(houses))
print("Total flats found: ",flats)

# Load GeoJSON
with open(src_file, encoding='utf-8') as f:
    gj = geojson.load(f)

# Loop throught all OSM shapes
assigned_flats = 0
pbar = tqdm.tqdm(total = len(gj['features']))
for feature in gj['features']:
    if (feature['geometry']['type'] == "Polygon") or (feature['geometry']['type'] == "MultiPolygon"):
        if 'flats' in feature['properties']:
            assigned_flats = assigned_flats + feature['properties']['flats']
            for house in list(houses):
                if house['fias'] == feature['properties']['fias']:
                    houses.remove(house)
    pbar.update(1)
print("Assigned to building: "+str(assigned_flats)+" flats")

houses_sorted = sorted(houses, key=lambda d: d['flats'], reverse=True)

# Write forgotten houses to file
with open(folder / 'unassigned_houses.txt', 'w', encoding='utf8') as f:
    for house in houses_sorted:
        print(house['address'],' - ',house['flats'], file=f)
