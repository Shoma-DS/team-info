import argparse
import http.client
import httplib2
import os
import random
import time
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# Explicitly tell the underlying library that we are allowing OAuthlib to
# run over HTTP for local testing.
# os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret.
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

# Maximum number of times to retry a failed HTTP request.
MAX_RETRIES = 10

# Error codes to retry.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, http.client.NotConnected,
                        http.client.IncompleteRead, http.client.ImproperConnectionState,
                        http.client.CannotSendRequest, http.client.CannotSendHeader,
                        http.client.ResponseNotReady, http.client.BadStatusLine)

RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

def get_authenticated_service(account_name):
    config_dir = os.path.expanduser(f'~/.config/team-info/youtube-upload/{account_name}')
    os.makedirs(config_dir, exist_ok=True)
    
    token_file = os.path.join(config_dir, 'token.json')
    secrets_file = os.path.join(config_dir, 'client_secrets.json')
    
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(secrets_file):
                raise FileNotFoundError(f"Missing client_secrets.json in {config_dir}")
            
            flow = InstalledAppFlow.from_client_secrets_file(secrets_file, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    return build(API_SERVICE_NAME, API_VERSION, credentials=creds)

def initialize_upload(youtube, options):
    tags = None
    if options.keywords:
        tags = options.keywords.split(',')

    body = {
        'snippet': {
            'title': options.title,
            'description': options.description,
            'tags': tags,
            'categoryId': options.category
        },
        'status': {
            'privacyStatus': options.privacy,
            'selfDeclaredMadeForKids': False
        }
    }
    
    if options.publish_at:
        body['status']['publishAt'] = options.publish_at

    insert_request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=MediaFileUpload(options.file, chunksize=-1, resumable=True)
    )

    resumable_upload(insert_request)

def resumable_upload(request):
    response = None
    error = None
    retry = 0
    while response is None:
        try:
            print('Uploading file...')
            status, response = request.next_chunk()
            if response is not None:
                if 'id' in response:
                    print(f'Video id "{response["id"]}" was successfully uploaded.')
                else:
                    exit(f'The upload failed with an unexpected response: {response}')
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = f'A retriable HTTP error {e.resp.status} occurred: {e.content}'
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = f'A retriable error occurred: {e}'

        if error is not None:
            print(error)
            retry += 1
            if retry > MAX_RETRIES:
                exit('No longer attempting to retry.')

            max_sleep = 2**retry
            sleep_seconds = random.random() * max_sleep
            print(f'Sleeping {sleep_seconds} seconds and then retrying...')
            time.sleep(sleep_seconds)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', required=True, help='Video file to upload')
    parser.add_argument('--account', required=True, help='Account name (acoriel, etc.)')
    parser.add_argument('--title', default='Test Video Title', help='Video title')
    parser.add_argument('--description', default='Test Video Description', help='Video description')
    parser.add_argument('--category', default='22', help='Numeric video category (22 is People & Blogs)')
    parser.add_argument('--keywords', default='', help='Video keywords, comma separated')
    parser.add_argument('--privacy', default='unlisted', choices=['public', 'private', 'unlisted'], help='Video privacy status')
    parser.add_argument('--publish-at', help='ISO 8601 formatted datetime (e.g. 2024-04-10T18:00:00Z)')

    args = parser.parse_args()

    if not os.path.exists(args.file):
        exit(f'Please specify a valid file: {args.file}')

    try:
        youtube = get_authenticated_service(args.account)
        initialize_upload(youtube, args)
    except HttpError as e:
        print(f'An HTTP error {e.resp.status} occurred:\n{e.content}')
    except Exception as e:
        print(f'An error occurred: {e}')
