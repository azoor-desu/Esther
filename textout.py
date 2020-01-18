import __main__ as esther

mute=True

def Print(output):
    if not mute:
        print (output)

def EstherReply(output):
    print (esther.persona + ": " + output)
    
def SystemPrint(output):
        print ("System: " + output)

def SystemWarning(output):
    print ("WARNING: " + output)
    
def SystemError(output):
    print ("ERROR: " + output)