import requests
import json
import time
from pathlib import Path

region = '1490490e-49c5-421c-9572-5673ba5d80c8'
area = None # 'e23ad948-ac70-40e7-bc90-88935d668086'
city = 'eacb5f15-1a2e-432e-904a-ca56bd635f1b' #'f073b28a-b8f8-4eee-adfd-cfbf769c6771'
settlement = None #'66453ea6-2a7d-4a39-82c5-aabaa8f7f074'
resultdir = Path.cwd() / 'get-buildings' / 'lipetsk'

def GetBuildings(request,id):
    reqURL = 'https://dom.gosuslugi.ru/homemanagement/api/rest/services/houses/public/searchByAddress'
    reqHeaders={
        'Request-GUID': '9b12126e-630e-431c-8008-9df34af6d753',
        'Session-GUID': '30d32344-e667-4a01-bdc3-8df2809d9f1c'
        }
    reqParams = {
        'pageIndex':0,
        'elementsPerPage' : 100
    }
    reqJson = {
        'regionCode' : region,
        'areaCode' : area,
        'cityCode' : city,
        'settlementCode' : settlement
    } | request
    index = 0
    total = 1
    while index<total:
        reqParams['pageIndex'] = reqParams['pageIndex']+1

        resultPath = resultdir / (id+'-'+str(reqParams['pageIndex'])+'.json')
        if resultPath.is_file():
            print("File ",resultPath," exists. Skipping")
            index = index+10
            continue

        response = requests.post(url=reqURL,headers=reqHeaders,params=reqParams,json=reqJson)
        print('Response: ',response)           
        with open(resultPath, 'wb') as fb:
            for chunk in response.iter_content(chunk_size=128):
                fb.write(chunk)
        try:
            respJson = response.json()
        except:
            print("Request pageIndex=",reqParams['pageIndex'],' failed')
            continue
        total = respJson['total']
        print('Total: ',total)

        for building in respJson['items']:
            index = index+1
            print(index, building['cadastreNumber'], building['address']['formattedAddress'])
        
        time.sleep(3)


# =======================================================================
# Get territories

response = requests.get('https://dom.gosuslugi.ru/nsi/api/rest/services/nsi/fias/v4/planning/structure/elements', 
                    params={
                        'actual':'true',
                        'itemsPerPage':1000,
                        'page':1,
                        'regionCode':region,
                        'areaCode':area,
                        'cityCode':city,
                        'settlementCode':settlement
                    })
territories = response.json()
with open(resultdir / 'territories.json', 'w', encoding='utf8') as f:
    json.dump(territories, f, ensure_ascii=False, indent=4)

# =======================================================================
# Loop through territories

for territory in territories:
    print(territory['aoGuid'], territory['formalName'])
    GetBuildings({'planningStructureElementCode' : territory['aoGuid']},territory['aoGuid'])

# =======================================================================
# Get streets

response = requests.get('https://dom.gosuslugi.ru/nsi/api/rest/services/nsi/fias/v4/streets', 
                    params={
                        'actual':'true',
                        'itemsPerPage':1000,
                        'page':1,
                        'regionCode':region,
                        'areaCode':area,
                        'cityCode':city,
                        'settlementCode':settlement
                    })
streets = response.json()
with open(resultdir / 'streets.json', 'w', encoding='utf8') as f:
    json.dump(streets, f, ensure_ascii=False, indent=4)

# =======================================================================
# Loop through streets

for street in streets:
    print(street['aoGuid'], street['formalName'])
    GetBuildings({'streetCode' : street['aoGuid']},street['aoGuid'])
