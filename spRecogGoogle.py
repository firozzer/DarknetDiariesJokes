import os, subprocess, json
from google.cloud import speech

def getTimestampsFromGoogle(latestEpNo, roughCut):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    client = speech.SpeechClient.from_service_account_file("googleSAfrzecoolKey.json")

    filename = f"{latestEpNo}c.flac"
    audio = speech.RecognitionAudio(uri=f"gs://drknt_drs_audio_hodler/{filename}")
    speech_context = speech.SpeechContext(phrases=["this is darknet diaries", "break master cylinder"],boost=5) # provide what you're looking for here

    config = speech.RecognitionConfig(
        enable_word_time_offsets=1,
        language_code="en-US",
        speech_contexts = [speech_context]
    )

    # check STT usage secs if beyond free quota then exit
    with open('info.json') as f: jsonData = json.load(f)
    gglSTTUsageSecs = jsonData['GoogleSTTUsageSecs']
    if gglSTTUsageSecs > 3400: # only 3600 secs pm free
        print("Used up my quota of Google STT API. Exitting.")
        exit()

    # i think next line execution is complete once upload is done. Then an identifier is used in next line to obtain results (which may take time if file is long). 
    print(f"Google STT obtaining {filename} from GCS...")
    operation = client.long_running_recognize(config=config, audio=audio)
    print("Done. Now, awaiting results...")
    response = operation.result(timeout=240) 
    print("Results recvd.")
    
    # update STT secs usage in info.json. Rmmbr Ggle rounds off to increments of 15.
    jsonData['GoogleSTTUsageSecs'] += response.total_billed_time.total_seconds()
    with open("info.json", "w") as f:
        json.dump(jsonData, f)

    stuffToWriteToFile = f"\n\nEp No {str(latestEpNo)}" + '\n' + str(response.results)
    with open("gsttResults.txt", "a") as f:
        f.write(stuffToWriteToFile)

    cutStartObtained = False
    for result in response.results:
        stuffFound = result.alternatives[0].transcript.lower()
        if 'cylinder' in stuffFound and 'master' in stuffFound and not cutStartObtained:
            for wordData in result.alternatives[0].words:
                zeWord = wordData.word.lower()
                if zeWord == 'cylinder': 
                    print(wordData)
                    cutStart = float(str(wordData.end_time.seconds) + '.'+ str(wordData.end_time.microseconds)[:2]) + 0.2
                    cutStartObtained = True
                    print("So, start cutting at", cutStart)
                    break
        if cutStartObtained and ('diaries' in stuffFound or 'diary' in stuffFound or 'fairies' in stuffFound or 'fairy' in stuffFound):
            for wordData in result.alternatives[0].words:
                zeWord = wordData.word.lower()
                if zeWord == 'diary' or zeWord == "diaries" or zeWord == 'fairy' or zeWord == "fairies":
                    print(wordData)
                    cutEnd = float(str(wordData.end_time.seconds) + '.'+ str(wordData.end_time.microseconds)[:2]) + 2
                    if cutStart > cutEnd:
                        print('cutEnd before cutStart, so incorrect. Continuing checking.')
                    else:
                        print("And, stop cutting at", cutEnd)
                        break
    epDuration = float(subprocess.check_output(f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {latestEpNo}.mp3", shell=True).decode('utf-8').strip()[:-4])
    cutStart =  round(epDuration - roughCut + cutStart, 2)
    cutEnd = round(epDuration - roughCut + cutEnd, 2)
    with open('timestamps.txt', 'a') as f:
        f.write(f"{latestEpNo} {cutStart} {cutEnd}\n")
    return cutStart, cutEnd
