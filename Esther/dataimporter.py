import os
import Esther
import json

#APP_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
TRAIN_PATH = "data/training.json"

class DataImporter():
    trainingdata = {}

    def PopulateOutlinesDict(this):
        print ("DataImporter: Loading Training Data...")
        this.PopulateTrainingData()
        print ("DataImporter: Finished loading Training Data")

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
        this.AddOutline("ask_day", ["what","day","is","it"],(1,2,1.5,1.5))
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
    # "phrase[0]" :
    #[("intentName", [phrases], [(phrasePosDiffAVG, phrasePosDiffSD)], [phraseWeight], slrAVG, slrSD)]
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
        phrasePosDiffAvgSd = [(0,0),] * len(phrases)

        if phrases[0] in this.outlines:
            this.outlines.get(phrases[0]).append((intentName, phrases, phrasePosDiffAvgSd, newPhraseWeight,0,0))
        else:
            this.outlines.setdefault(phrases[0],[]).append((intentName, phrases, phrasePosDiffAvgSd, newPhraseWeight,0,0))

    #loads existing json file into trainingdata dict
    def PopulateTrainingData(this):
        print ("DataImporter: Reading disk training data")
        if os.path.exists(TRAIN_PATH):
            with open (TRAIN_PATH,'r') as fp:
                this.trainingdata = json.load(fp)
            print ("DataImporter: Reading training data finished")
        else:
            print ("DataImporter: NOTICE! Disk training data is not found. Creating blank training data file.")
        print (str(this.trainingdata))

    # trainingdata structure:
    # "outline key":
    # [([phrasePosDiff], usrinputlength)]
    #Try to add data into the trainingdata dict, from processor.py when a match is found.
    def UpdateTrainingData(this, phrases, phrasePos, usrinputlength):        
        #need to convert: 
        #[phrases] >> _outlineKey (string)
        #[phrasePos] >> [phrasePosDiff]

        #need to convert [phrases] into one single string
        _outlineKey = ""
        for item in phrases:
            if _outlineKey != "":
                _outlineKey = _outlineKey + " " + item
            else:
                _outlineKey = item

        phrasePosDiff = [0,] * len(phrasePos)
        #need to convert [phrasePos] >> [phrasePosDiff]
        for i in range(1,len(phrasePos)): #index 0 is always value 0, so start loop from 1.
            phrasePosDiff[i] = phrasePos[i] - phrasePos[i-1]

        #Make _data
        _data = (phrasePosDiff,usrinputlength)

        #_data is in this format: ([phrasePosDiff], usrinputlength)
        if _outlineKey in this.trainingdata:
            if _data not in this.trainingdata[_outlineKey]: #Add data if OUTLINE exists and _data is not in dict yet
                this.trainingdata[_outlineKey].append(_data)
            else:
                print ("DataImporter/UpdateTrainingData(): Data already exists.")
        else:
            this.trainingdata.setdefault(_outlineKey,[]) #If key does not exist, create one and add the data to it.
            this.trainingdata[_outlineKey].append(_data)
        this.WriteTrainingData()

    def WriteTrainingData(this):
        print ("DataImporter: Writing training data")
        with open (TRAIN_PATH,'w') as fp:
            json.dump(this.trainingdata,fp, sort_keys=True)
        print ("DataImporter: Writing data completed.")