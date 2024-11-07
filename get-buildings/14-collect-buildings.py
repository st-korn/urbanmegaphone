from pathlib import Path
import json

folder = Path.cwd() / 'get-buildings' / 'gunib'

houses = []

for file in Path('.',folder).glob("*-*-*-*-*-?.json", case_sensitive=False):
    print(file)
    with open(file, encoding='utf-8') as f:
        data = json.load(f)
        if data['total']>0:
            for item in data['items']:
                house = {}
                house['fias'] = item['address']['house']['houseGuid']
                house['address'] = item['address']['formattedAddress']
                house['cadastre'] = item['cadastreNumber']
                house['type'] = item['houseType']['houseTypeName']
                house['floors'] = item['maxFloorCount']
                house['flats'] = item['residentialPremiseCount']
                houses.append(house)

print(str(len(houses))+' houses found.')
with open(folder / 'dom.gosuslugi.ru.json', 'w', encoding='utf8') as f:
    json.dump(houses, f, ensure_ascii=False, indent=4)

