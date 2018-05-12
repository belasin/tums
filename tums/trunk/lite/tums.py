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
from twisted.internet import reactor, defer
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
from twisted.internet.protocol import ClientCreator

# Tums imports
import Tree, Realm, Database, xmlrpc, bot, lang, Checks
from Core import Utils, Auth, WebUtils
from Pages import Index, Users

# THIVE
from ThebeProtocol import proto, thive

# General 
import cPickle, os 

if len(sys.argv) > 1:
    if sys.argv[1] == "--radauth":
        if len(sys.argv) > 3:
            username = sys.argv[2]
            password = sys.argv[3]
            radauth = Auth.RadiusLDAPAuthenticator()
            res = radauth.authenticateUser(username, password)
            if res:
                uids = []
                lastIndex = 0
                index = 0
                try:
                    l = open('/tmp/radpool')
                    for i in l:
                        lastIndex += 1
                        j = i.strip('\n').strip()
                        if j:
                            if j == username:
                                index = lastIndex
                            uids.append(j)
                    l.close()
                except:
                    # no pool 
                    pass

                if index:
                    # Already assigned:
                    thisIndex = index
                else:
                    # Never seen
                    index = len(uids)+1
                    if index > 252:
                        # If our pool is extinct - we need a new one
                        index = 1
                        uids = [username]
                    else:
                        uids.append(username)
                l = open('/tmp/radpool', 'wt')
                l.write('\n'.join(uids))
                l.close()

                print "Framed-Protocol = PPP" 
                print "Service-Type = Framed-User"
                print "Framed-Compression = Van-Jacobson-TCP-IP"
                print "Framed-IP-Address = 10.10.10.%d" % (index+1)
                print "Fall-Through = Yes"
                sys.exit(0)
            sys.exit(255)
        else:
            print "Invalid parameters"
            sys.exit(255)

try:
    db = Database.DatabaseBroker('mysql://exilog:exilogpw@localhost/exilog')
    squidDb = Database.MySAR('mysql://mysar:mysar@localhost/mysar')
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

def pingDB(db, squidDb):
    def noCB(_):
        print "DB Keepalive"
        pass
    def noEB(_):
        print _
        pass

    db.getLastMessages().addCallbacks(noCB, noEB)
    squidDb.getConfig().addCallbacks(noCB, noEB)

    reactor.callLater(4000, pingDB, db, squidDb)

def initialiseDB(db, squidDb):
    d = db.startup()
    d2 = squidDb.startup()
    def strap(_):
        print "Database started ", _
        reactor.callLater(2, pingDB, db, squidDb)
        #reactor.connectTCP(bot.server, 6667, bot.tbFactory())

    return defer.DeferredList([d, d2]).addCallback(strap)

if type(db) == Database.DatabaseBroker:
    reactor.callWhenRunning(initialiseDB, db, squidDb)

xmlClient = xmlrpc.XMLRPCClient()

class ThebeMessenger(thive.ThebeMessageHandler):
    files = {}
    
    def thive_user(self, messageId, params, data):
        """ User record updated/new. 
            if the user exists, initialise a call to Users.editPage otherwise 
            pass to Users.addPage

            Plain text password is passed from server down to client node.
        """
        locator = params[0] # A resource locator (userid@domain)
        type = params[1]

        newdata = {}
        for kv in data.split('`'):
            if kv:
                k, v = kv.split(':',1)
                newdata[k] = v
        tumsUser = []
        squid = False
        admin = False

        for i in newdata['emp'].split('+'):
            if 'squid' in i:
                squid = True
            if 'tumsAdmin' in i:
                admin = True
            if 'tumsUser' in i:
                tumsUser = i.strip(']').split('[')[-1].split(',') # list in brackets.
        
        flags = {
            'vpn':False,
            'ftpE':False,
            'ftpG':False,
            'copyto': u"",
        }

        flagsi = newdata['flags'].split('+')
        f = ['vpn', 'ftpE', 'ftpG']
        for n, d in enumerate(flagsi[0]):
            flags[f[n]] = d == "-"
        
        if len(flagsi) > 1:
            flags['copyto'] = flagsi[1]

        submitData = {
            'userPermissions.employeeType':     squid, 
            'userPermissions.tumsUser':         tumsUser,
            'userPermissions.tumsAdmin':        admin,
            'userPermissions.accountStatus':    newdata['active'] == "active",

            'userSettings.uid':             newdata['name'],
            'userSettings.userPassword':    newdata['password'], 
            'userSettings.sn':              unicode(newdata['sn']), 
            'userSettings.givenName':       unicode(newdata['giveName']),

            'mailSettings.vacation':        newdata['vacation'],
            'mailSettings.vacen':           newdata['vacEnable'] == "True",

            'userPermissions.copyto':          flags['copyto'],
            'userAccess.vpnEnabled':        flags['vpn'],
            'userAccess.ftpEnabled':        flags['ftpE'],
            'userAccess.ftpGlobal':         flags['ftpG'],
        }

        # Initialise all the psuedo-fields
        for i in range(10):
            submitData['mailSettings.mailAlternateAddress%s' % i] = u""
            submitData['mailSettings.mailForwardingAddress%s' % i] = u""

        # Teardown our real data 
        for n, d in enumerate(newdata['mailAlias'].split('+')):
            submitData['mailSettings.mailAlternateAddress%s' % n] = unicode(d)

        for n, d in enumerate(newdata['mailForward'].split('+')):
            submitData['mailSettings.mailForwardingAddress%s' % n] = unicode(d)

        # Dummy form
        form = None
        #print submitData

        # decide which instance to create
        if type == "new":
            # Add new user (Not implemented on Thebe yet...
            addInstance = Users.addPage()
            p = addInstance.submitForm(None, None, submitData)
        else:
            #print "Edit ", locator
            # Alteration of existing user.
            try:
                editInstance = Users.editPage(None, (None,None,None,None), locator.split('@')[0], newdata['domain'])
                p = editInstance.submitForm(None, None, submitData)
            except Exception, e:
                print e, "ERROR"

        self.sendMessage(self.master.hiveName, 'OK', messageId)

    def thive_updatepackage(self, messageId, params, data):

        def sendPackageNames(names):
            for name in names.replace('\n', ' ').split():
                self.handler.sendMessage(self.handler.master.hiveName, "newupdate:%s:--" % (name))

        def updateComplete(ans):
            self.sendMessage(self.master.hiveName, 'OK', messageId)
            if os.path.exists('/etc/debian_version'):
                r = WebUtils.system(
                    'debsecan --only-fixed --suite etch --format packages'
                )
            else:
                r = WebUtils.system(
                    'glsa-check -ln affected 2>&1 | grep "......-.. \[N\]" | sed \'s/.*N\\] \\(.*\\):.*/\\1/\''
                )

            return r.addCallback(sendPackageNames)

        if os.path.exists('/etc/debian_version'):
            # Debian package update
            cmd = "DEBIAN_FRONTEND=\"noninteractive\" aptitude -q -y install "
            return WebUtils.system(cmd + ' '.join(params)).addCallback(updateComplete)
        else:
            return WebUtils.system('; '.join(['emerge %s' % i for i in params])).addCallback(updateCompleted)

    def thive_useprofile(self, messageId, params, data):
        """ Switch our running profile. """
        profile = params[0]

        # Make sure we know about this profile

        l = os.listdir('/usr/local/tcs/tums/profiles/')
        if profile+".py" in l:
            newProfile = profile+".py"
            l = open(Settings.BaseDir + '/runningProfile', 'wt')
            l.write(newProfile)
            l.close()
            l = open(Settings.BaseDir + '/currentProfile', 'wt')
            l.write(newProfile)
            l.close()
            WebUtils.system("cp %s/%s %s/config.py; /usr/local/tcs/tums/configurator -r" % (Settings.BaseDir, newProfile, Settings.BaseDir))
        else:
            self.sendMessage(self.master.hiveName, 'log:PNF001:Profile %s not found' % newProfile)

        self.sendMessage(self.master.hiveName, 'OK', messageId)

    def thive_getProfile(self, messageId, params, data):
        profile = params[0]

        l = open ('%s/profiles/%s.py' % (Settings.BaseDir, profile))
        
        conf = cPickle.loads(data)
        for k,v in conf.items():
            l.write('%s = %s\n' % (k, v))
        l.close()

        self.sendMessage(self.master.hiveName, 'OK', messageId)


    def thive_FILE(self, messageId, params, data):
        """Get a file through THIVE
        @param params: Parameters of this argument. Filename
        @param data: The data for this file"""
        #print "Receiving file ", params[0]
        self.files[params[0]] = open(params[0], 'wt')
        self.files[params[0]].write(data)
        self.files[params[0]].flush()
        self.sendMessage(self.master.hiveName, 'OK', messageId)

    def thive_FILEP(self, messageId, params, data):
        """ Piece of a file """
        self.files[params[0]].write(data)
        self.files[params[0]].flush()
        self.sendMessage(self.master.hiveName, 'OK', messageId)

    def thive_FILEE(self, messageId, params, data):
        #print "File finished"
        self.files[params[0]].close()
        self.sendMessage(self.master.hiveName, 'OK', messageId)

    def thive_HELO(self, messageId, params, data):
        #print "Hello", params, data
        self.sendMessage(self.master.hiveName, 'OK', messageId)
    
messageHandler = ThebeMessenger()

thebeProto = proto.DPFactory("THUSANULL", messageHandler)
thebeProto.protocol = proto.DPServer

checker = Checks.SelfChecker(messageHandler)

def startTHIVE(name):
    # Got the name of our node
    #thebeProto.master.myName = name
    #thebeProto.hiveAddress = Settings.hiveAddress
    #thebeProto.connectMaster(thebeProto.hiveAddress)
    #reactor.callLater(20, checker.startCheckers)
    print name

reactor.callWhenRunning(xmlClient.checkKey, startTHIVE)

myLang = lang.Text('en')
application = service.Application('TUMS')
tums = internet.TCPServer(9682, Realm.deploy((db, squidDb, myLang, messageHandler)))
tumsSSL = internet.SSLServer(9683, Realm.deploy((db, squidDb, myLang, messageHandler)), xmlrpc.ServerContextFactory())
thebe = internet.SSLServer(54321, thebeProto, xmlrpc.ServerContextFactory())
tums.setServiceParent(application)
tumsSSL.setServiceParent(application)
thebe.setServiceParent(application)

## TwistD bootstrap code
nodaemon = 0
log = '/var/log/tums.log'
if len(sys.argv) > 1:
    if sys.argv[1] == "-n":
        nodaemon = 1
        log = None

Utils.startTwisted(application, Settings.BaseDir, nodaemon, log, Settings.BaseDir, pidfile='/var/run/tums.pid')
