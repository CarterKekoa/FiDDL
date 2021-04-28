from flask import Flask, render_template, json, request, redirect, url_for, session, send_from_directory, flash
from flask.globals import request
from flask.templating import render_template_string
from jws import verify                                                  #import flask libries, render_template is so we can make front end
import pyrebase
from pyrebase.pyrebase import storage  
import firebase_admin
from firebase_admin import storage as admin_storage, credentials, firestore
from collections import OrderedDict
import os
import imghdr
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google.cloud import language_v1 as language

from werkzeug.utils import secure_filename                               #takes a file name and returns a secure version of it
import subprocess
from datetime import timedelta                                          # used for permanent sessions
import smartlock

# Facial Recognition File Imports
import FacialRecognition.recognize as recognize
import FacialRecognition.extract_embeddings as extract_embeddings
import FacialRecognition.train_model as train_model

# Testing multifile format
from auth.auths import authsBP      # import the blueprints
from users.user import userBP
from general.main import mainBP
from doorbell.google_nest_api import nestBP


app = Flask(__name__)                                                    #call flask constuctor from object #__name__ references this file
   
app.register_blueprint(authsBP, url_prefix="")      # register the blue prints
app.register_blueprint(userBP, url_prefix="")
app.register_blueprint(mainBP, url_prefix="")
app.register_blueprint(nestBP, url_prefix="")

# Upload Image ---------------------------------
# TODO: put these in a private config file
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["PNG", "JPG", "JPEG"]
app.config["MAX_IMAGE_FILESIZE"] = 4 * 1024 * 1024    # 1,572,864 Bytes or 1572.864 KB

app.config["FIDDL_DIR"] = os.path.dirname(os.path.abspath(__file__)) # absolute path to this file
app.config["IMAGE_UPLOAD_DIR"] = os.path.join(app.config["FIDDL_DIR"], "photosTest")
app.config["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(app.config["FIDDL_DIR"], "fiddl-1604901867274-1d28c44d691d.json")
#print("app.config[GOOGLE_APPLICATION_CREDENTIALS]: ", app.config["GOOGLE_APPLICATION_CREDENTIALS"])
#app.config["PARENT_DIR"] = os.path.join(app.config["FILE_DIR"], os.pardir) # absolute path to this file's root directory


#Initializations  ////////////////////////////////__________________________________________________
#creden = service_account.Credentials.from_service_account_file(app.config["GOOGLE_APPLICATION_CREDENTIALS"])
#client = language.LanguageServiceClient(credentials=creden)
#print("+++++++++++++++++++++++++", client)

firebase = pyrebase.initialize_app(json.load(open('firebase/firebaseConfig.json')))
auth = firebase.auth()
db = firebase.database()                                    
fb_storage = firebase.storage()

cred = credentials.Certificate(json.load(open('firebase/fiddl-dev-firebase-adminsdk-80a9k-10d924f0ef.json')))
admin = firebase_admin.initialize_app(cred, {
    'storageBucket': 'fiddl-dev.appspot.com'
})
bucket = admin_storage.bucket()

# Add initializations to sesson to be used by BluePrints
app.config['firebase'] = firebase
app.config['auth'] = auth
app.config['db'] = db
app.config['storage'] = fb_storage
app.config['bucket'] = bucket
#app.config['client'] = client

#if running from command line, turn on dev mode
if not os.environ.get('SECRET_KEY') is None:
    app.secret_key = os.environ["SECRET_KEY"]                  # To get Heroku Envrionment Variable
app.permanent_session_lifetime = timedelta(hours=2)            # how long permanent session will last, hours,min,days

if __name__ == "__main__":      
    print("__main__")
    app.secret_key = os.urandom(24)                                # random secret key to track if user is logged in
    app.run(debug=True, host="0.0.0.0", port=os.environ.get("PORT", 5000))         #dev mode, server updates on own, shows errors
