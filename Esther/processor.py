import os
import pkgutil
import re
import dataimporter

APP_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
MOD_PATH = os.path.join(APP_PATH, "modules")

class Processor():
    #outline structure
    # "phrase[0]" :
    #[("intentName", [phrases], [(phrasePosDiffAVG, phrasePosDiffSD)], [phraseWeight], slrAVG, slrSD)]
    outlines = {}
    synonyms = {}
    entities = {}

    def __init__(this):
        print ("Processor: Starting processor initialization" )
        this.data = dataimporter.DataImporter()
        this.outlines = this.data.PopulateOutlinesDict()
        print (str(this.outlines))

        this.LoadAllModules()

        #synonyms need to be able to extract multiple words from usrinput and replace them
        this.synonyms.setdefault("require","need")
        this.synonyms.setdefault("pc","computer")
        this.synonyms.setdefault("rig","computer")
        this.synonyms.setdefault("battlestation","computer")

        this.entities.setdefault("!days",["monday","tuesday","wednesday","thursday","friday","saturday","sunday"])
        this.entities.setdefault("!daysrelative",["yesterday","today","tomorrow"])

        print ("Processor: Processor initialized!\n")
        
    def LoadAllModules(this):
        print ("Module Loader: Loading all modules into processor instance...")

        locations = [MOD_PATH]
        this.modules = []

        for finder, name, ispkg in pkgutil.walk_packages(locations):
            try:
                loader = finder.find_module(name)
                mod = loader.load_module(name)
            except:
                print ("Skipped module '" + name + "' due to an error.")
            else:
                print ("Found module '" + name + "'")
                this.modules.append(mod)

        print ("{} modules(s) loaded".format(len(this.modules)))

    def ProcessInput(this,_usrinput):

        usrinput = this.FormatUsrinput(_usrinput)

        #Create a dict for score sorting
        #Format:
        #scores[0] = "intentName": (scoreValue, [("entityType1","entityValue1") , ("enitityType2", "entityValue2")], [phrases], [phrasePos], usrinputlength)
        scores = {}

        #Iterate every word in user sentence
        for i in range(0,len(usrinput)):

            #if current user word matches keyword
            if usrinput[i] in this.outlines:

                #Iterate through all outlines within this starting phrase
                for nestedOutline in this.outlines.get(usrinput[i]):
                    print ("Recognized intent : " + str(nestedOutline))

                    #Find any requests for entity in nestedOutline
                    requestedEntities = []
                    extractedEntities = []
                    requestedEntityToRemove = ""
                    #ENTITIES STUFF: populate requestedEntities
                    for j in range(0,len(nestedOutline[1])):
                        if nestedOutline[1][j][0] == '!': #if phrase starts with !
                            requestedEntities.append(nestedOutline[1][j]) #add that entity group to be used later

                    #create tracker for which position each phrase appears in user's sentence, phasePos
                    phrasePos = [-1,] * len(nestedOutline[1])
                    this.SetPhrasePos(i, usrinput,nestedOutline, phrasePos, requestedEntities, extractedEntities, requestedEntityToRemove)
                    #check if any phrasePos values are -1. Invalidate this entire outline if so.
                    if -1 in phrasePos:
                        print ("**Some phrase is not found in this outline: " + str(nestedOutline[1]) + " Skipping this outline**")
                        continue
                    print ("Phrase's position in user sentence: " + str(phrasePos))

                    #Calculating scores
                    #Take phraseWeight and apply below formula.
                    #If not the first phrase, do this: phraseBaseScore - ((currindex - previndex - 1) * distMod * phraseWeight)
                    #distMod will range from 0 (no penalty) to 1 (100% score penalty for each length away. 2 words means 200% penalty.)
                    #add all scores together
                    
                    outlineScore = this.CalculateOutlineScore(phrasePos, nestedOutline, len(usrinput))
                    
                    #if scores alr exists, use the higher score
                    if nestedOutline[0] in scores:
                        if scores[nestedOutline[0]][0] < outlineScore:
                            scores[nestedOutline[0]] = (outlineScore,extractedEntities, nestedOutline[1], phrasePos, len(usrinput))
                    else:
                        scores.setdefault(nestedOutline[0],(outlineScore,extractedEntities, nestedOutline[1], phrasePos, len(usrinput)))

        print ("Final Results: " + str(scores))

        #Search for highest score
        highestScore = -1
        highestKey = ""

        for key, value in scores.items():
            if value[0] > highestScore:
                highestScore = value[0]
                highestKey = key

        if highestScore != -1:
            print ("Intent chosen: \"" + highestKey + "\" with values: "+ str(scores[highestKey]))
            #Update training data for matches.

            #scores[0] IS TEMPORARY. scores[0] == top probability. 
            #scores[x][2] = phrases | scores[x][3] = phrasePos  | scores[x][4] = usrinputlength 
            this.data.UpdateTrainingData(scores[highestKey][2], scores[highestKey][3], scores[highestKey][4])

    def FormatUsrinput(this, _usrinput):
        #clean up the user input. Remove all punctuations, leaving only . - and '
        tempusrinput = re.sub('[`~!@#$^&*()_+=[{}}\|:;<,>?/"]','',_usrinput).lower().split(' ')
        usrinput = []

        #split the 's and 'nt away.
        for i in range(0,len(tempusrinput)):
            if '\'' in tempusrinput[i]:
                splitted = tempusrinput[i].split('\'',1)
                usrinput.append(splitted[0])
                usrinput.append("\'" + splitted[1])
            else:
                usrinput.append(tempusrinput[i])

        #remove fullstop at end if any
        for i in range(0,len(usrinput)):
            if usrinput[i][len(usrinput[i])-1] == '.':
                usrinput[i] = usrinput[i][:-1]
            #replace all synonyms
            if usrinput[i] in this.synonyms:
                usrinput[i] = this.synonyms[usrinput[i]]
        return usrinput
    
    def SetPhrasePos(this, i, usrinput, nestedOutline, phrasePos, requestedEntities, extractedEntities, requestedEntityToRemove):
        #Start to scan the rest of the sentence using each outline in outlines[item]
        #Start scanning from detected word onwards, not full sentence.
        for j in range(i,len(usrinput)):
            if usrinput[j] in nestedOutline[1]: #if current word of user matches any phrases in outline
                phrasePos[nestedOutline[1].index(usrinput[j])] = j #Set phrasePos of corresponding phrase to index j

            #ENTITIES STUFF
            #Run word through list of requestedEntities, if any
            if len(requestedEntities) != 0:            
                for entityGrp in requestedEntities:
                    #print ("User's word now: " + usrinput[j] + " \nthe list to compare:" + str(this.entities[entityGrp]))
                    if usrinput[j] in this.entities[entityGrp]: #if user input matches relevant entities, give the !entity a phrasePos value.
                        phrasePos[nestedOutline[1].index(entityGrp)] = j
                        extractedEntities.append((entityGrp,usrinput[j])) #stores extracted entity as ("entityName","entityValue")
                        #print("ADDEEEEEED")
                        requestedEntityToRemove = entityGrp #disallow adding multiple entites if any to one outline. If outline requires one entity, return only one entity. Takes the first matched entity.
                        break
                if requestedEntityToRemove != "":
                    requestedEntities.remove(requestedEntityToRemove)
                    requestedEntityToRemove = ""

    def CalculateOutlineScore(this, phrasePos, nestedOutline, usrinputlength):
        outlineScore = 0
        phraseWeight = nestedOutline[3]
        phrasePosDiffAvgSd = nestedOutline[2]
        slrAVG = nestedOutline[4]
        slrSD = nestedOutline[5]
        phrasePosDiff = [0,] * len(phrasePos)

        #phraseDistModMultiplier = 0.3 #Random values my d00d, cos original might be too high
        #slrModMultiplier = 0.3 #Random values my d00d

        #Calculate [phrasePosDiff]
        #Convert [phrasePos] to [phrasePosDiff] e.g. [1,3,8] > [0,2,5]
        for i in range(1,len(phrasePos)): #index 0 is always value 0, so start loop from 1.
            phrasePosDiff[i] = phrasePos[i] - phrasePos[i-1]
        
        for i in range(0,len(phraseWeight)):
            #Check if AVG and SD from training data exists
            if slrAVG is not -1:
                phraseDistMod = abs(phrasePosDiff[i] - phrasePosDiffAvgSd[i][0]) / phrasePosDiffAvgSd[i][1]
                slr = this.data.GetSumOfList(phrasePosDiff) / usrinputlength
                slrMod = abs(slr - slrAVG) / slrSD
                outlineScore = outlineScore + phraseWeight[i] * phraseDistMod * slrMod #sum [phraseWeight] with modifiers to get total score
            #No training data exists. Calculate according to distance away.
            else: 
                outlineScore = outlineScore + (phraseWeight[i] - (phrasePosDiff[i] * 0.06))

        print ("Score for this outline: " + str(outlineScore))
        return outlineScore