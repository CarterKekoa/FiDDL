#run with 'python app.py'   can view on 'localhost:5000'

from flask import Flask, render_template, json
from flask.globals import request
from jws import verify     #import flask libries, render_template is so we can make front end
import pyrebase

app = Flask(__name__)                        #call flask constuctor from object #__name__ references this file

# Google Firebase ////////////////////////////////__________________________________________________


#initialize database
firebase = pyrebase.initialize_app(json.load(open('firebase/firebaseConfig.json')))
auth = firebase.auth()
db = firebase.database()

#Dummy data to see how to send it to html, make using dictionaires
all_posts = [
    {
        'title': 'Post 1',
        'content': 'This is the content of post 1',
        'author': 'Carter'
    },
    {
        'title': 'Post 2',
        'content': 'This is the content of post 2'
    }
]

#Dummy Data to set up Google auth
users1 = [{'uid': 1, 'name': 'Carter Mooring'}]

#pushing dummy data to firebase
# db.child("posts").push(all_posts)
# db.child("posts").update(all_posts)
# db.child("posts").remove()


# Routes ////////////////////////////////////////____________________________________________
#DEVELOPMENT

@app.route('/api/userinfo')
def userinfo():
    return {'data': users1}, 200

@app.route('/')                                                #@ is a decorator, flask uses this to define its urls, define url with a route
def welcome():
    return render_template('welcome.html')                       #must be in directory (folder) names templates, grabs file form there

@app.route('/register', methods=['GET', 'POST'])
def register():
    badEmail = 'There is already an account with this email address'
    goodEmail = 'Good email submitted'
    badPassMatch = 'Your passwords do not match. Please try again.'
    created = 'User account successfully created'
    if request.method == 'POST':
        email = request.form['email']
        try:
            app.logger.info(goodEmail)
        except:
            app.logger.info(badEmail)                           #Email already exists, code 400
            render_template('register.html', b=badEmail)
        password = request.form['password']
        passwordCheck = request.form['passwordConfirm']         #Confirm Password
        if password != passwordCheck:
            app.logger.info(badPassMatch)
            return render_template('register.html', bpm=badPassMatch)
        user = auth.create_user_with_email_and_password(email, password)
        app.logger.info(created)
        auth.send_email_verification(user['idToken'])           #send a user confirmation email
        verify = 'An email has been sent to' + email + ". Please verify your account before logging in."
        auth.get_account_info(user['idToken'])
        db.child("todo").push(user)
        todo = db.child("todo").get()
        to = todo.val()
        #TODO: have it actually switch to the login screen and url. Must login again. wont login without being verified.
        return render_template('login.html', verify)
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    unsuccesful = 'Please check your email or password'
    succesful = 'Login Successful'
    if request.method == 'POST':
        email = request.form['email']
        #TODO: verify if user has verified their account 
        password = request.form['password']
        #TODO: stay logged in button?
        try:
            auth.sign_in_with_email_and_password(email, password)
            app.logger.info(succesful)
            #TODO: move to next screen
            return render_template('login.html', s=succesful)
        except:
            app.logger.info('Login Failed: ' + unsuccesful)
            return render_template('login.html', us=unsuccesful)
    return render_template('login.html')

#PRACTICE
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
