import sys
import os
import textout
import processor
import pyaudio
import wave

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
        textout.EstherReply("Hello. I am " + persona + ". How may I be of service?")

        CHUNK = 1024
        #RES_PATH = os.path.join(os.getcwd(), "data\\resources\\beep_hi.wav")
        RES_PATH = "/home/pi/Esther/Esther/data/resources/beep_hi.wav"
        wf = wave.open(RES_PATH, 'rb')
        stream = this.p.open(format=this.p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True)
        data = wf.readframes(CHUNK)
        while len(data) > 0:
            stream.write(data)
            data = wf.readframes(CHUNK)
        stream.stop_stream()
        stream.close()
        this.p.terminate()
    
    #Main running loop for taking input and stuff.
    def run(this):
        while True:
            userInput = input('You: ')

            intent = this.pcs.ProcessInput(userInput) #Returns: (intentName, [(entityType)]) OR NONE
            this.FindAction(intent)
          

            print ("------------------------")
            print ("------------------------")
            textout.EstherReply("What can I do for you?")

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