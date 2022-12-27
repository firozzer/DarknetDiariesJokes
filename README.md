# DarknetDiariesJokes

Check out all the jokes here: https://www.youtube.com/watch?v=LfZgLPnjEGI

This is a script that runs regularly to check if a new DD ep is out, & if yes, then the latest joke is appended to YouTube video.

# tldr: 
Grab latest ep mp3 from DD website, feed into Google STT to obtain exact joke timestamps, use ffmpeg to cut out joke, append to prev YT vid & re-upload.

# tswm:
`main.py` is the script start point, gets called by cron every 15 mins to check if a new ep has come out. If it has, new ep name, mp3 & artwork are downloaded. Next using ffmpeg the final 90 secs are cut out and uploaded to Google Cloud Storage. Next `spRecogGoogle.py` gets called which takes the file from GCS & feeds it into Google Speech To Text API. Once results are recvd from STT API, the exact cut start & cut end timestamps for the joke are identified & returned back to `main.py` where ffmpeg cuts out the exact joke audio. Next `imgPrsg.py` gets called which using `Pillow` library, takes the artwork, makes it fit the pre-defined resolution, adds ep name as overlay on the artwork & returns to `main.py`. Next ffmpeg joins the mp3 & jpg to make an mkv of the latest joke, which is then appended to the previosly made video. Final video (alongwith timestamped description) is handed over to YouTube API for the upload. The script finals up with updating this very `README.md` with the latest YT vid URL + deleting prev YT video + cleaning up all the temp files.

The `archived` folder contains files which were used earlier in the dev stage, including `speech recog using vosk.py` which I had originally planned to use for local STT faciliation. However had to cancel this as my server's 1 GB RAM was too little for it lol. `chapterMaker.py` is another file in there which contains a really cool ffmpeg command which auto-detects scene changes in videos. Used this inititally to instantly obtain the YouTube chapters/timestamps from Eps 47 till 124. This joke tradition Jack started from Ep 47 onwards, hence no eps appear before that.

Started building on 23rd Sep 2022, writing this on 5th Oct 2022.
