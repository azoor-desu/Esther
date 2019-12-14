import sys
import textout
import processor

persona = "Esther"

class Esther(object):
    
    #Runs once on program startup.
    def setup(this):
        print ("\n-----Setting up!-----\n")
        this.pcs = processor.Processor()
        print ("-----Setup Finished!-----\n")
        print ("------------------------")
        textout.EstherReply("Hello. I am " + persona + ". How may I be of service?")
    
    #Main running loop for taking input and stuff.
    def run(self):
        while True:
            userInput = input('You: ')

            self.pcs.ProcessInput(userInput)

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