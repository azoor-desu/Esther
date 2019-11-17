import textout
import os
import pkgutil
import re

APP_PATH = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir))
MOD_PATH = os.path.join(APP_PATH, "modules")

class Processor():
    outlines = {}
    keywords = {}
    synonyms = {}
    entitiesList = {}

    def __init__(this):
        print ("Initializing processor...")
        this.LoadAllModules()

        this.keywords.setdefault("ask_time",["time"])
        this.keywords.setdefault("ask_if_faggot",["faggot"])

        this.synonyms.setdefault("computer",["pc","rig","battlestation"])

        this.entitiesList.setdefault("!days",["monday","tuesday","wednesday","thursday","friday","saturday","sunday"])
        this.entitiesList.setdefault("!days_relative",["yesterday","today","tomorrow"])

        this.AddOutline(["what","time"], "ask_time", 1,0.1)
        this.AddOutline(["give","time"], "ask_time", 1,0.1)
        this.AddOutline(["tell","me","time"], "ask_time", 1,0.1)
        this.AddOutline(["need","time"], "ask_time", 1,0.1)
        this.AddOutline(["require","time"], "ask_time", 1,0.1)
        this.AddOutline(["do","know","time"], "ask_time", 1,0.1)
        this.AddOutline(["have","current","time"], "ask_time", 1,0.15)
        this.AddOutline(["hello","you","faggot"], "ask_if_faggot", 1,0.1)
        this.AddOutline(["time"], "ask_time", 0.8,0)
        this.AddOutline(["are","you","faggot"], "ask_if_faggot", 1,0.3)

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
        #("intentName", probability, distMod, [phrase], noKeywords),
        #("intentName", probability, distMod, [phrase], noKeywords),
        #("intentName", probability, distMod, [phrase], noKeywords)
        # ]
    def AddOutline (this, phraseList, intentName, probability, distMod):
        #find number of keywords in phrases
        noKeywords = 0
        if this.keywords.get(intentName,0) != 0:
            for item in phraseList:
                if item in this.keywords[intentName]:
                    noKeywords += 1
        if phraseList[0] in this.outlines:
            this.outlines.get(phraseList[0]).append((intentName,probability, distMod, phraseList, noKeywords))
        else:
            this.outlines.setdefault(phraseList[0],[]).append((intentName,probability, distMod, phraseList, noKeywords))

    def ProcessInput(this,_usrinput):
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

        #Create a dict for score sorting
        scores = {}

        #Iterate every word in user sentence
        for i in range(0,len(usrinput)):
            print ("Now checking: " + usrinput[i])
            #if current user word matches keyword
            if usrinput[i] in this.outlines:

                #Iterate through all outlines within this starting phrase
                for nestedOutline in this.outlines.get(usrinput[i]):

                    #create tracker for which position each phrase appears in user's sentence
                    print (nestedOutline)
                    phrasePos = [-1,] * len(nestedOutline[3])

                    #Start to scan the rest of the sentence using each outline in outlines[item]
                    #Start scanning from detected word onwards, not full sentence.
                    for j in range(i,len(usrinput)):
                        if usrinput[j] in nestedOutline[3]:
                            phrasePos[nestedOutline[3].index(usrinput[j])] = j
                    print (phrasePos)

                    #Calculating scores
                    #1 divide score by amount of phrases (if 4 phrases, each word will be worth 0.25)
                    #Keywords will hold more weight. Set in the intent txt file.
                    #Weighted values: 0 means hold no weight, 1 means normal weight, 2 means twice the weight.
                    #2 Use distMod. If not the first phrase, do this: phraseScore - ((currindex - previndex - 1) * distMod * phraseScore)
                    #distMod will range from 0 (length dosent matter) to 1 (100% score penalty for each length away. 2 words means 200% penalty.)
                    #3 Use probability to round off the shiz. Default will be 1.
                    
                    outlineScore = 0
                    phraseScore = [0,] * len(phrasePos)
                    keywordWeight = 1.6;

                    #Calculate base phraseScore for each phrase based on whether it is a keyword or not
                    totalScore = len(phraseScore) - nestedOutline[4] + keywordWeight * nestedOutline[4]

                    for k in range(0,len(phraseScore)):
                        if nestedOutline[3][k] in this.keywords[nestedOutline[0]]:
                            phraseScore[k] = 1/totalScore*keywordWeight
                        else:
                            phraseScore[k] = 1/totalScore*1
                        if k != 0:
                            outlineScore += phraseScore[k] - ((abs(phrasePos[k] - phrasePos[k-1]) - 1) * phraseScore[k] * nestedOutline[2])
                        else:
                            outlineScore += phraseScore[k]

                    outlineScore *= nestedOutline[1]
                    print (phraseScore)
                    print (outlineScore)
                    #if scores alr exists, use the higher score
                    if scores.get(nestedOutline[0],-1) != -1:
                        if scores[nestedOutline[0]] < outlineScore:
                            scores[nestedOutline[0]] = outlineScore
                    else:
                        scores.setdefault(nestedOutline[0],outlineScore)
        print (scores)