import textout
import os
import pkgutil
import re

APP_PATH = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir))
MOD_PATH = os.path.join(APP_PATH, "modules")

class Processor():
    outlines = {}
    synonyms = {}
    entities = {}

    def __init__(this):
        print ("Initializing processor...")
        this.LoadAllModules()

        this.synonyms.setdefault("require","need")
        this.synonyms.setdefault("pc","computer")
        this.synonyms.setdefault("rig","computer")
        this.synonyms.setdefault("battlestation","computer")

        this.entities.setdefault("!days",["monday","tuesday","wednesday","thursday","friday","saturday","sunday"])
        this.entities.setdefault("!daysrelative",["yesterday","today","tomorrow"])

        this.AddOutline("ask_time", ["what","time"],(0,0.1),(1,2))
        this.AddOutline("ask_time", ["give","time"],(0,0.1),(1,2))
        this.AddOutline("ask_time", ["tell","me","time"],(0,1,0.1),(1,1,2))
        this.AddOutline("ask_time", ["need","time"],(0,0.1),(1,2))
        this.AddOutline("ask_time", ["do","know","time"],(0,0.1,0.1),(1,1,2))
        this.AddOutline("ask_time", ["have","current","time"],(0,0.1,0.1),(1,1,2))

        this.AddOutline("ask_if_faggot", ("are","you","faggot"),(0,0.1,0.1),(0.1,0.2,2))
        this.AddOutline("ask_if_faggot", ("hello","you","faggot"),(0,0.1,0.1),(0.5,0.2,2))

        this.AddOutline("ask_day", ["what","day","!daysrelative"],(0,0.1,0.1),(1,2,2))
        this.AddOutline("ask_day", ["give","me","day","!daysrelative"],(0,0.1,0.1,0.1),(1,1,2,2))
        this.AddOutline("ask_day", ["tell","me","day","!daysrelative"],(0,0.1,0.1,0.1),(1,1,2,2))
        this.AddOutline("ask_day", ["need","day","!daysrelative"],(0,0.1,0.1),(1,2,2))

        this.AddOutline("ask_date", ["what","date","!daysrelative"],(0,0.1,0.1),(1,2,2))
        this.AddOutline("ask_date", ["give","me","date","!daysrelative"],(0,0.1,0.1,0.1),(1,1,2,2))
        this.AddOutline("ask_date", ["tell","me","date","!daysrelative"],(0,0.1,0.1,0.1),(1,1,2,2))
        this.AddOutline("ask_date", ["need","date","!daysrelative"],(0,0.1,0.1),(1,2,2))

        this.AddOutline("ask_date", ["what","date","is","!days"],(0,0.1,0.1,1),(1,2,1,2))
        this.AddOutline("ask_date", ["what","date","on","!days"],(0,0.1,0.1,1),(1,2,1,2))
        this.AddOutline("ask_date", ["give","me","date","!days"],(0,0.1,0.1,0.5),(1,1,2,2))
        this.AddOutline("ask_date", ["need","date","!days"],(0,0.1,0.1),(1,2,2))

        this.AddOutline("ask_date_day", ["need","date","!daysrelative","!days"],(0,0.1,0.1,0.1),(1,2,2,2))

        print ("Processor initialized!\n")
        
    def LoadAllModules(this):
        print ("Loading all modules into processor instance...")

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

        #outline structure
        # "phrase[0]" : [
        #("intentName", [phrases], [(phrasePosDiffSD, phrasePosDiffAVG)], [phraseWeight], slrSD, slrAVG), etc... <<Replaced distmod with the tuple, added slrSD and slrAVG at the end. No change in exisitng pos.
        # ] 
    def AddOutline (this, intentName, phrases, distMod, phraseWeight):
        #phraseWeight is in [1,1,2,1] format, need to convert such that they all add up to 1.
        totalWeightRaw = 0
        newTuple = [0,]* len(phraseWeight)

        for rawWeight in phraseWeight:
            totalWeightRaw += rawWeight #get sum of all weights
        for i in range(0,len(phraseWeight)):
            newTuple[i] = (phraseWeight[i] / totalWeightRaw) #set new value into each tuple.

        if phrases[0] in this.outlines:
            this.outlines.get(phrases[0]).append((intentName, phrases, distMod, newTuple))
        else:
            this.outlines.setdefault(phrases[0],[]).append((intentName, phrases, distMod, newTuple))

    def ProcessInput(this,_usrinput):
        usrinput = this.FormatUsrinput(_usrinput)

        #Create a dict for score sorting
        #Format:
        #scores[0] = "intentName": (scoreValue, [("entityType1","entityValue1") , ("enitityType2", "entityValue2")])
        scores = {}

        #Iterate every word in user sentence
        for i in range(0,len(usrinput)):

            #if current user word matches keyword
            if usrinput[i] in this.outlines:

                #Iterate through all outlines within this starting phrase
                for nestedOutline in this.outlines.get(usrinput[i]):
                    print ("Recognized intent : " + str(nestedOutline))

                    #Find any requests for entity in nestedOutline
                    requestedEntites = []
                    extractedEntities = []
                    requestedEntityToRemove = ""
                    for j in range(0,len(nestedOutline[1])):
                        if nestedOutline[1][j][0] == '!': #if phrase starts with !
                            requestedEntites.append(nestedOutline[1][j]) #add that entity group to be used later

                    #create tracker for which position each phrase appears in user's sentence
                    phrasePos = [-1,] * len(nestedOutline[1])
                    
                    #Start to scan the rest of the sentence using each outline in outlines[item]
                    #Start scanning from detected word onwards, not full sentence.
                    for j in range(i,len(usrinput)):
                        if usrinput[j] in nestedOutline[1]: #if current word of user matches any phrases in outline
                            phrasePos[nestedOutline[1].index(usrinput[j])] = j #Set phrasePos of corresponding phrase to index j
                        #Run word through list of requestedEntities, if any
                        if len(requestedEntites) != 0:
                            
                            for entityGrp in requestedEntites:
                                print ("User's word now: " + usrinput[j] + " \nthe list to compare:" + str(this.entities[entityGrp]))
                                if usrinput[j] in this.entities[entityGrp]: #if user input matches relevant entities, give the !entity a phrasePos value.
                                    phrasePos[nestedOutline[1].index(entityGrp)] = j
                                    extractedEntities.append((entityGrp,usrinput[j])) #stores extracted entity as ("entityName","entityValue")
                                    print("ADDEEEEEED")
                                    requestedEntityToRemove = entityGrp #disallow adding multiple entites if any to one outline. If outline requires one entity, return only one entity. Takes the first matched entity.
                                    break
                            if requestedEntityToRemove != "":
                                requestedEntites.remove(requestedEntityToRemove)
                                requestedEntityToRemove = ""
                            
                    print ("Phrase's position in user sentence: " + str(phrasePos))

                    #Calculating scores
                    #Take phraseWeight and apply below formula.
                    #If not the first phrase, do this: phraseBaseScore - ((currindex - previndex - 1) * distMod * phraseWeight)
                    #distMod will range from 0 (no penalty) to 1 (100% score penalty for each length away. 2 words means 200% penalty.)
                    #add all scores together
                    
                    outlineScore = 0

                    for k in range(0,len(phrasePos)):
                        #if this position index is not -1, it has a legit position in user's sentence. 
                        #If not, phrase does not exist in user's sentence, so do not calculate.
                        if phrasePos[k] != -1:
                            #use base score to calculate modifier for words apart, and then add onto final score for this outline
                            if k != 0:
                                if phrasePos[k] - phrasePos[k-1] > 0: #if the position diff is -ve, e.g. [time, need] instead of [need, time], SKIP. DO NOT ADD ANY SCORE.
                                    outlineScore += nestedOutline[3][k] - ((phrasePos[k] - phrasePos[k-1] - 1) * nestedOutline[2][k] * nestedOutline[3][k])
                            else:
                                outlineScore += nestedOutline[3][k]

                    print ("Score for this outline: " + str(outlineScore))

                    #if scores alr exists, use the higher score
                    if nestedOutline[0] in scores:
                        if scores[nestedOutline[0]][0] < outlineScore:
                            scores[nestedOutline[0]] = (outlineScore,extractedEntities)
                    else:
                        scores.setdefault(nestedOutline[0],(outlineScore,extractedEntities))
        print ("Final Results: " + str(scores))

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