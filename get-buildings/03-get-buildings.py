region = '1490490e-49c5-421c-9572-5673ba5d80c8'
area = None # 'e23ad948-ac70-40e7-bc90-88935d668086'
city = 'eacb5f15-1a2e-432e-904a-ca56bd635f1b' #'f073b28a-b8f8-4eee-adfd-cfbf769c6771'
settlement = None #'66453ea6-2a7d-4a39-82c5-aabaa8f7f074'

import requests

response = requests.post('https://dom.gosuslugi.ru/homemanagement/api/rest/services/houses/public/searchByAddress', 
                        params = {
                            'itemsPerPage' : 10,
                            'pageIndex':1
                        },
                        json = {
                            'regionCode' : region,
                            'cityCode' : city
                        })               
buildings = response.text()

print(buildings)