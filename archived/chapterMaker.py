import re, pyperclip
import datetime
import os

with open("tses extracted by ffmpeg.txt") as f:
    data = f.read()

sRes = re.findall("pts_time:(.+)pos:", data)

# making a dic of ep nos & names from the gathered jpgs
os.chdir(os.path.dirname(os.path.abspath(__file__)))
filenames = next(os.walk(os.path.dirname(os.path.abspath(__file__))), (None, None, []))[2]  # [] if no file
epsDic = {}
for fname in filenames:
    if fname[-3:] == 'jpg': 
        fnameSplitted = fname[:-4].split()
        epsDic[int(fnameSplitted[1])] = ' '.join(fnameSplitted[2:])

chaptersInDesc = "00:00 Ep 47 Project Raven\n"

for idx,res in enumerate(sRes):
    timeStamp = int(float(res.strip()))
    tsInHHMMSS = str(datetime.timedelta(seconds=timeStamp))
    wholeLine = f"{tsInHHMMSS} - Ep {idx+48} {epsDic[idx+48]} \n"
    chaptersInDesc += wholeLine

pyperclip.copy(chaptersInDesc)

