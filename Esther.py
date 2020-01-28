import sys
import os
import textout
import processor
import pyaudio
import wave
import stt

persona = "Esther"

class Esther(object):

    #Runs once on program startup.
    def setup(this):
        print ("\n-----Setting up!-----\n")
        this.pcs = processor.Processor()
        this.pcs.entities.setdefault("!persona",[persona.lower(),])
        this.p = pyaudio.PyAudio()
        print ("-----Setup Finished!-----\n")
        print ("------------------------")
        
    #Main running loop for taking input and stuff.
    def run(this):

        textout.EstherReply("Hello. I am " + persona + ". Call for me if you need anything!")
        stt.PassiveListening(this,stt.ActiveListening)

    def ProcessTranscribed(this,input):
        
        intent = this.pcs.ProcessInput(input) #Returns: (intentName, [(entityType)]) OR NONE
        this.FindAction(intent)

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