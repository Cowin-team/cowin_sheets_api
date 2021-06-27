# importing the required libraries
import os
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import time
from datetime import datetime
import re
import requests
import syslog
import json
import copy

syslog.openlog('csa')


def log(msg):
    syslog.syslog(msg)


class GoogleSheets:
    def __init__(self, creds_file='creds.json', ping_wait=1):
        log('Initializing google sheets')

        # define the scope
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

        # add credentials to the account
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)

        self.params = {'address': '', 'sensor': 'false', 'region': 'india',
                       'key': 'AIzaSyBGrgbjTkmWhyjyyGq8fWzigE6xECz1Mcc'}

        self.GOOGLE_MAPS_API_URL = 'https://maps.googleapis.com/maps/api/geocode/json'
        self.map_URL = 'https://www.google.com/maps/'

        # authorize the clientsheet
        self.client = gspread.authorize(creds)
        self.ping_wait = ping_wait
        self.sheet_columns = ['Name', 'Address', 'lat', 'Long', 'URL', 'COVID Beds', 'Oxygen Beds', 'ICU',
                              'Ventilator Beds', 'LAST UPDATED', 'Contact', 'Source URL']

        self.vaccination_center_sheet_columns = [
            "Center ID",
            "Name",
            "Lat",
            "Long",
            "Address",
            "District",
            "State",
            "Pincode",
            "Block Name",
            "Fee Type",
            "Opening Time",
            "Closing Time",
            "LAST UPDATED",
            "COVISHIELD Min Age 45 Dose-1 Availability",
            "COVISHIELD Min Age 45 Dose-2 Availability",
            "COVISHIELD Min Age 18 Dose-1 Availability",
            "COVISHIELD Min Age 18 Dose-2 Availability",
            "COVAXIN Min Age 45 Dose-1 Availability",
            "COVAXIN Min Age 45 Dose-2 Availability",
            "COVAXIN Min Age 18 Dose-1 Availability",
            "COVAXIN Min Age 18 Dose-2 Availability",
            "SPUTNIK Min Age 45 Dose-1 Availability",
            "SPUTNIK Min Age 45 Dose-2 Availability",
            "SPUTNIK Min Age 18 Dose-1 Availability",
            "SPUTNIK Min Age 18 Dose-2 Availability",
        ]

    def update_bulk(self, bulk_data):
        resp_list = []

        for hospital in bulk_data:
            log('Updating sheet: [%s] hospital: [%s]' % (hospital['Sheet Name'], hospital['Name']))

            resp = self.update(hospital)
            resp_list.append(resp)

            # if 'message' in resp:
            #     log('Successfully updated sheet [%s] hospital [%s]. Message: [%s]' %
            #         (hospital['Sheet Name'], hospital['Name'], resp['message']))
            if 'error' in resp:
                log('Error updating. Data: [%s] Error: [%s]' % (json.dumps(hospital), resp['error']))

            time.sleep(self.ping_wait)

        return resp_list

    def update(self, hospital):
        name_alphanumeric = re.sub(r'\W+', '', hospital['Name']).lower()
        resp = json.loads(json.dumps(hospital))

        try:
            # get the instance of the Spreadsheet
            sheet = self.client.open(hospital['Sheet Name'])

            # get the first sheet of the Spreadsheet
            sheet_instance = sheet.get_worksheet(0)

            # get all the records of the hospital
            records_data = sheet_instance.get_all_records()

            # convert the json to dataframe
            records_df = pd.DataFrame.from_dict(records_data)
        except Exception as e:
            resp['error'] = 'Error Reading sheets. Sheet Name: [%s] Error: [%s]' % (hospital['Sheet Name'], str(e))
            return resp

        try:
            if hospital['Check LAST UPDATED']:
                records_df['LAST UPDATED'] = pd.to_datetime(records_df['LAST UPDATED'], infer_datetime_format=True)
        except Exception as e:
            resp['error'] = 'Error in format of [LAST UPDATED] column in google sheets. Error: [%s]' % str(e)
            return resp

        try:
            if records_df.empty is not True:
                records_df['Name'] = records_df.Name.str.replace('[^a-zA-Z0-9]', '')
                records_df['Name'] = records_df.Name.str.lower()
                index_list = records_df[(records_df['Name'] == name_alphanumeric)].index
            else:
                index_list = []
        except Exception as e:
            resp['error'] = 'Error in comparing the name of hospital of google sheets with the name in the request. ' \
                            'Sheet Name: [%s] Error: [%s]' % (hospital['Name'], str(e))
            return resp
        try:
            # # check if the hospital already exists
            if len(index_list):
                is_update = False

                if hospital['Check LAST UPDATED']:
                    is_update = records_df['LAST UPDATED'][index_list[0]] < datetime.strptime(hospital['LAST UPDATED'],
                                                                                              '%Y-%m-%d %H:%M:%S')
                is_diff = False
                row = records_df[records_df['Name'] == name_alphanumeric]
                row_cols = row.columns

                for col in row_cols:
                    if col in hospital.keys():
                        # Check if there is a diff between the hospital and the sheet for this row
                        if row[col].values[0] != hospital[col]:
                            row[col] = hospital[col]
                            is_diff = True

                if is_diff or is_update:
                    try:
                        sheet_instance.delete_row(int(index_list[0]) + 2)
                        sheet_instance.insert_row(row.values[0].tolist(), index=int(index_list[0]) + 2)
                        resp['message'] = 'Edited row: [%s]' % str(hospital['Name'])
                        return resp
                    except Exception as e:
                        resp['error'] = 'Error editing row: [%s] Error: [%s]' % (str(hospital['Name']), str(e))
                        return resp
                else:
                    resp['message'] = 'The sheet has the latest update, request rejected'
                    return resp
            else:
                geodata = dict()
                self.params['address'] = hospital['Address']

                try:
                    req = requests.get(self.GOOGLE_MAPS_API_URL, params=self.params)
                    res = req.json()

                    # Use the first result
                    result = res['results'][0]

                    geodata['lat'] = result['geometry']['location']['lat']
                    geodata['lng'] = result['geometry']['location']['lng']
                    geodata['address'] = result['formatted_address']
                    map_url = self.map_URL + '@' + str(geodata['lat']) + ',' + str(geodata['lng']) + ',16z'
                except Exception as e:
                    resp['error'] = 'Error trying to get lat/lng for [%s] Error: [%s]' % (str(hospital['Name']), str(e))
                    return resp

                row_values = []
                for key in self.sheet_columns:

                    if key in hospital.keys():
                        row_values.append(hospital[key])
                    else:
                        if geodata and key == 'lat':
                            row_values.append(geodata['lat'])
                        elif geodata and key == 'Long':
                            row_values.append(geodata['lng'])
                        elif geodata and key == 'URL':
                            row_values.append(map_url)
                        else:
                            row_values.append(None)
                try:
                    sheet_instance.insert_row(row_values, index=len(records_df.index) + 2)
                    resp['message'] = 'Inserted row: [%s]' % str(hospital['Name'])
                    return resp
                except Exception as e:
                    resp['error'] = 'Error inserting new row: [%s] Error: [%s]' % (str(hospital['Name']), str(e))
                    return resp
        except Exception as e:
            resp['error'] = 'Error: [%s]' % str(e)
            return resp

    def update_vaccine_bulk(self, bulk_data):
        resp_list = []

        for vaccination_center in bulk_data:
            log('Updating sheet: [%s] vaccination center: [%s]' % (vaccination_center['Sheet Name'], vaccination_center['Name']))

            resp = self.update_vaccine(vaccination_center)
            resp_list.append(resp)

            if 'error' in resp:
                log('Error updating. Data: [%s] Error: [%s]' % (json.dumps(vaccination_center), resp['error']))

            time.sleep(self.ping_wait)

        return resp_list

    def update_vaccine(self, vaccination_center):
        print("updating {}:{}".format(vaccination_center["Sheet Name"],vaccination_center["Name"]))
        resp = copy.deepcopy(vaccination_center)
        
        try:

            try:
                sheet = self.client.open(vaccination_center['Sheet Name'])
                sheet_instance = sheet.get_worksheet(0)
            except gspread.exceptions.SpreadsheetNotFound:
                if os.getenv('DEBUG_EMAIL') is not None:
                    print('spreadsheet not found, DEBUG_EMAIL found, creating spreadsheet')
                    sheet = self.client.create(title=vaccination_center['Sheet Name'])
                    sheet.add_worksheet(title="Sheet 1", rows="100", cols=str(len(self.vaccination_center_sheet_columns)))
                    sheet.share(os.getenv('DEBUG_EMAIL'), perm_type='user', role='writer')
                    sheet_instance = sheet.get_worksheet(0)
                    sheet_instance.insert_row(self.vaccination_center_sheet_columns, 1)
                else:
                    raise gspread.exceptions.SpreadsheetNotFound("{} not found".format(vaccination_center["Sheet Name"]))

            # get the first sheet of the Spreadsheet

            # get all the records of the hospital
            records_data = sheet_instance.get_all_records()

            # convert the json to dataframe
            records_df = pd.DataFrame.from_dict(records_data)
        except Exception as e:
            print(e)
            resp['error'] = 'Error Reading sheets. Sheet Name: [%s] Error: [%s]' % (vaccination_center['Sheet Name'], str(e))
            return resp

        update_vaccination_center = False
        if not records_df.empty:
            index_list = records_df[(records_df['Center ID'] == vaccination_center["Center ID"])].index
            if len(index_list):
                update_vaccination_center = True

        try:
            if update_vaccination_center:

                records_df['LAST UPDATED'] = pd.to_datetime(records_df['LAST UPDATED'], format='%d-%m-%Y %H:%M:%S')

                is_update = False

                if vaccination_center['Check LAST UPDATED']:
                    is_update = records_df['LAST UPDATED'][index_list[0]] < datetime.strptime(vaccination_center['LAST UPDATED'], '%Y-%m-%d %H:%M:%S')
                is_diff = False
                row = records_df[records_df['Center ID'] == vaccination_center["Center ID"]]
                row_cols = row.columns

                for col in row_cols:
                    if col in vaccination_center.keys():
                        # Check if there is a diff between the hospital and the sheet for this row
                        if row[col].values[0] != vaccination_center[col]:
                            row[col] = vaccination_center[col]
                            is_diff = True

                if is_diff or is_update:
                    try:
                        sheet_instance.delete_row(int(index_list[0]) + 2)
                        sheet_instance.insert_row(row.values[0].tolist(), index=int(index_list[0]) + 2)
                        resp['message'] = 'Edited row: [%s]' % str(vaccination_center['Name'])
                        return resp
                    except Exception as e:
                        resp['error'] = 'Error editing row: [%s] Error: [%s]' % (str(vaccination_center['Name']), str(e))
                        return resp
                else:
                    resp['message'] = 'The sheet has the latest update, request rejected'
                    return resp
            else:

                vaccination_center["URL"] = self.map_URL + '@' + str(vaccination_center['Lat']) + ',' + str(vaccination_center['Long']) + ',16z'

                row_values = []
                for key in self.vaccination_center_sheet_columns:

                    if key in vaccination_center.keys():
                        row_values.append(vaccination_center[key])
                    else:
                        row_values.append(None)
                try:
                    sheet_instance.insert_row(row_values, index=len(records_df.index) + 2)
                    resp['message'] = 'Inserted row: [%s]' % str(vaccination_center['Name'])
                    return resp
                except Exception as e:
                    resp['error'] = 'Error inserting new row: [%s] Error: [%s]' % (str(vaccination_center['Name']), str(e))
                    return resp
        except Exception as e:
            resp['error'] = 'Error: [%s]' % str(e)
            return resp

    def get_all_sheets(self):
        titles_list = []
        for spreadsheet in self.client.openall():
            print(spreadsheet.title)
            titles_list.append(spreadsheet.title)

        return titles_list


if __name__ == '__main__':
    sheets = GoogleSheets()
    data = {'Sheet Name': 'Thanjavur Beds', 'Name': 'Rohiniiii Hospital*',
            'Address': 'Government Hospital, Kinathukadavu, Tamil Nadu 642109, India', 'COVID Beds': 226,
            'Oxygen Beds': 372, 'ICU': 20, 'LAST UPDATED': '2021-05-06 15:25:37', 'Check LAST UPDATED': True}

    sheets.update(data)
