import os
import Esther
import json
import textout

#APP_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
cwd = os.getcwd()
TRAIN_PATH = os.path.join(cwd,"data","training.json")
INTENT_PATH = os.path.join(cwd,"data","intents")
SYNONYMS_PATH = os.path.join(cwd,"data","synonyms")
ENTITIES_PATH = os.path.join(cwd,"data","entities")

class DataImporter():
    trainingdata = {}
    outlines = {}

    #--------------------TRAINING DATA--------------------------
    # "outline key": [([phrasePosDiff], usrinputlength)]

    #loads existing json file into trainingdata dict
    def PopulateTrainingData(this):
        textout.SystemPrint ("DataImporter: Loading Training Data...")
        
        textout.SystemPrint ("DataImporter: Reading disk training data")
        if os.path.exists(TRAIN_PATH):
            with open (TRAIN_PATH,'r') as fp:
                this.trainingdata = json.load(fp)
            textout.SystemPrint ("DataImporter: Training data loaded!")
        else:
            textout.SystemPrint ("DataImporter: NOTICE! Disk training data is not found. Creating blank training data file.")

    def UpdateTrainingData(this, phrases, phrasePos, usrinputlength, outlines):
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
        _data = [phrasePosDiff,usrinputlength]

        #_data is in this format: ([phrasePosDiff], usrinputlength)
        if _outlineKey in this.trainingdata:
            if _data not in this.trainingdata[_outlineKey]: #Add data if OUTLINE exists and _data is not in dict yet
                textout.SystemPrint ("DataImporter/UpdateTrainingData(): Data does not exist, adding!")
                this.trainingdata[_outlineKey].append(_data)
                this.WriteTrainingData()
                this.UpdateOutlinesWithTrainingData(outlines)
            else:
                textout.SystemPrint ("DataImporter/UpdateTrainingData(): Data already exists.")
        else:
            textout.SystemPrint ("DataImporter/UpdateTrainingData(): Data does not exist, adding!")
            this.trainingdata.setdefault(_outlineKey,[]) #If key does not exist, create one and add the data to it.
            this.trainingdata[_outlineKey].append(_data)
            this.WriteTrainingData()
            this.UpdateOutlinesWithTrainingData(outlines)
        
    def WriteTrainingData(this):
        textout.SystemPrint ("DataImporter: Writing training data")
        with open (TRAIN_PATH,'w') as fp:
            json.dump(this.trainingdata,fp, sort_keys=True)
        textout.SystemPrint ("DataImporter: Writing data completed.")

    #-------------------------OUTLINES---------------------------
    # "phrase[0]" : [("intentName", [phrases], [(phrasePosDiffAVG, phrasePosDiffSD)], [phraseWeight], slrAVG, slrSD)]

    #REQUIRES TRAINING DATA TO BE LOADED FIRST.
    def PopulateOutlinesDict(this):

        textout.SystemPrint ("DataImporter: Loading intent outlines from disk...")

        if os.path.exists(INTENT_PATH):
            fileDirectories = filter(lambda x: x[-4:] == '.txt', os.listdir(INTENT_PATH))
            for filename in fileDirectories:
                #strip and split ReadTxtFile at the same time.
                intentTextArray = [x.strip().lower() for x in this.ReadTxtFile(os.path.join(INTENT_PATH,filename)).split('\n')]
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
                    this.AddOutline(filename.replace(".txt",""),phrasesCleaned,phraseWeight)
            textout.SystemPrint ("DataImporter: Intent outlines loaded!")
        else:
            textout.SystemWarning ("DataImporter: WARNING! Intent outlines folder is not found. Not loading any outlines!")
        return this.outlines

    def ReadTxtFile(this, filepath):
        with open(filepath, 'r') as fd:
            stringg = fd.read()
        return stringg

    #REQUIRES TRAINING DATA TO BE LOADED FIRST.
    def AddOutline (this, intentName, phrases, phraseWeight):

        newPhraseWeight = this.ConvertPhraseWeight(phraseWeight)

        #Assigning AVG and SD values for SLR and phrasePosDiff
        #combine phrases so can search trainingdata dict
        trainingdatakey = this.CombineStringsList(phrases)

        #search for outline in trainingdata.
        if (trainingdatakey in this.trainingdata and len(this.trainingdata[trainingdatakey]) > 3): #make sure there is at least 3 examples.

            phrasePosDiffAvgSd = this.GetPhrasePosDiffAvgSdFromTrainingData(trainingdatakey)
            slr = this.GetSLRFromTrainingData(trainingdatakey)

            #add to outlines
            if phrases[0] in this.outlines:
                this.outlines.get(phrases[0]).append((intentName, phrases, phrasePosDiffAvgSd, newPhraseWeight,this.GetAvgOfList(slr),this.GetSDOfList(slr)))
            else:
                this.outlines.setdefault(phrases[0],[]).append((intentName, phrases, phrasePosDiffAvgSd, newPhraseWeight,this.GetAvgOfList(slr),this.GetSDOfList(slr)))

        else:
            #if above if conditions are not fufiled, need to generate default AVG SD values.
            #GENERATING DEFAULT SD and AVG values for both slr and phrasePos
            if phrases[0] in this.outlines:
                this.outlines.get(phrases[0]).append((intentName, phrases, [(0,0),] * len(phrases), newPhraseWeight,-1,-1))
            else:
                this.outlines.setdefault(phrases[0],[]).append((intentName, phrases, [(0,0),] * len(phrases), newPhraseWeight,-1,-1))

    def UpdateOutlinesWithTrainingData(this, outlines):
        #Things to change in nestedOutlines: [phrasePosDiffAvgSd] (index 2), slrAVG (index 4), slrSD (index 5)
        #Run through all training data entries, find corresponding nestedOutline, and re-write that nestedOutline.
        newOutline = outlines
        for key, value in this.trainingdata.items():
            #Find the nestedOutline from outlines.
            if len(this.trainingdata[key]) > 3:
                phrases = key.split(' ')
                for i in range(0,len(outlines[phrases[0]])):
                    if phrases in outlines[phrases[0]][i]:
                        #Edit nestedoutline
                        slr = this.GetSLRFromTrainingData(key)
                        newOutline[phrases[0]][i] = (newOutline[phrases[0]][i][0], newOutline[phrases[0]][i][1], this.GetPhrasePosDiffAvgSdFromTrainingData(key), newOutline[phrases[0]][i][3],this.GetAvgOfList(slr),this.GetSDOfList(slr))
        return this.outlines

    #------------------------SYNONYMS & ENTITIES IMPORTING----------------------------
    def PopulateSynonymsDict(this):
        synonyms = {}
        textout.SystemPrint ("DataImporter: Loading synonyms from disk...")

        if os.path.exists(SYNONYMS_PATH):
            fileDirectories = filter(lambda x: x[-4:] == '.txt', os.listdir(SYNONYMS_PATH))
            for filename in fileDirectories:
                #strip and split ReadTxtFile at the same time.
                synonymTextArray = [x.strip().lower() for x in this.ReadTxtFile(os.path.join(SYNONYMS_PATH,filename)).split('\n')]
                #Shovel each line of synonymTextArray into a dict entry
                for dictEntry in synonymTextArray:
                    phrases = [x.strip() for x in dictEntry.split(':')]
                    synonyms.setdefault(phrases[0],phrases[1])
            textout.SystemPrint ("DataImporter: Synonyms data loaded")
        else:
            textout.SystemWarning ("DataImporter: WARNING! Synonyms folder is not found. Not loading any synonyms!")
        return synonyms

    def PopulateEntitiesDict(this):
        entities = {}
        textout.SystemPrint ("DataImporter: Loading entities from disk...")

        if os.path.exists(INTENT_PATH):
            fileDirectories = filter(lambda x: x[-4:] == '.txt', os.listdir(ENTITIES_PATH))
            for filename in fileDirectories:
                #strip and split ReadTxtFile at the same time.
                entitiesTextArray = [x.strip().lower() for x in this.ReadTxtFile(os.path.join(ENTITIES_PATH,filename)).split('\n')]
                entityRequest = "!" + filename.replace(".txt","")
                entities.setdefault(entityRequest,entitiesTextArray)

            textout.SystemPrint ("DataImporter: Entities loaded!")
        else:
            textout.SystemWarning ("DataImporter: WARNING! Entities folder is not found. Not loading any entities!")
        return entities

    #------------------------------MISC----------------------------------

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

    def GetPhrasePosDiffAvgSdFromTrainingData(this, trainingdatakey):
        #Getting phrasePosDiffAvgSd

        #phraseLists = Flip the columns and rows of trainingdata
        #When looping through trainingdata, get all the index 0s of each trainingdata item into one list, index 1s into another etc
        #Basically change so that each 
        #trainingdata[0] >> 1, 2, 3 | trainingdata[1] >> 4, 5, 6 | trainingdata[2] >> 7, 8, 9
        #becomes:
        #phraseLists[0] >> 1, 4, 7 | phrasePosDiff[1] >>2, 5, 8 | phrasePosDiff[2] >> 3, 6, 9
        phraseLists = []
        for i in range(0, len(this.trainingdata[trainingdatakey][0][0])):
            phraseValues = []
            for item in this.trainingdata[trainingdatakey]:
                phraseValues.append(item[0][i])
            phraseLists.append(phraseValues)
        #phraseList GET.

        #Finally, calculate the AVG and SD
        phrasePosDiffAvgSd = []
        for item in phraseLists:
            phrasePosDiffAvgSd.append((this.GetAvgOfList(item), this.GetSDOfList(item)))
        return phrasePosDiffAvgSd

    def GetSLRFromTrainingData(this, trainingdatakey):
        slr = []
        for trainingdatavalues in this.trainingdata[trainingdatakey]:
            #SLR is sentence length ratio
            #slr = sum of phrasePosDiff / sentence length
            slr.append(this.GetSumOfList(trainingdatavalues[0]) / trainingdatavalues[1])
        return slr

    def ConvertPhraseWeight(this, phraseWeight):
        #phraseWeight is in [1,1,2,1] format, need to convert such that they all add up to 1.
        totalWeightRaw = 0
        newPhraseWeight = [0,] * len(phraseWeight)
        for rawWeight in phraseWeight:
            totalWeightRaw += rawWeight #get sum of all weights
        for i in range(0,len(phraseWeight)):
            newPhraseWeight[i] = (phraseWeight[i] / totalWeightRaw) #set new value into each tuple.
        return newPhraseWeight

    #Check if string is a number anot
    def isNumber(s):
        try:
            float(s)
            return True
        except ValueError:
            return False