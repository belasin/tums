#!/usr/bin/python
from enamel import authentication, deployment, pages, servers, storage, deferreds, tags
from enamel import sql
import enamel
import cPickle, time, os

# Twisted extras
from twisted.internet import reactor

# Our stuff
import Settings, Database

# Pages
from Pages import Index

# Thebe 2 protocol
from ThebeProtocol import proto, xmlc, thive

from lib import rrd, system
# Construct a message handler

DEBUG = False

def noise(txt):
    if DEBUG:
        print txt

def BlankCallback(_):
    print _

class MyMessageHandler(thive.ThebeMessageHandler):
    def __init__(self, *a, **kw):

        thive.ThebeMessageHandler.__init__(self)

        self.enamel = None
        self.userBurst = {}
        self.dataQueue = []
        self.updateBurst = {}

        reactor.callLater(60, self.runRRDQueue)

    def thive_user(self, source, messageId, params, data):
        locator = params[0]
        # In burst mode we erase recieved records from the internal store
        # this happens now, because we need to be very fast
        if self.userBurst.get(source, False):
            self.userBurst[source]['cnt'] += 1
            if locator in self.userBurst[source]['myusers']:
                del self.userBurst[source]['myusers'][locator]
               
        detail = {}
        for i in data.split('`'):
            if i:
                k, v = tuple(i.split(':', 1))
                detail[k] = v
               
        def processRecord(user):
            if not user:
                self.enamel.storage.addServerUser(source, detail)
            else:
                self.enamel.storage.updateServerUser(source, user[0], detail)
              
            self.sendMessage(source, "OK", messageId)
             
        return self.enamel.storage.findServerUser(source, detail['name'], detail['domain']).addCallback(processRecord)

    def runRRDQueue(self):
        print "Running rrd queue"
        if self.dataQueue:
            blck = open(Settings.BaseDir+'tscript.sh','wt')
            blck.write('#!/bin/bash\n')
            print "%s items to process" % len(self.dataQueue)
            for i in self.dataQueue:
                source, name, tn, value, gauge = i
                blck.write(rrd.updateRRACMD(source, name, tn, value, gauge=gauge)+'\n')
            self.dataQueue = []
            blck.close()
            os.chmod('tscript.sh', 0755)
            def done(_):
                print done
            system.system(Settings.BaseDir+'tscript.sh').addCallback(done)

        reactor.callLater(60, self.runRRDQueue)

    def updateRRD(self, tn, source, name, value, gauge=False):
        self.dataQueue.append((source, name, tn, value, gauge))

    def thive_perfdat(self, source, messageId, params, data):
        """
        Performance data items - params[0] contains performance data type (disk, network, load etc)
        'data' contains the data for this performance record to be understood by the corresponding
        type parser.
        """
        noise( "Performance data type %s of: %s" % (params[0], data))
        if len(params) > 1:
            # We have time
            tn = int(params[1])
        else:
            tn = int(time.time())

        def ifaces(data):
            accepted = ['eth', 'ppp', 'tap']
            for i in data.split(','):
                lm = i.split(':')
                name = 'iface-%s' % lm[0]
                if i[:3] in accepted:
                    self.updateRRD(tn, source, name+'i', int(float(lm[1])))
                    self.updateRRD(tn, source, name+'o', int(float(lm[2])))

        def ioload(data):
            ln = data.split(':')

            self.updateRRD(tn, source, 'load-5',  float(ln[0]), True)
            self.updateRRD(tn, source, 'load-10', float(ln[1]), True)
            self.updateRRD(tn, source, 'load-15', float(ln[2]), True)

            self.updateRRD(tn, source, 'vmstat-i', int(ln[3]), True)
            self.updateRRD(tn, source, 'vmstat-o', int(ln[4]), True)

        def eximstat(data):
            ln = data.split(':')
            self.updateRRD(tn, source, 'exim-rcvd', int(ln[0]))
            self.updateRRD(tn, source, 'exim-delv', int(ln[1]))
            self.updateRRD(tn, source, 'exim-rejc', int(ln[2]))

        def mailq(data):
            ln = data.split()
            bvol, mvol = map(int, ln)
            self.updateRRD(tn, source, 'mailq-bvol', bvol/1024)
            self.updateRRD(tn, source, 'mailq-mvol', mvol)

            # Trigger alerts here....
            if bvol > 78643200:
                # If the volume is high, we don't really care how many messages are the cause
                self.enamel.storage.logMessage('CRITICAL', 'Message volume has exceeded 75MB. Currently %sMB' % (bvol/(1024*1024)), source
                    ).addBoth(BlankCallback)
            elif mvol > 300:
                self.enamel.storage.logMessage('CRITICAL', 'Message volume has exceeded 300 messages. Currently %s messages' % (mvol), source
                    ).addBoth(BlankCallback)

        def diskstat(data):
            # Not sure what to do with this yet
            ln = data.split(';')

            for disk in ln:
                device, mount, size,  avail = disk.split(':')
                size = int(size)
                avail = int(avail)

                mountpart = mount.replace('/', 'SLASH')

                self.updateRRD(tn, source, 'disk-%s' % mountpart, size - avail, True)

        l = {
            'ifaces': ifaces,
            'ioload': ioload,
            'eximstat': eximstat,
            'diskstat': diskstat,
            'mailqueue' : mailq
        }

        l[params[0]](data)
        
        self.sendMessage(source, "OK", messageId)

    def thive_userburst(self, source, messageId, params, data):
        """ Client is requesting a user burst mode.
            We consider all users passed during this time to be an absolute for that server. 
            Any users in the database which are not passed after the burst must be deleted from the database.
            Passed with the burst notice is the number of users that will be bursted, this is to ensure
            asynchronous updates are waited for before the noburst notice is adhered to.
            """
        noise("Newburst %s" % source)
        def startBurst(users):
            self.userBurst[source] = {
                'start':time.time(),
                'cnt':0,
                'need':int(params[0]),
                'myusers':dict(tuple([("%s@%s" % (i[3], i[2]), i[0]) for i in users]))
            }
            noise(self.userBurst[source])
            self.sendMessage(source, "OK", messageId)

        return self.enamel.storage.getServerUsers(source).addCallback(startBurst)

    def thive_usernoburst(self, source, messageId, params, data, cnt=0):
        """ Symbolises the end of a user burst sequence. 
            Users not transfered by the time 'cnt' (users processed) reaches 'need' (users sent)
            are discarded from the database
        """
        noise(self.userBurst[source])
        def done(_):
            noise(_)

        if self.userBurst[source]['cnt'] != self.userBurst[source]['need']:
            if cnt < 5:
                cnt += 1
                noise("Burst data outstanding. Waiting" + '.'*cnt)
                reactor.callLater(1, self.thive_usernoburst, source, messageId, params, data, cnt)
            else:
                print "Burst timeout. oh dear..."

            return  # Don't delete anything when our burst is incomplete...

        if self.userBurst.get(source, False):
            for uri,id in self.userBurst[source]['myusers'].items():
                self.enamel.storage.delServerUser(source, id=id).addCallback(done)

        self.userBurst[source] = False
        self.sendMessage(source, "OK", messageId)

    def thive_deluser(self, source, messageId, params, data):
        user = params[0]
        domain = params[1]
        def done(_):
            self.sendMessage(source, "OK", messageId)
        return self.enamel.storage.delServerUser(source, name=user, domain=domain).addCallback(done)

    def thive_config(self, source, messageId, params, data):
        # params : 1 Config profile name
        # data   : cPickle encoded profile
        profileName = params[0]
        #print profileName, data
        l = open('/usr/home/thebe/thebe2/configs/%s%s.py' % (source, profileName), 'wt')
        conf = cPickle.loads(data)
        for k,v in conf.items():
            l.write('%s = %s\n' % (k,v))
        l.close()
        self.sendMessage(source, "OK", messageId)

    def thive_event(self, source, messageId, params, data):
        # An event sent by the TUMS host, like an error or fatal issue
        self.enamel.storage.logMessage(params[0], data, source).addBoth(BlankCallback)

        self.sendMessage(source, "OK", messageId)

    def thive_newupdate(self, source, messageId, params, data): 
        packageName = params[0]
        self.sendMessage(source, "OK", messageId)
        # Try and negotiate whether this is a new burst or still in a burst
        newBurst = False
        print self.updateBurst
        if self.updateBurst.get(source, None):
            if self.updateBurst[source] + 120 < time.time():
                newBurst = True
        else:
            self.updateBurst[source] = time.time()
            newBurst = True

        def addNew(_):
            print packageName
            self.enamel.storage.addUpdate(source, packageName).addBoth(BlankCallback)
        if newBurst:
            print "Flushing old updates..."
            self.enamel.storage.flushUpdates(source).addCallbacks(addNew, BlankCallback)
        else:
            addNew(None)

    def thive_updateApplied(self, source, messageId, params, data):
        packageName = params[0]
        self.sendMessage(source, "OK", messageId)
        self.enamel.storage.updateApplied(source, packageName).addBoth(BlankCallback)

    def thive_tumsversion(self, source, messageId, params, data):
        self.sendMessage(source, "OK", messageId)
        self.enamel.storage.updateServerVersion(source, params[0]).addBoth(BlankCallback)

    def sendCommand(self, destination, command, params, data):
        print "Sending ", command, destination, params, data
        self.sendMessage(destination, "%s:%s:%s" % (command, ' '.join(params), data))

messageHandler = MyMessageHandler()
thebeProto = proto.DPFactory("THUSAMASTER1", messageHandler)
thebeProto.protocol = proto.DPServer

class ThebeAvatar:
    def __init__(self, username = "", password = "", id = 0, gids = [0] ):
        print "Got UID", id
        self.uid = id
        self.gids = gids
        self.username = username

class ThebeAuth(authentication.DatabaseAuthenticator):
    def handleAuthenticationResult(self, result, username, password):
        print result, username, password
        def gotGids(gid):
            # Get the gid
            print gid
            if gid:
                gids = [i[2] for i in gid]
            else:
                # Set -1 here if the user is not in any group at all - we can't
                # assume that they are 1 (Thusa Group)
                gids = [0]
            return ThebeAvatar(username, password, result[0], gids)
        
        def gotBusted(r):
            print r
            print "Yikes.."
            return ThebeAvatar(username, password, result[0], [-1])

        if result:
            print "Hello!"
            return self.enamel.storage.getGids(result[0]).addCallbacks(gotGids, gotBusted)
        else:
            raise authentication.UnauthorizedLogin()
from OpenSSL import SSL

class ServerContextFactory:
    """ Factory for SSL context generation, see genkey.sh for generating
        OpenSSL certificates. """
    def getContext(self):
        """Create an SSL context."""
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        ctx.use_certificate_file(Settings.BaseDir + '/server.pem')
        ctx.use_privatekey_file(Settings.BaseDir + '/privkey.pem')
        return ctx

class ThebeWeb(enamel.Enamel):
    """ Thebe Web management frontend """
    indexPage = Index.Index
    loginPage = Index.Login
    # XXX change this to MySQL at best convenience
    storage = Database.ThebeStorage('mysql://thebe:thebe@localhost/thebe')
    tcsClients = messageHandler
    tcsMaster = thebeProto.master
    #proto.DPMaster # DP Master contains core of HIVE connections
    authenticator = ThebeAuth 
    anonymousAccess = False
    server = servers.TwistedSSL
    port = 8000

    vhostEnable = True

    def __init__(self, *a, **kw):
        """ Overide here to add storage to our tcsClients THIVE protocol """
        enamel.Enamel.__init__(self, *a, **kw)
        self.tcsClients.storage = self.storage
        # Add our self to the messageHandler as a parent for database access
        self.tcsClients.enamel = self

    def site(self):
        return (enamel.Enamel.site(self)[0], ServerContextFactory())

    # Our custom stuff
    thebeProto = thebeProto
    Settings = Settings
IThebeWeb = ThebeWeb()

class ThebeProto:
    """ Thebe HIVE protocol instance"""
    server = servers.TwistedSSL
    storage = None
    port = 54321

    def site(self):
        return (thebeProto, xmlc.ServerContextFactory())

class ThebeXMLRPC:
    """ Thebe XMLRPC Web services backend """
    server = servers.TwistedSSL
    storage = None
    port = 9680

    def site(self):
        from twisted.web import server
        return (server.Site(xmlc.ThebeXML(IThebeWeb)), xmlc.ServerContextFactory())

deployment.run('thebe', [ 
    IThebeWeb, 
    ThebeXMLRPC(), 
    ThebeProto()
], pidLoc="./")

