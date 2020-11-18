#run with 'python app.py'   can view on 'localhost:5000'

from flask import Flask, render_template, json
from flask.globals import request     #import flask libries, render_template is so we can make front end
import pyrebase

app = Flask(__name__)                        #call flask constuctor from object #__name__ references this file

# Google Firebase ////////////////////////////////__________________________________________________
firebaseConfig = {
    'apiKey': "AIzaSyBI068aAZtlskhzAAAyJJ_eTB88jiy_auQ",
    'authDomain': "fiddl-dev.firebaseapp.com",
    'databaseURL': "https://fiddl-dev.firebaseio.com",
    'projectId': "fiddl-dev",
    'storageBucket': "fiddl-dev.appspot.com",
    'messagingSenderId': "792330223312",
    'appId': "1:792330223312:web:74d186ef299b8cb88628d5",
    'measurementId': "G-M3D4L2WYTQ"
}

#initialize database
firebase = pyrebase.initialize_app(firebaseConfig)
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

#pushing dummy data to firebase
# db.child("posts").push(all_posts)
# db.child("posts").update(all_posts)
# db.child("posts").remove()


# Routes ////////////////////////////////////////____________________________________________
#DEVELOPMENT

#define url with a route
@app.route('/')                                                #@ is a decorator, flask uses this to define its urls
def welcome():
    return render_template('welcome.html')                       #must be in directory (folder) names templates, grabs file form there

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        db.child("todo").push(email)
        todo = db.child("todo").get()
        to = todo.val()
        return render_template('register.html', t=to.values())
    return render_template('register.html')

@app.route('/login')
def login():
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
