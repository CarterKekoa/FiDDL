# google_nest_api.py
from flask import Blueprint, render_template, session, current_app, request, redirect, url_for, flash
import requests
import json
import os
import base64

# Helper File Imports
import doorbell.utils as utils
import fiddl_utils as fiddl_utils

# Facial Recognition File Imports
import FacialRecognition.recognize as recognize

nestBP = Blueprint("doorbell", __name__, static_folder="static", template_folder="templates")

IMAGE_URL = None
ID_DETERMINED = None
PROBA = None
PAYLOAD = None

def handle_payload(payload):
    current_app.logger.info("[DOORBELL] Payload received, Passing to Google Nest API functions")
    print("1")
    event_info = []
    event_info = utils.callback(payload)
    print("6")
    
    if(event_info):
        print("7")
        image_url = event_info[0]
        event_token = event_info[1]
        headers = event_info[2]
        firebase, auth, db, storage, bucket = fiddl_utils.initialize_data()
        current_app.logger.info("[DOORBELL] Storing Event Image in Database")
        
        response = requests.get(image_url, headers=headers, stream=True)
        storage.child("images/nestDoorbell/" + event_token).put(response.content)
        imageURL = storage.child("images/temp/" + event_token).get_url(None)
        IMAGE_URL = imageURL
        current_app.logger.info("[DOORBELL] Image Saved to Database Succesfully")
        print(fiddl_utils.bcolors.OKBLUE, "                             Database Image URL: ", imageURL, fiddl_utils.bcolors.ENDC)

        try:
            current_app.logger.info("[DOORBELL] Analyzing Person in Photo")
            anazlyzeInfo = recognize.facialRecognition(imageURL)

            # TODO: Delete these photos once analyzed
            # delete_temp_image_path = "images/nestDoorbell/" + event_token
            # blob = bucket.blob(delete_temp_image_path)
            # print(fiddl_utils.bcolors.OKBLUE, "                             Image Blob being deleted: ", blob, fiddl_utils.bcolors.ENDC)
            # blob.delete()
            current_app.logger.info("[UPLOAD-IMAGE] Photo Analyzed (not currently deleting from temporary storage)")
        except:
            # Analyze Fail
            current_app.logger.warning("[ERROR - ANALYZE] Error Occured: ")
            fiddl_utils.PrintException()

        print(fiddl_utils.bcolors.OKBLUE, "                             FR analyzed info: ", anazlyzeInfo, fiddl_utils.bcolors.ENDC)
        current_app.logger.info("[UPLOAD-IMAGE] Photo saved and Analyzed by FR")
        
        userIdDetermined = anazlyzeInfo[0]
        proba = anazlyzeInfo[1]
        ID_DETERMINED = userIdDetermined
        PROBA = proba
        print(fiddl_utils.bcolors.OKBLUE, "                             User recognized (userIdDetermined): ", userIdDetermined, fiddl_utils.bcolors.ENDC)
        print(fiddl_utils.bcolors.OKBLUE, "                             Confidence (probability): ", proba, fiddl_utils.bcolors.ENDC)
        
        # TODO: If the userIdDetermined is the person registered to the home, unlock the door
        # if userIdDetermined.lower() == session['localId'].lower():
        #     current_app.logger.info("[UPLOAD-IMAGE] Person recognized as logged in user")
        #     # Unlocks the door while the user is logged in
        #     smartlock.unlock()
        #     current_app.logger.warning("[UPLOAD-IMAGE] Door Unlocked")
        #     userNameDetermined = session["firstName"]
        #     print(fiddl_utils.bcolors.OKBLUE, "                             User Recognized as: ", userNameDetermined, fiddl_utils.bcolors.ENDC)
        # else:
        #     current_app.logger.warning("[UPLOAD-IMAGE] Photo analyzed is not the logged in user.")
        #     userNameDetermined = "UnKnown Person in Photo"

        # Returning any 2xx status indicates successful receipt of the message.
    print("8")

@nestBP.route('/doorbell', methods=["POST"])
def recieve_message_handler():
    print()
    current_app.logger.info("[DOORBELL] Doorbell Event Found----------------------------------------------------------------------------------")
    current_app.logger.info("[DOORBELL] Google Cloud Platform has sent (pushed) to us a message from the doorbell")

    envelope = json.loads(request.data.decode('utf-8'))
    print(fiddl_utils.bcolors.OKGREEN, "                             [Nest Doorbell] \n JSON Envelope: ", envelope, fiddl_utils.bcolors.ENDC)
    payload = base64.b64decode(envelope['message']['data'])
    print(fiddl_utils.bcolors.OKGREEN, "                             JSON Payload: ", payload, fiddl_utils.bcolors.ENDC)
    print("0")
    handle_payload(payload)
    print("0.1")
    current_app.logger.info("[DOORBELL] Acknowledging Message")
    print("0.2")
    return 'OK', 200

@nestBP.route('/doorbell/image', methods=["GET",  "POST"])
def show_success():
    return render_template('doorbell.html', image=IMAGE_URL, IdDetermined=ID_DETERMINED, proba=PROBA)