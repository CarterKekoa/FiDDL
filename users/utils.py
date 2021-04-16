import linecache
import sys
from flask import Flask, current_app, flash, session
import pyrebase

import requests
import json
import os

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

