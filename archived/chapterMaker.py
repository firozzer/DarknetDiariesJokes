import re, pyperclip, datetime, os

# ffmpeg code to create ffout.txt asf:
# ffmpeg -i ytVidNew.mkv  -filter:v "select='gt(scene,0.2)',showinfo" -f null - 2> ffout.txt

with open("ffout.txt") as f:
    data = f.read()

sRes = re.findall("pts_time:(.+)pos:", data)

# making a dic of ep nos & names from the gathered jpgs
os.chdir(os.path.dirname(os.path.abspath(__file__)))
filenames = next(os.walk(os.path.dirname(os.path.abspath(__file__))), (None, None, []))[2]  # [] if no file
epNoAndNamesDic = {}
for fname in filenames:
    if fname[-3:] == 'jpg': 
        fnameSplitted = fname[:-4].split()
        epNoAndNamesDic[int(fnameSplitted[1])] = ' '.join(fnameSplitted[2:])

chaptersInDesc = "0:00:00 - Ep 47 Project Raven\n"

for idx,res in enumerate(sRes):
    timeStamp = int(float(res.strip()))
    tsInHHMMSS = str(datetime.timedelta(seconds=timeStamp))
    wholeLine = f"{tsInHHMMSS} - Ep {idx+48} {epNoAndNamesDic[idx+48]} \n"
    chaptersInDesc += wholeLine

pyperclip.copy(chaptersInDesc)