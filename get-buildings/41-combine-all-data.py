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
houses_total = len(dfHouses.index)
flats_total = dfHouses['flats'].sum()
print("\nDOM.GOSUSLUGI.RU houses loaded:")
print(dfHouses)
print(houses_total," houses found.")
print(flats_total," flats found.")

# Load GeoJSON
with open(src_file, encoding='utf-8') as f:
    gjOSM = geojson.load(f)
gdfOSM = gpd.read_file(gjOSM)
print("\nOSM.ORG GeoJSON loaded:")
print(gdfOSM)

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
gdfPKK = gpd.read_file(gjPKK)
print("\nPKK.ROSREESTR.RU points of cadastre loaded:")
print(gdfPKK)

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
gdfYandex = gpd.read_file(gjYandex)
print("\nMAP.YANDEX.RU points of FIAS loaded:")
print(gdfYandex)

# Merge houses with PKK.ROSREESTR.RU and MAP.YANDEX.RU points
gdfHouses=dfHouses.merge(right=gdfPKK, how='left', left_on="cadastre", right_on="cadastre")
gdfHouses=gdfHouses.merge(right=gdfYandex, how='left', left_on="fias", right_on="fias")
gdfHouses['geometry'] = gdfHouses['geometry_x'].fillna(gdfHouses['geometry_y'])
gdfHouses = gdfHouses.drop('geometry_x', axis='columns')
gdfHouses = gdfHouses.drop('geometry_y', axis='columns')
gdfHouses = gpd.GeoDataFrame(gdfHouses)
print("\nDOM.GOSUSLUGI.RU houses are merged with PKK.ROSREESTR.RU and MAP.YANDEX.RU map points:")
print(gdfHouses)

HousesNotFoundOnMap = gdfHouses[gdfHouses['geometry'].isnull()]
if len(HousesNotFoundOnMap.index) == 0:
    print("Congratulations! All houses hava points on map!")
else:
    print("Warning: some houses form DOM.GOSUSLUGI.RU can not be found on map PKK.ROSREESTR.RU or MAP.YANDEX.RU:")
    print(HousesNotFoundOnMap)

gdfPKK = gpd.GeoDataFrame(gdfPKK.merge(right=dfHouses, how='left', left_on="cadastre", right_on='cadastre'))
gdfYandex = gpd.GeoDataFrame(gdfYandex.merge(right=dfHouses, how='left', left_on="fias", right_on='fias'))

# For each OSM building find largest house 
gdfOSM2 = gdfOSM.sjoin(gdfHouses, how="left", predicate='contains')
gdfOSM2 = gdfOSM2.sort_values('flats')
gdfOSM2 = gdfOSM2.drop_duplicates(subset='geometry', keep="last")
houses_assigned = len(gdfOSM2['fias'].dropna().unique())
flats_assigned = gdfOSM2['flats'].sum()
print("\nAssign points of the houses to OSM buildings, that are contained in them")
print(gdfOSM2)
print(houses_assigned," houses assigned (",round(houses_assigned/houses_total*100,1),"%)")
print(flats_assigned," flats assigned (",round(flats_assigned/flats_total*100,1),"%)")



# Save GeoJSON to file
gdfAll = gpd.GeoDataFrame(pd.concat([gdfOSM2, gdfPKK, gdfYandex], ignore_index=True, sort=False))
gdfAll.to_file(dst_file, driver="GeoJSON")  
print("GeoJSON saved.")
