from pathlib import Path
import json
from pyproj import Transformer
import textdistance

folder = Path.cwd() / 'get-buildings' / 'lipetsk'
transformer = Transformer.from_crs(4326, 3857,always_xy=True)

points = {}
# Loop throught yandex JSON responses
for file in Path('.',folder/'yandex').glob("*.json", case_sensitive=False):
    with open(file, encoding='utf-8') as f:
        yandex = json.load(f)
        fias = Path(file).stem

        # Fix yandex bug: find the result, who is most similar to original request of yandex geocoder
        # This is not always the first result in yandex response ¯\_(ツ)_/¯
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
        
        # Get and tranform WGS84 coordinates of best result to Web-Mercator projection
        coords = yandex['response']['GeoObjectCollection']['featureMember'][max_index]['GeoObject']['Point']['pos'].split()
        (a,b) = transformer.transform(float(coords[0]),float(coords[1]))

        # Add point to collection
        points[fias]=[a,b]

# Write points to file
with open(folder / 'yandex.json', 'w', encoding='utf8') as f:
    json.dump(points, f, ensure_ascii=False, indent=4)
print("MAP.YANDEX.RU points of FIAS collected.")