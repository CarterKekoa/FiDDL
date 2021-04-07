# google_nest_api.py
# fiddl
# author: Drew Bies
# description: this program connects to the google nest doorbell camera through the google cloud services.
#   get_access_token() retrieves the authentication token needed to access the doorbell device.
#   get_rtsp_stream() retrieves a live stream url of the camera feed in rtsp format.
#   pull_messages() pulls all messages in the queue from the doorbell with a timeout
#   callback(message) is called from pull_messages() for every message found. 
#       the message is filtered based on the eventId (person, motion, chime)
#       uses the eventId to call get_image(eventId)
#   get_image(eventId) retrieves the image and saves it to the desired location using the eventId

from flask import Blueprint, current_app, render_template, request
import requests
import json
import os
import base64

# Helper File Imports
import users.utils as utils
import fiddl_utils as fiddl_utils

# TODO: add to requirements
# pip install --upgrade google-cloud-pubsub
from google.cloud import pubsub_v1

nestBP = Blueprint("doorbell", __name__, static_folder="static", template_folder="templates")

@nestBP.route('/doorbell', methods=["POST"])
def recieve_message_handler():
    print("--------------------")
    envelope = json.loads(request.data.decode('utf-8'))
    print("envelope", envelope)
    payload = base64.b64decode(envelope['message']['data'])
    print("payload", payload)
    # Returning any 2xx status indicates successful receipt of the message.
    return 'OK', 200

# TODO: have this done automatically and change the file location
# $env:GOOGLE_APPLICATION_CREDENTIALS="C:\Users\Drew\iCloudDrive\Documents\senior design\fiddl-1604901867274-1d28c44d691d.json"

DEVICE_ID = 'AVPHwEvDLJQsZiLE6-AA7XH4J3OLKg5pqUIh69kYCOlASNxvmDK0IRRa0bjHoNEWLLoHiOanMP1stHjUXVspoNc0DG1luQ'
CLIENT_ID = '94523447905-vo4v1a5613fj3ep5p8s29vemet0bqnmt.apps.googleusercontent.com'
CLIENT_SECRET = '0eJ1_AS1KltV0hrSFWAGvIGX'
PROJECT_ID = '428fdda2-61c1-41b1-b271-1e4a657994ac'
AUTH_CODE = '4/0AY0e-g5gzJuAbg57kqCnHA9ODF1WKp8dIYDlTl-aHCU4O6W4pL85vS0fMd1VvpYcVw4zBQ'
REFRESH_TOKEN = '1//06QVtkS0U9RwBCgYIARAAGAYSNwF-L9IrFfNFhp_wKWJhLM3HEFVeJeVZ9SP8ro_Wt4624K-L9CKxj5-_ctAFDgI_VI-vLXQyKoc'

# path to google credentials json
#cred_location = 'C:\Users\Drew\iCloudDrive\Documents\senior design\fiddl-1604901867274-1d28c44d691d.json'

# timeout for pulling messages
timeout = 5.0


# gets the access token by using the refresh token
def get_access_token():
    # construct the json request
    url_str = 'https://www.googleapis.com/oauth2/v4/token?client_id=' + CLIENT_ID + '&client_secret=' + CLIENT_SECRET + '&refresh_token=' + REFRESH_TOKEN + '&grant_type=refresh_token'
    
    response = requests.post(url_str)
    json_object = response.json()
    token = json_object['access_token']
    return token

# get the image url using the eventId
def get_image(eventId):
    print("Get image started")
    # construct the json POST request
    url_str = 'https://smartdevicemanagement.googleapis.com/v1/enterprises/' + PROJECT_ID + '/devices/' + DEVICE_ID + ':executeCommand'

    data = '{ "command" : "sdm.devices.commands.CameraEventImage.GenerateImage", "params" : {"eventId" :  "' + eventId + '", }, }'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + get_access_token(),
    }

    # response from the google cloud
    response = requests.post(url_str, headers=headers, data=data).json()

    if 'error' in response:
        print('Error: ' + response['error']['message'])
        return

    results = response['results']
    image_url = results['url']
    event_token = results['token']

    headers = {
        'Authorization': 'Basic ' + event_token,
    }

    # TODO: change file_path to desired location
    filename = "EventPhoto.jpg"

   
    #file_path = 'C:/Users/Drew/Desktop/'
    print("Image saving to DB")
    response = requests.get(image_url, headers=headers, stream=True)
    STORAGE.child("images/nestDoorbell/" + filename).put(response.content)
    imageURL = STORAGE.child("images/temp/" + filename).get_url(None)
    # with open(file_path + 'doorbell_image.jpeg', 'wb') as out_file:
    #     print('\n****saving to ' + file_path + '\n')
    #     out_file.write(response.content)


# parse the message received from pull_messages()
def callback(message):
    print("Call back")
    # convert message into a python dictionary of the event
    event_json = json.loads(bytes.decode(message.data))
    event_type = event_json['resourceUpdate']['events']

    # TODO: look into web hooks waiting for the api, or subscribe to the event
    # TODO: Self assing SSL certificate heroku
    person = 'sdm.devices.events.CameraPerson.Person'
    motion = 'sdm.devices.events.CameraMotion.Motion'
    chime = 'sdm.devices.events.DoorbellChime.Chime'
    event = chime
    # using 'sdm.devices.events.CameraPerson.Person' to get person events only
    if event in event_type:
        print("Chime Event Found")
        event_id = event_type[event]['eventId']
        # get the image
        get_image(event_id)

    # delete the message from the queue
    message.ack()

# pull all the messages in the event queue
def pull_messages():
    print("pull_messages started")
    # returns error if credentials are not set
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = current_app.config["GOOGLE_APPLICATION_CREDENTIALS"]
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = 'projects/fiddl-1604901867274/subscriptions/fiddl-sub'
    #subscriber = current_app.config['client']
    #os.system('$env:GOOGLE_APPLICATION_CREDENTIALS="C:\Users\Drew\iCloudDrive\Documents\senior design\fiddl-1604901867274-1d28c44d691d.json"')
    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    print(f"Listening for messages on {subscription_path}..\n")

    # Wrap subscriber in a 'with' block to automatically call close() when done.
    with subscriber:
        try:
            # When `timeout` is not set, result() will block indefinitely,
            # unless an exception is encountered first.
            print("####################DATA FOUND $$$$$$$$$$$$$$$$$$$$$")
            streaming_pull_future.result(timeout=timeout)
        except TimeoutError:
            streaming_pull_future.cancel()
            print("Not found")


# initalize events for the doorbell
def init_events():
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + get_access_token(),
    }

    response = requests.get('https://smartdevicemanagement.googleapis.com/v1/enterprises/428fdda2-61c1-41b1-b271-1e4a657994ac/devices', headers=headers)
    print(response.json())


# returns the url for a rtsp stream of the doorbell camera
def get_rtsp_stream():
    # construct the json POST request
    url_str = 'https://smartdevicemanagement.googleapis.com/v1/enterprises/' + PROJECT_ID + '/devices/' + DEVICE_ID + ':executeCommand'

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + get_access_token(),
    }

    data = '{ "command" : "sdm.devices.commands.CameraLiveStream.GenerateRtspStream", "params" : {} }'

    # get the response from the google cloud
    response = requests.post(url_str, headers=headers, data=data)

    # json results
    results = response.json()['results']
    rstp_url = results['streamUrls']['rtspUrl']
    stream_token = results['streamToken']
    stream_extension_token = results['streamExtensionToken']
    expiration_time = results['expiresAt']
    return rstp_url

@nestBP.route('/doorbell', methods=["GET", "POST"])
def nest():
    print("Doorbell function")
    #firebase, auth, db, storage, bucket = fiddl_utils.initialize_data()
    pull_messages()

    return render_template('doorbell.html')