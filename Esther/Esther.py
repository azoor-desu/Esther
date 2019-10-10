import sys
from utilities import textout
from utilities import processor

persona = "Esther"

class Esther(object):
    
    #Runs once on program startup.
    def setup(self):
        print ("\n-----Setting up!-----")
        self.pcs = processor.Processor()
        print ("-----Setup Finished!-----\n")
        print ("------------------------")
        textout.EstherReply("Hello. I am " + persona + ". How may I be of service?")
    
    #Main running loop for taking input and stuff.
    def run(self):
        while 0==0:
            userInput = input('You: ')
            self.pcs.ProcessInput(userInput)
            print ("------------------------\n")
            print ("------------------------")
            textout.EstherReply("What can I do for you?")

app = Esther()

#Main Thread
if __name__ == "__main__":
    print ("*******************************************************")
    print ("*                ---PROJECT ESTHER---                 *")
    print ("*         Experimental AI automated assistant         *")
    print ("*******************************************************")
    app.setup()
    app.run() #Loop here.
    sys.exit()