import subprocess, os, json, wave

from vosk import Model, KaldiRecognizer

os.chdir(os.path.dirname(os.path.abspath(__file__)))
filenames = next(os.walk(os.path.dirname(os.path.abspath(__file__))), (None, None, []))[2]  # [] if no file

# cutting full ep to just ending few secs
roughCut = 90
# for fname in filenames:
#     if fname[-3:] != "mp3":
#         continue
#     # RETAIN EXPLICIT MENTION OF '-ac 1" audio channel 1, i think Vosk ets prob otherwise in recgnzin
#     subprocess.run(f"ffmpeg -y -sseof -{roughCut} -i {fname} -ac 1 {fname[:-4]}c.wav", shell=True)

model = Model(r"C:\Users\firoz\Desktop\darknetDiaries\vosk-model-en-us-0.22\vosk-model-en-us-0.22")
print('loaded succ')

# this is vosk speech recognition bit
for fname in filenames:
    cutStart, cutEnd = False, False
    if fname[-3:] != "wav":
        continue
    print('\ndoing', fname)
    if os.path.isfile(f"{fname[:-5]}f.mp3"):
        print('Already done, conitniuing')
        continue

    wf = wave.open(fname, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)
    cutStartObtained = False
    while True:
        # this frames cutting is problematic. 20% of times it cuts on the word you're looking for & hence hardocded if check later on fails.
        data = wf.readframes(6000)

        if len(data) == 0:
            print('breaking premature, means TSs not obtained.')
            break
        if rec.AcceptWaveform(data):
            result_dict = json.loads(rec.Result())
            print(result_dict['text'])
            recogResults = result_dict.get("text", "")
            if not cutStartObtained:
                if ('cylinder' in recogResults or 'islander' in recogResults) and 'master' in recogResults:
                    for res in result_dict['result']:
                        if res['word'] == 'cylinder' or res['word'] == 'islander':
                            print(res)
                            cutStart = res['end'] + 0.20
                            print("Start cutting at: ", cutStart)
                            cutStartObtained = True
            if cutStartObtained:
                if 'diaries' in recogResults or 'diary' in recogResults or 'die' in recogResults or 'dice' in recogResults:
                    for res in result_dict['result']:
                        if res['word'] == 'diaries' or res['word'] == 'dies' or res['word'] == 'diary' or res['word'] == 'die' or res['word'] == 'dies' or res['word'] == 'dice':
                            print(res)
                            cutEnd = res['end'] + 2
                            print("End cutting at: ", cutEnd)
                            print('breaking from inside')
                            break
                    if cutStart > cutEnd: print('cutEnd before cutStart, so incorrect. Continuing checking.')
                    else: break
    if cutStart:
        epDuration = float(subprocess.check_output(f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {fname[:-5]}.mp3").decode('utf-8').strip()[:-4])
        cutStart =  round(epDuration - roughCut + cutStart, 2)
        cutEnd = round(epDuration - roughCut + cutEnd, 2)
        with open('timestamps.txt', 'a') as f:
            f.write(f"{fname[:-5]} {cutStart} {cutEnd}\n")

        subprocess.run(f"ffmpeg -y -ss {cutStart} -to {cutEnd} -i {fname[:-5]}.mp3 -c copy {fname[:-5]}f.mp3", shell=True)