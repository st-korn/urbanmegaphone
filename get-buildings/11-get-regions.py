import requests

response = requests.get('https://dom.gosuslugi.ru/nsi/api/rest/services/nsi/fias/v4/regions')
regions = response.json()

for region in regions:
    print(region['aoGuid'], region['formalName'], region['shortName'])