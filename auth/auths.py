from flask import Blueprint, render_template, session, current_app, request, redirect, url_for, flash

authsBP = Blueprint("auth", __name__, static_folder="static", template_folder="templates")

    
def initialize_data():
    firebase = current_app.config['firebase']
    auth = current_app.config['auth']
    db = current_app.config['db']
    storage = current_app.config['storage']
    USER = current_app.config['USER']
    return firebase, auth, db, storage, USER

# User email is verified
def email_verified_check():
    return False

#Login Page ---------------------------------
@authsBP.route('/login', methods=['GET', 'POST'])
def login():
    #Alert Messages
    loginStart = "Login Process initial check began (Login - Good)"
    current_app.logger.info(loginStart)
    try:
        #User already logged in check
        print(session['usr'])                                   #simple test to see if a user is already logged in, if yes go to home page
        current_app.logger.info("A user is already logged in")
        return redirect(url_for('users.home'))                        #Send to home page
    except KeyError:
        firebase, auth, db, storage, USER = initialize_data()
        # Alert Messages
        unsuccesful = 'Your email or password was incorrect (Login - Bad)'
        succesful = 'Login Successful (Login - Good)'
        loginData = 'Login user data added to Global (Login - Good)'
        dataGrab = 'User data grabbed from Firebase (Login - Good)'
        loginSuccess = ' logged in, moving to home screen (Login - Good)'
        registerScreen = 'Navigating to Register Screen Instead (Login - Good)'
        loginBegan = "Login checks started (Login - Good)"
        sessionStarted = "Loged in user session started (Login - Good)"
        
        current_app.logger.info(loginBegan)

        #Check if button is pressed
        if request.method == 'POST':
            #Check which button
            if request.form['button'] == 'login': 
                #Login Button Pressed
                email = request.form['email']
                password = request.form['password']
                print(email, password)
                #TODO: stay logged in button?
                try:
                    #Log user in with input credentails
                    user = auth.sign_in_with_email_and_password(email, password)
                    current_app.logger.info(succesful)
                    #TODO: verify if user has verified their email 
                    
                    for val in user:
                        print("val:", val)

                    print("kind:", user['kind'])
                    print("localId:", user['localId'])
                    print("email:", user['email'])
                    print("displayName:", user['displayName'])
                    print("idToken:", user['idToken'])
                    print("registered:", user['registered'])
                    print("refreshToken:", user['refreshToken'])
                    print("expiresIn:", user['expiresIn'])

                    #Update session that a user is now logged in
                    session.permanent = True
                    session['usr'] = user['idToken']
                    session['localId'] = user['localId']
                    current_app.logger.info(sessionStarted)

                    #Add Data to Global USER to get data
                    USER["email"] = user["email"]
                    USER["uid"] = user["localId"]
                    current_app.logger.info(loginData)

                    #Grab users name
                    data = db.child("users").child(USER["uid"]).get().val()         #opens users in db, then finds person by  uid in db
                    current_app.logger.info(dataGrab)

                    #Parse the returned OrderedDict of data
                    for val in data.values():
                        #Grab logining in users name from database. Not necessary here
                        for k,v in val.items():
                            current_app.logger.info("login k,v:" + k,v)
                            if k == 'firstName':
                                current_app.logger.info("login v")
                                name = v
                    current_app.logger.info("User logged in: " + name)

                    #Send user to Home screen
                    current_app.logger.info(name + loginSuccess)
                    return redirect(url_for('users.home'))
                except:
                    #Login Fail
                    # TODO: output error message instead
                    current_app.logger.info('Login Failed: ' + unsuccesful)
                    return redirect(url_for('auth.login'))
            elif request.form['button'] == 'registerScreen':
                #Switch to Register Screen
                current_app.logger.info(registerScreen)
                return redirect(url_for('auth.register'))
        elif request.method == 'GET':
            return render_template('login.html') 
    
    return render_template('login.html')

# Registration Page ---------------------------------
@authsBP.route('/register', methods=['GET', 'POST'])
def register():
    try:
        #Check if a user is already logged in
        print(session['usr'])                                    #simple test to see if a user is already logged in, if yes go to home page
        current_app.logger.info("A user is already logged in")
        return redirect(url_for('users.home'))                         #Send to home page if user is logged in
    except KeyError:
        firebase, auth, db, storage, USER = initialize_data()
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
                    current_app.logger.info(goodEmail)
                except:
                    current_app.logger.info(badEmail)
                    redirect('register')                                    #Email already exists, code 400
                
                #Valid Password checks
                password = request.form['password']
                passwordCheck = request.form['passwordConfirm']             #Confirm Password
                if password != passwordCheck:
                    current_app.logger.info(badPassMatch)
                    return redirect('register')

                try:
                    #Create User
                    auth.create_user_with_email_and_password(email, password)           #this automatically hashes the password!
                    current_app.logger.info(created)

                    #Verify User Email
                    # auth.send_email_verification(user['idToken'])                     #send a user confirmation email
                    verify = 'An email has been sent to' + email + ". Please verify your account before logging in."
                    current_app.logger.info(verify)
                    #TODO: make them verify before this happens, same in login

                    #Log User In
                    user = auth.sign_in_with_email_and_password(email, password)
                    current_app.logger.info(loggedIn)

                    #Session pdate that a user is now logged in
                    session.permanent = True                        # This user session will last for 2 hours or until logged out
                    session['usr'] = user['idToken']
                    print(session)
                    print(session['usr'])

                    #Add Data to Global USER - For RTDB 
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
                    current_app.logger.info(dataAdded)

                    #Go to Home Page for New User
                    current_app.logger.info(registerSuccess)
                    return redirect(url_for('users.home'))                                        #Redirect routes
                except:
                    #Registration Fail
                    current_app.logger.info(registerFail)
                    return redirect(url_for('auth.register'))
            elif request.form['button'] == 'loginScreen':
                #Switch to login screen
                current_app.logger.info(loginPage)
                return redirect(url_for('auth.login'))
            else:
                return render_template('register.html')
        elif request.method == 'GET':
            return render_template('register.html')
  
    return render_template('register.html')

#Logout request ---------------------------------
@authsBP.route('/logout', methods=['GET', 'POST'])   
def logout():
    #Alert Messages - Dev
    loggedOut = "User successfully logged out"
    loggoutFail = "Failed to log user out"

    #User Flash Alerts
    logoutSuccess = "You have been succesfully logged out"
    
    try:
        firebase, auth, db, storage, USER = initialize_data()
        #Logout User
        auth.current_user = None                        #Logout from firebase Auth
        session.permanent = False 
        session.clear()                                 #Clear User Session
        current_app.logger.info(loggedOut)
        flash(logoutSuccess, "info")                    #"info" is the type of message for more customization if we want, others are warning, info, error
    except KeyError:
        current_app.logger.info(loggoutFail)
    return redirect(url_for('auth.login'))