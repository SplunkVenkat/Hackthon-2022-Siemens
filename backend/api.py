from flask import Flask,jsonify,render_template,Response,request,abort
import pymongo
from datetime import datetime
from flask_cors import CORS
#192.168.120.65
app = Flask(__name__,  template_folder='./templates')
CORS(app)

client = pymongo.MongoClient("mongodb+srv://ergobot:ergobot@cluster0.ebhix5u.mongodb.net/?retryWrites=true&w=majority")

position = client["position"]
users = position["users"]

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/users/pose/day')
def get_user_stats_by_day():
    try:
        email = request.args.get('email')
        date = request.args.get('date')
        dat = users.find_one({"email": email, "days.date": str(datetime.strptime(date, '%Y-%m-%d').date())},{"_id":0, "now":0})
        return jsonify(dat)
    except:
        abort(422)
        
#@app.route('/users/vision', methods = ['POST', 'GET'])
#def get_user_stats_by_day():
#    try:
#        email = request.args.get('email')
#        if request.method == 'POST':
#            data = request.get_json()
#            dat = users.find_one({"email": email, "days.date": str(datetime.strptime(date, '%Y-%m-%d').date())},{"_id":0, "now":0})
#            return jsonify(dat)
#    except:
#        abort(422)
    
@app.route('/users/pose/range')
def get_user_stats_by_range():
    try:
        email = request.args.get('email')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        start_time = datetime.combine(datetime.strptime(start_date, '%Y-%m-%d').date(), datetime.min.time())
        end_time = datetime.combine(datetime.strptime(end_date, '%Y-%m-%d').date(), datetime.max.time())
        dat = users.find_one({"email": email, "good_pos.start": {"$gte": start_time, "$lt": end_time}, "bad_pos.start": {"$gte": start_time, "$lt": end_time}},{"_id":0, "now":0})
        return jsonify(dat)
    except:
        abort(422)

@app.route('/users/now')
def whatnow():
    email = request.args.get('email')
    dat = users.find_one({"email": email},{"_id":0, "now":1}) 
    return jsonify(dat)

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')