import subprocess

def Gfail(*a):
    """ A fireable which does nothing (useful to return from getattrs)"""
    pass

def processReadliner(cmd, callback):
    PIPE = subprocess.PIPE
    p = subprocess.Popen(['%s 2>&1' % cmd],  shell = True,
        env={"PATH": "/bin:/usr/bin:/sbin:/usr/sbin:/usr/local/tcs/tums"},
        stdin=PIPE, stdout=PIPE, bufsize=100
    )
    r = None
    line = ""
    while r == None:
        r = p.poll()
        data = p.stdout.read(16)
        for i in data:
            if i == "\n":
                callback(line)
                line = ""
            else:
                line += i
    callback(line)
    

class AttrHooker(object):
    commands = []
    name = ""
    
    help = {}
    
    def __init__(self, config= None):
        self.config = config
        
    def __genCMDList__(self, actionName="command"):
        """Generate a list of methods for self object making sure it matches the actionName
        Methods that would match would be actionName(self)/actionName_*(self)
        """
        actionName = actionName==None and "command" or actionName
        def checkMethodName(methodName):
            """Checks to see that the methodName provided matches required criteria"""
            if len(methodName) >= len(actionName) and methodName[:1] != '_':
                if len(methodName) == len(actionName) and methodName == actionName:
                    return True
                if methodName[:len(actionName)+1] == actionName+"_":
                    return True
            return False
        return filter(checkMethodName, dir(self))
    
    def genCmdDoc(self, actionName=None):        
        helpname = (actionName==None or actionName not in self.help) and "__default__" or actionName              
        return helpname in self.help and self.help[helpname] or False
        

    def genAllDoc(self, actionName=None):
        """Generates Command Documentation based on the inline documentation for all subcommands"""
        def getCommandDoc():
            """Gets a list of commands then compiles a formated command help"""
            cmdList = self.__genCMDList__(actionName)        
            methodDocs = [("- %s" % getattr(self, method).__doc__) for method in cmdList]
            return str.join("\n", filter(lambda x: x != "- None", methodDocs) )
        
        print "%s\n%s" % (self.genCmdDoc(actionName), getCommandDoc())
        return(Gfail)
        
class ActionHooker(object):
    commands = []
    
    commandHooks = {}
    
    name = ""
    
    def __init__(self, config= None):
        self.config = config
        
    def __getattr__(self, attr):
        attrSplit = attr.split('_')
        if attrSplit[0] in self.commandHooks:
            command = attrSplit.pop(0)
            try:                
                if len(attrSplit) < 1:
                    if len(self.name) > 0:
                        try:
                            cmd = getattr(self.commandHooks[command], self.name + '_' + command)
                            return(cmd)
                        except:
                            f = getattr(self.commandHooks[command], "genAllDoc")
                            return f(self.name)
                else:
                    if len(self.name) < 1:             
                        return getattr(self.commandHooks[command], str.join('_', attrSplit))
                    else:
                        return getattr(self.commandHooks[command], self.name + '_' + str.join('_', attrSplit))
            except:                
                print "No such subcommand: %s" % ' '.join(attr.split('_'))     
                f = getattr(self.commandHooks[command], "genAllDoc") 
                return f(self.name)
                
        if attr in self.commands:
            return getattr(self, "command_%s" % attr)
        else:
            print "No such subcommand: %s" % ' '.join(attr.split('_'))    
            print self.getCommandDoc()
            return Gfail
    
    def attachHook(self, hook):
        self.commandHooks[hook.name] = hook
    
    def docgen(self, actionName=None):
        return(Gfail)


    def getCommandDoc(self):
        """Gets a list of commands then compiles a formated command help"""
        def executeMethod(commandName):
            """Executes the genCmdDoc method of the supplied method"""
            f = getattr(self.commandHooks[commandName],'genCmdDoc')                
            docText = f(self.name)
            try: 
                return len(docText) > 0 and "\n    %s" % docText or ""
            except:
                return ""
        methodDocs = []
        for commandName in self.commandHooks.keys():
            commandText = executeMethod(commandName)
            if len(commandText) > 0:
                methodDocs.append("- %s <sub command>%s" % (commandName ,commandText))
        return str.join("\n", filter(lambda x: len(x) > 1, methodDocs) )
    
    def __repr__(self):
        """Generates Command Documentation based on the inline documentation"""
        return self.getCommandDoc()
    

def renameIfaces(ifaceName):
    return ifaceName

def fixIfaces(ifaceName):
    return ifaceName

def validInetaddr(addr):
    if not '/' in addr:
        return False
    pre = addr.split('/')
    if len(pre[0].split('.')) != 4:
        return False
    prelist = pre[0].split('.')
    prelist.append(pre[1])
    for i in prelist:
        try:
            p = int(i)
            if p > 255:
                return False
        except:
            return False
    if int(pre[1]) > 32:
        return False
    return True

