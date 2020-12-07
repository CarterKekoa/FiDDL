# google_nest_api.py
# fiddl
# author: Drew Bies
# description: this program connects to the google nest doorbell camera. 
#   get_access_token() retrieves the authentication token needed to access the doorbell device.
#   get_rtsp_stream() retrieves a live stream url of the camera feed in rtsp format.

import requests
import json


DEVICE_ID = 'AVPHwEvDLJQsZiLE6-AA7XH4J3OLKg5pqUIh69kYCOlASNxvmDK0IRRa0bjHoNEWLLoHiOanMP1stHjUXVspoNc0DG1luQ'
CLIENT_ID = '94523447905-vo4v1a5613fj3ep5p8s29vemet0bqnmt.apps.googleusercontent.com'
CLIENT_SECRET = '0eJ1_AS1KltV0hrSFWAGvIGX'
PROJECT_ID = '428fdda2-61c1-41b1-b271-1e4a657994ac'
AUTH_CODE = '4/0AY0e-g5gzJuAbg57kqCnHA9ODF1WKp8dIYDlTl-aHCU4O6W4pL85vS0fMd1VvpYcVw4zBQ'
REFRESH_TOKEN = '1//06QVtkS0U9RwBCgYIARAAGAYSNwF-L9IrFfNFhp_wKWJhLM3HEFVeJeVZ9SP8ro_Wt4624K-L9CKxj5-_ctAFDgI_VI-vLXQyKoc'


# gets the access token by using the refresh token
def get_access_token():
    url_str = 'https://www.googleapis.com/oauth2/v4/token?client_id=' + CLIENT_ID + '&client_secret=' + CLIENT_SECRET + '&refresh_token=' + REFRESH_TOKEN + '&grant_type=refresh_token'
    # will return json with token value named access_token
    
    response = requests.post(url_str)
    json_object = response.json()
    token = json_object['access_token']
    #print('access token: ' + token)
    return token

# returns the url for a rtsp stream of the doorbell camera
def get_rtsp_stream():
    url_str = 'https://smartdevicemanagement.googleapis.com/v1/enterprises/' + PROJECT_ID + '/devices/' + DEVICE_ID + ':executeCommand'

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + get_access_token(),
    }

    data = '{ "command" : "sdm.devices.commands.CameraLiveStream.GenerateRtspStream", "params" : {} }'

    response = requests.post(url_str, headers=headers, data=data)

    # json results
    results = response.json()['results']
    rstp_url = results['streamUrls']['rtspUrl']
    stream_token = results['streamToken']
    stream_extension_token = results['streamExtensionToken']
    expiration_time = results['expiresAt']
    return rstp_url

