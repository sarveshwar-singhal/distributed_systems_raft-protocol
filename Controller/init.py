import json
import os
from flask import Flask, render_template, request, jsonify, redirect
# import pymongo
from markupsafe import escape
import logging
import requests
import socket

app = Flask(__name__)


'''
MongoDB connections to collections and database
'''
# mongo_server        = pymongo.MongoClient("mongodb://root:pwd@localhost:27017/")
# db_server = os.getenv('MONGO_SERVER')
# print("\n\n\n\n",db_server,"\n\n\n\n\n")
# mongo_server        = pymongo.MongoClient(db_server)
# db_instance         = mongo_server["my-db"]
# users_collection    = db_instance["users"]



isleader = os.getenv('IS_LEADER')
FORMAT = 'utf-8'
MSG = {
  "sender_name": None,
  "request": None,
  "term": None,
  "key": None,
  "value": None
}


'''
Template for escaping out user urls 
'''
@app.route("/<name>")
def hello(name):
    return f"Hello, {escape(name)}!"

'''
Template for GET - Method
'''
@app.route("/")
def hello_world():
    temp = "node1"
    port = 5555
    ADDR = (temp, port)
    skt = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    skt.bind(ADDR)
    msg = MSG
    msg['sender_name'] = 'controller'
    msg['request'] = 'LEADER_INFO'
    skt.sendto(json.dumps(msg).encode(FORMAT), ADDR)
    res, addr = skt.recvfrom(2048)
    res_dict = json.loads(res)
    node_name = socket.gethostname()
    if(node_name != res_dict['LEADER']):
        logging.warning(f"http://{res_dict['LEADER']}:{os.getenv(res_dict + '_port')}/")
        return redirect(f"http://{res_dict['LEADER']}:{os.getenv(res_dict+'_port')}/")
    # if isleader == 'false':
    #     logging.warning(f"http://localhost:{os.getenv('LEADER_PORT')}/")
    #     return redirect(f"http://localhost:{os.getenv('LEADER_PORT')}/") #NON_LEADER_MESSAGE
    return render_template('index.html')
    #return "<b>Hello World ...</b>"

"""
@app.route("/showmessages")
def show_messages():
    isleader = os.getenv('IS_LEADER')
    
    
    try:
        records = users_collection.find()
        user_names = [doc['user_name'] for doc in records]
        return jsonify({"user_names" : user_names})
    except Exception as e: 
        logging.error("\n\n\n\n",e.args,"\n\n\n\n\n")
    

'''
Template for POST - method
'''
@app.route('/api/add_message', methods=['POST'])
def add_message():
    if request.method == 'POST':
        try:
            data = request.form.to_dict()
            user_name = data['user_name']

            ports = os.getenv('WORKER_PORTS')
            data = {}
            if ports and isleader == "true":
                for port in ports.split(','):
                    url = f'http://{port}/api/add_message'
                    response = requests.post(url, data = {'user_name':user_name})
                    if response.status_code == 200:
                        data[url] = "SUCCESS"
                    else:
                        data[url] = "FAILED"
            result = users_collection.insert_one({"user_name":user_name})
            
            print(result.inserted_id)
            return jsonify(SUCCESS=True,data = data)

        except Exception as e:
            logging.warning("e.args")
            obj = {"SUCCESS":False,"args": e}
            return jsonify(obj)

@app.route('/api/get_all_messages', methods=['POST'])
def get_all_messages():
        if request.method == 'POST':
            try:
                ports = os.getenv('WORKER_PORTS')
                data = {}
                
                records = users_collection.find()
                user_names = [doc['user_name'] for doc in records]
                if isleader == "true":
                    data["leader"] = user_names
                else:
                    data = user_names

                if ports and isleader == "true":
                    for port in ports.split(','):
                        url = f'http://{port}/api/get_all_messages'
                        response = requests.post(url)
                        if response.status_code == 200:
                            logging.warning(response)
                            data[url] = response.json()["data"]
                        else:
                            data[url] = "FAILED"

                
                
                return jsonify({"data" : data})
            except Exception as e: 
                logging.error("\n\n\n\n",e.args,"\n\n\n\n\n")
                
"""

if __name__ == "__main__":
    port = int(os.getenv('PORT'))
    app.run(host="0.0.0.0",port=port)
