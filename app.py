#run with 'python app.py'   can view on 'localhost:5000'

from flask import Flask, render_template     #import flask libries, render_template is so we can make front end

app = Flask(__name__)                        #call flask constuctor from object #__name__ references this file

#define url with a route
@app.route('/')                                                #@ is a decorator, flask uses this to define its urls
def index():
    return render_template('index.html')                       #must be in directory (folder) names templates, grabs file form there

@app.route('/home/users/<string:name>/posts/<int:id>')         #this runs the same function below, but now with url 'localhost:5000/home', so both pages show this now
def hello(name, id):                                           #this code runs when we get to the above url, now 'name' references '<string:name>' so we can grab what is in the url there
    return "Hello, " + name + " your id is: " + str(id)

@app.route('/onlyget', methods=['GET', 'POST'])                #only allows get requests and posts, can specify which methods we want to do that using methods=...
def get_req():
    return 'You can only get this webpage.'


if __name__ == "__main__":  #if running from command line, turn on dev mode
    app.run(debug=True)     #dev mode, server updates on own, shows errors