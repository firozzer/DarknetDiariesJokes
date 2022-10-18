import logging

from google.cloud import storage

def uploadFileToGCS(pathh):
    bucketName = "drknt_drs_audio_hodler"
    storage_client = storage.Client.from_service_account_json('myCreds/googleSrvcAcKey.json')
    bucket = storage_client.bucket(bucketName)
    logging.info(f"Uploading {pathh} to GCS...")
    blob = bucket.blob(pathh)
    blob.upload_from_filename(pathh)
    logging.info("Done.")
    return True

def deleteFileFromGCS(fname):
    bucketName = "drknt_drs_audio_hodler"
    storage_client = storage.Client.from_service_account_json('myCreds/googleSrvcAcKey.json')
    bucket = storage_client.bucket(bucketName)    
    blob = bucket.blob(fname)
    blob.delete()
    logging.info(f"{fname} deleted from GCS.")
    return True

