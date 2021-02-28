from flask import Blueprint, render_template, session, current_app, request, redirect, url_for, flash
import os       # Used when getting the uploaded image
from werkzeug.utils import secure_filename       #takes a file name and returns a secure version of it, for saving new photo file name

# Facial Recognition File Imports
import FacialRecognition.recognize as recognize
import FacialRecognition.extract_embeddings as extract_embeddings
import FacialRecognition.train_model as train_model

userBP = Blueprint("users", __name__, static_folder="static", template_folder="templates")


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
        return True
    else:
        return False

# Check image file size 
def allowed_image_filesize(file_size):
    if int(file_size) <= current_app.config["MAX_IMAGE_FILESIZE"]:
        return True
    else:
        return False

# grabs each users photos and returns their urls in a Dictionary
def all_users():
    firebase, auth, db, storage, USER = initialize_data()
    data = db.child("users").get().val()    # grabs all user TokenIds
    print("Data: ")
    print(data.values())

    all_user_photo_locations = {}

    #Parse the returned OrderedDict of data
    for val in data:
        #Grab logining in users name from database. Not necessary here
        all_user_photo_locations[val] = []
        data2 = db.child("users").child(val).child("photos").get()

        try:
            data2 = data2.val()

            # data has the id of each photo paired with the actual photo file name
            # Parse the returned OrderedDict for filenames of user photos
            #print("data2: " + str(data2))
            for k,v in data2.items():
                #storage.child("images/" + userId + "/" + val).download(val, val)           # dowloads image to local folder, testing only
                print("v: ", v)
                imageURL = storage.child("images/" + str(val) + "/" + v).get_url(None)      # URL for Google Storage Photo location
                print("imageURL: ", imageURL)
                all_user_photo_locations[val].append(imageURL)                 # Stores the URL of each photo for the user
    
        except AttributeError:
            print("This user: '", val, "' has no photos. Skipped")
        
        
        
        print("HERE 288888888888888888888888888888888888888888888888888888888888888888888888")  
    print(all_user_photo_locations)
    return all_user_photo_locations

# Home Page ---------------------------------
@userBP.route('/home', methods=["GET", "POST"])
def home():
    #Alert Messages
    userLogedIn = "User is still logged in (Home - Good)."
    userNotIn = "No user logged in (Home - Bad)."
    noPhoDisplay = "User has no photos to display"

    try:
        #Check if user is logged in
        print(session['usr'])
        current_app.logger.info(userLogedIn)

        firebase, auth, db, storage, USER = initialize_data()

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
            print("session[usr]:", session['usr'])
            print("USER[uid]", USER["uid"])
            print("data", data)

            # data has the id of each photo paired with the actual photo file name
            # Parse the returned OrderedDict for filenames of user photos
            for val in data.values():
                print("val: " + str(val))               # val = file names of photos stored (from database aka dictionary)
                #storage.child("images/" + userId + "/" + val).download(val, val)           # dowloads image to local folder, testing only
                imageURL = storage.child("images/" + userId + "/" + val).get_url(None)      # URL for Google Storage Photo location
                print("imageURL: " + str(imageURL))
                images.append(imageURL)                 # Stores the URL of each photo for the user
            USER["image_locations"] = images            # Stores the users URL list in Global variable. TODO: Make sure to delete this when session ends
            #print(str(USER["image_locations"]))
            print("Display Photos End---------------------------------------")
            return render_template('home.html', firstName=USER["firstName"], images=USER["image_locations"])
        except:
            render_template('home.html', firstName=USER["firstName"])
        
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
        current_app.logger.info(userNotIn)
        return redirect(url_for('auth.login'))
    
    return render_template('home.html')



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

                    image.seek(0)                               #NEED THIS! We point to the end of the file above to find the size, this causes a empty file to upload without this fix
                    
                    #Check if to run FR or Store photo
                    if request.form.get('analyzer') == 'analyze':
                        #Analyze Check box checked. Run FR on uploaded image then
                        image.save(os.path.join(current_app.config["IMAGE_ANALYZE_UPLOAD"], filename))          #Saves analyzed photo to photosTest/analyzePhotos to be used by FR
                        anazlyzeInfo = recognize.facialRecognition("photosTest/analyzePhotos/" + filename)
                        os.remove("photosTest/analyzePhotos/" + filename)           # remove the photo from photosTest/analyzePhotos
                        print(anazlyzeInfo)
                        userIdDetermined = anazlyzeInfo[0]
                        proba = anazlyzeInfo[1]
                        # TODO: Shawns Code is called here
                        if userIdDetermined.lower() == USER["uid"].lower():
                            # TODO: Tell lock to unlock for correct user
                            print(userIdDetermined + " " + USER["firstName"])
                            userNameDetermined = USER["firstName"]
                            
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

                        # TODO:
                        #Update Facial Embeddings with new photo for user
                        print("Extract Start ------------------------------------")
                        temp_all_users_dict = all_users()
                        extract_embeddings.create_embeddings(temp_all_users_dict, USER["firstName"])
                        train_model.train()
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