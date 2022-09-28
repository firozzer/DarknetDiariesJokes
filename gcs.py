# Imports the Google Cloud client library
from google.cloud import storage

def uploadFileToGCS(pathh):
    bucketName = "drknt_drs_audio_hodler"
    storage_client = storage.Client.from_service_account_json('googleSAfrzecoolKey.json')
    bucket = storage_client.bucket(bucketName)
    print(f"Uploading {pathh} to GCS...")
    blob = bucket.blob(pathh)
    blob.upload_from_filename(pathh)
    print("Done.")
    return True

def deleteFileFromGCS(fname):
    bucketName = "drknt_drs_audio_hodler"
    storage_client = storage.Client.from_service_account_json('googleSAfrzecoolKey.json')
    bucket = storage_client.bucket(bucketName)    
    blob = bucket.blob(fname)
    blob.delete()
    print(f"{fname} deleted from GCS.")
    return True

