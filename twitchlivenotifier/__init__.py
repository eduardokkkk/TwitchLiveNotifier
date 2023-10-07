# -*- coding: utf-8 -*-

"""
Twitch Live Notifier
~~~~~~~~~~~~~~~~~~~

Python script to notify a Discord server when the streamer goes live, with the current game and box art.

:copyright: (c) 2017-2020 Dylan Kauling
:license: GPLv3, see LICENSE for more details.

"""

__title__ = 'twitchlivenotifier'
__author__ = 'Dylan Kauling'
__license__ = 'GPLv3'
__copyright__ = 'Copyright 2017-2020 Dylan Kauling'
__version__ = '0.3'

import time
import sys
import configparser

import requests
import zc.lockfile

twitch_client_id = ''
twitch_secret_key = ''
twitch_app_token_json = {}
twitch_user = ''
stream_api_url = ''
stream_url = ''
numbers = [] #all the whatsapp numbers to send the notification
config_path = '' # your config.ini path

def get_lock():
    try:
        print("Acquiring lock...")
        global lock
        lock = zc.lockfile.LockFile('lock.lock')
    except:
        print("Failed to acquire lock, terminating...")
        sys.exit()

def config():
    config_file = configparser.ConfigParser()
    config_file.read(config_path)
    twitch_config = config_file['Twitch']


    try:
        twitch_config = config_file['Twitch']
    except KeyError:
        print('[Twitch] section not found in config file. Please set values for [Twitch] in config.ini')
        print('Take a look at config_example.ini for how config.ini should look.')
        sys.exit()

    global twitch_user
    try:
        twitch_user = twitch_config['User']
    except KeyError:
        print('User not found in Twitch section of config file. Please set User under [Twitch] in config.ini')
        print('This is the broadcaster\'s Twitch name, case-insensitive.')
        sys.exit()


    global twitch_client_id
    try:
        twitch_client_id = twitch_config['ClientId']
    except KeyError:
        print('ClientId not found in Twitch section of config file. Please set ClientId under [Twitch] in config.ini')
        print('This is the Client ID you receive when registering an application as a Twitch developer.')
        print('Please check the README for more instructions.')
        sys.exit()

    global twitch_secret_key
    try:
        twitch_secret_key = twitch_config['ClientSecret']
    except KeyError:
        print('ClientSecret not found in Twitch section of config file. Please set ClientSecret under [Twitch] in '
              'config.ini')
        print('This is the Client Secret you receive when registering an application as a Twitch developer.')
        print('Please check the README for more instructions.')
        sys.exit()


    global stream_api_url
    stream_api_url = "https://api.twitch.tv/helix/streams"

    global stream_url
    stream_url = "https://www.twitch.tv/" + twitch_user.lower()



    Twilio_config = config_file['Twilio']


    global Twilio_accountSid
    Twilio_accountSid = Twilio_config['account_sid']

    global Twilio_authToken
    Twilio_authToken = Twilio_config['accountAuth_token']

    
    global client 
    client = Client(Twilio_accountSid, Twilio_authToken)


    global Twilio_message
    Twilio_message = Twilio_config['Message']






def authorize():
    token_params = {
        'client_id': twitch_client_id,
        'client_secret': twitch_secret_key,
        'grant_type': 'client_credentials',
    }
    app_token_request = requests.post('https://id.twitch.tv/oauth2/token', params=token_params)
    global twitch_app_token_json
    twitch_app_token_json = app_token_request.json()


def main():
    twitch_json = {'data': []}
    while len(twitch_json['data']) == 0:
        twitch_headers = {
            'Client-ID': twitch_client_id,
            'Authorization': 'Bearer ' + twitch_app_token_json['access_token'],
        }
        twitch_params = {'user_login': twitch_user.lower()}
        request_status = 401
        while request_status == 401:
            twitch_request = requests.get(stream_api_url, headers=twitch_headers, params=twitch_params)
            request_status = twitch_request.status_code
            if request_status == 401:
                authorize()
                twitch_headers['Authorization'] = 'Bearer ' + twitch_app_token_json['access_token']
                continue
            twitch_json = twitch_request.json()

        if len(twitch_json['data']) == 1:
            print("Stream is live.")

            stream_json = twitch_json['data'][0]
            stream_title = stream_json['title']
            stream_game_id = stream_json['game_id']

            user_search_url = "https://api.twitch.tv/helix/users"
            user_params = {'login': twitch_user.lower()}
            user_response = {}
            request_status = 401
            while request_status == 401:
                user_request = requests.get(user_search_url, headers=twitch_headers, params=user_params)
                request_status = user_request.status_code
                if request_status == 401:
                    authorize()
                    twitch_headers['Authorization'] = 'Bearer ' + twitch_app_token_json['access_token']
                    continue
                user_response = user_request.json()





            status_code = 0
            while status_code != 204:
                for number in number:
                    message = client.messages.create(
                        from_='whatsapp:+14155238886',
                        body=Twilio_message,
                        to=f'whatsapp:{number}'
                    )

                if message.sid:
                    print("Successfully called Twilio API. Waiting 5 seconds to terminate...")
                    time.sleep(5)
                    break
               
                else:
                    print("Failed to call Twilio API. Waiting 5 seconds to retry...")
                    time.sleep(5)
        else:
            print("Stream is not live. Waiting 5 seconds to retry...")
            time.sleep(5)


if __name__ == "__main__":
    config()
    authorize()
    main()
