from flask import Flask, render_template, json, request, redirect, url_for, session, send_from_directory, flash
from flask.globals import request
from flask.templating import render_template_string
from jws import verify                                                  #import flask libries, render_template is so we can make front end
import pyrebase
from collections import OrderedDict
import os
import imghdr
from pyrebase.pyrebase import Storage                                    #for images
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




app = Flask(__name__)                                                    #call flask constuctor from object #__name__ references this file
   
app.register_blueprint(authsBP, url_prefix="")      # register the blue prints
app.register_blueprint(userBP, url_prefix="")
app.register_blueprint(mainBP, url_prefix="")

# Upload Image ---------------------------------
# TODO: put these in a private config file
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["PNG", "JPG", "JPEG"]
app.config["MAX_IMAGE_FILESIZE"] = 4 * 1024 * 1024    # 1,572,864 Bytes or 1572.864 KB

app.config["FIDDL_DIR"] = os.path.dirname(os.path.abspath(__file__)) # absolute path to this file
app.config["IMAGE_UPLOAD_DIR"] = os.path.join(app.config["FIDDL_DIR"], "photosTest")

#app.config["PARENT_DIR"] = os.path.join(app.config["FILE_DIR"], os.pardir) # absolute path to this file's root directory


#Initializations  ////////////////////////////////__________________________________________________
firebase = pyrebase.initialize_app(json.load(open('firebase/firebaseConfig.json')))
auth = firebase.auth()
db = firebase.database()                                    
app.secret_key = os.urandom(24)                                     # random secret key to track if user is logged in
app.permanent_session_lifetime = timedelta(hours=2)                 # how long permanent session will last, hours,min,days
storage = firebase.storage()

# Add initializations to sesson to be used by BluePrints
app.config['firebase'] = firebase
app.config['auth'] = auth
app.config['db'] = db
app.config['storage'] = storage

# Initialize USER as a global dictionary
USER = {
    "firstName": "",
    "lastName": "",
    "email": "",
    "uid": "",
    "photos": [],
    "image_locations": []
    }
app.config['USER'] = USER

if __name__ == "__main__":      #if running from command line, turn on dev mode
    app.run(debug=True)         #dev mode, server updates on own, shows errors
