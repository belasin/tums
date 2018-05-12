#!/usr/bin/python
import sys
sys.path.append('.')

try:
    import Settings
    sys.path.append(Settings.BaseDir)
except:
    # The usual place 
    sys.path.append('/usr/local/tcs/tums')

# Nevow imports
from nevow import rend, loaders, tags
from twisted.application import service, internet, strports, app
from twisted.web import server, static
from twisted.python import failure
from twisted.internet import reactor
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

# Tums imports
import Tree, Realm, Database, xmlrpc
from Core import Utils, FlowCollector
from Pages import Index

try:
    db = Database.DatabaseBroker('mysql://exilog:exilogpw@localhost/exilog')
except Exception, c:
    print "No database to initialise" 
    print c 
    print "--- End of DB failure ---" 

try:
    l = open(Settings.BaseDir+'/initial').read()
    if "1" in l:
        #Settings.BaseDir = '/usr/local/tcs/tums'
        db = "FIRSTRUN"
except:
    print "No first"
    # Not first run
    pass

def pingDB(db):
    def noCB(_):
        print "DB Keepalive"
        pass
    def noEB(_):
        print _
        pass
    db.getLastMessages().addCallbacks(noCB, noEB)

    reactor.callLater(4000, pingDB, db)

def initialiseDB(db):
    d = db.startup()
    def strap(_):
        print "Database started ", _
        reactor.callLater(2, pingDB, db)
    return d.addCallback(strap)

if type(db) == Database.DatabaseBroker:
    reactor.callWhenRunning(initialiseDB, db)

xmlClient = xmlrpc.XMLRPCClient()

reactor.callLater(1, xmlrpc.threadQueueLoop, xmlClient)

reactor.callLater(120, xmlClient.selfChecks)
reactor.callLater(300, xmlClient.glsaAutoCheck)

def deploy():
    return xmlrpc.server.Site(xmlrpc.ClientServer())

application = service.Application('TUMS')

theberpc = internet.SSLServer(int(Settings.thebePort), deploy(), xmlrpc.ServerContextFactory())
flowcollector = internet.UDPServer(9685, FlowCollector.flowCollector())
tumsSSL = internet.SSLServer(9683, Realm.deploy(db), xmlrpc.ServerContextFactory())
tums = internet.TCPServer(9682, Realm.deploy(db))

theberpc.setServiceParent(application)
flowcollector.setServiceParent(application)
tumsSSL.setServiceParent(application)
tums.setServiceParent(application)

## TwistD bootstrap code
nodaemon = 0
log = '/var/log/tums.log'
if len(sys.argv) > 1:
    if sys.argv[1] == "-n":
        nodaemon = 1
        log = None

Utils.startTwisted(application, Settings.BaseDir, nodaemon, log, Settings.BaseDir)
