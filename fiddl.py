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

from werkzeug.utils import secure_filename                               #takes a file name and returns a secure version of it
import subprocess
<<<<<<< HEAD
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



=======
import recognize
import extract_embeddings
import train_model
>>>>>>> 7f50cb52cd217e5e0c1e2e3d8df351cb3bcf5805

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

#if running from command line, turn on dev mode
if not os.environ.get('SECRET_KEY') is None:
    app.secret_key = os.environ["SECRET_KEY"]                  # To get Heroku Envrionment Variable
app.permanent_session_lifetime = timedelta(hours=2)            # how long permanent session will last, hours,min,days

homeOwners = ["kevin", "carter"]


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

<<<<<<< HEAD
if __name__ == "__main__":      
    print("__main__")
    app.secret_key = os.urandom(24)                                # random secret key to track if user is logged in
=======
ALL = {
    "all_images": []
}

# Functions ////////////////////////////////////////____________________________________________
# Check if image is allowed function
def allow_image(filename):
    #check for dot in file name
    if not "." in filename:
        return False
    
    ext = filename.rsplit(".", 1)[1]

    #convert type to upper case
    if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return True
    else:
        return False

# Check image file size 
def allowed_image_filesize(file_size):
    if int(file_size) <= app.config["MAX_IMAGE_FILESIZE"]:
        return True
    else:
        return False

# User email is verified
def email_verified_check():
    return False

# Create a list of all photo URLs
def all_photo_grab():
    print("All Photos Start---------------------------------------")
    print("storage: " + str(storage))
    # TODO:
    #ref = storage.child("images").child("65TP5SoqLCOGc8FyHAgeDHSoO422").listAll()
    #print("ref: " + str(ref))
    #for file in files:
    #    print("child: " + str(storage.child(file.name).get_url(None)))
    #images = []                                                                     #image url storage list
    #data = db.child("users").child(USER["uid"]).child("photos").get().val()         #opens users in db, then finds person by  uid in db
    # data has the id of each photo paired with the actual photo file name
    # Parse the returned OrderedDict for filenames of user photos
    #for val in data.values():
        #print("val: " + str(val))               # val = file names of photos stored (from database aka dictionary)
        #storage.child("images/" + userId + "/" + val).download(val, val)           # dowloads image to local folder, testing only
     #   imageURL = storage.child("images/" + userId + "/" + val).get_url(None)      # URL for Google Storage Photo location
        #print("imageURL: " + str(imageURL))
    #    images.append(imageURL)                 # Stores the URL of each photo for the user
    #USER["image_locations"] = images            # Stores the users URL list in Global variable. TODO: Make sure to delete this when session ends
    #print(str(USER["image_locations"]))
    print("All Photos End---------------------------------------")



# Routes ////////////////////////////////////////____________________________________________
# Welcome Page ---------------------------------
@app.route('/', methods=['GET', 'POST'])                                                #@ is a decorator, flask uses this to define its urls, define url with a route
def welcome():
    #Check if screen buttons are clicked
    if request.method == "POST":
        if request.form['button'] == 'loginScreen':
            redirect(url_for('/login'))
        elif request.form['button'] == 'registerScreen':
            redirect(url_for('/register'))
    all_photo_grab()
    return render_template('welcome.html')                       #must be in directory (folder) names templates, grabs file form there


# Registration Page ---------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        #Check if a user is already logged in
        print(session['usr'])                                    #simple test to see if a user is already logged in, if yes go to home page
        app.logger.info("A user is already logged in")
        return redirect(url_for('home'))                         #Send to home page if user is logged in
    except KeyError:
        render_template('register.html')

        # Alert Messages
        badEmail = 'There is already an account with this email address (Register - Bad)'
        goodEmail = 'Good email submitted (Register - Good)'
        badPassMatch = 'Your passwords do not match. Please try again. (Register - Bad)'
        created = 'User account successfully created (Register - Good)'
        loggedIn = 'New User logged in to account (Register - Good)'
        dataAdded = 'New user data added to Firebase (Register - Good)'
        registerFail = 'Failed to register user (Register - Bad)'
        userIn = 'User already logged in, rerouting. (Register - Good)'
        registerSuccess = 'Full registration successful (Register - Good)'
        loginPage = "Navigating to Login Page Instead (Register - Good)"
    
        # Check if Buttons are clicked
        if request.method == 'POST':
            if request.form['button'] == 'register':
                #Register button clicked
                firstName = request.form['firstName']
                lastName = request.form['lastName']
                #Valid email checks
                try:
                    email = request.form['email']                           #grab user input email
                    app.logger.info(goodEmail)
                except:
                    app.logger.info(badEmail)
                    redirect('register')                                    #Email already exists, code 400
                
                #Valid Password checks
                password = request.form['password']
                passwordCheck = request.form['passwordConfirm']             #Confirm Password
                if password != passwordCheck:
                    app.logger.info(badPassMatch)
                    return redirect('register')

                try:
                    #Create User
                    auth.create_user_with_email_and_password(email, password)           #this automatically hashes the password!
                    app.logger.info(created)

                    #Verify User Email
                    # auth.send_email_verification(user['idToken'])                     #send a user confirmation email
                    verify = 'An email has been sent to' + email + ". Please verify your account before logging in."
                    app.logger.info(verify)
                    #TODO: make them verify before this happens, same in login

                    #Log User In
                    user = auth.sign_in_with_email_and_password(email, password)
                    app.logger.info(loggedIn)

                    #Session pdate that a user is now logged in
                    session['usr'] = user['idToken']
                    print(session)
                    print(session['usr'])

                    #Add Data to Global USER - For RTDB 
                    global USER
                    USER["firstName"] = firstName
                    USER["lastName"] = lastName
                    USER["email"] = user["email"]
                    USER["uid"] = user["localId"]
                    
                    #Add data to realtime database
                    data = {
                        "firstName": firstName,
                        "lastName": lastName,
                        "email": email
                    }
                    db.child("users").child(USER["uid"]).push(data, user['idToken'])        #Push user data to RTDB
                    app.logger.info(dataAdded)

                    #Go to Home Page for New User
                    app.logger.info(registerSuccess)
                    return redirect(url_for('home'))                                        #Redirect routes
                except:
                    #Registration Fail
                    app.logger.info(registerFail)
                    return redirect(url_for('register'))
            elif request.form['button'] == 'loginScreen':
                #Switch to login screen
                app.logger.info(loginPage)
                return redirect(url_for('login'))
            else:
                return render_template('register.html')
        elif request.method == 'GET':
            return render_template('register.html')
  
    return render_template('register.html')


#Login Page ---------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    #Alert Messages
    loginStart = "Login Process initial check began (Login - Good)"

    app.logger.info(loginStart)
    try:
        #User already logged in check
        print(session['usr'])                                   #simple test to see if a user is already logged in, if yes go to home page
        app.logger.info("A user is already logged in")
        return redirect(url_for('home'))                        #Send to home page
    except KeyError:
        # Alert Messages
        unsuccesful = 'Your email or password was incorrect (Login - Bad)'
        succesful = 'Login Successful (Login - Good)'
        loginData = 'Login user data added to Global (Login - Good)'
        dataGrab = 'User data grabbed from Firebase (Login - Good)'
        loginSuccess = ' logged in, moving to home screen (Login - Good)'
        registerScreen = 'Navigating to Register Screen Instead (Login - Good)'
        loginBegan = "Login checks started (Login - Good)"
        sessionStarted = "Loged in user session started (Login - Good)"
        
        app.logger.info(loginBegan)

        #Check if button is pressed
        if request.method == 'POST':
            #Check which button
            if request.form['button'] == 'login': 
                #Login Button Pressed
                email = request.form['email']
                password = request.form['password']
                #TODO: stay logged in button?
                try:
                    #Log user in with input credentails
                    user = auth.sign_in_with_email_and_password(email, password)
                    app.logger.info(succesful)

                    #TODO: verify if user has verified their email 
                    
                    #Update session that a user is now logged in
                    session['usr'] = user['idToken']
                    app.logger.info(sessionStarted)

                    #Add Data to Global USER to get data
                    global USER
                    USER["is_logged_in"] = True
                    USER["email"] = user["email"]
                    USER["uid"] = user["localId"]
                    app.logger.info(loginData)

                    #Grab users name
                    data = db.child("users").child(USER["uid"]).get().val()         #opens users in db, then finds person by  uid in db
                    app.logger.info(dataGrab)

                    #Parse the returned OrderedDict of data
                    for val in data.values():
                        #Grab logining in users name from database. Not necessary here
                        for k,v in val.items():
                            app.logger.info("login k,v:" + k,v)
                            if k == 'firstName':
                                app.logger.info("login v")
                                name = v
                    app.logger.info("User logged in: " + name)

                    #Send user to Home screen
                    app.logger.info(name + loginSuccess)
                    return redirect(url_for('home'))
                except:
                    #Login Fail
                    app.logger.info('Login Failed: ' + unsuccesful)
                    return redirect(url_for('login'))
            elif request.form['button'] == 'registerScreen':
                #Switch to Register Screen
                app.logger.info(registerScreen)
                return redirect(url_for('register'))

        elif request.method == 'GET':
            return render_template('login.html') 
            
    return render_template('login.html')


#Logout request ---------------------------------
@app.route('/logout', methods=['GET', 'POST'])   
def logout():
    #Alert Messages - Dev
    loggedOut = "User successfully logged out"
    loggoutFail = "Failed to log user out"

    #User Flash Alerts
    logoutSuccess = "You have been succesfully logged out"
    
    try:
        #Logout User
        auth.current_user = None                        #Logout from firebase Auth
        session.clear()                                 #Clear User Session
        app.logger.info(loggedOut)
        flash(logoutSuccess, "info")                    #"info" is the type of message for more customization if we want, others are warning, info, error
    except KeyError:
        app.logger.info(loggoutFail)
    return redirect(url_for('login'))


# Home Page ---------------------------------
@app.route('/home', methods=["GET", "POST"])
def home():
    #Alert Messages
    userLogedIn = "User is still logged in (Home - Good)."
    userNotIn = "No user logged in (Home - Bad)."
    noPhoDisplay = "User has no photos to display"

    try:
        #Check if user is logged in
        print(session['usr'])
        app.logger.info(userLogedIn)

        userId = auth.current_user['localId']               #auth.current_user is how we get the current users data

        #Grab users name
        user = db.child("users").child(USER["uid"]).get().val()
        #Parse the returned OrderedDict of data
        for val in user.values():
            #Grab logining in users name from database. Not necessary here
            for k,v in val.items():
                print(k,v)
                if k == 'firstName':
                    name = v
                    USER["firstName"] = name
                    print(name)
        

        try:
            # Prints stored user photos to users home screen
            print("Display Photos Start---------------------------------------")
            images = []                                                                     #image url storage list
            data = db.child("users").child(USER["uid"]).child("photos").get().val()         #opens users in db, then finds person by  uid in db
            # data has the id of each photo paired with the actual photo file name
            # Parse the returned OrderedDict for filenames of user photos
            for val in data.values():
                #print("val: " + str(val))               # val = file names of photos stored (from database aka dictionary)
                #storage.child("images/" + userId + "/" + val).download(val, val)           # dowloads image to local folder, testing only
                imageURL = storage.child("images/" + userId + "/" + val).get_url(None)      # URL for Google Storage Photo location
                #print("imageURL: " + str(imageURL))
                images.append(imageURL)                 # Stores the URL of each photo for the user
            USER["image_locations"] = images            # Stores the users URL list in Global variable. TODO: Make sure to delete this when session ends
            #print(str(USER["image_locations"]))
            print("Display Photos End---------------------------------------")
            return render_template('home.html', firstName=name, images=images)
        except:
            render_template('home.html', firstName=name)
        
        if request.method == "POST":
            #Check if button is clicked
            if request.form['button'] == 'addNewPhoto':
                #Add new photo button
                return redirect(url_for('upload_image'))
            elif request.form['button'] == 'updateMyHome':
                #TODO: make this my home portion
                render_template('/home')
            elif request.form['button'] == 'logoutButton':
                #Logout Button
                return redirect(url_for('logout'))
            elif request.form['button'] == 'analyzePhoto':
                #facial_rec = FacialRec()
                #facial_rec.images = images
                #print(facial_rec.images)
                #TODO:
                print("TODO")
            return render_template('home.html')

        if request.method == "GET":
            render_template('home.html')

    except KeyError:
        app.logger.info(userNotIn)
        return redirect(url_for('login'))
    
    return render_template('home.html')


# Upload Image ---------------------------------
#temp image upload location
#TODO: put these in a private config file
app.config["IMAGE_UPLOAD"] = "photosTest"
app.config["IMAGE_ANALYZE_UPLOAD"] = "photosTest/analyzePhotos"
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["PNG", "JPG", "JPEG"]
app.config["MAX_IMAGE_FILESIZE"] = 4 * 1024 * 1024    #1,572,864 Bytes or 1572.864 KB

# Upload Image ---------------------------------
@app.route('/upload-image', methods=["GET", "POST"])
def upload_image():
    # Alert Messages
    userLogedIn = "User is still logged in (PhotoUpload - Good)."
    userNotIn = "No user logged in (PhotoUpload - Bad)."

    try:
        print(session['usr'])                   #this is equal to logged in users id token->  user['idToken']
        app.logger.info(userLogedIn)
        #TODO: add a logout button, make sure to delete session for use on logout
        #user = session['usr']

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
                    app.logger.info(badFileSize)
                    return redirect(request.url)
                
                #Check for file name
                if image.filename == "":
                    app.logger.info(noFileName)
                    return redirect(request.url)
                
                #Check if image has correct type
                if not allow_image(image.filename):
                    app.logger.info(badFileName)
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

                    image.seek(0)                               #NEED THIS! We point to the end of the file above to find the size, this causes a empty file to upload without this fix
                    
                    #Check if to run FR or Store photo
                    if request.form.get('analyzer') == 'analyze':
                        #Analyze Check box checked. Run FR on uploaded image then
                        image.save(os.path.join(app.config["IMAGE_ANALYZE_UPLOAD"], filename))          #Saves analyzed photo to photosTest/analyzePhotos to be used by FR
                        analyzeInfo = recognize.facialRecognition("photosTest/analyzePhotos/" + filename)
                        print(analyzeInfo)
                        
                        if analyzeInfo[0] in homeOwners:
                            nameDetermined = "Approved Person"
                        else:
                            nameDetermined = "Unapproved Person"
                        proba = analyzeInfo[1]

                        # TODO: Shawns Code is called here
                        if nameDetermined == USER["firstName"]:
                            # TODO: Tell lock to unlock for correct user
                            print(nameDetermined + " " + USER["firstName"])
                            
                        return render_template("upload_image.html", name=nameDetermined, proba=proba)
                    else:
                        #Images being uploaded to db instead
                        #Save photo to local directory, Testing only
                        #image.save(os.path.join(app.config["IMAGE_UPLOAD"], filename))  #save images to /photosTest for testing
                    
                        #Save user photo to Google Storage
                        storage.child("images/" + userId + "/" + filename).put(image, userIdToken)
                        app.logger.info(dataAdded)

                        #Add filename to Global USER
                        USER["photos"].append(filename)
                        print(USER)

                        #Add photo filename data to realtime database, for reference later
                        db.child("users").child(userId).child("photos").push(filename)
                        app.logger.info(dataAdded)

                        # TODO:
                        #Update Facial Embeddings with new photo for user
                        print("Extract Start ------------------------------------")
                        #extract_embeddings.create_embeddings(USER["image_locations"], USER["firstName"])
                        train_model.train()

                return redirect(request.url)
            elif request.form['button'] == 'logoutButton':
                #Logout Button
                return redirect(url_for('logout'))
            elif request.form['button'] == 'backHomeButton':
                #Logout Button
                return redirect(url_for('home'))
    except KeyError:
        #No user logged in
        app.logger.info(userNotIn)
        return redirect(url_for('login'))
    
    return render_template("upload_image.html")



#PRACTICE ---------------------------------
@app.route('/api/userinfo')
def userinfo():
    return {'data': users1}, 200

@app.route('/posts')
def posts():
    return render_template('posts.html', posts=all_posts)        # defined the variable posts, this is the one we can now use in html file

@app.route('/home/users/<string:name>/posts/<int:id>')         #this runs the same function below, but now with url 'localhost:5000/home', so both pages show this now
def hello(name, id):                                           #this code runs when we get to the above url, now 'name' references '<string:name>' so we can grab what is in the url there
    return "Hello, " + name + " your id is: " + str(id)

@app.route('/onlyget', methods=['GET', 'POST'])                #only allows get requests and posts, can specify which methods we want to do that using methods=...
def get_req():
    return 'You can only get this webpage.'



if __name__ == "__main__":      #if running from command line, turn on dev mode
>>>>>>> 7f50cb52cd217e5e0c1e2e3d8df351cb3bcf5805
    app.run(debug=True)         #dev mode, server updates on own, shows errors
