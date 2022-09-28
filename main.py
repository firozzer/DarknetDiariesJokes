import requests, re, subprocess, os, json, time

from bs4 import BeautifulSoup

from imgPrsg import processZeJPG
from spRecogGoogle import getTimestampsFromGoogle
from gcs import uploadFileToGCS, deleteFileFromGCS
from youtubeStuff import uploadVideoToYoutube, deleteVideoFromYoutube, getYTVidStatus

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# get next Ep no to check
with open('info.json') as f:
    jsonData = json.load(f)
    latestEpNo = jsonData['lastEpUppdToYT']+1
    oldVidID = jsonData['ytVidID']

# get title, artwork & mp3 of ep
latestEpURL = f"https://darknetdiaries.com/episode/{latestEpNo}/"
r = requests.get(latestEpURL)
if r.ok:
    soup = BeautifulSoup(r.content, features='html.parser')

    # get ep title
    epName = soup.find('title').text[:-18]

    # get artwork
    epArtwork = soup.find('div', class_='hero__image')
    epArtworkURL = "https://darknetdiaries.com" + epArtwork['style'][22:-1]
    print(f"Downloading ep {latestEpNo} artwork...")
    artworkReq = requests.get(epArtworkURL)
    with open(f"{latestEpNo}.jpg", 'wb') as f:
        f.write(artworkReq.content)
    print("Done.")

    # get mp3
    if os.path.exists(f'{latestEpNo}.mp3'):
        print("MP3 present on disk, skipping download")
    else:
        scriptElems = soup.find_all('script')
        urlPattern = """https://.{10,90}mp3"""
        mp3URL = re.search(urlPattern, str(scriptElems))[0]
        print(f"Downloading ep {latestEpNo} mp3...")
        mp3Req = requests.get(mp3URL)
        with open(f'{latestEpNo}.mp3', 'wb') as f:
            f.write(mp3Req.content)
        print("Done.")
else:
    print('New ep not up yet.')
    exit()

# PROCESSING THE MP3
# grab last few mins of full ep,
roughCut = 90
# passing af with s16 bit depth to create smaller (half size) file. ac 1 specifies only 1 audio channel needed othewse Google gets thrown.
subprocess.run(f"ffmpeg -y -sseof -{roughCut} -i {latestEpNo}.mp3 -af aformat=s16:44100 -ac 1 {latestEpNo}c.flac", shell=True)

#uploading to GCS so GTTS can process it
succeeded = uploadFileToGCS(f"{latestEpNo}c.flac")
if not succeeded: 
    print("Problem in gcs.py upload, exiting.")
    exit()

# get exact timestamps using Google TTS
cutStart, cutEnd = getTimestampsFromGoogle(latestEpNo, roughCut)

# get final joke cut audio
subprocess.run(f"ffmpeg -y -ss {cutStart} -to {cutEnd} -i {latestEpNo}.mp3 -c copy {latestEpNo}f.mp3", shell=True)

# PROCESSING THE JPG
succeeded = processZeJPG(f"{latestEpNo}.jpg", epName)
if not succeeded: 
    print('Problem in artwork processing')
    exit()

# add jpg to mp3
subprocess.run(f"ffmpeg -y -loop 1 -framerate 5 -i {latestEpNo}f.jpg -i {latestEpNo}f.mp3 -shortest -acodec copy -vcodec mjpeg {latestEpNo}f.mkv", shell=True)

# join new ep to old eps
with open("concat.txt", 'w') as f: f.write(f"file 'ytVid.mkv'\nfile '{latestEpNo}f.mkv")
subprocess.run(f"""ffmpeg -f concat -i concat.txt -c copy ytVidNew.mkv; rm concat.txt""", shell=True)

# upload to YouTube
ytFilename = "ytVidNew.mkv"
ytTitle = f"Darknet Diaries Jokes (updated till Ep {latestEpNo} {epName})"
ytDesc = "All the jokes that Jack Rhysider cracks at the end of each show."
ytTags = ['darknet diaries', 'jack rhysider', 'cybersecurity', 'tech', 'hacking', 'jokes']
ytCategory = "24" # apparently for enternationament
ytPrivacyStatus = 'private'
newVidID = uploadVideoToYoutube(ytFilename,ytTitle,ytDesc,ytTags,ytCategory,ytPrivacyStatus)

succeeded = deleteFileFromGCS(f"{latestEpNo}c.flac")
if not succeeded: 
    print("Problem in gcs.py upload, exiting.")
    exit()

print('Waiting for uploaded video to get processed...')
while getYTVidStatus(newVidID) != 'processed':
    time.sleep(30)
print('Done. Deleting old video from YouTube...')
deleteVideoFromYoutube(oldVidID)
print("Done.")

#upadte info.json with new epNo
with open('info.json') as f: jsonData = json.load(f)
jsonData['lastEpUppdToYT'] = latestEpNo
jsonData['ytVidID'] = newVidID
with open('info.json', "w") as f: json.dump(jsonData, f)

# Deleting ep.mp3, epc.flac, epf.mp3, epf.mkv, ep.jpg, epf.jpg, old YT vid & GCS:epc.flac.
subprocess.run(f"rm ytVid.mkv {latestEpNo}f.* {latestEpNo}c.flac {latestEpNo}.*; mv ytVidNew.mkv ytVid.mkv", shell=True)
print("Deleted all local files.")