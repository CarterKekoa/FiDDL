from flask import Blueprint, render_template, session, current_app, request, redirect, url_for, flash
import os       # Used when getting the uploaded image
from werkzeug.utils import secure_filename       #takes a file name and returns a secure version of it, for saving new photo file name
import smartlock

# Facial Recognition File Imports
import FacialRecognition.recognize as recognize
import FacialRecognition.extract_embeddings as extract_embeddings
import FacialRecognition.train_model as train_model

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

    # Check if the image filename has already been stored
    if not session.get('userPhotoNames') is None:
        for k,v in session['userPhotoNames'].items():
            if v == filename:
                current_app.logger.warning("[UPLOAD_IMAGE] Invalid, Image File Name is already stored")
                dupFileName = "This file name has previously been stored on this account. This could mean this same photo has also already been uploaded to this account. Please try a new photo for best accuracy."
                flash(dupFileName, "info")                    #"info" is the type of message for more customization if we want, others are warning, info, error
                return False

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
                return redirect(url_for('users.upload_image'))
            elif request.form['button'] == 'updateMyHome':
                #TODO: make this my home portion
                render_template('/home')
            elif request.form['button'] == 'logoutButton':
                #Logout Button
                return redirect(url_for('auth.logout'))
            return render_template('home.html')
        elif request.method == "GET":
            render_template('home.html')
    else:
        current_app.logger.warning("[HOME] No user currently logged in, redirecting moving to [LOGIN]----------------------------------------------------------------------------------")
        return redirect(url_for('auth.login'))
    return render_template('home.html')


# TODO: optimize this route
# Upload Image ---------------------------------
@userBP.route('/upload-image', methods=["GET", "POST"])
def upload_image():
    # Alert Messages
    userLogedIn = "User is still logged in (PhotoUpload - Good)."
    userNotIn = "No user logged in (PhotoUpload - Bad)."

    try:
        print(session['usr'])                   #this is equal to logged in users id token->  user['idToken']
        current_app.logger.info(userLogedIn)
        #TODO: add a logout button, make sure to delete session for use on logout
        #user = session['usr']

        firebase, auth, db, storage, USER = initialize_data()

        # Alert Messages
        noFileName = 'Image must have a file name.'
        badFileSize = 'Image file size is too large.'
        badFileName = 'That image extension or file name is not allowed'
        dataAdded = 'User photos added to Google Storage'

        
        if request.method == "POST":
            if request.files:
                image = request.files["image"]                        #works the same as user input email in register, get the image file
                print("image: ")
                print(image)

                #Grab the file size
                image.seek(0, os.SEEK_END)
                file_size = image.tell()
                print("Image File Size: ")
                print(file_size)

                #Check the image file size
                if not allowed_image_filesize(file_size):
                    #TODO: alert user on screen of the issue
                    current_app.logger.info(badFileSize)
                    return redirect(request.url)
                
                #Check for file name
                if image.filename == "":
                    current_app.logger.info(noFileName)
                    return redirect(request.url)
                
                #Check if image has correct type
                if not allow_image(image.filename):
                    current_app.logger.info(badFileName)
                    return redirect(request.url)
                else:
                    #All tests pass, we can now save the photo to database
                    filename = secure_filename(image.filename)          #create new secure file name
                    print("Secure Filename: ")
                    print(filename)
                    
                    #User data available tests
                    #print("session['usr']: " + session['usr'])
                    #print("user: " + user)
                    #print("auth.current_user: " + auth.current_user)
    
                    #Get user local Id to store their photos seperate
                    userId = auth.current_user['localId']               #auth.current_user is how we get the current users data, userId is so each user has their own photo folder
                    print("userId: ")
                    print(userId)
                    userIdToken = auth.current_user['idToken']
                    print("userIdToken auth.current_user['idToken']:", userIdToken)

                    image.seek(0)                               #NEED THIS! We point to the end of the file above to find the size, this causes a empty file to upload without this fix
                    
                    #Check if to run FR or Store photo
                    if request.form.get('analyzer') == 'analyze':
                        #Analyze Check box checked. Run FR on uploaded image then
                        image.save(os.path.join(current_app.config["IMAGE_ANALYZE_UPLOAD"], filename))          #Saves analyzed photo to photosTest/analyzePhotos to be used by FR
                        anazlyzeInfo = recognize.facialRecognition("photosTest/analyzePhotos/" + filename)
                        os.remove("photosTest/analyzePhotos/" + filename)           # remove the photo from photosTest/analyzePhotos
                        print("analyze infor FR recognize:", anazlyzeInfo)
                        userIdDetermined = anazlyzeInfo[0]
                        proba = anazlyzeInfo[1]
                        # TODO: Shawns Code is called here
                        print("userIdDetermined:", userIdDetermined)
                        print("USER[uid]:", USER["uid"])
                        print("")
                        if userIdDetermined.lower() == session['localId'].lower():
                            # TODO: Tell lock to unlock for correct user
                            smartlock.unlock()
                            print(userIdDetermined + " " + session['localId'])
                            userNameDetermined = session["firstName"]
                            
                        return render_template("upload_image.html", name=userNameDetermined, proba=proba)
                    else:
                        #Images being uploaded to db instead
                        #Save photo to local directory, Testing only
                        #image.save(os.path.join(current_app.config["IMAGE_UPLOAD"], filename))  #save images to /photosTest for testing
                    
                        #Save user photo to Google Storage
                        storage.child("images/" + userId + "/" + filename).put(image, userIdToken)
                        current_app.logger.info(dataAdded)

                        #Add filename to Global USER
                        USER["photos"].append(filename)
                        print(USER)

                        #Add photo filename data to realtime database, for reference later
                        db.child("users").child(userId).child("photos").push(filename)
                        current_app.logger.info(dataAdded)
                        """
                        # TODO:
                        #Update Facial Embeddings with new photo for user
                        print("Extract Start ------------------------------------")
                        
                        temp_all_users_dict = all_users()
                        # TODO: used to say extract_embeddings.create_embeddings(temp_all_users_dict, USER['FirstName'])
                        #  pretty sure I didnt need it so we could move the button functions  to welcome page
                        extract_embeddings.create_embeddings(temp_all_users_dict)
                        train_model.train()
                        """
                return redirect(request.url)
            elif request.form['button'] == 'logoutButton':
                #Logout Button
                return redirect(url_for('auth.logout'))
            elif request.form['button'] == 'backHomeButton':
                #Logout Button
                return redirect(url_for('general.home'))
    except KeyError:
        #No user logged in
        current_app.logger.info(userNotIn)
        return redirect(url_for('auth.login'))
    
    return render_template("upload_image.html")