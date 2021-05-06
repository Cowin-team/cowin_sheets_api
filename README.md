# cowin_sheets_api
An API to update the google sheets when a request is received.
It is developed in python

## Packages

Project is created with:
* oauth2client: 4.1.3
* gspread: 3.7.0
* pandas: 1.0.4
* Flask: 1.1.2


Install the packages using pip:
```pip install -r requirements.txt```

## Setup

The api can be started by running the command
`python main.py`
This starts the api on the local host with the available port

## Data formats
The api accepts POST request to `http:localhost:port/update` and `http:localhost:port/updateBulk`

For single row update use `http:localhost:port/update` and for bulk update use  `http:localhost:port/updateBulk`. The bulk update takes a list of JSON, where each JSON follows the template given below


The data shall contain all the column from the COVID Bed Google Sheets. 

Required feilds: `Sheet Name`, `Name` and  `Check LAST UPDATED` are required feilds. 
The LAST UPDATED should be in `%Y-%m-%d %H:%M:%S` format and the Check LAST UPDATED should be `True` or `False`. 

The Check LAST UPDATED flag makes the backend check and update the LAST UPDATED value,  if the update time of current request is more recent than the value in the sheet
``` json
    {
        "Sheet Name": "Thanjavur Beds",
        "Name":"Fake",
        "URL":"https://www.google.com/maps/place/Thanjavur+Medical+College/@10.7580923,79.1035782,17z/data=!4m9!1m2!2m1!1sThanjavur+Medical+College!3m5!1s0x3baabf337761a613:0x69900b85db55755e!8m2!3d10.7586!4d79.1066!15sChlUaGFuamF2dXIgTWVkaWNhbCBDb2xsZWdlWiwKD21lZGljYWwgY29sbGVnZSIZdGhhbmphdnVyIG1lZGljYWwgY29sbGVnZZIBDm1lZGljYWxfc2Nob29ssAEA",
        "COVID Beds": 226,
        "Oxygen Beds":372,
        "ICU": 200,
        "Ventilator Beds": 500,
        "LAST UPDATED": "2021-05-03 15:24:37",
		"Check LAST UPDATED": False		
    }
```

## Deploy

```
gcloud app deploy
```