from flask import Blueprint, render_template, request, session, current_app, redirect, url_for, flash

# Facial Recognition File Imports
import FacialRecognition.recognize as recognize
import FacialRecognition.extract_embeddings as extract_embeddings
import FacialRecognition.train_model as train_model

mainBP = Blueprint("general", __name__, static_folder="static", template_folder="templates")

# Helper File Imports
import general.utils as utils
import fiddl_utils as fiddl_utils


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
            current_app.logger.info("[WELCOME] Training FR Models based on current users and photos available...")
            try:
                current_app.logger.info("[WELCOME] Training Models...")
                temp_all_users_dict = utils.all_users()
                extract_embeddings.create_embeddings(temp_all_users_dict)
                train_model.train()
                current_app.logger.info("[WELCOME] Models Trained")
                modelsTrained = "New Facial Recognition models succesfully computed. Any new users and images are now included."
                flash(modelsTrained, "info")                    #"info" is the type of message for more customization if we want, others are warning, info, error
            except:
                current_app.logger.info("[ERROR - WELCOME] Error Occured...")
                fiddl_utils.PrintException()
            return redirect(url_for('general.welcome'))
    elif request.method == "GET":
        return render_template('welcome.html')                    #must be in directory (folder) names templates, grabs file form there
