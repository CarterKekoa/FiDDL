from flask import Blueprint, render_template, session, current_app, request, redirect, url_for, flash

authsBP = Blueprint("auth", __name__, static_folder="static", template_folder="templates")

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

# User email is verified
def email_verified_check():
    return False

#Login Page ---------------------------------------------------------------------------------------------------
@authsBP.route('/login', methods=['GET', 'POST'])
def login():
    current_app.logger.info("[LOGIN]")
    # Check if a user is already logged in
    if not session.get('usr') is None:
        current_app.logger.warning("[LOGIN] A user is already logged in, redirecting moving to [HOME]----------------------------------------------------------------------------------")
        print(bcolors.WARNING, "                             Loged in user: ", session['localId'], bcolors.ENDC)
        return redirect(url_for('users.home'))                        #Send to home page
    else:
        # Start Login Process
        current_app.logger.info("[LOGIN] No session['usr'] found (AKA No user currently logged in (Good since logging in): ")
        firebase, auth, db, storage, USER = initialize_data()

        print()
        current_app.logger.info("[LOGIN] Login Process Started----------------------------------------------------------------------------------")
        
        #Check if HTML button is pressed
        if request.method == 'POST':
            if request.form['button'] == 'login': 
                #Login Button Pressed
                email = request.form['email']
                password = request.form['password']
                print(bcolors.OKBLUE, "                             Entered Email: ", email, " Pass: ", password, bcolors.ENDC)
                #TODO: stay logged in button?
                try:
                    current_app.logger.info("[LOGIN] Google Authentication Started")
                    #Log user in with input credentails
                    user = auth.sign_in_with_email_and_password(email, password)
                    current_app.logger.info("[LOGIN] Google Authentication Success, storing user info")
                    #TODO: verify if user has verified their email 
                    # Prints to see what is returned from Google auth
                    """
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
                    """

                    #Update session that a user is now logged in
                    session.permanent = True
                    session['usr'] = user['idToken']        # stores the users long Id number
                    session['localId'] = user['localId']    # stores the users short Id (This is what their data/photos are stored under)
                    session['email'] = user["email"]        # stores the users email
                    current_app.logger.info("[LOGIN] Session Started with user info stored")
                    print(bcolors.OKBLUE, "                             Logged in User localId: ", session['localId'], bcolors.ENDC)

                    #Grab users name
                    current_app.logger.info("[LOGIN] Google User Data Grab Started")
                    data = db.child("users").child(session['localId']).get().val()         #opens users in db, then finds person by  uid in db
                    good_data = False

                    #Parse the returned OrderedDict of data
                    for val in data.values():
                        #Grab logining in users name from database. Not necessary here
                        for k,v in val.items():
                            print(bcolors.OKBLUE, "                             Users Google Data: key: ", k, " value: ", v, bcolors.ENDC)
                            session[k] = v
                            if k == 'firstName':
                                good_data = True
                        if good_data:
                            current_app.logger.info("[LOGIN] Google User Data Grab Success")
                        else:
                            print(bcolors.WARNING, "                             [ERROR Described Below]", bcolors.ENDC)
                            current_app.logger.info("[ERROR - LOGIN] Google User Data Grab Fail, check user: ", session['localId'], " database for more info")
                            return redirect(url_for('auth.login'))
                    current_app.logger.info("[LOGIN] Login Process Ended, Moving to [HOME]----------------------------------------------------------------------------------")
                    return redirect(url_for('users.home'))
                except Exception as err:
                    #Login Fail
                    print(bcolors.FAIL, "                             [ERROR Described Below]", bcolors.ENDC)
                    current_app.logger.info("[ERROR - LOGIN] Error Occured: ")
                    print(bcolors.FAIL, "                             ", err, bcolors.ENDC)
                    current_app.logger.info("[LOGIN] Login Process Ended, restarting [LOGIN]----------------------------------------------------------------------------------")
                    return redirect(url_for('auth.login'))
            elif request.form['button'] == 'registerScreen':
                #Switch to Register Screen
                current_app.logger.info("[LOGIN] Switching to Register Screen")
                current_app.logger.info("[LOGIN] Login Process Ended, moving to [REGISTER]----------------------------------------------------------------------------------")
                return redirect(url_for('auth.register'))
        elif request.method == 'GET':
            return render_template('login.html') 
    return render_template('login.html')
# End of Login Route ---------------------------------------------------------------------------------------------------

# Registration Page ---------------------------------------------------------------------------------------------------
@authsBP.route('/register', methods=['GET', 'POST'])
def register():
    current_app.logger.info("[REGISTER]")
    # Check if a user is already logged in
    if not session.get('usr') is None:
        current_app.logger.warning("[REGISTER] A user is already logged in, redirecting moving to [HOME]----------------------------------------------------------------------------------")
        print(bcolors.WARNING, "                             Loged in user: ", session['localId'], bcolors.ENDC)
        return redirect(url_for('users.home'))                        #Send to home page
    else:
        # Start Login Process
        current_app.logger.info("[REGISTER] No session['usr'] found (AKA No user currently logged in (Good since registering): ")
        firebase, auth, db, storage, USER = initialize_data()

        print()
        current_app.logger.info("[REGISTER] Registration Process Started----------------------------------------------------------------------------------")
    
        # Check if Buttons are clicked
        if request.method == 'POST':
            if request.form['button'] == 'register':
                try:
                    # Register button clicked
                    firstName = request.form['firstName']
                    lastName = request.form['lastName']
                    # Valid email checks
                    email = request.form['email']                           #grab user input email
                    #Valid Password checks
                    password = request.form['password']
                    passwordCheck = request.form['passwordConfirm']             #Confirm Password

                    if password != passwordCheck:
                        current_app.logger.warning("[REGISTER] Passwords did not match, restating [REGISTER]")
                        noPasswordMatch = "Your Passwords did not match. Please try again."
                        flash(noPasswordMatch, "info")                    #"info" is the type of message for more customization if we want, others are warning, info, error
                        return redirect('auth.register')
                except Exception as err:
                    # Register Fail
                    print(bcolors.FAIL, "                             [ERROR Described Below]", bcolors.ENDC)
                    current_app.logger.warning("[ERROR - REGISTER] Error Occured: ")
                    print(bcolors.FAIL, "                             ", err, bcolors.ENDC)
                    current_app.logger.warning("[REGISTER] Register Process Ended, restarting [REGISTER]----------------------------------------------------------------------------------")
                    fieldsNotFilled = "Issue when trying to grab your entered information. Please make sure to fill in all the fields."
                    flash(fieldsNotFilled, "info")                    #"info" is the type of message for more customization if we want, others are warning, info, error
                    return redirect(url_for('auth.register'))
                
                print(bcolors.OKBLUE, "                             Entered Email: ", email, " Pass: ", password, bcolors.ENDC)
                print(bcolors.OKBLUE, "                             Entered firstName: ", firstName, " lastName: ", lastName, bcolors.ENDC)
                current_app.logger.info("[REGISTER] User register information grabed.")

                # Registe the user in Google Firebase
                try:
                    # Create User in Firebase
                    auth.create_user_with_email_and_password(email, password)           #this automatically hashes the password!
                    current_app.logger.info("[REGISTER] User email and password registered in Google Firebase")

                    # TODO: Verify User Email, make them verify before this happens, same in login
                    #auth.send_email_verification(user['idToken'])                     #send a user confirmation email
                    #verify = 'An email has been sent to' + email + ". Please verify your account before logging in."
                    #current_app.logger.info(verify)
                   
                    # Log User In
                    user = auth.sign_in_with_email_and_password(email, password)
                    current_app.logger.info("[REGISTER] Google Authentication Success, storing user info")

                    # Update session that a user is now logged in
                    session.permanent = True
                    session['usr'] = user['idToken']        # stores the users long Id number
                    session['localId'] = user['localId']    # stores the users short Id (This is what their data/photos are stored under)
                    session['email'] = user["email"]        # stores the users email
                    session['firstName'] = firstName
                    session['lastName'] = lastName
                    current_app.logger.info("[REGISTER] Session Started with user info stored")
                    print(bcolors.OKBLUE, "                             Logged in User localId: ", session['localId'], bcolors.ENDC)
                    
                    #Add data to realtime database
                    data = {
                        "firstName": firstName,
                        "lastName": lastName,
                        "email": email
                    }
                    # TODO: Potentially change this and isntead of pushing in an object, push each individually?
                    db.child("users").child(session['localId']).push(data, session['usr'])        #Push user data to RTDB
                    current_app.logger.info("[REGISTER] User register info stored in firebase")

                    # Go to Home Page for New User
                    current_app.logger.info("[REGISTER] Registration Process Ended Successfully, Moving to [HOME]----------------------------------------------------------------------------------")
                    return redirect(url_for('users.home'))                                        #Redirect routes
                except Exception as err:
                    # Register Fail
                    print(bcolors.FAIL, "                             [ERROR Described Below]", bcolors.ENDC)
                    current_app.logger.warning("[ERROR - REGISTER] Error Occured: ")
                    print(bcolors.FAIL, "                             ", err, bcolors.ENDC)
                    current_app.logger.warning("[REGISTER] Registration Process Ended on fail, restarting [REGISTER]----------------------------------------------------------------------------------")
                    return redirect(url_for('auth.register'))
            elif request.form['button'] == 'loginScreen':
                #Switch to Login Screen
                current_app.logger.info("[REGISTER] Switching to Login Screen")
                current_app.logger.info("[REGISTER] Registration Process Ended on switch, moving to [LOGIN]----------------------------------------------------------------------------------")
                return redirect(url_for('auth.login'))
        elif request.method == 'GET':
            return render_template('register.html')
    return render_template('register.html')
# End of Registration Route ---------------------------------------------------------------------------------------------------

#Logout request ---------------------------------
@authsBP.route('/logout', methods=['GET', 'POST'])   
def logout():
    current_app.logger.info("[LOGOUT]")
    # Check if a user is already logged in
    if not session.get('usr') is None:
        current_app.logger.info("[LOGOUT] A user is logged in, good since logging out")
        print(bcolors.WARNING, "                             Loged in user: ", session['localId'], bcolors.ENDC)
        try:
            firebase, auth, db, storage, USER = initialize_data()
            #Logout User
            auth.current_user = None                        #Logout from firebase Auth
            session.permanent = False 
            session.clear()                                 #Clear User Session
            current_app.logger.info("[LOGOUT] Google auth the session closed succesfully.")
            logoutSuccess = "You have been succesfully logged out."
            flash(logoutSuccess, "info")                    #"info" is the type of message for more customization if we want, others are warning, info, error
        except Exception as err:
                    # Register Fail
                    print(bcolors.FAIL, "                             [ERROR Described Below]", bcolors.ENDC)
                    current_app.logger.warning("[ERROR - LOGOUT] Error Occured: ")
                    print(bcolors.FAIL, "                             ", err, bcolors.ENDC)
                    current_app.logger.warning("[LOGOUT] Logout Process Ended on fail, restarting at [LOGIN]----------------------------------------------------------------------------------")
    else:
        current_app.logger.info("[LOGOUT] No user logged in, logout impossible.")
    return redirect(url_for('auth.login'))