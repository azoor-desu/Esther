import os
import pkgutil
import re
import dataimporter
import textout

APP_PATH = os.getcwd()
MOD_PATH = os.path.join(APP_PATH, "modules")

class Processor():
    #outline structure
    # "phrase[0]" :
    #[("intentName", [phrases], [(phrasePosDiffAVG, phrasePosDiffSD)], [phraseWeight], slrAVG, slrSD)]
    outlines = {}
    synonyms = {}
    entities = {}

    def __init__(this):
        textout.SystemPrint("Processor: Starting processor initialization" )
        this.data = dataimporter.DataImporter()
        this.data.PopulateTrainingData()
        this.outlines = this.data.PopulateOutlinesDict()
        this.synonyms = this.data.PopulateSynonymsDict()
        this.entities = this.data.PopulateEntitiesDict()
        this.LoadAllModules()

        textout.SystemPrint ("Processor: Processor initialized!\n")
        
    def LoadAllModules(this):
        textout.SystemPrint ("Module Loader: Loading all modules into processor instance...")

        locations = [MOD_PATH]
        this.modules = []

        for finder, name, ispkg in pkgutil.walk_packages(locations):
            try:
                loader = finder.find_module(name)
                mod = loader.load_module(name)
            except:
                textout.SystemPrint ("Skipped module '" + name + "' due to an error.")
            else:
                textout.SystemPrint ("Found module '" + name + "'")
                this.modules.append(mod)

        textout.SystemPrint ("{} modules(s) loaded".format(len(this.modules)))
    
    #------------------------------PROCESSING----------------------------------
    def ProcessInput(this,_usrinput):

        usrinput = this.FormatUsrinput(_usrinput)

        #Create a dict for score sorting
        #Format:
        #scores[0] = "phrases together": (scoreValue, [(entityType)], [phrases], [phrasePos], usrinputlength, intentName)
        scores = {}

        #Iterate every word in user sentence
        for i in range(0,len(usrinput)):

            #if current user word matches keyword
            if usrinput[i] in this.outlines:

                #Iterate through all outlines within this starting phrase
                for nestedOutline in this.outlines.get(usrinput[i]):
                    textout.SystemPrint ("Recognized intent : " + str(nestedOutline))

                    #create tracker for which position each phrase appears in user's sentence, phasePos
                    phrasePos = [-1,] * len(nestedOutline[1])
                    this.SetPhrasePos(i, usrinput,nestedOutline, phrasePos)
                    extractedEntities = this.GetExtractedEntities(i, usrinput,nestedOutline, phrasePos)

                    #check if any phrasePos values are -1. Invalidate this entire outline if so.
                    if -1 in phrasePos:
                        textout.SystemPrint ("**Some phrase is not found in this outline: " + str(nestedOutline[1]) + " Skipping this outline**")
                        continue
                    textout.Print ("Phrase's position in user sentence: " + str(phrasePos))

                    #Calculating scores
                    #Take phraseWeight and apply below formula.
                    #If not the first phrase, do this: phraseBaseScore - ((currindex - previndex - 1) * distMod * phraseWeight)
                    #distMod will range from 0 (no penalty) to 1 (100% score penalty for each length away. 2 words means 200% penalty.)
                    #add all scores together
                    
                    outlineScore = this.CalculateOutlineScore(phrasePos, nestedOutline, len(usrinput))
                    scores.setdefault(this.CombineStringsList(nestedOutline[1]),(outlineScore,extractedEntities, nestedOutline[1], phrasePos, len(usrinput), nestedOutline[0]))

        textout.SystemPrint ("Final Results: " + str(scores))

        #Search for highest score
        highestKey = ""

        textout.Print ("---------------Sorting score--------------------")
        for key, value in scores.items():
            if highestKey == "":
                #First item in loop
                highestKey = key
                textout.Print ("First outline set: \"" + highestKey + "\" with values: "+ str(scores[highestKey]))
            else:
                if value[0] > 0.3: #Disregard any value below 0.3 score
                    #If number of phrases in value > number of phrases in highest key
                    if len(value[2]) > len(scores[highestKey][2]):
                        highestKey = key
                    #If value of this score is higher than the highest so far
                    elif value[0] > scores[highestKey][0]:
                        highestKey = key

        if highestKey != "":
            textout.SystemPrint ("Intent chosen: \"" + highestKey + "\" with values: "+ str(scores[highestKey]))
            #Update training data for matches.

            #scores[0] IS TEMPORARY. scores[0] == top probability. 
            #scores[x][2] = phrases | scores[x][3] = phrasePos  | scores[x][4] = usrinputlength 
            this.data.UpdateTrainingData(scores[highestKey][2], scores[highestKey][3], scores[highestKey][4], this.outlines)
        print ("")

    def FormatUsrinput(this, _usrinput):
        #clean up the user input. Remove all punctuations, leaving only . - ! and '
        tempusrinput = re.sub("[^\sa-zA-Z.'!-]+",'',_usrinput).lower()

        #Replace synonyms before splitting
        #https://stackoverflow.com/questions/17730788/search-and-replace-with-whole-word-only-option
        def replace(match):
            return this.synonyms[match.group(0)]
        tempusrinput = re.sub('|'.join(r'\b%s\b' % re.escape(s) for s in this.synonyms), 
        replace, tempusrinput)

        tempusrinput = tempusrinput.split(' ')
        usrinput = []

        #split the 's away.
        #Although most other contractions have been split and dealt with, 's comes with two flavours that cannot be synonymnized:
        #noun's - everyone's cookies
        #'s as in is - everyone's dead
        for i in range(0,len(tempusrinput)):

            #remove empty cells
            if len(tempusrinput[i]) == 0:
                continue

            #split the 's
            if '\'s' in tempusrinput[i]:
                splitted = tempusrinput[i].split('\'',1)
                usrinput.append(splitted[0])
                usrinput.append("\'" + splitted[1])
            else:
                usrinput.append(tempusrinput[i])        

        #remove fullstop at end if any
        for i in range(0,len(usrinput)):
            if len(usrinput[i]) > 0 and usrinput[i][len(usrinput[i])-1] == '.':
                usrinput[i] = usrinput[i][:-1]
        return usrinput
    
    def SetPhrasePos(this, currentUsrinputIndex, usrinput, nestedOutline, phrasePos):
        #Start to scan the rest of the sentence using each outline in outlines[item]
        #Start scanning from detected word onwards, not full sentence.
        for i in range(currentUsrinputIndex,len(usrinput)):
            if usrinput[i] in nestedOutline[1]: #if current word of user matches any phrases in outline
                phrasePos[nestedOutline[1].index(usrinput[i])] = i #Set phrasePos of corresponding phrase to index i
                #Entities are left out of setting phrasePos, GetExtractedEntities will set the phrasePos.
        print ("")

    def GetExtractedEntities(this, currentUsrinputIndex, usrinput, nestedOutline, phrasePos):
        entityRequests = [] #Keeps track of what entities are still needed to be extracted.
        entityRequestsIndex = 0 #Tracks which entityRequest to be searching for.
        entityRequestIndexInOutline = [] #For use in setting phrasePos.
        entityLookupDict = {} #Stores phrases used by entityRequests, changes on each new entityRequest
        entityLengths = [] #Different lengths of entityLookupDict keys. No repetitons. Changes with entityLookupDict
        #e.g. "monday" = 1 word length, "the day after" = 3 word length. entityLengths = [1,3]
        extractedEntities = [] #Extracted from usrinput, the actual phrases that will be returned
        #Format: [(phrase, entityRequest), ...]

        def PopulateDict(entityRequest):
            entityLookupDict.clear()
            entityLengths.clear()
            for entity in this.entities[entityRequest]:
                entityLookupDict.setdefault(entity, entityRequest)

                length = len(entity.split(' '))
                if length not in entityLengths:
                    entityLengths.append (length)

        def AssignPhrasePos(wordIndex):
            phrasePos[entityRequestIndexInOutline[entityRequestsIndex]] = wordIndex

        #searches through entityLookupDict for a match with usrinput[currentUsrinputIndex]
        #Returns true if match is found, false if not.
        def SearchThroughDict(currentWordIndex):
            for lengths in entityLengths:
                if lengths == 1:
                    if usrinput[currentWordIndex] in entityLookupDict:
                        extractedEntities.append((usrinput[currentWordIndex], entityLookupDict[usrinput[currentWordIndex]]))
                        AssignPhrasePos(currentWordIndex)
                        return True
                else:
                    extendedPhrase = ""
                    if currentWordIndex + lengths <= len(usrinput): #Prevent out of range error if last word of the sentence
                        for i in range(currentWordIndex, currentWordIndex + lengths):
                            extendedPhrase = extendedPhrase + " " + usrinput[i] 
                        extendedPhrase = extendedPhrase.strip()
                        if extendedPhrase in entityLookupDict:
                            extractedEntities.append((extendedPhrase, entityLookupDict[extendedPhrase]))
                            AssignPhrasePos(currentWordIndex)
                            return True
            return False

        #MainThread
        #Populate entityRequests
        for i in range(0,len(nestedOutline[1])):
            if nestedOutline[1][i][0] == '!': #if phrase starts with '!'
                entityRequests.append(nestedOutline[1][i])
                entityRequestIndexInOutline.append(i)

        if len(entityRequests) != 0:
            PopulateDict(entityRequests[entityRequestsIndex])

            #Extracting entites
            for i in range(currentUsrinputIndex, len(usrinput)):
                if entityRequestsIndex < (len(entityRequests)) and SearchThroughDict(i) is True:
                    if entityRequestsIndex + 1 < len(entityRequests):
                        entityRequestsIndex = entityRequestsIndex + 1
                        PopulateDict(entityRequests[entityRequestsIndex])
                    else:
                        break
        #print (extractedEntities)
        return extractedEntities

    def CalculateOutlineScore(this, phrasePos, nestedOutline, usrinputlength):
        outlineScore = 0
        phraseWeight = nestedOutline[3]
        phrasePosDiffAvgSd = nestedOutline[2]
        slrAVG = nestedOutline[4]
        slrSD = nestedOutline[5]
        phrasePosDiff = [0,] * len(phrasePos)

        #Calculate [phrasePosDiff]
        #Convert [phrasePos] to [phrasePosDiff] e.g. [1,3,8] > [0,2,5]
        for i in range(1,len(phrasePos)): #index 0 is always value 0, so start loop from 1.
            phrasePosDiff[i] = phrasePos[i] - phrasePos[i-1]
        
        #Calculating phraseDistMod for each phrase
        for i in range(0,len(phraseWeight)):

            #Check if AVG and SD from training data exists
            if slrAVG is not -1:

                #Index 0: Only phraseweight
                #Index 1 onwards: Phraseweight and phraseDistMod (sd/avg)
                if i == 0:
                    textout.Print("----------First Phrase------------")
                    textout.Print ("old outline is: " + str(outlineScore)) 
                    textout.Print("phraseweight: " + str(phraseWeight[i]))
                    outlineScore = outlineScore + phraseWeight[i]
                    textout.Print ("result outline is: " + str(outlineScore)) 
                    textout.Print("----------------------")
                else:
                    textout.Print("----------Subsequent Phrase------------")
                    textout.Print ("phrasePosDiff is: " + str(phrasePosDiff[i]) )
                    textout.Print("phrasePosAvg: " + str(phrasePosDiffAvgSd[i][0]))
                    textout.Print("phrasePosSd: " + str(phrasePosDiffAvgSd[i][1]))
                    textout.Print("----------------------")
                    #phraseDistMod = abs(phrasePosDiff[i] - phrasePosDiffAvgSd[i][0]) / phrasePosDiffAvgSd[i][1]
                    #outlineScore = outlineScore + phraseWeight[i] * phraseDistMod

                    #How to use AVG and SD
                    #All values within the range AVG+SD : AVG-SD recieve 0 distance penalty.
                    #All values that fall outside that range will recieve penalty, starting from 0 up to infinity

                    if phrasePosDiffAvgSd[i][0] - phrasePosDiffAvgSd[i][1] <= phrasePosDiff[i] <= phrasePosDiffAvgSd[i][0] + phrasePosDiffAvgSd[i][1]:
                        textout.Print ("No penalty cos phraseposdiff is in range of the SDs") 
                        textout.Print ("old outline is: " + str(outlineScore))
                        textout.Print("phraseweight: " + str(phraseWeight[i]))
                        outlineScore = outlineScore + phraseWeight[i] #No penalty in range
                        textout.Print ("result outline is: " + str(outlineScore))
                        textout.Print("----------------------")
                    else:
                        #Calculate how far out of the range value is
                        amountOut = 0
                        if phrasePosDiff[i] > phrasePosDiffAvgSd[i][0]:
                            #If phraseposdiff is at the right side, bigger that AVG + SD
                            amountOut = phrasePosDiff[i] - (phrasePosDiffAvgSd[i][0] + phrasePosDiffAvgSd[i][1])
                        else:
                            #If phraseposdiff is at the left side, smaller that AVG - SD
                            amountOut = (phrasePosDiffAvgSd[i][0] - phrasePosDiffAvgSd[i][1]) - phrasePosDiff[i]

                        if phrasePosDiffAvgSd[i][1] != 0: #prevent divide by zero error if program saves repeated entries

                            #phraseDistMod = (SD - amountOut) / SD >> IF amountOut is smaller than SD (usually), returns value 1 to 0.00001
                            #IF (SD - amountOut) is <= 0 (-ve) (exceeds AVG + SD + SD range, very out-there value), oh ho ho big big penalty dude
                            if (phrasePosDiffAvgSd[i][1] - amountOut) > 0:
                                phraseDistMod = (phrasePosDiffAvgSd[i][1] - amountOut) / phrasePosDiffAvgSd[i][1]
                            else:
                                #penalty: put a minimum cap on how low the penalty goes, cos it'll go quite low
                                phraseDistMod = 0.01
                        else:
                            #If SD is 0, leave phraseDistMod as default 1.
                            phraseDistMod = 1
                            textout.SystemWarning("Uh-oh, a phrasePosSD has a value of 0. Assigning default value for phraseModDist.")
                            textout.SystemWarning("Please check training data for outline: " + str(nestedOutline[0]))

                        #apply penalty to the phrase then add it to outlinescore
                        textout.Print ("Apply penalty cos phraseposdiff is out of range of the SDs") 
                        textout.Print ("old outline is: "+ str(outlineScore))
                        textout.Print("phraseweight: "+ str(phraseWeight[i]))
                        textout.Print ("phraseDistMod is: "+ str( phraseDistMod))
                        outlineScore = outlineScore + phraseWeight[i] * phraseDistMod

                        textout.Print ("result outline is: "+ str(outlineScore))
                        textout.Print("----------------------")
            else:
                #No training data exists. Calculate according to distance away.
                 outlineScore = outlineScore + (phraseWeight[i] - (phrasePosDiff[i] * 0.06))
                 textout.Print ("NO TRAINING DATA. Doing default dist away calculations.")
                 textout.Print ("result outline is: " + str(outlineScore)) 
        #Calculating slrMod for entire outline
        textout.Print("----------Calculating SLR after phrases------------")
        textout.Print ("old outline is: " + str(outlineScore))
        
        slr = this.data.GetSumOfList(phrasePosDiff) / usrinputlength
        textout.Print("slr: " + str(slr))
        textout.Print("slrAVG: " + str(slrAVG))
        textout.Print("slrSD: " + str(slrSD))

        #If slr is out of SD range, apply penalty. If not, ignore and leave alone.
        if slrAVG - slrSD > slr > slrAVG + slrSD:

            #Calculate how much out of the range slr is
            amountOut = 0
            if slr > slrAVG:
                #If slr is at the right side, bigger that AVG + SD
                amountOut = slr - (slrAVG + slrSD)
            else:
                #If slr is at the left side, smaller that AVG - SD
                amountOut = slr - (slrAVG - slrSD)
            textout.Print("amountOut: " + str(amountOut))

            #slrMod = amountOut / SD * 100 | 10/10 useful comment
            slrMod = amountOut / slrSD * 100
            textout.Print("slrMod:  "+ str(slrMod))

            #Apply slrMod to entire outline
            outlineScore = outlineScore * slrMod
            textout.Print ("result outline is: " + str(outlineScore))
            textout.Print("----------------------")
        else:
            textout.Print ("No penalty cos slr is in range of the SDs") 

        textout.SystemPrint ("Score for this outline: " + str(outlineScore))
        return outlineScore

    #------------------------------MISC----------------------------------

    def CombineStringsList(this, inputlist):
        combined = ""
        for item in inputlist:
            if combined != "":
                combined = combined + " " + item
            else:
                combined = item
        return combined