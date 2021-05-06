import requests
import json

url = 'https://true-source-312806.et.r.appspot.com/update'

result = '{"Name": "KG Multi Speciality Hospital", "COVID Beds": 29, "Oxygen Beds": 19, "ICU": 10, "Ventilator Beds": 12, "LAST UPDATED": "2021-05-06 02:59:05", "Contact": 7094409938.0, "Sheet Name": "Pune Beds"}'
response=requests.post(url, json=json.loads(result), verify=False)

print(response.json())