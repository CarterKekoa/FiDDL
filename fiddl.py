#run with 'python app.py'   can view on 'localhost:5000'

from flask import Flask, render_template, json, redirect, url_for
from flask.globals import request
from jws import verify     #import flask libries, render_template is so we can make front end
import pyrebase
from collections import OrderedDict

app = Flask(__name__)                        #call flask constuctor from object #__name__ references this file

# Google Firebase ////////////////////////////////__________________________________________________
#initialize database
firebase = pyrebase.initialize_app(json.load(open('firebase/firebaseConfig.json')))
auth = firebase.auth()
db = firebase.database()

# Initialize USER as a global dictionary
USER = {
    "is_logged_in": False,
    "firstName": "",
    "lastName": "",
    "email": "",
    "uid": ""
    }


#Dummy Data to set up Google auth
users1 = [{'uid': 1, 'name': 'Carter Mooring'}]

#pushing dummy data to firebase
# db.child("posts").push(all_posts)
# db.child("posts").update(all_posts)
# db.child("posts").remove()


# Routes ////////////////////////////////////////____________________________________________
# Welcome Page
@app.route('/')                                                #@ is a decorator, flask uses this to define its urls, define url with a route
def welcome():
    return render_template('welcome.html')                       #must be in directory (folder) names templates, grabs file form there

# Registration Page
@app.route('/register', methods=['GET', 'POST'])
def register():
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
            auth.create_user_with_email_and_password(email, password)
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
            #auth.get_account_info(user['idToken'])             #get user idToken, not sure if we need this  yet
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
    #Template Rendered
    render_template('login.html')
    
    # Alert Messages
    unsuccesful = 'Your email or password was incorrect'
    succesful = 'Login Successful'
    loginData = 'Login user data added to Global'
    dataGrab = 'User data grabbed from Firebase'
    loginSuccess = ' logged in, moving to home screen'
    
    # If data is posted <form class="form-signin" action="/login" method="post">
    if request.method == 'POST':
        email = request.form['email']
        #TODO: verify if user has verified their account 
        password = request.form['password']
        #TODO: stay logged in button?
        try:
            #Log user in with input credentails
            user = auth.sign_in_with_email_and_password(email, password)
            app.logger.info(succesful)

            #Add Data to Global USER
            global USER
            USER["is_logged_in"] = True
            USER["email"] = user["email"]
            USER["uid"] = user["localId"]
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
@app.route('/home')
def home():
    #TODO: YEEEESH
    
    return render_template('home.html')

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
