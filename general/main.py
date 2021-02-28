from flask import Blueprint, render_template, request

mainBP = Blueprint("general", __name__, static_folder="static", template_folder="templates")

# Routes ////////////////////////////////////////____________________________________________
# Welcome Page ---------------------------------
@mainBP.route('/', methods=['GET', 'POST'])                                                #@ is a decorator, flask uses this to define its urls, define url with a route
def welcome():
    #Check if screen buttons are clicked
    if request.method == "POST":
        if request.form['button'] == 'loginScreen':
            redirect(url_for('/authsBP.login'))
        elif request.form['button'] == 'registerScreen':
            redirect(url_for('/authsBP.register'))
    return render_template('welcome.html')                       #must be in directory (folder) names templates, grabs file form there
