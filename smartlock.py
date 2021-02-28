import json
import requests


# Get the smartlock ID

token = "23bc996cebcfdfaa5021c3f4b7bcd16e91985fb959f7484a9a0a5fb39e02144640a3cc670abb687c"

def get_smartlock():
	headers = {"Authorization": "Bearer {}".format(token)}
	lock = requests.get("https://api.nuki.io/smartlock", headers=headers)
	json_data = json.loads(lock.text)
	smartlock = json_data[0]["smartlockId"]
	return smartlock

def lock():
	lock = get_smartlock()	
	header = {
		'Content-Type': 'application/json',	
        'Accept': 'application/json',
        'Authorization': "Bearer {}".format(token)
    }
	lock_request = requests.post("https://api.nuki.io/smartlock/{}/action/lock".format(lock), headers=header)
	return lock_request.status_code

	
def unlock():
	lock = get_smartlock()	
	header = {
		'Content-Type': 'application/json',	
        'Accept': 'application/json',
        'Authorization': "Bearer {}".format(token)
    }

	lock_request = requests.post("https://api.nuki.io/smartlock/{}/action/unlock".format(lock), headers=header)
	return lock_request.status_code 

