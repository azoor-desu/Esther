import os
import Esther
import json

#APP_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
cwd = os.getcwd()
TRAIN_PATH = os.path.join(cwd,"data","training.json")
INTENT_PATH = os.path.join(cwd,"data","intents")
SYNONYMS_PATH = "data/synonyms/"
ENTITIES_PATH = "data/entities/"

class DataImporter():
    # "outline key": [([phrasePosDiff], usrinputlength)]
    trainingdata = {}
    outlines = {}

    def PopulateOutlinesDict(this):
        print ("DataImporter: Loading Training Data...")
        this.PopulateTrainingData()
        print ("DataImporter: Finished loading Training Data")

        print ("DataImporter: Loading intent outlines from disk...")

        if os.path.exists(INTENT_PATH):
            fileDirectories = filter(lambda x: x[-4:] == '.txt', os.listdir(INTENT_PATH))
            for filename in fileDirectories:
                #strip and split ReadTxtFile at the same time.
                intentTextArray = [x.strip() for x in this.ReadTxtFile(os.path.join(INTENT_PATH,filename)).split('\n')]
                #Shovel each line of intentText into an outline entry
                for outlineRaw in intentTextArray:
                    phrases = [x.strip() for x in outlineRaw.split(' ')]
                    phraseWeight =[]
                    phrasesCleaned=[] #add version without the [] at the back of the phrase
                    #add phraseweight
                    for phrase in phrases:
                        if '[' in phrase and ']' in phrase:
                            #split the string by [ and ], by replacing ] with [, then split all by ['s
                            phraseSplit = phrase.replace(']','[').split('[')
                            number = phraseSplit[1]
                            phrasesCleaned.append(phraseSplit[0]) #add version without the [] at the back of the phrase
                            phraseWeight.append(float(number))
                        else:
                            #No [x] number found, putting default phraseweight as 1
                            phraseWeight.append(1)
                            phrasesCleaned.append(phrase)
                    this.AddOutline(filename,phrasesCleaned,phraseWeight)
                    print ("Adding outline intentname: " + filename)
                    print ("Adding outline phrases: " + str(phrases))
                    print ("Adding outline phraseWeight: " + str(phraseWeight))
            print ("DataImporter: Reading intent outlines data finished")
        else:
            print ("DataImporter: WARNING! Disk intent outlines folder is not found. Not loading any outlines!")
        return this.outlines

    def ReadTxtFile(this, filepath):
        with open(filepath, 'r') as fd:
            stringg = fd.read()
        return stringg

    def isNumber(s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def AddOutline (this, intentName, phrases, phraseWeight):
    #outline structure
    # "phrase[0]" :
    #[("intentName", [phrases], [(phrasePosDiffAVG, phrasePosDiffSD)], [phraseWeight], slrAVG, slrSD)]

        #CONVERSION OF PHRASEWEIGHT
        #phraseWeight is in [1,1,2,1] format, need to convert such that they all add up to 1.
        totalWeightRaw = 0
        newPhraseWeight = [0,] * len(phraseWeight)
        for rawWeight in phraseWeight:
            totalWeightRaw += rawWeight #get sum of all weights
        for i in range(0,len(phraseWeight)):
            newPhraseWeight[i] = (phraseWeight[i] / totalWeightRaw) #set new value into each tuple.

        #Assigning AVG and SD values for SLR and phrasePosDiff
        #combine phrases so can search trainingdata dict
        trainingdatakey = this.CombineStringsList(phrases)

        #search for outline in trainingdata.
        if (trainingdatakey in this.trainingdata and len(this.trainingdata[trainingdatakey]) > 3): #make sure there is at least 3 examples.

            #Getting phrasePosDiffAvgSd

            #When looping through trainingdata, get all the index 0s of each trainingdata item into one list, index 1s into another etc
            #Basically change so that each 
            #trainingdata[0] >> 1, 2, 3 | trainingdata[1] >> 4, 5, 6 | trainingdata[2] >> 7, 8, 9
            #becomes:
            #phraseLists[0] >> 1, 4, 7 | phrasePosDiff[1] >>2, 5, 8 | phrasePosDiff[2] >> 3, 6, 9
            phraseLists = []
            for i in range(0, len(phrases)):
                phraseValues = []

                for item in this.trainingdata[trainingdatakey]:
                    phraseValues.append(item[0][i])

                phraseLists.append(phraseValues)
            print ("PHRASELISTS: " + str(phraseLists))

            phrasePosDiffAvgSd = []
            for item in phraseLists:
                phrasePosDiffAvgSd.append((this.GetAvgOfList(item), this.GetSDOfList(item)))
            print ("\n\n" + str(phrasePosDiffAvgSd) + "\n\n")
            #Getting slrAVG and slrSD
            #Create list with all the slr values
            slr = []
            for trainingdatavalues in this.trainingdata[trainingdatakey]:
                slr.append(this.GetSumOfList(trainingdatavalues[0]) / trainingdatavalues[1])

            if phrases[0] in this.outlines:
                this.outlines.get(phrases[0]).append((intentName, phrases, phrasePosDiffAvgSd, newPhraseWeight,this.GetAvgOfList(slr),this.GetSDOfList(slr)))
            else:
                this.outlines.setdefault(phrases[0],[]).append((intentName, phrases, phrasePosDiffAvgSd, newPhraseWeight,this.GetAvgOfList(slr),this.GetSDOfList(slr)))

            return #Below won't run. Don't generate default blank values.

        #if above if conditions are not fufiled, need to generate default AVG SD values.
        #GENERATING DEFAULT SD and AVG values
        if phrases[0] in this.outlines:
            this.outlines.get(phrases[0]).append((intentName, phrases, [(0,0),] * len(phrases), newPhraseWeight,-1,-1))
        else:
            this.outlines.setdefault(phrases[0],[]).append((intentName, phrases, [(0,0),] * len(phrases), newPhraseWeight,-1,-1))

    #loads existing json file into trainingdata dict
    def PopulateTrainingData(this):
        print ("DataImporter: Reading disk training data")
        if os.path.exists(TRAIN_PATH):
            with open (TRAIN_PATH,'r') as fp:
                this.trainingdata = json.load(fp)
            print ("DataImporter: Reading training data finished")
        else:
            print ("DataImporter: NOTICE! Disk training data is not found. Creating blank training data file.")
        #print (str(this.trainingdata))

    def UpdateTrainingData(this, phrases, phrasePos, usrinputlength):
    # trainingdata structure:
    # "outline key":
    # [([phrasePosDiff], usrinputlength)]
    #Try to add data into the trainingdata dict, from processor.py when a match is found.

        #need to convert: 
        #[phrases] >> _outlineKey (string)
        #[phrasePos] >> [phrasePosDiff]

        #need to convert [phrases] into one single string
        _outlineKey = this.CombineStringsList(phrases)

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

    def CombineStringsList(this, inputlist):
        combined = ""
        for item in inputlist:
            if combined != "":
                combined = combined + " " + item
            else:
                combined = item
        return combined

    def GetSumOfList (this, inputlist):
        sum = 0
        for item in inputlist:
            sum = sum + item
        return sum

    def GetAvgOfList(this, inputlist):
        return (this.GetSumOfList(inputlist) / len(inputlist))

    def GetSDOfList(this, inputlist):
        avg = this.GetAvgOfList(inputlist)
        sd = 0
        if avg != 0:
            for item in inputlist:
                sd = sd + ((item - avg)*(item - avg))
            sd = sd / (len(inputlist)  - 1)
            import math
            return math.sqrt(sd)
        else:
            return 1 #if the average is 0, sd should be 0 also (ignoring the fact that the formula cannot handle 0)
            #BUT, if SD is less than 1, the penalty would be too great cos the minimum words away would be 1.
            #SO, cap SD at 1.

    def BackupOutlines():
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