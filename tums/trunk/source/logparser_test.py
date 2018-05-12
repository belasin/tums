#!/usr/bin/python
import sys
sys.path.append('.')
sys.path.append('/usr/lib/python2.5/site-packages')
sys.path.append('/usr/lib/python2.5')
sys.path.append('/usr/local/tcs/tums/lib')
sys.path.append('/usr/local/tcs/tums')

from twisted.internet import reactor
from LogParser import Squid
from Core import Utils
from twisted.application import service, internet, strports, app
import Database
import Settings
import LogParser

def DBKeepAlive(db):
    def handleResult(_, failed=False):
        if failed:
            print "Error Pinging DB"
            print _ 
        else:
            print "DB Keepalive"
            pass

    db.pingDB().addCallback(handleResult).addErrback(handleResult, True)
    reactor.callLater(1000, DBKeepAlive, db)

def initDB(dbList):
    callbackList = []
    for db in dbList:
        print "Starting DB "
        callbackList.append(db.startup())
        reactor.callLater(30, DBKeepAlive, db)

    def dbStarted(db):
        print "Database Started"

    return defer.DeferredList(callbackList).addCallback(dbStarted)

def init():
    squidDB = Database.MySAR('mysql://mysar:mysar@localhost/mysar')
    squidDB.startup()
    reactor.callLater(120, DBKeepAlive, squidDB)
    squidhandler = Squid.Parser('/var/log/squid/access.log',squidDB)
    #eximhandler = LogParser.logFileHandlers('/var/log/exim4/mainlog')
    sdHandler = LogParser.deferHandler(squidhandler)
    #edHandler = LogParser.deferHandler(eximhandler)
    reactor.callInThread(sdHandler.loop)

reactor.callWhenRunning(init)
reactor.suggestThreadPoolSize(5)
application = service.Application('TUMS-Logparser')
## TwistD bootstrap code
nodaemon = 0
log = '/var/log/tums-logparser.log'
if len(sys.argv) > 1:
    if sys.argv[1] == "-n":
        nodaemon = 1
        log = None

nodaemon = 1
log = None


if __name__ == '__main__':
    Utils.startTwisted(application, Settings.BaseDir, nodaemon, log, Settings.BaseDir, pidfile='/var/run/tums-logparser.pid')
