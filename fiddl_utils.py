import linecache
import sys
from flask import current_app

# Initialize Functions -------------------------------------------------------
def initialize_data():
    firebase = current_app.config['firebase']
    auth = current_app.config['auth']
    db = current_app.config['db']
    storage = current_app.config['storage']
    #storageRef = current_app.config['storageRef']
    bucket = current_app.config['bucket'] 
    return firebase, auth, db, storage, bucket

# Style Functions -------------------------------------------------------
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

def PrintException():
    """This Parces an exceptions info and prints useful information for tracing the error
    """
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print(bcolors.FAIL, 'EXCEPTION({}) IN ({}, LINE {} "{}"): {}'.format(exc_type, filename, lineno, line.strip(), exc_obj), bcolors.ENDC)
    print 