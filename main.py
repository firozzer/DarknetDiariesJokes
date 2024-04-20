import requests, re, subprocess, os, json, time, datetime, logging, sys

from bs4 import BeautifulSoup

from imgPrsg import processZeJPG
from spRecogGoogle import getTimestampsFromGoogle
from gcs import uploadFileToGCS, deleteFileFromGCS
from youtubeStuff import uploadVideoToYoutube, deleteVideoFromYoutube, getYTVidStatus, setThumbnailForYTVideo
from myCreds.telegramCreds import tgBotToken, myTgChatID

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def sendTgMsg(text='blablabla'):
    url = f'https://api.telegram.org/bot{tgBotToken}/sendMessage'
    payload = {'chat_id': myTgChatID, 'text': text}
    r = requests.post(url,json=payload)
    return r

def getEpMP3nameAndJPEG(latestEpURL):
    r = requests.get(latestEpURL)
    if r.ok:
        sendTgMsg(f"New Darknet Diaries ep {latestEpNo} is being processed. Take a look.")
        soup = BeautifulSoup(r.content, features='html.parser')

        # get ep title
        epName = soup.find('title').text[:-18]

        # get artwork
        epArtwork = soup.find('div', class_='hero__image')
        epArtworkURL = "https://darknetdiaries.com" + epArtwork['style'][22:-1]
        logging.info(f"Downloading ep {latestEpNo} artwork...")
        artworkReq = requests.get(epArtworkURL)
        with open(f"{latestEpNo}.jpg", 'wb') as f:
            f.write(artworkReq.content)
        logging.info("Done.")

        # get mp3
        if os.path.exists(f'{latestEpNo}.mp3'):
            logging.info("MP3 present on disk, skipping download")
        else:
            scriptElems = soup.find_all('script')
            urlPattern = """"mp3":(.+")"""
            mp3URL = re.search(urlPattern, str(scriptElems)).group(1).strip()[1:-1] # the indexex trimming in end are to get rid of quotes
            logging.info(f"Downloading ep {latestEpNo} mp3...")
            mp3Req = requests.get(mp3URL)
            with open(f'{latestEpNo}.mp3', 'wb') as f:
                f.write(mp3Req.content)
            logging.info("Done.")
        return epName
    else:
        logging.info(f'Ep {latestEpNo} not up yet.')
        exit()

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

# configure logging settings
sys.excepthook = handle_exception # this helps to log all uncaught exceptions
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("darknet.log"), logging.StreamHandler()])
logging.getLogger("urllib3").setLevel(logging.INFO) #as these guys spam a lot in DEBUG

# get next Ep no to check
with open('info.json') as f:
    jsonData = json.load(f)
    latestEpNo = jsonData['lastEpUppdToYT']+1
    oldVidID = jsonData['ytVidID']

# get title, artwork & mp3 of ep
latestEpURL = f"https://darknetdiaries.com/episode/{latestEpNo}/"
epName = getEpMP3nameAndJPEG(latestEpURL)

# PROCESSING THE MP3
# grab last few mins of full ep,
roughCut = 90
# passing af with s16 bit depth to create smaller (half size) file. ac 1 specifies only 1 audio channel needed othewse Google gets thrown.
subprocess.run(f"ffmpeg -y -sseof -{roughCut} -i {latestEpNo}.mp3 -af aformat=s16:44100 -ac 1 {latestEpNo}c.flac", shell=True)

#uploading to GCS so GSTT can process it. Direct uploads from local system are restricted to 60 secs / 10 MB max.
succeeded = uploadFileToGCS(f"{latestEpNo}c.flac")
if not succeeded: 
    logging.warning("Problem in GoogCloudStorage file uploading, exiting.")
    exit()

# get exact timestamps using Google STT
cutStart, cutEnd = getTimestampsFromGoogle(latestEpNo, roughCut)
logging.info(f"Final cutStart & cutEnd are: {cutStart} {cutEnd}")

# get final joke cut audio
subprocess.run(f"ffmpeg -y -ss {cutStart} -to {cutEnd} -i {latestEpNo}.mp3 -c copy {latestEpNo}f.mp3", shell=True)

# PROCESSING THE JPG
succeeded = processZeJPG(f"{latestEpNo}.jpg", epName)
if not succeeded: 
    logging.warning('Problem in artwork processing')
    exit()

# add jpg to mp3
logging.info("Adding JPG to cut-out joke audio...")
subprocess.run(f"""ffmpeg -y -loop 1 -i {latestEpNo}f.jpg -i {latestEpNo}f.mp3 -shortest -acodec copy -vcodec libx265 -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2" {latestEpNo}f.mkv""", shell=True) # encoding into tiny x265 file as later on uplading 100 MB+ YT vids crash on Oracle 1 GB RAM server
logging.info("Done.")

# join new ep to old eps
with open("concat.txt", 'w') as f: f.write(f"file 'ytVid.mkv'\nfile '{latestEpNo}f.mkv'")
subprocess.check_output(f"""ffmpeg -y -f concat -i concat.txt -c copy ytVidNew.mkv""", shell=True)
if os.name == 'nt': # means i'm running code on ASSASSIN Windows 10 PC
    subprocess.check_output(f"""del concat.txt""", shell=True)
else:
    subprocess.check_output(f"""rm concat.txt""", shell=True)

# upload to YouTube
ytFilename = "ytVidNew.mkv"
ytTitle = f"Darknet Diaries Jokes (updated till Ep {latestEpNo} {epName})"
ytTags = ['darknet diaries', 'jack rhysider', 'cybersecurity', 'tech', 'hacking', 'jokes']
ytCategory = "24" # apparently for enternationament
ytPrivacyStatus = 'public'

# constructing new Youtube description
with open("descYTVid.txt") as f: ytDescOld = f.read()
durationOfLastYTVid = int(float(subprocess.check_output(f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 ytVid.mkv", shell=True).decode('utf-8').strip()[:-4]))
tsOfNewAddition = str(datetime.timedelta(seconds=durationOfLastYTVid))
ytDesc = ytDescOld + f"\n{tsOfNewAddition} - Ep {latestEpNo} {epName}"

newVidID = uploadVideoToYoutube(ytFilename,ytTitle,ytDesc,ytTags,ytCategory,ytPrivacyStatus)
sendTgMsg(f"Uploaded {ytTitle} to YT. Take a look: https://youtu.be/{newVidID}")

logging.info('Waiting for uploaded video to get processed...')
while getYTVidStatus(newVidID) != 'processed':
    time.sleep(30)
logging.info('Done. Setting thumbnail for new video...')
setThumbnailForYTVideo(newVidID, f"{latestEpNo}f.jpg")
#deleteVideoFromYoutube(oldVidID)
logging.info("Done.")

succeeded = deleteFileFromGCS(f"{latestEpNo}c.flac")
if not succeeded: 
    logging.warning("Problem in GoogCloudStorage file deletion, maybe file deleted during debugging earlier? Continuing nevertheless")
    sendTgMsg("Problem in GoogCloudStorage file deletion in the Darknet Diaries auto Youtube upload project. Check it & delete file from GCS or you'll get charged there's some free tier limit.")

#upadte info.json & descYTVid.txt with new data
with open('info.json') as f: jsonData = json.load(f) # ncsry to open again as GSTT has been updated in file
jsonData['lastEpUppdToYT'] = latestEpNo
jsonData['ytVidID'] = newVidID
with open('info.json', "w") as f: json.dump(jsonData, f)
with open("descYTVid.txt", 'w') as f: f.write(ytDesc)

# updating Github Readme page with latest vid URL. Commented it all out for now as Github has changed auth method, will need to study.
# with open("README.md") as f: data = f.read()
# data = data.split('\n')
# data[2] = f'Check out all the jokes here: https://www.youtube.com/watch?v={newVidID}'
# newData = '\n'.join(data)
# with open("README.md", 'w') as f: f.write(newData)
# subprocess.run("""git add README.md descYTVid.txt info.json timestamps.txt""", shell=True)
# subprocess.run(f"""git commit -m "auto git commit upon ep{latestEpNo} upload" """, shell=True)
# subprocess.run("""git push github main" """, shell=True) # keep on separate lines so that Windows compatible

# Deleting ep.mp3, epc.flac, epf.mp3, epf.mkv, ep.jpg, epf.jpg, old YT vid & GCS:epc.flac.
if os.name == 'nt': # means i'm running code on ASSASSIN Windows 10 PC
    subprocess.run(f"del ytVid.mkv {latestEpNo}f.* {latestEpNo}c.flac {latestEpNo}.*", shell=True)
    subprocess.run(f"ren ytVidNew.mkv ytVid.mkv", shell=True)
else: # assuming else running on Ubuntu
    subprocess.run(f"rm ytVid.mkv {latestEpNo}f.* {latestEpNo}c.flac {latestEpNo}.*; mv ytVidNew.mkv ytVid.mkv", shell=True)
logging.info("Deleted all local files.")
