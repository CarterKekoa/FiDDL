from flask import Blueprint, render_template, session, current_app, request, redirect, url_for, flash
import os       # Used when getting the uploaded image
from werkzeug.utils import secure_filename       #takes a file name and returns a secure version of it, for saving new photo file name
import smartlock
from PIL import Image
import cv2
import json
import base64

# Helper File Imports
import users.utils as utils
import fiddl_utils as fiddl_utils

# Facial Recognition File Imports
import FacialRecognition.recognize as recognize
import FacialRecognition.extract_embeddings as extract_embeddings
import FacialRecognition.train_model as train_model
import FacialRecognition.detect_faces as detect_faces

userBP = Blueprint("users", __name__, static_folder="static", template_folder="templates")

# Home Page ---------------------------------------------------------------------------------------------------
@userBP.route('/home', methods=["GET", "POST"])
def home():
    current_app.logger.info("[HOME]")
    homeowner = False
    names_list = []
    admitted_names_list = []
    # Check if a user is already logged in
    if not session.get('usr') is None:
        print()
        current_app.logger.info("[HOME] Home Process Started----------------------------------------------------------------------------------")
        current_app.logger.info("[HOME] A user is logged in, continue.")
        print(fiddl_utils.bcolors.OKBLUE, "                             Loged in user: ", session['localId'], fiddl_utils.bcolors.ENDC)
        firebase, auth, db, storage, bucket = fiddl_utils.initialize_data()

        #Grab users name
        user = db.child("users").child(session['localId']).get().val()
        if session["firstName"] == "kevin":
            homeowner = True

        #Parse the returned OrderedDict of data
        for uID, name in db.child("user_names").get().val().items():
            names_list.append(name)

        for uID, name in db.child("admitted_users").get().val().items():
            admitted_names_list.append(name)

        try:
            if request.method == "GET":
                #userId = auth.current_user['localId']               #auth.current_user is how we get the current users data
                photo_names_in_db = {}  # will be popluated with all of the users uploaded photo names
                images = []             # will store the urls of the users photos
                image_names = []        # will simply store the images names that exist in the users database
                current_app.logger.info("[HOME] Attempting to grab users database information...")

                #Parse the returned OrderedDict of data
                for val in user.values():
                    #Grab logining in users name from database. Not necessary here
                    for k,v in val.items():
                        #print(k,v)
                        if k[0] == '-':
                            photo_names_in_db[k] = v
                            image_names.append(v)
                            imageURL = storage.child("images/" + session['localId'] + "/" + v).get_url(None)      # URL for Google Storage Photo location
                            images.append(imageURL)                 # Stores the URL of each photo for the user
                        else:
                            session[k] = v
                            print(fiddl_utils.bcolors.OKBLUE, "                             session[", k, "]:", session[k], fiddl_utils.bcolors.ENDC)
                    
                session['userPhotoNames'] = photo_names_in_db        # session['userPhotoNames'] has the id of each photo paired with the actual photo file name
                print(fiddl_utils.bcolors.OKBLUE, "                             session['userPhotoNames']: ", session['userPhotoNames'], fiddl_utils.bcolors.ENDC)
                session["userImageURLs"] = images
                session["justPhotoNames"] = image_names
                print()
                print(fiddl_utils.bcolors.OKBLUE, "                             session['userImageURLs']: ", session['userImageURLs'], fiddl_utils.bcolors.ENDC)
                print()
                current_app.logger.info("[HOME] Users database information grabbed succesfully.")
                # TODO: Display more user info, kinds we need are probably user home nickname and
                

                # Prints stored user photos to users home screen
                current_app.logger.info("[HOME] Displaying photos to screen...")


            elif request.method == "POST":
                try:
                    #Check if button is clicked
                    if request.form['button'] == 'addNewPhoto':
                        #Add new photo button
                        current_app.logger.info("[HOME] Switching to [UPLOAD-IMAGE]----------------------------------------------------------------------------------")
                        return redirect(url_for('users.upload_image'))
                    elif request.form['button'] == 'clearPhotosButton':
                        ## Can't figure out how to clear photos from storage, database works
                        #for Pid, name in db.child("users").child(session['localId']).child("photos").get().val().items():
                            #print("name: ", name)
                            #storage.child("images/" + session['localId'] + "/").delete(name)
                        db.child("users").child(session['localId']).child("photos").remove()
                        session["userImageURLs"] = []
                        session["justPhotoNames"] = []
                    elif request.form['button'] == 'submitPersonsButton':
                        admitted_names_list = request.form.getlist("persons")
                        for person in admitted_names_list:
                            admitted = False
                            for uID, name in db.child("admitted_users").get().val().items():
                                if person == name:
                                    admitted = True
                            if admitted == False:
                                db.child("admitted_users").push(person)
                        for uID, name in db.child("admitted_users").get().val().items():
                            if name not in admitted_names_list:
                                db.child("admitted_users").child(uID).remove()
                     elif request.form['input'] == 'pullNestMessagesButton':
                        # TODO: Doorbell
                        print("Pull nest messages button clicked")
                        return redirect(url_for('users.nest'))
                    elif request.form['button'] == 'logoutButton':
                        #Logout Button
                        current_app.logger.info("[HOME] Loggin Out, switching to [LOGOUT]----------------------------------------------------------------------------------")
                        return redirect(url_for('auth.logout'))
                except:
                    # Fail
                    current_app.logger.warning("[ERROR - Buttons] Error Occured: ")
                    fiddl_utils.PrintException()

            # have a homeowner variable and return different templates depending on who is logged in
            if homeowner == True:
                return render_template('home.html', admitted_names=admitted_names_list, user_names=names_list, firstName=session["firstName"], images=session["userImageURLs"], imgNames = session["justPhotoNames"])
            else:
                return render_template('home.html', firstName=session["firstName"], images=session["userImageURLs"], imgNames = session["justPhotoNames"])
        except:
            # Home Fail
            current_app.logger.warning("[ERROR - HOME] Error Occured: ")
            fiddl_utils.PrintException()
            if homeowner == True:
                return render_template('home.html', admitted_names=admitted_names_list, user_names=names_list, firstName=session["firstName"], images=session["userImageURLs"], imgNames = session["justPhotoNames"])
            else:
                return render_template('home.html', firstName=session["firstName"], images=session["userImageURLs"], imgNames = session["justPhotoNames"])



# Upload Image ---------------------------------
@userBP.route('/upload-image', methods=["GET", "POST"])
def upload_image():
    current_app.logger.info("[UPLOAD-IMAGE]")
    print(fiddl_utils.bcolors.OKBLUE, "                             app.configapp.config[IMAGE_UPLOAD_DIR]: ", current_app.config["IMAGE_UPLOAD_DIR"], fiddl_utils.bcolors.ENDC)
    
    # Check if a user is already logged in
    print(fiddl_utils.bcolors.OKBLUE, "                             session.get('usr') is None: ", session.get('usr') is None, fiddl_utils.bcolors.ENDC)

    if not session.get('usr') is None:
        print()
        current_app.logger.info("[UPLOAD-IMAGE] Upload Image Process Started----------------------------------------------------------------------------------")
        current_app.logger.info("[UPLOAD-IMAGE] A user is logged in, continue.")
        print(fiddl_utils.bcolors.OKBLUE, "                             Loged in user: ", session['localId'], fiddl_utils.bcolors.ENDC)

        firebase, auth, db, storage, bucket = fiddl_utils.initialize_data()
        
        if request.method == "POST":
            try:
                if request.files:
                    current_app.logger.info("[UPLOAD-IMAGE] Starting to get user photo")
                    image = request.files["image"]                        #works the same as user input email in register, get the image file
                    #print(fiddl_utils.bcolors.WARNING, "                             file type: ", type(image), fiddl_utils.bcolors.ENDC)

                    print(fiddl_utils.bcolors.OKBLUE, "                             Image Grabbed: ", image, fiddl_utils.bcolors.ENDC)

                    #Grab the file size
                    image.seek(0, os.SEEK_END)
                    file_size = image.tell()
                    print(fiddl_utils.bcolors.OKBLUE, "                             Images File Size: ", file_size, fiddl_utils.bcolors.ENDC)

                    #Check the image file size
                    if not utils.allowed_image_filesize(file_size):
                        current_app.logger.info("[UPLOAD-IMAGE] FAIL Bad File Size")
                        return redirect(request.url)
                    
                    #Check for file name
                    if image.filename == "":
                        current_app.logger.info("[UPLOAD-IMAGE] FAIL No file name")
                        return redirect(request.url)
                    
                    #Check if image has correct type
                    if not utils.allow_image(image.filename):
                        current_app.logger.info("[UPLOAD-IMAGE] FAIL Bad image type")
                        return redirect(request.url)
                    else:
                        #All tests pass, we can now save the photo to database
                        current_app.logger.info("[UPLOAD-IMAGE] Good photo attributes, grabbing the image")
                        filename = secure_filename(image.filename)          #create new secure file name
                        print(fiddl_utils.bcolors.OKBLUE, "                             Secure Image Filename: ", filename, fiddl_utils.bcolors.ENDC)
        
                        #Get user local Id to store their photos seperate
                        #userId = auth.current_user['localId']               #auth.current_user is how we get the current users data, userId is so each user has their own photo folder
                        print(fiddl_utils.bcolors.OKBLUE, "                             session['localId']: ", session['localId'], fiddl_utils.bcolors.ENDC)
                        #userIdToken = auth.current_user['idToken']
                        userIdToken = session['localId']
                        #print(fiddl_utils.bcolors.OKBLUE, "                             userIdToken: ", userIdToken, fiddl_utils.bcolors.ENDC)
                        
                        image.seek(0)                               #NEED THIS! We point to the end of the file above to find the size, this causes a empty file to upload without this fix
                        
                        #Check if to run FR or Store photo
                        if request.form.get('analyzer') == 'analyze':
                            #Analyze Check box checked. Run FR on uploaded image then
                            # Save to database temporarily duh
                            try:
                                current_app.logger.info("[UPLOAD-IMAGE] Temp. saving to database and analyzing")
                                storage.child("images/temp/" + filename).put(image, userIdToken)
                                current_app.logger.info("[UPLOAD-IMAGE] Photo saved, grabbing url")
                                imageURL = storage.child("images/temp/" + filename).get_url(None)
                                
                                anazlyzeInfo = recognize.facialRecognition(imageURL)

                                delete_temp_image_path = "images/temp/" + filename
                                blob = bucket.blob(delete_temp_image_path)
                                print(fiddl_utils.bcolors.OKBLUE, "                             Image Blob being deleted: ", blob, fiddl_utils.bcolors.ENDC)
                                blob.delete()
                                current_app.logger.info("[UPLOAD-IMAGE] Photo Analyzed and deleted from temporary storage")
                            except:
                                # Analyze Fail
                                current_app.logger.warning("[ERROR - ANALYZE] Error Occured: ")
                                fiddl_utils.PrintException()
    
                            #image.save(os.path.join(current_app.config["IMAGE_UPLOAD_DIR"]))          #Saves analyzed photo to photosTest/analyzePhotos to be used by FR
                            #anazlyzeInfo = recognize.facialRecognition(os.path.join(current_app.config["IMAGE_UPLOAD_DIR"], filename))
                            print(fiddl_utils.bcolors.OKBLUE, "                             FR analyzed info: ", anazlyzeInfo, fiddl_utils.bcolors.ENDC)
                            current_app.logger.info("[UPLOAD-IMAGE] Photo saved and Analyzed by FR")
                            #os.remove(os.path.join(current_app.config["IMAGE_UPLOAD_DIR"], filename))           # remove the photo from photosTest/analyzePhotos
                            
                            userIdDetermined = anazlyzeInfo[0]
                            proba = anazlyzeInfo[1]
                            print(fiddl_utils.bcolors.OKBLUE, "                             User recognized (userIdDetermined): ", userIdDetermined, fiddl_utils.bcolors.ENDC)
                            print(fiddl_utils.bcolors.OKBLUE, "                             Confidence (probability): ", proba, fiddl_utils.bcolors.ENDC)
                            
                            if userIdDetermined.lower() == session['localId'].lower():
                                current_app.logger.info("[UPLOAD-IMAGE] Person recognized as logged in user")
                                # Unlocks the door while the user is logged in
                                smartlock.unlock()
                                current_app.logger.warning("[UPLOAD-IMAGE] Door Unlocked")
                                userNameDetermined = session["firstName"]
                                print(fiddl_utils.bcolors.OKBLUE, "                             User Recognized as: ", userNameDetermined, fiddl_utils.bcolors.ENDC)
                            else:
                                current_app.logger.warning("[UPLOAD-IMAGE] Photo analyzed is not the logged in user.")
                                userNameDetermined = "UnKnown Person in Photo"
                            
                            return render_template("upload_image.html", name=userNameDetermined, proba=proba)
                        else:
                            #Images being uploaded to db instead
                            current_app.logger.info("[UPLOAD-IMAGE] Photo is being uploaded to users database...")
                            
                            if not utils.used_filename(filename):
                                # used to detect and crop faces in images. Doesnt really improve FR accuracy so it will die here
                                #image.save(os.path.join(current_app.config["IMAGE_UPLOAD_DIR"], filename))          #Saves analyzed photo to photosTest/analyzePhotos to be used by FR
                                #detect_faces.detect_face(os.path.join(current_app.config["IMAGE_UPLOAD_DIR"], filename))
                                #storage.child("images/" + session['usr'] + "/" + filename).put(os.path.join(current_app.config["IMAGE_UPLOAD_DIR"], filename), userIdToken)
                                #os.remove(os.path.join(current_app.config["IMAGE_UPLOAD_DIR"], filename))           # remove the photo from photosTest/analyzePhotos
                                current_app.logger.info("[UPLOAD-IMAGE] Photo saved and Analyzed by FR")
                                
                                #TODO: test the photo the user is uploading and tell them if it is good or not
                                #Save user photo to Google Storage
                                storage.child("images/" + session['localId'] + "/" + filename).put(image, userIdToken)
                                current_app.logger.info("[UPLOAD-IMAGE] Photo stored.")

                                #Add photo filename data to realtime database, for reference later
                                db.child("users").child(session['localId']).child("photos").push(filename)
                                current_app.logger.info("[UPLOAD-IMAGE] Photo filename stored.")

                    return redirect(request.url)
                elif request.form['button'] == 'logoutButton':
                    #Logout Button
                    current_app.logger.info("[UPLOAD-IMAGE] Loggin Out, switching to [LOGOUT]----------------------------------------------------------------------------------")
                    return redirect(url_for('auth.logout'))
                elif request.form['button'] == 'backHomeButton':
                    #Home Button
                    current_app.logger.info("[UPLOAD-IMAGE] Switching to [HOME]----------------------------------------------------------------------------------")
                    return redirect(url_for('users.home'))
            except:
                # Upload Image Fail
                current_app.logger.warning("[ERROR - UPLOAD-IMAGE] Error Occured: ")
                fiddl_utils.PrintException()
    else:       
        #No user logged in
        current_app.logger.warning("[UPLOAD-IMAGE] No user currently logged in, redirecting moving to [LOGIN]----------------------------------------------------------------------------------")
        return redirect(url_for('auth.login'))
    
    return render_template("upload_image.html")
