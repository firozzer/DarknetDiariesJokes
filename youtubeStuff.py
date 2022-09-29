import pickle, os
from urllib import request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload


def createServiceObj():
    CLIENT_SECRET_FILE = "oauthCS.json"
    API_SERVICE_NAME = 'youtube'
    API_VERSION = 'v3'
    SCOPES = ['https://www.googleapis.com/auth/youtube']

    cred = None

    pickle_file = f'token_{API_SERVICE_NAME}_{API_VERSION}.pickle'
    # print(pickle_file)

    if os.path.exists(pickle_file):
        with open(pickle_file, 'rb') as token:
            cred = pickle.load(token)

    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            cred = flow.run_local_server()

        with open(pickle_file, 'wb') as token:
            pickle.dump(cred, token)

    try:
        service = build(API_SERVICE_NAME, API_VERSION, credentials=cred)
        # print(API_SERVICE_NAME, 'service created successfully')
        return service
    except Exception as e:
        print(e)
        print(f'Failed to create service instance for {API_SERVICE_NAME}')
        os.remove(pickle_file)
        return None


def deleteVideoFromYoutube(id):
    service = createServiceObj()
    response = service.videos().delete(id=id).execute()

def uploadVideoToYoutube(fname, title, desc, tags, category, privacyStatus):
    service = createServiceObj()
    request = service.videos().insert(
        part="snippet,status,id",
        body={
          "snippet": {
            "categoryId": category,
            "description": desc,
            "title": title,
            "tags": tags
          },
          "status": {
            "privacyStatus": privacyStatus
          }
        },
        media_body=MediaFileUpload(fname)
    )
    print("Uploading vid to YouTube...")
    response = request.execute()
    videoId = response['id']
    print("Done. Video ID: ", videoId)
    return videoId

def getYTVidStatus(id):
    service = createServiceObj()
    request = service.videos().list(
        part="status",
        id=id
    ).execute()
    return request['items'][0]['status']['uploadStatus']