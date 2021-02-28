from flask import Flask, request, jsonify, session, render_template
from flask_restful import Resource, Api 
import sqlite3
import json
import requests

secure_shared_service = Flask(__name__)
api = Api(secure_shared_service)


# Get the smartlock ID

token = "23bc996cebcfdfaa5021c3f4b7bcd16e91985fb959f7484a9a0a5fb39e02144640a3cc670abb687c"

def get_smartlock():
	headers = {"Authorization": "Bearer {}".format(token)}
	lock = requests.get("https://api.nuki.io/smartlock", headers=headers)
	json_data = json.loads(lock.text)
	smartlock = json_data[0]["smartlockId"]
	return smartlock

class lockRoute(Resource):
	def get(self):
		lock = get_smartlock()
		print(lock)  
		header = {
            'Content-Type': 'application/json',	
            'Accept': 'application/json',
            'Authorization': "Bearer {}".format(token)
        }

		lock_request = requests.post("https://api.nuki.io/smartlock/{}/action/lock".format(lock), headers=header)
		print(lock_request)	
		return jsonify("The door is locked.")

class unlockRoute(Resource):
	def get(self):	
		lock = get_smartlock()
		print(lock)  
		header = {
            'Content-Type': 'application/json',	
            'Accept': 'application/json',
            'Authorization': "Bearer {}".format(token)
        }

		lock_request = requests.post("https://api.nuki.io/smartlock/{}/action/unlock".format(lock), headers=header)
		print(lock_request)	
		return jsonify("The door is unlocked.")

@secure_shared_service.route('/view')
def view():
	return render_template('index.html')

	
api.add_resource(lockRoute, '/lock', endpoint="lock")
api.add_resource(unlockRoute, '/unlock', endpoint="unlock")


def main():
    secure_shared_service.run(host='127.0.0.1', debug=True)

if __name__ == '__main__':
    main()
 

