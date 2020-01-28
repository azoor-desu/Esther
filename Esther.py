import sys
import os
import textout
import processor
import pyaudio
import wave
import snowboydecoder

persona = "Esther"


class Esther(object):

    def __init__(this):
        this.interrupted = False;

    #Runs once on program startup.
    def setup(this):
        print ("\n-----Setting up!-----\n")
        this.pcs = processor.Processor()
        this.pcs.entities.setdefault("!persona",[persona.lower(),])
        this.p = pyaudio.PyAudio()
        print ("-----Setup Finished!-----\n")
        print ("------------------------")
        

    
    TOP_DIR = os.path.dirname(os.path.abspath(__file__))
    MODEL_FILE = os.path.join(TOP_DIR, "Esther.pmdl")
    #Main running loop for taking input and stuff.
    def run(this):

        detector = snowboydecoder.HotwordDetector("/home/pi/Esther/Esther.pmdl", sensitivity=0.5)
        print('Listening... Press Ctrl+C to exit')
        textout.EstherReply("Hello. I am " + persona + ". Call for me if you need anything!")

        # main loop, Passive Listening
        detector.start(detected_callback=this.ActiveListening,
               interrupt_check=this.interrupt_callback,
               sleep_time=0.03)
            
    def interrupt_callback(this):
        return this.interrupted

    def ActiveListening(this):
        threshold = None
        textout.SystemPrint("Started to listen actively")

        #RECORD A WAV FILE, CUTOFF AT 12s OR FALLS BELOW THRESHOLD
        #SEND TO WITAI
        #RECIEVE INPUT
        #SEND TO PROCESSOR AND RETURN INTENT
        #FIND ACTION.

        userInput = input('You: ')
        textout.SystemPrint("PESUDO-ACTIVELISTENING ENDED")
        intent = this.pcs.ProcessInput(userInput) #Returns: (intentName, [(entityType)]) OR NONE

        this.FindAction(intent)
        textout.SystemPrint("Stopped listening actively")

        print ("------------------------")
        print ("------------------------")
        textout.EstherReply("Call for me if you need anything!")

        

    def FindAction(this, intent): #Finds the relevant action module and runs it.
        if intent != None:
            for module in this.pcs.modules:
                if intent[0] in module.INTENTS:
                    module.handle(intent[0],intent[1])
                    break;
                if module == this.pcs.modules[len(this.pcs.modules) - 1]:
                    textout.SystemWarning("No module to handle this intent: " + intent[0])
                    textout.SystemWarning("Did you leave out writing this intent in a module?")
                    for module in this.pcs.modules:
                        if "unknown" in module.INTENTS:
                            module.handle("unknown",None)
        else: #if intent is NONE
            for module in this.pcs.modules:
                if "unknown" in module.INTENTS:
                    module.handle("unknown",None)
                    break;

app = Esther()

#Main Thread
if __name__ == "__main__":
    print ("*********************************************************")
    print ("**                                                     **")
    print ("**                ---PROJECT ESTHER---                 **")
    print ("**  Experimental Voice Assistant for the Raspberry Pi  **")
    print ("**                                                     **")
    print ("*********************************************************")
    app.setup()
    app.run() #Loop here.
    sys.exit()