from pathlib import Path
import json
import geojson
from pyproj import Transformer

folder = Path.cwd() / 'get-buildings' / 'lipetsk'
src_file = folder / 'lipetsk.osm.geojson'
dst_file = folder / 'lipetsk.pnts.geojson'

# Load houses
with open(folder / 'dom.gosuslugi.ru.json', encoding='utf-8') as f:
    houses = json.load(f)

# Load GeoJSON
with open(src_file, encoding='utf-8') as f:
    gj = geojson.load(f)

coords = {}

# Load PKK points
transformer = Transformer.from_crs(3857, 4326)
with open(folder / 'pkk.txt', encoding='utf-8') as f:
    for line in f:
        data = line.rstrip().split(',')
        if data[1]:
            (b,a) = transformer.transform(data[1],data[2])
            coords[data[0]] = (a,b)
            print(data[0],a,b)
            geo = geojson.Feature( geometry=geojson.Point((a,b)) )
            geo.properties['cadastr'] = data[0]
            gj['features'].append(geo)

# Load Yandex points
pointsYandex = []
for file in Path('.',folder/'yandex').glob("*.json", case_sensitive=False):
    with open(file, encoding='utf-8') as f:
        yandex = json.load(f)
        fias = Path(file).stem
        coords = yandex['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos'].split()
    print(fias, coords[0], coords[1])
    geo = geojson.Feature( geometry=geojson.Point((float(coords[0]), float(coords[1]))) )
    geo.properties['fias'] = fias
    gj['features'].append(geo)

# Save GeoJSON to file
with open(dst_file, 'w', encoding='utf8') as f:
    geojson.dump(gj, f, ensure_ascii=False, indent=4)

