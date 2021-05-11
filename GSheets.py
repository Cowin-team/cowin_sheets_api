# importing the required libraries
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import time
from datetime import datetime
import re

class GoogleSheets:
	def __init__(self, creds_file = 'creds.json', ping_wait = 1):

		# define the scope
		scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']

		# add credentials to the account
		creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)

		# authorize the clientsheet 
		self.client = gspread.authorize(creds)
		self.ping_wait = ping_wait
		self.sheet_columns = ['Name', 'Address', 'lat', 'Long', 'URL', 'COVID Beds', 'Oxygen Beds', 'ICU', 'Ventilator Beds', 'LAST UPDATED', 'Contact', 'Source URL']

	def update_bulk(self, bulk_data):

		for data in bulk_data:
			resp = self.update(data)
			print(resp)
			time.sleep(self.ping_wait)
			if "Error" in resp:
				return resp

		return {"Sucess":bulk_data}

	def update(self, data):
		print("\n\n", data, "\n")
		name_alphanumeric = re.sub(r'\W+', '', data['Name']).lower()
		try:
			# get the instance of the Spreadsheet
			sheet = self.client.open(data["Sheet Name"])

			# get the first sheet of the Spreadsheet
			sheet_instance = sheet.get_worksheet(0)
			# get all the records of the data
			records_data = sheet_instance.get_all_records()
			# convert the json to dataframe
			records_df = pd.DataFrame.from_dict(records_data)
		except Exception as e:
			return "Error Reading sheets\t: "  +  data["Sheet Name"] + "\nError Message:\t" + str(e)

		try:
			if data['Check LAST UPDATED']:
				records_df['LAST UPDATED'] = pd.to_datetime(records_df['LAST UPDATED'], infer_datetime_format=True)
		except Exception as e:
			return "Error in format of 'LAST UPDATED' column in google sheets"  + "\nError Message:\t" + str(e)
		
		try:
			if (records_df.empty is not True):
				records_df['Name'] = records_df.Name.str.replace('[^a-zA-Z0-9]', '')
				records_df['Name'] = records_df.Name.str.lower()
				index_list = records_df[(records_df['Name'] == name_alphanumeric)].index	
			else:
				index_list = []
		except Exception as e:
			return "Error in comparing the name of hospital of google sheets with the name in the request:\t"  + data['Name'] + "\nError Message:\t" + str(e)
		try:
			# # check if the data already exists
			if (len(index_list)):

				isUpdate = False
				if data['Check LAST UPDATED']:
					isUpdate = records_df['LAST UPDATED'][index_list[0]] < datetime.strptime(data['LAST UPDATED'], "%Y-%m-%d %H:%M:%S")
				isDiff = False
				row = records_df[records_df['Name'] == name_alphanumeric]
				row_cols = row.columns
				for col in row_cols:
					if col in data.keys():
						# Check if there is a diff between the data and the sheet for this row
						if row[col].values[0] != data[col]:
							row[col] = data[col]
							isDiff = True
				if isDiff or isUpdate:
					try:
						sheet_instance.delete_row(int(index_list[0])+2)
						sheet_instance.insert_row(row.values[0].tolist(), index=int(index_list[0])+2)
						return {"Sucess": "edited row:\t"+ str(data['Name'])}
					except Exception as e:
						return "Error Editing editing row:\t" + str(data['Name']) + "\nError Message:\t" + str(e)
				else:
					return{"resp":"The sheet has the latest update, request rejected"}
			else:
				# sheet_columns = list(records_df.columns)
				row_values = []
				for key in self.sheet_columns:
					if key in data.keys():
						row_values.append(data[key])
					else:
						row_values.append(None)
				
				try:
					sheet_instance.insert_row(row_values, index=len(records_df.index)+2)
					return {"Sucess": "Inserted row: "+ str(data['Name'])}
				except Exception as e:
					return "Error Inserting new row: " + str(data['Name']) + "\nError Message:\t" + str(e)
			
		except Exception as e:
			return "Error unknown: \nError Message:\t"  + str(e)
			
		
	def get_all_sheets(self):
		titles_list = []
		for spreadsheet in self.client.openall():
			print(spreadsheet.title)
			titles_list.append(spreadsheet.title)
			
		return titles_list

if __name__ == "__main__":
    sheets = GoogleSheets()
    data = {
        "Sheet Name": "Thanjavur Beds",
        "Name": "Rohini Hospital*",
        "URL": "https://www.google.com/maps/place/Thanjavur+Medical+College/@10.7580923,79.1035782,17z/data=!4m9!1m2!2m1!1sThanjavur+Medical+College!3m5!1s0x3baabf337761a613:0x69900b85db55755e!8m2!3d10.7586!4d79.1066!15sChlUaGFuamF2dXIgTWVkaWNhbCBDb2xsZWdlWiwKD21lZGljYWwgY29sbGVnZSIZdGhhbmphdnVyIG1lZGljYWwgY29sbGVnZZIBDm1lZGljYWxfc2Nob29ssAEA",
        "COVID Beds": 226,
        "Oxygen Beds": 372,
        "ICU": 20,
        "LAST UPDATED": "2021-05-06 15:25:37", 
		"Check LAST UPDATED": True
    }

    print(sheets.update(data))
