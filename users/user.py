from flask import Blueprint, render_template, session, current_app, request, redirect, url_for, flash
import os       # Used when getting the uploaded image
from werkzeug.utils import secure_filename       #takes a file name and returns a secure version of it, for saving new photo file name
import smartlock
from PIL import Image
import cv2

# Facial Recognition File Imports
import FacialRecognition.recognize as recognize
import FacialRecognition.extract_embeddings as extract_embeddings
import FacialRecognition.train_model as train_model
import FacialRecognition.detect_faces as detect_faces

userBP = Blueprint("users", __name__, static_folder="static", template_folder="templates")


# Colors for colored terminal prints
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def initialize_data():
    firebase = current_app.config['firebase']
    auth = current_app.config['auth']
    db = current_app.config['db']
    storage = current_app.config['storage']
    USER = current_app.config['USER']
    return firebase, auth, db, storage, USER
   
# Check if image is allowed function
def allow_image(filename):
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
        flash(badFileName, "info")                    #"info" is the type of message for more customization if we want, others are warning, info, error
        return False

# Check image file size 
def allowed_image_filesize(file_size):
    if int(file_size) <= current_app.config["MAX_IMAGE_FILESIZE"]:
        current_app.logger.info("[UPLOAD_IMAGE] Valid Image File Size")
        return True
    else:
        current_app.logger.warning("[UPLOAD_IMAGE] Invalid Image File Size")
        badFileSize = "File size is too large. Be sure the file size is less than 1,572,864 Bytes or 1572.864 KB"
        flash(badFileSize, "info")                    #"info" is the type of message for more customization if we want, others are warning, info, error
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
                flash(dupFileName, "info")                    #"info" is the type of message for more customization if we want, others are warning, info, error
                return True
    current_app.logger.info("[UPLOAD_IMAGE] Image File Name is new.")
    return False

# Home Page ---------------------------------------------------------------------------------------------------
@userBP.route('/home', methods=["GET", "POST"])
def home():
    current_app.logger.info("[HOME]")
    # Check if a user is already logged in
    if not session.get('usr') is None:
        print()
        current_app.logger.info("[HOME] Home Process Started----------------------------------------------------------------------------------")
        current_app.logger.info("[HOME] A user is logged in, continue.")
        print(bcolors.OKBLUE, "                             Loged in user: ", session['localId'], bcolors.ENDC)
        firebase, auth, db, storage, USER = initialize_data()
        try:
            userId = auth.current_user['localId']               #auth.current_user is how we get the current users data
        
            photo_names_in_db = {}  # will be popluated with all of the users uploaded photo names
            images = []             # will store the urls of the users photos
            image_names = []        # will simply store the images names that exist in the users database
            
            current_app.logger.info("[HOME] Attempting to grab users database information...")
            #Grab users name
            user = db.child("users").child(session['localId']).get().val()
            #Parse the returned OrderedDict of data
            for val in user.values():
                #Grab logining in users name from database. Not necessary here
                for k,v in val.items():
                    #print(k,v)
                    if k[0] == '-':
                        photo_names_in_db[k] = v
                        image_names.append(v)
                        imageURL = storage.child("images/" + userId + "/" + v).get_url(None)      # URL for Google Storage Photo location
                        images.append(imageURL)                 # Stores the URL of each photo for the user
                    else:
                        session[k] = v
                        print(bcolors.OKBLUE, "                             session[", k, "]:", session[k], bcolors.ENDC)
                
            session['userPhotoNames'] = photo_names_in_db        # session['userPhotoNames'] has the id of each photo paired with the actual photo file name
            print(bcolors.OKBLUE, "                             session['userPhotoNames']: ", session['userPhotoNames'], bcolors.ENDC)
            session["userImageURLs"] = images
            session["justPhotoNames"] = image_names
            print()
            print(bcolors.OKBLUE, "                             session['userImageURLs']: ", session['userImageURLs'], bcolors.ENDC)
            print()
            current_app.logger.info("[HOME] Users database information grabbed succesfully.")
            # TODO: Display more user info, kinds we need are probably user home nickname and

            # Prints stored user photos to users home screen
            current_app.logger.info("[HOME] Displaying photos to screen...")
            return render_template('home.html', firstName=session["firstName"], images=session["userImageURLs"], imgNames = session["justPhotoNames"])
        except Exception as err:
            # Home Fail
            print(bcolors.FAIL, "                             [ERROR Described Below]", bcolors.ENDC)
            current_app.logger.warning("[ERROR - HOME] Error Occured: ")
            print(bcolors.FAIL, "                             ", err, bcolors.ENDC)
            render_template('home.html', firstName=session["firstName"])
        
        if request.method == "POST":
            #Check if button is clicked
            if request.form['button'] == 'addNewPhoto':
                #Add new photo button
                current_app.logger.info("[HOME] Switching to [UPLOAD-IMAGE]----------------------------------------------------------------------------------")
                return redirect(url_for('users.upload_image'))
            elif request.form['button'] == 'updateMyHome':
                #TODO: make this for editing user info
                render_template('/home')
            elif request.form['button'] == 'logoutButton':
                #Logout Button
                current_app.logger.info("[HOME] Loggin Out, switching to [LOGOUT]----------------------------------------------------------------------------------")
                return redirect(url_for('auth.logout'))
            return render_template('home.html')
        elif request.method == "GET":
            render_template('home.html')
    else:
        current_app.logger.warning("[HOME] No user currently logged in, redirecting moving to [LOGIN]----------------------------------------------------------------------------------")
        return redirect(url_for('auth.login'))
    return render_template('home.html')

# Upload Image ---------------------------------
@userBP.route('/upload-image', methods=["GET", "POST"])
def upload_image():
    current_app.logger.info("[UPLOAD-IMAGE]")
    print(bcolors.OKBLUE, "                             app.configapp.config[IMAGE_UPLOAD_DIR]: ", current_app.config["IMAGE_UPLOAD_DIR"], bcolors.ENDC)
    
    # Check if a user is already logged in
    if not session.get('usr') is None:
        print()
        current_app.logger.info("[UPLOAD-IMAGE] Upload Image Process Started----------------------------------------------------------------------------------")
        current_app.logger.info("[UPLOAD-IMAGE] A user is logged in, continue.")
        print(bcolors.OKBLUE, "                             Loged in user: ", session['localId'], bcolors.ENDC)

        firebase, auth, db, storage, USER = initialize_data()
        
        if request.method == "POST":
            try:
                if request.files:
                    current_app.logger.info("[UPLOAD-IMAGE] Starting to get user photo")
                    image = request.files["image"]                        #works the same as user input email in register, get the image file
                    #print(bcolors.WARNING, "                             file type: ", type(image), bcolors.ENDC)

                    print(bcolors.OKBLUE, "                             Image Grabbed: ", image, bcolors.ENDC)

                    #Grab the file size
                    image.seek(0, os.SEEK_END)
                    file_size = image.tell()
                    print(bcolors.OKBLUE, "                             Images File Size: ", file_size, bcolors.ENDC)

                    #Check the image file size
                    if not allowed_image_filesize(file_size):
                        current_app.logger.info("[UPLOAD-IMAGE] FAIL Bad File Size")
                        return redirect(request.url)
                    
                    #Check for file name
                    if image.filename == "":
                        current_app.logger.info("[UPLOAD-IMAGE] FAIL No file name")
                        return redirect(request.url)
                    
                    #Check if image has correct type
                    if not allow_image(image.filename):
                        current_app.logger.info("[UPLOAD-IMAGE] FAIL Bad image type")
                        return redirect(request.url)
                    else:
                        #All tests pass, we can now save the photo to database
                        current_app.logger.info("[UPLOAD-IMAGE] Good photo attributes, grabbing the image")
                        filename = secure_filename(image.filename)          #create new secure file name
                        print(bcolors.OKBLUE, "                             Secure Image Filename: ", filename, bcolors.ENDC)
        
                        #Get user local Id to store their photos seperate
                        userId = auth.current_user['localId']               #auth.current_user is how we get the current users data, userId is so each user has their own photo folder
                        print(bcolors.OKBLUE, "                             userId: ", userId, bcolors.ENDC)
                        userIdToken = auth.current_user['idToken']
                        #print(bcolors.OKBLUE, "                             userIdToken: ", userIdToken, bcolors.ENDC)

                        image.seek(0)                               #NEED THIS! We point to the end of the file above to find the size, this causes a empty file to upload without this fix
                        
                        #Check if to run FR or Store photo
                        if request.form.get('analyzer') == 'analyze':
                            #Analyze Check box checked. Run FR on uploaded image then
                            # TODO: this save isnt working when deployed. May have to try just passing the image directly
                            image.save(os.path.join(current_app.config["IMAGE_UPLOAD_DIR"], filename))          #Saves analyzed photo to photosTest/analyzePhotos to be used by FR
                            anazlyzeInfo = recognize.facialRecognition(os.path.join(current_app.config["IMAGE_UPLOAD_DIR"], filename))
                            print(bcolors.OKBLUE, "                             FR analyzed info: ", anazlyzeInfo, bcolors.ENDC)
                            current_app.logger.info("[UPLOAD-IMAGE] Photo saved and Analyzed by FR")
                            
                            os.remove(os.path.join(current_app.config["IMAGE_UPLOAD_DIR"], filename))           # remove the photo from photosTest/analyzePhotos
                            
                            userIdDetermined = anazlyzeInfo[0]
                            proba = anazlyzeInfo[1]
                            print(bcolors.OKBLUE, "                             User recognized (userIdDetermined): ", userIdDetermined, bcolors.ENDC)
                            print(bcolors.OKBLUE, "                             Confidence (probability): ", proba, bcolors.ENDC)
                            
                            if userIdDetermined.lower() == session['localId'].lower():
                                # Unlocks the door while the user is logged in
                                smartlock.unlock()
                                print(userIdDetermined + " " + session['localId'])
                                current_app.logger.info("[UPLOAD-IMAGE] Photo recognized as logged in user.")
                                userNameDetermined = session["firstName"]
                                print(bcolors.OKBLUE, "                             User Recognized as: ", userNameDetermined, bcolors.ENDC)
                            else:
                                current_app.logger.warning("[UPLOAD-IMAGE] Photo analyzed is not the logged in user.")
                                userNameDetermined = "UnKnown Person in Photo"
                            
                            return render_template("upload_image.html", name=userNameDetermined, proba=proba)
                        else:
                            #Images being uploaded to db instead
                            current_app.logger.info("[UPLOAD-IMAGE] Photo is being uploaded to users database...")
                            
                            if not used_filename(filename):
                                # used to detect and crop faces in images. Doesnt really improve FR accuracy so it will die here
                                #image.save(os.path.join(current_app.config["IMAGE_UPLOAD_DIR"], filename))          #Saves analyzed photo to photosTest/analyzePhotos to be used by FR
                                #detect_faces.detect_face(os.path.join(current_app.config["IMAGE_UPLOAD_DIR"], filename))
                                #storage.child("images/" + userId + "/" + filename).put(os.path.join(current_app.config["IMAGE_UPLOAD_DIR"], filename), userIdToken)
                                #os.remove(os.path.join(current_app.config["IMAGE_UPLOAD_DIR"], filename))           # remove the photo from photosTest/analyzePhotos
                                current_app.logger.info("[UPLOAD-IMAGE] Photo saved and Analyzed by FR")
                                
                                #TODO: test the photo the user is uploading and tell them if it is good or not
                                #Save user photo to Google Storage
                                storage.child("images/" + userId + "/" + filename).put(image, userIdToken)
                                current_app.logger.info("[UPLOAD-IMAGE] Photo stored.")

                                #Add photo filename data to realtime database, for reference later
                                db.child("users").child(userId).child("photos").push(filename)
                                current_app.logger.info("[UPLOAD-IMAGE] Photo filename stored.")

                    return redirect(request.url)
                elif request.form['button'] == 'logoutButton':
                    #Logout Button
                    current_app.logger.info("[UPLOAD-IMAGE] Loggin Out, switching to [LOGOUT]----------------------------------------------------------------------------------")
                    return redirect(url_for('auth.logout'))
                elif request.form['button'] == 'backHomeButton':
                    #Home Button
                    current_app.logger.info("[UPLOAD-IMAGE] Switching to [HOME]----------------------------------------------------------------------------------")
                    return redirect(url_for('general.home'))
            except Exception as err:
                # Home Fail
                print(bcolors.FAIL, "                             [ERROR Described Below]", bcolors.ENDC)
                current_app.logger.warning("[ERROR - UPLOAD-IMAGE] Error Occured: ")
                print(bcolors.FAIL, "                             ", err, bcolors.ENDC)
    else:       
        #No user logged in
        current_app.logger.warning("[UPLOAD-IMAGE] No user currently logged in, redirecting moving to [LOGIN]----------------------------------------------------------------------------------")
        return redirect(url_for('auth.login'))
    
    return render_template("upload_image.html")