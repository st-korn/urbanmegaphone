from pathlib import Path
import json
import httpx
import time

folder = Path.cwd() / 'get-buildings' / 'lipetsk'

# Load houses
with open(folder / 'houses.dom.gosuslugi.ru.json', encoding='utf-8') as f:
    houses = json.load(f)

# Read prevois coordinates
coords = {}
try:
    with open(folder / 'pkk.txt', encoding='utf-8') as f:
        for line in f:
            data = line.rstrip().split(',')
            coords[data[0]] = (data[1],data[2])
except:
    None

# Loop through houses
for house in houses:
    if house['cadastre']:
        print (house['cadastre'])
        if house['cadastre'] in coords.keys():
            print('Already exist, skipping...')
            continue
        # Send request to pkk
        #with no_ssl_verification():
        response = httpx.get('https://pkk.rosreestr.ru/api/features/5', 
                                params={
                                    'text':house['cadastre'],
                                    'limit':40,
                                    'skip':0,
                                    'tolerance':2
                                },
                                verify=False)
        data = response.json()
        if data['total']>0:
            if 'center' in data['features'][0].keys():
                print( data['features'][0]['center']['x'], data['features'][0]['center']['y'] )
                with open(folder / 'pkk.txt', 'a', encoding='utf-8') as f:
                    f.write(house['cadastre']+","+str(data['features'][0]['center']['x'])+","+str(data['features'][0]['center']['y'])+"\n")
            else:
                print('No coordinates')
                with open(folder / 'pkk.txt', 'a', encoding='utf-8') as f:
                    f.write(house['cadastre']+",,\n")
        else:
            print('Not found')
            with open(folder / 'pkk.txt', 'a', encoding='utf-8') as f:
                    f.write(house['cadastre']+",,\n")
        time.sleep(1)