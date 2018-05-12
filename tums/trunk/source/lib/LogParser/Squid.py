from LogParser import logFileHandlers
from twisted.internet import defer
from datetime import datetime

class Parser(logFileHandlers):

    writer = None

    sessionList = []

    purgeSessionList = []

    userHosts = {}

    userIps = {}

    currentSites = {}

    currentSitesDate = None

    userEntries = {}

    lastTime = 0

    parseFromTime = 0

    currentTimeDiff = 0

    inCacheStatus = ['TCP_HIT','TCP_REFRESH_HIT','TCP_DENIED','TCP_REF_FAIL_HIT','TCP_NEGATIVE_HIT','TCP_MEM_HIT','TCP_OFFLINE_HIT']

    def __init__(self, filename, writer=None):
        if not writer:
            writer = DummyWriter()
        self.writer = writer
        logFileHandlers.__init__(self,filename)

    def readLine(self, line):
        """Parses the squid log entry and instantiates a session or populates existing sessions"""
        def handleLastEntryTime(res):
            try:
                self.parseFromTime = float(res)
            except:
                self.parseFromTime = 1
            return checkTime()
        
        def checkTime():
            if thistime <= self.parseFromTime:
                return
            else:
                return self.parseLine(currentLine, thistime)

        currentLine = line.rstrip().split()
        try:
            thistime = float(currentLine[0])
        except:
            return 

        if not self.parseFromTime: #Lets zoom to the last entry which was loaded in the db so make sure that these entries are all new
            return self.writer.getLastEntryTime().addCallback(handleLastEntryTime)
        else:
            return checkTime()
        
    def parseLine(self, currentLine, thistime):
        if self.currentSitesDate != datetime.fromtimestamp(thistime).date():
            currentSites = {}
            userEntries = {}
            self.currentSitesDate = datetime.fromtimestamp(thistime).date()
        if self.lastTime:
            self.currentTimeDiff += thistime - self.lastTime
        if self.currentTimeDiff > 10:
            for session in self.sessionList:
                session.incrementTimer(self.currentTimeDiff)
            self.currentTimeDiff = 0
            self.purge()
        self.lastTime = thistime
        #Format the data
        data = {
            'time': thistime,
            'reqBytes': int(currentLine[1]),
            'inBytes': int(currentLine[4]),
            'status': currentLine[3].split('/'),
            'type': currentLine[5],
            'userHost': currentLine[2],
            'fullUrl': currentLine[6],
            'connect': currentLine[8].split('/'),
            'username': len(currentLine[7]) > 1 and currentLine[7] or None,
            'cacheMode': False,
            'site': None,
            'contentType': len(currentLine[9]) > 1 and currentLine[9] or None
        }
        #Generate a website host address
        hostdet = currentLine[6].split('/')
        if len(hostdet) == 1:
            if int(data["status"][1]) >= 200 and int(data["status"][1]) < 400:
                #hostdet = hostdet[0]
                hostdet = ['','',hostdet[0]]
        if data["status"][0] in self.inCacheStatus:
            data["cacheMode"] = True
        if len(hostdet) > 2:
            data['site'] = '/'.join(hostdet[0:3])
            #Check the last entry from the domain is not an int
            try:
                lastval = int(hostdet[2].split(".")[-1].split(":")[0])
            except Exception, _exp:
                lastval = None
            if hostdet[2] != data['connect'][1] and not lastval: #If the domain is not in the connect string i.e. it is not the direct connect then lets take the last 2 / 3 elements to build a host
                hostdet = hostdet[2].split('.') #Split by the dot
                if len(hostdet[-1]) > 2: #If it is a .com .net .org this
                    hostdet = ".".join(hostdet[-2:])
                else: #otherwise 
                    if len(hostdet) > 2: #if the number of domain elements is bigger than 2
                        hostdet = ".".join(hostdet[-3:]) #Then take the last 3 elements
                    else:
                        hostdet = ".".join(hostdet) #otherwise take the whole damn thing
            else:
                hostdet = hostdet[2]
        else:
            hostdet = data["fullUrl"]

        data["webHost"] = hostdet
        
        return self.handleEntry(data) #Create the session and write it

    def handleEntry(self, data):
        def gotHost(res=None):
            if not res:
                data["userIP"] = self.userIps[data["userHost"]]
            else:
                self.userIps[data["userHost"]] = res
                data["userIP"] = res
            
            """Session Logic start here"""
            #Does the userhost exist in memory ?
            if data["userHost"] not in self.userHosts:
                #if not create a user entry
                self.userHosts[data["userHost"]] = {}
            #Does a session exist?
            if data["webHost"] not in self.userHosts[data["userHost"]]:
                #Session does not exist so create it
                session = Session(data["userHost"],data["webHost"], data["time"], self.writer)
                d = session.addEntry(data)
                session.regTimeoutCallback(self.handleSessionTimeout)
                self.sessionList.append(session)
                self.userHosts[data["userHost"]][data["webHost"]] = session
            else:
                #Session exists then add entry
                d = self.userHosts[data["userHost"]][data["webHost"]].addEntry(data)
            return d

        def gotSite(res=None):
            """Callback with the current site details"""
            if not res:
                data["siteEntry"] = self.currentSites[data["webHost"]]
            else:
                self.currentSites[data["webHost"]] = res
                data["siteEntry"] = res

            """Caching mechanism for user host entries, we check if we have the entry on hand and if not we must fetch it, once the fetch is successfull the result is sent by callback of gotHost"""
            if data["userHost"] in self.userIps:
                return gotHost()
            else:
                return self.writer.getHostEntry(data["userHost"]).addCallback(gotHost)

        def gotUser(res=None):
            if not res:
                if data["username"]:
                    data["userEntry"] = self.userEntries[data["username"]]
                else:
                    data["userEntry"] = self.userEntries[data["userHost"]]
            else:
                print res
                self.userEntries[data["username"]] = res
                self.userEntries[data["userHost"]] = res
                data["userEntry"] = res

            """Check if we have an entry of the current site, if not then we let the db know to fetch it can once it has the site to fire the gotSite callback"""
            if data["webHost"] in self.currentSites:
                return gotSite()
            else:
                return self.writer.getSite(self.currentSitesDate,data["webHost"]).addCallback(gotSite)

        if data["username"]:
            if data["username"] in self.userEntries:
                return gotUser()
        if data["userHost"] in self.userEntries:
            return gotUser()
        else:
            return self.writer.getUserDetails(self.currentSitesDate,data["userHost"],data["username"]).addCallback(gotUser)

    def userLoop(self, time):
        """Clear out sessions when they expire reallife"""
        for session in self.sessionList:
            if time - session.startTime > session.maxTime:
                session.handleTimeout()
        self.purge()

    def handleSessionTimeout(self, session):
        self.purgeSessionList.append(session)

    def purge(self):
        while self.purgeSessionList:
            session = self.purgeSessionList.pop()
            if session in self.sessionList:
                self.sessionList.remove(session)
            if session.siteHost in self.userHosts[session.userHost]:
                del self.userHosts[session.userHost][session.siteHost]

    def runFinal(self):
        pass

    def __repr__(self):
        return "<Squid.Parser log file: %s>" % self.logFileName

class Session(object):
    
    entries = []
    
    siteHost = ""

    userHost = ""

    sessionID = None

    startTime = 0

    endTime = 0

    inBytes = 0

    outBytes = 0

    cacheIn = 0

    cacheOut = 0

    timeout = 300 #Seconds till session should expire

    maxTime = 3600

    hostnamesID = None

    sitesID = None

    usersID = None

    currentTime = 0

    currentCounter = 0

    timeout_fn = None

    writer = None

    def __init__(self, userHost, siteHost, startTime, writer):
        self.writer = writer
        self.siteHost = siteHost 
        self.userHost = userHost
        self.startTime = startTime

    def addEntry(self, data):
        """addEntry takes a data request that a client performs and tallies tha data and then writes the database entry"""
        def writeEntry(res=None):
            return self.writer.addEntry(data, self)
        def handleSessionCreate(res):
            self.sessionID = res
            return writeEntry()
        self.entries.append(data)
        self.endTime = data["time"] + 5
        self.currentTime = self.endTime - self.startTime
        self.inBytes += data["inBytes"]
        self.outBytes += data["reqBytes"]
        self.hostnamesID = data["userIP"]["id"]
        self.sitesID = data["siteEntry"]["id"]
        self.usersID = data["userEntry"]["id"]
        if type(self.hostnamesID) == list:
            self.hostnamesID = self.hostnamesID[0]
        if type(self.sitesID) == list:
            self.sitesID = self.sitesID[0]
        if type(self.usersID) == list:
            self.usersID = self.usersID[0]
        if data["cacheMode"]:
            self.cacheIn += data["inBytes"]
            self.cacheOut += data["reqBytes"]
        self.resetSessionTimer()
        if not self.sessionID:
            return self.writer.createSession(self).addCallback(handleSessionCreate)
        else:
            return self.writer.updateSession(self).addCallback(writeEntry)

    def resetSessionTimer(self):
        self.currentCounter = 0
        if self.currentTime > self.maxTime:
            self.handleTimeout()
    
    def incrementTimer(self,seconds):
        self.currentCounter += seconds
        if self.currentCounter > self.timeout:
            return self.handleTimeout()

    def handleTimeout(self):
        def handleRes(res, err=False):
            if callable(self.timeout_fn):
                self.timeout_fn(self)
            return True
        self.endTime += 5
        self.currentTime = self.endTime - self.startTime
        #handleRes()

        d = defer.maybeDeferred(self.writer.closeSession, self)
        d.addCallback(handleRes).addErrback(handleRes, True)
        return d
    
    def regTimeoutCallback(self,fn):
        self.timeout_fn = fn

    def __repr__(self):
        return "<User Web Session:%s,%s,%s,%s,%s,%s>" % (
            self.userHost,
            self.siteHost,
            datetime.fromtimestamp(self.startTime),
            datetime.fromtimestamp(self.endTime),
            self.currentTime,
            self.inBytes+self.outBytes
        )

class DummyWriter(object):

    def getLastEntryTime(self):
        d = defer.Deferred()
        d.callback(1)
        return d

    def getHostEntry(self, ipAddr):
        return None

    def getSite(self, date, site):
        return None

    def createSession(self, session):
        d = defer.Deferred()
        print "WRITER: Session Create %s" % session
        d.callback(1)
        return d

    def closeSession(self, session):
        d = defer.Deferred()
        print "WRITER: Session CloseWrite %s" % session
        return d

    def addEntry(self, data, sessionID):
        d = defer.Deferred()
        print "WRITER: Data Add %s sessionID" % data
        d.callback(None)
        return d
