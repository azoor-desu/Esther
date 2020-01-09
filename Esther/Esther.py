import sys
import textout
import processor

persona = "Esther"

class Esther(object):
    
    #Runs once on program startup.
    def setup(this):
        print ("\n-----Setting up!-----\n")
        this.pcs = processor.Processor()
        this.pcs.entities.setdefault("!persona",[persona.lower(),])
        print ("-----Setup Finished!-----\n")
        print ("------------------------")
        textout.EstherReply("Hello. I am " + persona + ". How may I be of service?")
    
    #Main running loop for taking input and stuff.
    def run(this):
        while True:
            userInput = input('You: ')

            intent = this.pcs.ProcessInput(userInput) #Returns: (intentName, [(entityType)]) OR NONE

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

            print ("------------------------")
            print ("------------------------")
            textout.EstherReply("What can I do for you?")

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