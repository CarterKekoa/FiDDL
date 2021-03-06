# google_nest_api.py
from flask import Blueprint, render_template, session, current_app, request, redirect, url_for, flash
import requests
import json
import os
import base64
import smartlock

# Helper File Imports
import doorbell.utils as utils
import fiddl_utils as fiddl_utils

# Facial Recognition File Imports
import FacialRecognition.recognize as recognize

nestBP = Blueprint("doorbell", __name__, static_folder="static", template_folder="templates")

IMG_URL = None
ID_DETERMINED = None
PROBA = None

def handle_payload(payload):
    current_app.logger.info("[DOORBELL] Payload received, Passing to Google Nest API functions")
    event_info = []
    event_info = utils.callback(payload)
    firebase, auth, db, storage, bucket = fiddl_utils.initialize_data()
    print(fiddl_utils.bcolors.OKBLUE, "                             event_info: ", event_info, fiddl_utils.bcolors.ENDC)


    
    if(event_info):
        print(fiddl_utils.bcolors.OKBLUE, "                             Good Event, Processing Image ", fiddl_utils.bcolors.ENDC)
        image_url = event_info[0]
        event_token = event_info[1]
        headers = event_info[2]
        event_id = event_info[3]
        current_app.logger.info("[DOORBELL] Storing Event Image in Database")
        
        response = requests.get(image_url, headers=headers, stream=True)

        storage.child("images/nestDoorbell/" + event_id).put(response.content)
        imageURL = storage.child("images/nestDoorbell/" + event_id).get_url(None)
        current_app.logger.info("[DOORBELL] Image Saved to Database Succesfully")
        print()
        print(fiddl_utils.bcolors.OKBLUE, "                             Database Image URL: ", imageURL, fiddl_utils.bcolors.ENDC)

        try:
            current_app.logger.info("[DOORBELL] Analyzing Person in Photo")
            anazlyzeInfo = recognize.facialRecognition(imageURL)
            print(fiddl_utils.bcolors.OKBLUE, "                             FR analyzed info: ", anazlyzeInfo, fiddl_utils.bcolors.ENDC)
            if(anazlyzeInfo):
                # TODO: Delete these photos once analyzed
                # delete_temp_image_path = "images/nestDoorbell/" + event_id
                # blob = bucket.blob(delete_temp_image_path)
                # print(fiddl_utils.bcolors.OKBLUE, "                             Image Blob being deleted: ", blob, fiddl_utils.bcolors.ENDC)
                # blob.delete()
                current_app.logger.info("[UPLOAD-IMAGE] Photo Analyzed (not currently deleting from temporary storage)")
                userIdDetermined = anazlyzeInfo[0]
                proba = anazlyzeInfo[1]
                print(fiddl_utils.bcolors.OKBLUE, "                             User recognized (userIdDetermined): ", userIdDetermined, fiddl_utils.bcolors.ENDC)
                print(fiddl_utils.bcolors.OKBLUE, "                             Confidence (probability): ", proba, fiddl_utils.bcolors.ENDC)
                current_app.logger.info("[UPLOAD-IMAGE] Photo saved and Analyzed by FR")
                # Returning any 2xx status indicates successful receipt of the message.
                render_template('doorbell.html', image=imageURL, IdDetermined=userIdDetermined, proba=proba)

                userNameDetermined = "Unknown"
                user = db.child("users").child(userIdDetermined).get().val()
                for val in user.values():
                    for k,v in val.items():
                        if k == "firstName":
                            for uID, name in db.child("admitted_users").get().val().items():
                                if name.lower() == v.lower():
                                    # Confidence level to unlock at
                                    if proba > 30:
                                        smartlock.unlock()
                                        current_app.logger.warning("[UPLOAD-IMAGE] Door Unlocked")
                                        userNameDetermined = name
                                        print(fiddl_utils.bcolors.OKBLUE, "                             User Recognized as: ", userNameDetermined, fiddl_utils.bcolors.ENDC)

                if userNameDetermined == "Unknown":
                    current_app.logger.warning("[UPLOAD-IMAGE] Person is unknown.")
                    userNameDetermined = "UnKnown Person in Photo"
            else:
                print(fiddl_utils.bcolors.WARNING, "                             Bad photo from Google Nest Doorbell", fiddl_utils.bcolors.ENDC)

        except:
            # Analyze Fail
            current_app.logger.warning("[ERROR - DOORBELL] Error Occured: ")
            fiddl_utils.PrintException()
            print(fiddl_utils.bcolors.WARNING, "                             Most Likely Bad Photo, ring doorbell to try again.", fiddl_utils.bcolors.ENDC)
            return None

    else:
        print(fiddl_utils.bcolors.OKBLUE, "                             Unwanted Event, just acknoweledge message. ", fiddl_utils.bcolors.ENDC)
        return None

@nestBP.route('/doorbell', methods=["POST"])
def recieve_message_handler():
    print()
    current_app.logger.info("[DOORBELL] Doorbell Event Found----------------------------------------------------------------------------------")
    current_app.logger.info("[DOORBELL] Google Cloud Platform has sent (pushed) to us a message from the doorbell")

    envelope = json.loads(request.data.decode('utf-8'))
    print(fiddl_utils.bcolors.OKGREEN, "                             [Nest Doorbell] \n JSON Envelope: ", envelope, fiddl_utils.bcolors.ENDC)
    payload = base64.b64decode(envelope['message']['data'])
    print(fiddl_utils.bcolors.OKGREEN, "                             JSON Payload: ", payload, fiddl_utils.bcolors.ENDC)

    handle_payload(payload)
    current_app.logger.info("[DOORBELL] Acknowledging Message")
    return 'OK', 200

@nestBP.route('/doorbell/image', methods=["GET",  "POST"])
def show_success():
    return render_template('doorbell.html', image=IMG_URL, IdDetermined=ID_DETERMINED, proba=PROBA)