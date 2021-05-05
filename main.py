import json
from flask import Flask, request, jsonify
from GSheets import GoogleSheets
from flask_cors import CORS, cross_origin
app = Flask(__name__)

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
sheets = GoogleSheets()

@app.route('/',methods = ['GET'])
def home():
    return "Cowin Sheets API"

@app.route('/health',methods = ['GET'])
def health():
    return "OK"

@app.route('/update',methods = ['POST'])
@cross_origin()
def get_record():
	
	# if request.method == "OPTIONS": # CORS preflight
	# 	return _build_cors_prelight_response()
	if request.method == "POST": # The actual request following the preflight
		# print("\n\n",request.data,"\n\n")
		record = json.loads(request.data)
		resp = sheets.update(record)
		print('resp', resp)
		return jsonify(resp)
	else:
		return {"error": "error occurred"}

if __name__ == '__main__':
   app.run(debug = True)