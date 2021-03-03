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
        current_app.logger.info("[LOGIN] The user: ", session['usr'], " is already logged in, redirecting home.")
        return redirect(url_for('users.home'))                        #Send to home page
    else:
        # Start Login Process
        current_app.logger.info("[LOGIN] No session['usr'] found (AKA No user currently logged in (Good since logging in): ")
        firebase, auth, db, storage, USER = initialize_data()

        registerScreen = 'Navigating to Register Screen Instead (Login - Good)'

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
                    current_app.logger.info("[ERROR - LOGIN] Error Occured: ", err)
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