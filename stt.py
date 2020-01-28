import snowboydecoder
import os
import textout

TOP_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = os.path.join(TOP_DIR, "Esther.pmdl")

def PassiveListening(this, callback):
    def returnfalse(): #hack to remove need for interrupt lmao
        return False

    detector = snowboydecoder.HotwordDetector("/home/pi/Esther/resources/Esther.pmdl", sensitivity=0.5)
    textout.SystemPrint("Started to listen passively")
    # main loop, Passive Listening
    detector.start(detected_callback=callback,
           interrupt_check=returnfalse,
           sleep_time=0.03)
    textout.SystemPrint("Stopped listening passively, SHOULD NOT PRINT UNLESS STOP PROGRAM")

def ActiveListening(this):
    threshold = None
    textout.SystemPrint("Started to listen actively")
    #RECORD A WAV FILE, CUTOFF AT 12s OR FALLS BELOW THRESHOLD
    #SEND TO WITAI
    #RECIEVE INPUT
    #SEND TO PROCESSOR AND RETURN INTENT
    #FIND ACTION.
    userInput = input('You: ')
    textout.SystemPrint("Stopped listening actively")
    
    