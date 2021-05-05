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
		return jsonify(resp)
# def _build_cors_prelight_response():
# 	response = make_response()
# 	response.headers.add("Access-Control-Allow-Origin", "*")
# 	response.headers.add('Access-Control-Allow-Headers', "*")
# 	response.headers.add('Access-Control-Allow-Methods', "*")
# 	return response
# 
# def _corsify_actual_response(response):
# 	response.headers.add("Access-Control-Allow-Origin", "*")
# 	return response

if __name__ == '__main__':
   app.run(debug = True)