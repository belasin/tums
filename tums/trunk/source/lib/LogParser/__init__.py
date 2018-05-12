from twisted.internet import reactor, threads, defer

class logFileHandlers(object):
    
    logFileName = ""

    __fd__ = ""

    isRunning = True

    isShuttingDown = False

    looping = False

    def __init__(self,filename):
        self.logFileName = filename
        self.__openFile__()

    def __checkFile__(self):
        """Checks the file is open and ready for reading otherwise it opens it"""
        if self.isShuttingDown:
            return
        if not self.__fd__:
            self.__openFile__()
        else:
            if self.__fd__.closed:
                self.__openFile()

    def __openFile__(self):
        """Closes any currently open file and then opens a file"""
        try:
            self.__fd__.close()
        except:
            self.__fd__ = None
        self.__fd__ = open(self.logFileName, "r")

    def __loop2__(self):
        """Main file line interator"""
        self.__checkFile__()
        def nextLine(result, err=False):
            if err:
                print "ERROR:" + str(result)
            if not self.isRunning:
                self.looping = False
                return
            self.looping = True    
            line = self.__fd__.readline()
            if line:
                d = defer.maybeDeferred(self.readLine, line)
                d.addCallback(nextLine).addErrback(nextLine, True)
                return d
            else:
                self.looping = False

        nextLine(False)
        
        if self.isRunning:
            self.userLoop(reactor.seconds())

        self.looping = False
    
    @defer.deferredGenerator
    def __loop__(self):
        self.__checkFile__()
        self.looping = True
        if not self.isRunning:
            d = defer.waitForDeferred(defer.Deferred())
            yield d
            self.looping = False
        else:
            for line in self.__fd__.readlines():
                if line:
                    d = defer.maybeDeferred(self.readLine, line)
                    d = defer.waitForDeferred(d)
                    yield d
                    res = d.getResult()
            if self.isRunning:
                d = defer.maybeDeferred(self.userLoop, reactor.seconds())
                d = defer.waitForDeferred(d)
                yield d
                res = d.getResult()
        self.looping = False

    def userLoop(self, time):
        pass

    def __shutdown__(self):
        try:
            self.__fd__.close()
        except:
            self.__fd__ = None
        return self.runFinal()

    def __repr__(self):
        return "<Standard Handler for file:%s>" % self.logFileName
                
    def readLine(self, line):
        pass

    def runFinal(self):
        pass

class deferHandler(object):
    loopInst = None
    def __init__(self, handler):
        if isinstance(handler,logFileHandlers):
            self.handler = handler
        else:
            raise Exception("Invalid logfile Parser")
        reactor.addSystemEventTrigger('before','shutdown',self.finalClose)

    def finalClose(self):
        if self.loopInst:
            print "Sending shutdown to %s" % self.handler
        self.handler.isRunning = False
        self.handler.isShuttingDown = True
        reactor.callLater(0.1, self.handler.__shutdown__)
        #d = self.handler.__shutdown__()

    def loop(self, firstPass=False):
        reactor.callLater(0.5, self.loop, True)
        if not firstPass:
            print "Handler started for %s" % self.handler
        else:
            if not self.handler.looping:
                return self.handler.__loop__()
            else:
                print "Loop is currently Running for %s" % self.handler

    def callBack(self, res):
        if res:
            print res
        self.loopInst = None

