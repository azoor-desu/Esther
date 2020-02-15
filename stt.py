import snowboydecoder
import os
import textout
import pyaudio
import audioop

TOP_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = os.path.join(TOP_DIR, "Esther.pmdl")

def PassiveListening(this, callback):
    def returnfalse(): #hack to remove need for interrupt lmao
        return False

    detector = snowboydecoder.HotwordDetector("/home/pi/Esther/resources/Esther.pmdl", sensitivity=0.5)
    # main loop, Passive Listening
    detector.start(detected_callback=callback,
           interrupt_check=returnfalse,
           sleep_time=0.03)
    textout.SystemPrint("Stopped listening passively, SHOULD NOT PRINT UNLESS PROGRAM STOPPED")

def ActiveListening(this):
    threshold = None
    textout.SystemPrint("Started to listen actively")
    #RECORD A WAV FILE, CUTOFF AT 12s OR FALLS BELOW THRESHOLD
    #SEND TO WITAI
    #RECIEVE INPUT
    #SEND TO PROCESSOR AND RETURN INTENT
    #FIND ACTION.

    p = pyaudio.PyAudio()
    stream_in_active = p.open(format=pyaudio.paInt16, channels=1,
                rate=16000, input=True,
                frames_per_buffer=1024)

    frames = []

    lastN = [144 * 1.2 for i in range(15)] #changing array length will determine if average will change faster or not

    for i in range(0, 187):

            data = stream_in_active.read(1024)
            frames.append(data)
            score = getScore(data)

            lastN.pop(0)
            lastN.append(score)
            average = sum(lastN) / float(len(lastN))
            print (str(average))

            if average < 144 - 20:
                textout.SystemPrint("Listening stopped, below threshold.")
                break

    textout.SystemPrint("Listening Timeout!")
    stream_in_active.stop_stream()
    stream_in_active.close()
    p.terminate()

    textout.SystemPrint("Stopped listening actively")

def getScore(data):
        rms = audioop.rms(data, 2)
        score = rms / 3
        return score

    
    