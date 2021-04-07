import linecache
import sys
from flask import Flask, current_app, flash, session
import pyrebase

import requests
import json
import os
from google.cloud import pubsub_v1

# gets the access token by using the refresh token
def get_access_token():
    DEVICE_ID = 'AVPHwEvDLJQsZiLE6-AA7XH4J3OLKg5pqUIh69kYCOlASNxvmDK0IRRa0bjHoNEWLLoHiOanMP1stHjUXVspoNc0DG1luQ'
    CLIENT_ID = '94523447905-vo4v1a5613fj3ep5p8s29vemet0bqnmt.apps.googleusercontent.com'
    CLIENT_SECRET = '0eJ1_AS1KltV0hrSFWAGvIGX'
    PROJECT_ID = '428fdda2-61c1-41b1-b271-1e4a657994ac'
    AUTH_CODE = '4/0AY0e-g5gzJuAbg57kqCnHA9ODF1WKp8dIYDlTl-aHCU4O6W4pL85vS0fMd1VvpYcVw4zBQ'
    REFRESH_TOKEN = '1//06QVtkS0U9RwBCgYIARAAGAYSNwF-L9IrFfNFhp_wKWJhLM3HEFVeJeVZ9SP8ro_Wt4624K-L9CKxj5-_ctAFDgI_VI-vLXQyKoc'
    # construct the json request
    url_str = 'https://www.googleapis.com/oauth2/v4/token?client_id=' + CLIENT_ID + '&client_secret=' + CLIENT_SECRET + '&refresh_token=' + REFRESH_TOKEN + '&grant_type=refresh_token'
    
    response = requests.post(url_str)
    json_object = response.json()
    token = json_object['access_token']
    return token

# get the image url using the eventId
def get_image(eventId):
    DEVICE_ID = 'AVPHwEvDLJQsZiLE6-AA7XH4J3OLKg5pqUIh69kYCOlASNxvmDK0IRRa0bjHoNEWLLoHiOanMP1stHjUXVspoNc0DG1luQ'
    CLIENT_ID = '94523447905-vo4v1a5613fj3ep5p8s29vemet0bqnmt.apps.googleusercontent.com'
    CLIENT_SECRET = '0eJ1_AS1KltV0hrSFWAGvIGX'
    PROJECT_ID = '428fdda2-61c1-41b1-b271-1e4a657994ac'
    AUTH_CODE = '4/0AY0e-g5gzJuAbg57kqCnHA9ODF1WKp8dIYDlTl-aHCU4O6W4pL85vS0fMd1VvpYcVw4zBQ'
    REFRESH_TOKEN = '1//06QVtkS0U9RwBCgYIARAAGAYSNwF-L9IrFfNFhp_wKWJhLM3HEFVeJeVZ9SP8ro_Wt4624K-L9CKxj5-_ctAFDgI_VI-vLXQyKoc'
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


    firebase = pyrebase.initialize_app(json.load(open('firebase/firebaseConfig.json')))
    auth = firebase.auth()
    db = firebase.database()                                    
    fb_storage = firebase.storage()
    #file_path = 'C:/Users/Drew/Desktop/'
    print("Image saving to DB")
    response = requests.get(image_url, headers=headers, stream=True)
    print("1")
    #storage = current_app.config['storage']
    print("2")
    fb_storage.child("images/nestDoorbell/" + filename).put(response.content)
    imageURL = fb_storage.child("images/temp/" + filename).get_url(None)
    # with open(file_path + 'doorbell_image.jpeg', 'wb') as out_file:
    #     print('\n****saving to ' + file_path + '\n')
    #     out_file.write(response.content)


# parse the message received from pull_messages()
def callback(message):
    print("Call back")
    # convert message into a python dictionary of the event
    event_json = json.loads(bytes.decode(message.data))
    event_type = event_json['resourceUpdate']['events']

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
    timeout = 5.0
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











# Process Functions -------------------------------------------------------
def allow_image(filename):
    """Checks if the incoming file has the correct file extension
    """
    #check for dot in file name
    if not "." in filename:
        return False
    
    ext = filename.rsplit(".", 1)[1]

    #convert type to upper case
    if ext.upper() in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        current_app.logger.info("[UPLOAD_IMAGE] Valid Image File Name")
        return True
    else:
        current_app.logger.warning("[UPLOAD_IMAGE] Invalid Image File Name")
        badFileName = "Please use an acceptable file name."
        flash(badFileName, "warning")                    #"info" is the type of message for more customization if we want, others are warning, info, error
        return False


def allowed_image_filesize(file_size):
    """Checks to see if the file size is too large
    """
    if int(file_size) <= current_app.config["MAX_IMAGE_FILESIZE"]:
        current_app.logger.info("[UPLOAD_IMAGE] Valid Image File Size")
        return True
    else:
        current_app.logger.warning("[UPLOAD_IMAGE] Invalid Image File Size")
        badFileSize = "File size is too large. Be sure the file size is less than 1,572,864 Bytes or 1572.864 KB"
        flash(badFileSize, "warning")                    #"info" is the type of message for more customization if we want, others are warning, info, error
        return False

def used_filename(filename):
    """This function checks if that filename (photo) has already been stored on the users account
    """
    # Check if the image filename has already been stored
    if not session.get('userPhotoNames') is None:
        for k,v in session['userPhotoNames'].items():
            if v == filename:
                current_app.logger.warning("[UPLOAD_IMAGE] Invalid, Image File Name is already stored")
                dupFileName = "This file name has previously been stored on this account. This could mean this same photo has also already been uploaded to this account. Please try a new photo for best accuracy."
                flash(dupFileName, "warning")                    #"info" is the type of message for more customization if we want, others are warning, info, error
                return True
    current_app.logger.info("[UPLOAD_IMAGE] Image File Name is new.")
    return False

