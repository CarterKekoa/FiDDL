from flask import Blueprint, render_template, request, session, current_app, redirect, url_for, flash

# Facial Recognition File Imports
import FacialRecognition.recognize as recognize
import FacialRecognition.extract_embeddings as extract_embeddings
import FacialRecognition.train_model as train_model

mainBP = Blueprint("general", __name__, static_folder="static", template_folder="templates")

def initialize_data():
    firebase = current_app.config['firebase']
    auth = current_app.config['auth']
    db = current_app.config['db']
    storage = current_app.config['storage']
    #storageRef = current_app.config['storageRef']
    return firebase, auth, db, storage

# grabs each users photos and returns their urls in a Dictionary
def all_users():
    firebase, auth, db, storage = initialize_data()
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
        
    print(all_user_photo_locations)
    return all_user_photo_locations

# Routes ////////////////////////////////////////____________________________________________
# Welcome Page ---------------------------------
@mainBP.route('/', methods=['GET', 'POST'])                                                #@ is a decorator, flask uses this to define its urls, define url with a route
def welcome():
    #Check if screen buttons are clicked
    
    if request.method == "POST":
        if request.form['button'] == 'loginScreen':
            return redirect(url_for('auth.login'))
        elif request.form['button'] == 'registerScreen':
            return redirect(url_for('auth.register'))
        elif request.form['button'] == 'trainButton':
            print("Extract Start ------------------------------------")
            temp_all_users_dict = all_users()
            extract_embeddings.create_embeddings(temp_all_users_dict)
            train_model.train()
            modelsTrained = "New Facial Recognition models succesfully computed. Any new users and images are now included."
            flash(modelsTrained, "info")                    #"info" is the type of message for more customization if we want, others are warning, info, error
            return redirect(url_for('general.welcome'))
    elif request.method == "GET":
        return render_template('welcome.html')                    #must be in directory (folder) names templates, grabs file form there
