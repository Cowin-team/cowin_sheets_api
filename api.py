import json
from flask import Flask, request, jsonify
from GSheets import GoogleSheets
from flask_cors import CORS, cross_origin
app = Flask(__name__)

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
sheets = GoogleSheets()

@app.route('/update',methods = ['POST'])
def get_record():
    record = json.loads(request.data)
    sheets.update(record)
    return jsonify(record)


if __name__ == '__main__':
   app.run(debug = True)