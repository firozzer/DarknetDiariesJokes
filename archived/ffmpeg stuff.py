import subprocess, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open('jokes.txt') as f:
    jokes = f.read()

jokes = jokes.split('\n')

for joke in jokes:
    epNo, start, end = joke.split()
    subprocess.run(f"ffmpeg -ss {start} -to {end} -i {epNo}.mp3 -c copy j{epNo}.mp3",shell=True)

# add photo to indiv files, then concat
for fileNo in range(110, 121):
    print(subprocess.run(f"ffmpeg -loop 1 -framerate 5 -i j{fileNo}.jpg -i f{fileNo}.wav -shortest -acodec copy -vcodec mjpeg j{fileNo}.mkv", shell=True))

subprocess.run("ffmpeg -f concat -i input.txt -c copy yolo.mkv", shell=True)
print("joined all.")

# crop videos
# for fileNo in range(47, 51):
#     subprocess.run(f"""ffmpeg -i j{fileNo}.mkv -filter:v "crop=640:640" jc{fileNo}.mkv""",shell=True)
#     break