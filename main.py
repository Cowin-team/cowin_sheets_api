import json
from flask import Flask, request, jsonify, make_response
from GSheets import GoogleSheets
from flask_cors import CORS, cross_origin
import time
app = Flask(__name__)

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
sheets = GoogleSheets()


@app.route('/', methods=['GET'])
def home():
    return "Cowin Sheets API"


@app.route('/health', methods=['GET'])
def health():
    return "OK"


@app.route('/update', methods=['POST'])
@cross_origin()
def get_record():
    if request.method == "POST":  # The actual request following the preflight
        record = json.loads(request.data)
        resp = sheets.update(record)
        return handle_response(resp)
    
    return handle_response({"error": "error occurred"})



@app.route('/updateBulk', methods=['POST'])
@cross_origin()
def get_bulk_record():
    if request.method == "POST":  # The actual request following the preflight
        record = json.loads(request.data)
        resp = sheets.update_bulk(record)
        return handle_response(resp)
    
    return handle_response({"error": "error occurred"})


def handle_response(response={}, status=200):
    if "error" in response:
        return make_response(jsonify(response)), 500 if status == 200 else status
    return make_response(jsonify(response)), status

if __name__ == '__main__':
   app.run(debug = True)
