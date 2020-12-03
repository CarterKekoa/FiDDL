#run with 'python app.py'   can view on 'localhost:5000'

import re
from flask import Flask, render_template, json, request, redirect, url_for, session, send_from_directory
from flask.globals import request
from jws import verify                                                  #import flask libries, render_template is so we can make front end
import pyrebase
from collections import OrderedDict
import os
import imghdr
from pyrebase.pyrebase import Storage                                    #for images
from werkzeug.utils import secure_filename                               #takes a file name and returns a secure version of it

app = Flask(__name__)                                                    #call flask constuctor from object #__name__ references this file

# Google Firebase ////////////////////////////////__________________________________________________
#initialize database
firebase = pyrebase.initialize_app(json.load(open('firebase/firebaseConfig.json')))
auth = firebase.auth()
db = firebase.database()                                    
#storageRef = firebase.storage.ref()                                #Points to the root reference
app.secret_key = os.urandom(24)                                     #random secret key to track if user is logged in
#storage = firebase.storage("gs://fiddl-dev.appspot.com")      # Get a reference to the storage service, which is used to create references in your storage bucket
storage = firebase.storage()

# Initialize USER as a global dictionary
USER = {
    "is_logged_in": False,
    "firstName": "",
    "lastName": "",
    "email": "",
    "uid": "",
    "photos": []
    }


# Functions ////////////////////////////////////////____________________________________________
#Check if image is allowed function
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

#Check image file size 
def allowed_image_filesize(file_size):
    if int(file_size) <= app.config["MAX_IMAGE_FILESIZE"]:
        return True
    else:
        return False

#User email is verified
def email_verified_check():
    return False


# Routes ////////////////////////////////////////____________________________________________
# Welcome Page
@app.route('/')                                                #@ is a decorator, flask uses this to define its urls, define url with a route
def welcome():
    return render_template('welcome.html')                       #must be in directory (folder) names templates, grabs file form there

# Registration Page
@app.route('/register', methods=['GET', 'POST'])
def register():
    #TODO: add user logged in check
    #Template Rendered
    render_template('register.html')

    # Alert Messages
    badEmail = 'There is already an account with this email address'
    goodEmail = 'Good email submitted'
    badPassMatch = 'Your passwords do not match. Please try again.'
    created = 'User account successfully created'
    loggedIn = 'New User logged in to account'
    dataAdded = 'New user data added to Firebase'
    registerFail = 'Failed to register user'
    userIn = 'User already logged in, rerouting.'
    registerSuccess = 'Full registration successful'

    # If data is Posted <form class="form-register" method="post"> in register.html
    if request.method == 'POST':
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        try:
            email = request.form['email']                           #grab user input email
            app.logger.info(goodEmail)
        except:
            app.logger.info(badEmail)
            redirect('register')                                #Email already exists, code 400
        
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
            # auth.send_email_verification(user['idToken'])           #send a user confirmation email
            verify = 'An email has been sent to' + email + ". Please verify your account before logging in."
            app.logger.info(verify)
            #TODO: make them verify before this happens, same in login

            #Log User In
            user = auth.sign_in_with_email_and_password(email, password)
            app.logger.info(loggedIn)

            #Add Data to Global USER
            global USER
            USER["is_logged_in"] = True
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
            db.child("users").child(USER["uid"]).push(data, user['idToken'])
            app.logger.info(dataAdded)

            #Go to Home Page for New User
            app.logger.info(registerSuccess)
            return redirect(url_for('home'))                   #Redirect routes
        except:
            app.logger.info(registerFail)
            return redirect(url_for('register'))
    else:
        if USER["is_logged_in"] == True:
            app.logger.info(userIn)
            return redirect(url_for('home'))
        else:
            app.logger.info(registerFail)
            redirect(url_for('register'))   
    return render_template('register.html')

#Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        print(session['usr'])           #simple test to see if a user is already logged in, if yes go to home page
        app.logger.info("A user is already logged in")
        #Template Rendered
        return redirect(url_for('home'))
    except KeyError:
        # Alert Messages
        unsuccesful = 'Your email or password was incorrect'
        succesful = 'Login Successful'
        loginData = 'Login user data added to Global'
        dataGrab = 'User data grabbed from Firebase'
        loginSuccess = ' logged in, moving to home screen'
        
        # If data is posted <form class="form-signin" action="/login" method="post">
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            #TODO: stay logged in button?
            try:
                #Log user in with input credentails
                user = auth.sign_in_with_email_and_password(email, password)
                app.logger.info(succesful)

                #TODO: verify if user has verified their account 
                

                #Update that a user is now logged in
                session['usr'] = user['idToken']
                app.logger.info(user['idToken'])
                app.logger.info("next")

                #Add Data to Global USER to get data
                global USER
                USER["is_logged_in"] = True
                USER["email"] = user["email"]
                USER["uid"] = user["localId"]
                app.logger.info(user["localId"])
                app.logger.info(loginData)
                #app.logger.info(USER["uid"])

                #Grab users name
                data = db.child("users").child(USER["uid"]).get().val()         #opens users in db, then finds person by  uid in db
                app.logger.info(dataGrab)
                app.logger.info(data)

                #Parse the returned OrderedDict of data
                for val in data.values():
                    for k,v in val.items():
                        app.logger.info("login k,v:" + k,v)
                        if k == 'firstName':
                            app.logger.info("login v")
                            name = v
                app.logger.info("User logged in: " + name)
                
                print(auth.current_user)

                #Move to Home screen
                app.logger.info(name + loginSuccess)
                return redirect(url_for('home'))
            except:
                app.logger.info('Login Failed: ' + unsuccesful)
                return redirect(url_for('login'))
        #else:
            #if USER["is_logged_in"] == True:
                #return redirect(url_for('home'))
            #else:
                #return redirect(url_for('login'))
    return render_template('login.html')

# Home Page
@app.route('/home', methods=["GET", "POST"])
def home():
    #TODO: YEEEESH
    try:
        print(session['usr'])
        app.logger.info("A user is already logged in")

        userId = auth.current_user['localId']               #auth.current_user is how we get the current users data

        #Grab users name
        data = db.child("users").child(USER["uid"]).child("photos").get().val()         #opens users in db, then finds person by  uid in db

        #Parse the returned OrderedDict for filenames of user photos
        #for val in data.values():
        #    print(val)
        #    storage.child("images/" + userId + "/" + val).download("images/" + userId + "/" + val, val)
        #TODO: print user photos to home screen
        

        if request.method == "POST":
            #Checks which buttons are clicked, url returned is in the form for the buttons
            if request.form['submit_button'] == 'addNewPhoto':
                redirect(url_for('upload_image'))
            elif request.form['submit_button'] == 'addNewPhoto':
                #TODO: make this my home portion
                render_template('/home')

            return render_template('home.html')

    except KeyError:
        app.logger.info("No user logged in, redirect to login")
        return redirect(url_for('login'))
    
    
    # How to update a existing data
    #db.child("users").child("Morty").update({"name": "Mortiest Morty"})

    # Removing existing data
    #db.child("users").child("Morty").remove()
    return render_template('home.html')



#temp image upload location
#TODO: put these in a private config file
app.config["IMAGE_UPLOAD"] = "photosTest"
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["PNG", "JPG", "JPEG"]
app.config["MAX_IMAGE_FILESIZE"] = 1.5 * 1024 * 1024    #1,572,864 Bytes or 1572.864 KB

# Upload Image
@app.route('/upload-image', methods=["GET", "POST"])
def upload_image():
    try:
        print(session['usr'])                   #this is equal to logged in users id token->  user['idToken']
        app.logger.info("A user is already logged in")
        #TODO: add a logout button, make sure to delete session for use on logout
        #user = session['usr']

        # Alert Messages
        noFileName = 'Image must have a file name.'
        badFileSize = 'Image file size is too large.'
        badFileName = 'That image extension or file name is not allowed'
        dataAdded = 'User photos added to Google Storage'

        
        if request.method == "POST":
            if request.files:
                image = request.files["image"]                        #works the same as user input emal in register, get the image file
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
                    
                    #Save photo to local directory, Testing only
                    #image.save(os.path.join(app.config["IMAGE_UPLOAD"], filename))  #save images to /photosTest for testing
                   
                    #Save user photo to Google Storage
                    storage.child("images/" + userId + "/" + filename).put(image, userIdToken)
                    app.logger.info(dataAdded)

                    
                    #Add filename to Global USER
                    global USER
                    USER["photos"].append(filename)
                    print(USER)

                    #Add photo filename data to realtime database, for reference later
                    db.child("users").child(userId).child("photos").push(filename)
                    app.logger.info(dataAdded)
                
                return redirect(request.url)
    except KeyError:
        app.logger.info("No user logged in, redirect to login")
        return redirect(url_for('login'))
    
    return render_template("upload_image.html")



#PRACTICE
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
    app.run(debug=True)         #dev mode, server updates on own, shows errors
