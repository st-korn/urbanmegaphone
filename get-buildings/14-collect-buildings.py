from pathlib import Path
import json

folder = Path.cwd() / 'get-buildings' / 'lipetsk'

houses = []
counter = 0
apartment_buildings = 0
individual_houses = 0
total_flats = 0

for file in Path('.',folder).glob("*-*-*-*-*-?.json", case_sensitive=False):
    print(file)
    with open(file, encoding='utf-8') as f:
        data = json.load(f)
        if data['total']>0:
            for item in data['items']:
                counter = counter + 1
                house = {}
                house['fias'] = item['address']['house']['houseGuid']
                house['address'] = item['address']['formattedAddress']
                house['cadastre'] = item['cadastreNumber']
                house['type'] = item['houseType']['houseTypeName']
                # Covert floors to integer
                try:
                    floors = int(item['maxFloorCount'])
                except:
                    floors = 1
                house['floors'] = floors
                # Assign one flat to individual houses
                try:
                    flats = int(item['residentialPremiseCount'])
                    if flats ==0:
                        flats = 1
                except:
                    flats = 1
                house['flats'] = flats
                # Search for duplicates
                found = False
                for idx2, house2 in enumerate(houses):
                    if house['address'] == house2['address']:
                        if house2['flats'] < house['flats']:
                            houses[idx2]['flats'] = house['flats']
                        if house2['floors'] is None:
                            houses[idx2]['floors'] = house['floors']
                        elif house['floors'] is not None:
                            if house2['floors'] < house['floors']:
                                houses[idx2]['floors'] = house['floors']
                        if house2['cadastre'] is None:
                            houses[idx2]['cadastre'] = house['cadastre']
                        houses[idx2]['fias'] = house['fias']
                        found = True
                if not(found):
                    houses.append(house)
                    if house['flats'] == 1:
                        individual_houses = individual_houses + 1
                    else:
                        apartment_buildings = apartment_buildings + 1
                    total_flats = total_flats + house['flats']

print("Total living houses found: ",counter)
print("Unique living houses: ",len(houses))
print("including ",apartment_buildings," apartment buildings and ",individual_houses," individual houses")
print("Total flats found: ",total_flats)

with open(folder / 'houses.dom.gosuslugi.ru.json', 'w', encoding='utf8') as f:
    json.dump(houses, f, ensure_ascii=False, indent=4)

