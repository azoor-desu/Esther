from utilities import textout
import os
import pkgutil

APP_PATH = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir))
MOD_PATH = os.path.join(APP_PATH, "modules")
UTIL_PATH = os.path.join(APP_PATH, "utilities")

class Processor():
    def __init__(this):
        print ("INITIALIZING PROCESSOR INSTANCE")
        this.LoadAllModules()
        
    def LoadAllModules(this):
        print ("LOADING MODULES FOR PROCESSOR")
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
        print ("{} MODULE(S) LOADED".format(len(this.modules)))

    def ProcessInput(this,string):
        #textout.EstherReply ("Hai. you said: " + string)
        
        #pass the string through ALL the keyword lists inside each module.
        #for
        print ("DOING DA PROCESSING")