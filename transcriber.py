

def TranscribeAudiofile(this,audiofile):
    #Can be a universal method for multiple different systems (e.g. Julius, wit.ai etc)
    #For now, customize for wit.ai.
    #wit.ai also returns the intents and everything already, so we'll have to account for that.

    # Flow: Snowboy becomes active for keyword,
    # Keyword detected, snowboy stops, 12 sec/threshold recording starts
    # Clip recorded, send it to transcriber.py.
    # transcriber software returns a string.
    print ("lalalala")