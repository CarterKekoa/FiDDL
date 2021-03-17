import fiddl_utils as fiddl_utils

def all_users():
    """grabs each users photos in database and returns their urls in a Dictionary
    """
    firebase, auth, db, storage, bucket= fiddl_utils.initialize_data()
    data = db.child("users").get().val()    # grabs all user TokenIds
    #print(fiddl_utils.bcolors.OKBLUE, "                             Users Grabbed: ", data.values(), fiddl_utils.bcolors.ENDC)
    all_user_photo_locations = {}

    #Parse the returned OrderedDict of data
    for user in data:
        #Grab logining in users name from database. Not necessary here
        all_user_photo_locations[user] = []

        data2 = db.child("users").child(user).child("photos").get() # grabbing photos directory
        # check if photos exist for the user. if not then we move to next user
        if not data2.val() == None:
            try:
                photo_name_dict = data2.val()   # stores a dictionary of the 'user's image names
                #print("photo_name_dict", type(photo_name_dict))

                # photo_name_dict has the id of each photo paired with the actual photo file name
                # Parse the returned OrderedDict for filenames of user photos
                # for each key in the dictionary of photo keys and names
                for key in photo_name_dict:
                    photo_name = photo_name_dict[key]   # get the value at the curent key position
                    #storage.child("images/" + userId + "/" + user).download(user, user)           # dowloads image to local folder, testing only
                    #print("photo_name: ", photo_name)
                    imageURL = storage.child("images/" + str(user) + "/" + photo_name).get_url(None)      # URL for Google Storage Photo location
                    #print("imageURL: ", imageURL)
                    all_user_photo_locations[user].append(imageURL)                 # Stores the URL of each photo for the user
            except:
                fiddl_utils.PrintException()
    return all_user_photo_locations