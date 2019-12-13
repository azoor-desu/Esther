import os
import Esther

APP_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
DATA_PATH = os.path.join(APP_PATH, "data")
TRAIN_PATH = os.path.join(DATA_PATH, "training.json")
DATA_PATH = os.path.join(DATA_PATH, "intents")

class DataImporter():

    def PopulateOutlinesDict(this):
        print ("DataImporter: Loading intent outlines from disk...")
        #DO LOADING. Load each txt file.
        #Sort data into the format below.
        #For each outline, search the trainingdata for e.g. "what time" as a key.
        #If key is found, calculate the relevant data and plonk it into AddOutline. If not, default values.
        #Plonk in phraseWeight data along as well.

        this.outlines = {}

        this.AddOutline("ask_time", ["what","time"],(1,2))
        this.AddOutline("ask_time", ["give","time"],(1,2))
        this.AddOutline("ask_time", ["tell","me","time"],(1,1,2))
        this.AddOutline("ask_time", ["need","time"],(1,2))
        this.AddOutline("ask_time", ["do","know","time"],(1,1,2))
        this.AddOutline("ask_time", ["have","current","time"],(1,1,2))

        this.AddOutline("ask_if_faggot", ("are","you","faggot"),(0.1,0.2,2))
        this.AddOutline("ask_if_faggot", ("hello","you","faggot"),(0.5,0.2,2))

        this.AddOutline("ask_day", ["what","day","!daysrelative"],(1,2,2))
        this.AddOutline("ask_day", ["give","me","day","!daysrelative"],(1,1,2,2))
        this.AddOutline("ask_day", ["tell","me","day","!daysrelative"],(1,1,2,2))
        this.AddOutline("ask_day", ["need","day","!daysrelative"],(1,2,2))

        this.AddOutline("ask_date", ["what","date","!daysrelative"],(1,2,2))
        this.AddOutline("ask_date", ["give","me","date","!daysrelative"],(1,1,2,2))
        this.AddOutline("ask_date", ["tell","me","date","!daysrelative"],(1,1,2,2))
        this.AddOutline("ask_date", ["need","date","!daysrelative"],(1,2,2))

        this.AddOutline("ask_date", ["what","date","is","!days"],(1,2,1,2))
        this.AddOutline("ask_date", ["what","date","on","!days"],(1,2,1,2))
        this.AddOutline("ask_date", ["give","me","date","!days"],(1,1,2,2))
        this.AddOutline("ask_date", ["need","date","!days"],(1,2,2))

        this.AddOutline("ask_date_day", ["need","date","!daysrelative","!days"],(1,2,2,2))

        return this.outlines

    #outline structure
    # "phrase[0]" : [
    #("intentName", [phrases], [(phrasePosDiffAVG, phrasePosDiffSD)], [phraseWeight], slrAVG, slrSD), etc... <<Replaced distmod with the tuple, added slrSD and slrAVG at the end. No change in exisitng pos.
    # ] 
    def AddOutline (this, intentName, phrases, phraseWeight):

        #CONVERSION OF PHRASEWEIGHT
        #phraseWeight is in [1,1,2,1] format, need to convert such that they all add up to 1.
        totalWeightRaw = 0
        newPhraseWeight = [0,] * len(phraseWeight)
        for rawWeight in phraseWeight:
            totalWeightRaw += rawWeight #get sum of all weights
        for i in range(0,len(phraseWeight)):
            newPhraseWeight[i] = (phraseWeight[i] / totalWeightRaw) #set new value into each tuple.

        #GENERATING DEFAULT SD and AVG values
        distMod = [(0,0),] * len(phrases)

        if phrases[0] in this.outlines:
            this.outlines.get(phrases[0]).append((intentName, phrases, distMod, newPhraseWeight,0,0))
        else:
            this.outlines.setdefault(phrases[0],[]).append((intentName, phrases, distMod, newPhraseWeight,0,0))