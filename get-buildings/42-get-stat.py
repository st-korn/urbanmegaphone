from pathlib import Path
import json
import geojson
import tqdm

folder = Path.cwd() / 'get-buildings' / 'lipetsk'
src_file = folder / 'lipetsk.pnts.geojson'

# Load houses
with open(folder / 'dom.gosuslugi.ru.json', encoding='utf-8') as f:
    houses = json.load(f)
print("DOM.GOSUSLUGI.RU houses loaded.")
print("Total living houses found: ",len(houses))

# Load GeoJSON
with open(src_file, encoding='utf-8') as f:
    gj = geojson.load(f)

# Loop throught all OSM shapes
assigned_flats = 0
pbar = tqdm.tqdm(total = len(gj['features']))
for feature in gj['features']:
    for house in houses:
        if (feature['geometry']['type'] == "Polygon") or (feature['geometry']['type'] == "MultiPolygon"):
            if 'fias' in feature['properties']:
                if house['fias'] == feature['properties']['fias']:
                    assigned_flats = assigned_flats + house['flats']
                    houses.remove(house)
                    break
    pbar.update(1)
print("Assigned to building: "+str(assigned_flats)+" flats")

# Write forgotten houses to file
with open(folder / 'unassigned_houses.txt', 'w', encoding='utf8') as f:
    print("-----------------------------------------------------------", file=f)
    print("Apartment buildings:", file=f)
    for house in houses:
        if house['flats'] > 1:
            print(house['address'],' - ',house['flats'], file=f)
    print("-----------------------------------------------------------", file=f)
    print("Individual houses:", file=f)
    for house in houses:
        if house['flats'] == 1:
            print(house['address'],' - ',house['flats'], file=f)

