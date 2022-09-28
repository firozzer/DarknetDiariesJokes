import requests, re, time, subprocess
from bs4 import BeautifulSoup

urlPattern = """https://.{10,90}mp3"""

with open("urls.txt") as f:
    mp3Links = f.read()

mp3Links = mp3Links.split()

# following to down mp3s``
for idx,link in enumerate(mp3Links[::-1]):
    epNo = idx+1
    if epNo < 122:
        continue
    print(f"Downloading ep no {epNo}    ", end="\r")
    r = requests.get(link)
    with open(f"{epNo}.mp3", 'wb') as f:
        f.write(r.content)

# mp3Links = []

# for epNo in range(124,0,-1):
#     r = requests.get(f"https://darknetdiaries.com/episode/{epNo}/")
#     mp3Link = re.search(urlPattern, str(r.content))
#     mp3Link =mp3Link[0]
#     mp3Links.append(mp3Link)
#     time.sleep(2)
#     print(f"Got Ep No: {epNo}", end="\r")

# # folwg is to grab artwork
# r = requests.get("https://darknetdiaries.com/episode/")
# soup = BeautifulSoup(r.content)
# titleElems = soup.find_all('h2', class_="post__title")
# titleNames = []
# for tit in titleElems:
#     titleNames.append(tit.text)

# photoElems = soup.find_all('div', class_="post__image")
# photoURLs = []
# for photo in photoElems:
#     photoURLs.append("https://darknetdiaries.com" + photo['style'][22:-1])

# for idx,title in enumerate(titleNames):
#     img_data = requests.get(photoURLs[idx]).content
#     with open(f"{title.replace(':', '')}.jpg", 'wb') as handler:
#         handler.write(img_data)
#     print(f'saved {title}, {len(titleNames)-idx} to go')