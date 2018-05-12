#!/usr/bin/python
#
#  Vulani TUMS 
#  Copyright (C) Thusa Business Support (Pty) Ltd.
#  All rights reserved
#  
#  tums.py - Core deamon startup file. 
#
import sys
sys.path.append('.')
sys.path.append('/usr/lib/python2.5/site-packages')
sys.path.append('/usr/lib/python2.5')
sys.path.append('/usr/local/tcs/tums/lib')
sys.path.append('/usr/local/tcs/tums')

import Settings

# Clean system
import sweeper
sweeper.cleanAll()

# Nevow imports
#from twisted.internet import epollreactor
#epollreactor.install()
from nevow import rend, loaders, tags
from twisted.application import service, internet, strports, app
from twisted.web import server, static
from twisted.python import failure
from twisted.internet import reactor, defer
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
from twisted.internet.protocol import ClientCreator
from twisted.application.service import IService

# Tums imports
import Tree, Realm, Database, xmlrpc, lang, Checks
from Core import Utils, Auth, WebUtils, confparse, Shorewall
from Pages import Index
from Pages.Users import Edit, Add

import encodings # Import hack to install encodings
from encodings import ascii, utf_8, latin_1

# THIVE
from ThebeProtocol import proto, thive

# General 
import cPickle, os 

# InfoServ
import InfoServ

myLang = lang.Text('en')

if len(sys.argv) > 1:
    if sys.argv[1] == "--radauth":
        if len(sys.argv) > 3:
            conf = confparse.Config()
            username = sys.argv[2]
            if username == 'root':
                print "Invalid parameters"
                sys.exit(255)
            password = sys.argv[3]
            radauth = Auth.RadiusLDAPAuthenticator()
            res = radauth.authenticateUser(username, password)
            if res:
                uids = []
                lastIndex = 0
                index = 0

                # Check for static IP
                if os.path.exists('/etc/openvpn/vpn-ccd/%s' % username):
                    # IP is configured in VPN CCD 
                    l = open('/etc/openvpn/vpn-ccd/%s' % username).read().replace('\n', '')
                    index = int(l.split()[1].split('.')[-1])-1
                else:
                    try:
                        l = open('/usr/local/tcs/tums/radpool')
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
                l = open('/usr/local/tcs/tums/radpool', 'wt')
                l.write('\n'.join(uids))
                l.close()

                print "Framed-Protocol = PPP" 
                print "Service-Type = Framed-User"
                print "Framed-Compression = Van-Jacobson-TCP-IP"
                print "Framed-IP-Address = 10.10.10.%d" % (index+1)
                if conf.RADIUS.get('frameroutes', {}):
                    if username in conf.RADIUS['frameroutes']:
                        ip, cidr = conf.RADIUS['frameroutes'][username].split('/')
                        mask = Utils.cidr2netmask(int(cidr))
                        print "Framed-Route = \"%s %s 1\"" % (ip, mask)
                print "Fall-Through = Yes"
                sys.exit(0)
            sys.exit(255)
        else:
            print "Invalid parameters"
            sys.exit(255)

try:
    db = Database.DatabaseBroker('mysql://exilog:exilogpw@localhost/exilog')
    squidDb = Database.MySAR('mysql://mysar:mysar@localhost/mysar')
    # Make the directory if it doesn't exist..
    if not os.path.exists('/usr/local/tcs/tums/uaxeldb/'):
        os.mkdir('/usr/local/tcs/tums/uaxeldb')
        os.chmod('/usr/local/tcs/tums/uaxeldb', 0777)
    updateDb = Database.UpdateCache('sqlite:////usr/local/tcs/tums/uaxeldb/update.db')
    telDB = Database.CDR('mysql://asteriskcdr:asteriskcdr@localhost/asteriskcdr')
    if not os.path.exists('/tmp/caportal'):
        os.mkdir('/tmp/caportal')
        os.chmod('/tmp/caportal', 0777)

except Exception, c:
    print "No database to initialise" 
    print c 
    print "--- End of DB failure ---" 

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

def initialiseDB(db, squidDb, updateDb, telDB):
    d = db.startup()
    d2 = squidDb.startup()
    d3 = updateDb.startup()
    d4 = telDB.startup()
    def strap(_):
        print "Database started ", _
        # Make sure updatedb is world read/write
        os.chmod('/usr/local/tcs/tums/uaxeldb/update.db', 0777)
        reactor.callLater(2, pingDB, db, squidDb)

        # Clean up our database
        def reAddRow(_, row):
            print "Fixing row", row
            updateDb.addFile(*row)
        
        def deleteDuplicates(fis):
            rows = []

            forDelete = []

            for row in fis:
                type, name, downloads, size = row
                bl = [type, name, downloads, size]
                
                if (bl in rows) and (bl not in forDelete):
                    forDelete.append(bl)
                else:
                    rows.append(bl)

            for row in forDelete:
                updateDb.deleteFile(row[1]).addCallback(reAddRow, row)

        updateDb.getAllFiles().addCallback(deleteDuplicates)

    return defer.DeferredList([d, d2, d3, d4]).addCallback(strap)

if type(db) == Database.DatabaseBroker:
    reactor.callWhenRunning(initialiseDB, db, squidDb, updateDb, telDB)

xmlClient = xmlrpc.XMLRPCClient()

class ThebeMessenger(thive.ThebeMessageHandler):
    #files = {}
    upgradeLock = False
    def thive_user(self, messageId, params, data):
        """ User record updated/new. 
            if the user exists, initialise a call to Users.Edit.editPage otherwise 
            pass to Users.Add.addPage

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
            addInstance = Add.addPage()
            p = addInstance.submitForm(None, None, submitData)
        else:
            #print "Edit ", locator
            # Alteration of existing user.
            try:
                db = (None,None,myLang,self)
                avatar = Auth.UserAvatar('root', '', 0, 0, True, [Settings.defaultDomain])
                editInstance = Edit.editPage(avatar, db, locator.split('@')[0], newdata['domain'])
                p = editInstance.submitForm(None, None, submitData)
            except Exception, e:
                print e, "ERROR"

        self.sendMessage(self.master.hiveName, 'OK', messageId)

    def thive_updatepackage(self, messageId, params, data):
        # Debian package update
        cmd = "DEBIAN_FRONTEND=\"noninteractive\" aptitude -q -y install " + ' '.join(params)

        l = file('/usr/local/tcs/tums/syscripts/periodic', 'at')

        l.write(cmd+'\n')

        l = file('/usr/local/tcs/tums/checkUpdates', 'wt')
        l.write('1')

        self.sendMessage(self.master.hiveName, 'OK', messageId)

    def thive_setOption(self, messageId, params, data):
        """ Called when we get a setOption command
            params : [BaseParameter, Configurator command, Init.d script]
            data: Base parameter set handler (executed in-line) - should act on configBase
        """
        conf = confparse.Config()
        configBase = getattr(conf, params[0])
        
        exec data

        # Persist the operation
        setattr(conf, params[0], configBase)

        self.sendMessage(self.master.hiveName, 'OK', messageId)

    def returnOk(self, messageId):
        self.sendMessage(self.master.hiveName, 'OK', messageId)

    def thive_adminpass(self, messageId, params, data):
        db = (None,None,myLang,self)
        avatar = Auth.UserAvatar('root', '', 0, 0, True, [Settings.defaultDomain])
        # Create a fake edit form
        editInstance = Edit.editPage(avatar, db, 'administrator', Settings.defaultDomain)
        thisForm = editInstance.form_editForm([])
        formData = thisForm.data

        formData['userSettings.userPassword'] = params[0]
        formData['userAccess.ftpGlobal'] = False
        formData['userAccess.vpnEnabled'] = False
        formData['userPermissions.copyto'] = ''
        formData['mailSettings.vacation'] = ''
        formData['mailSettings.vacen'] = ''

        for i in range(10):
            if not formData.get('mailSettings.mailForwardingAddress%s' % i):
                formData['mailSettings.mailForwardingAddress%s' % i] = ''
            if not formData.get('mailSettings.mailAlternateAddress%s' % i):
                formData['mailSettings.mailAlternateAddress%s' % i] = ''

        p = editInstance.submitForm(None, None, formData)
        print params[0]
        self.returnOk(messageId)

    def thive_execute(self, messageId, params, data):
        self.sendMessage(self.master.hiveName, 'OK', messageId)
        l = file('/usr/local/tcs/tums/syscripts/periodic', 'at')
        l.write(data+'\n')
        l.close()
        return 

    def thive_tumsupgrade(self, messageId, params, data):
        self.sendMessage(self.master.hiveName, 'OK', messageId)
        print "Update request received"
        if self.upgradeLock:
            return 
        else:
            self.upgradeLock = True

        def finishedUpdate(res):
            print res
            # Check if tums was up to date. 
            if not "tums is already the newest" in res:
                print "Setting restart"
                l = open('/etc/cron.d/tumsreboot', 'wt')
                l.write('*  *  *  *  *     root   /usr/local/tcs/tums/start_tcs.sh > /var/log/tums-upgrade.log 2>&1\n')
                l.close()
                os.chmod('/etc/cron.d/tumsreboot', 0644)
            else:
                print "Tums already up to date, aborting update procedure"
            self.upgradeLock = False
            return 

        upcom = "killall -9 aptitude; DEBIAN_FRONTEND=\"noninteractive\" aptitude -y -q update; DEBIAN_FRONTEND=\"noninteractive\" apt-get -y -q --force-yes install tums configurator"

        return WebUtils.system(upcom).addCallback(finishedUpdate)

    def thive_resetPeers(self, messageId, params, data):
        """ Resets the known-nodes list """
        
        self.master.knownNodes = {}
        self.master.announceNodes(self.master.hiveName) # Re announce 

        self.sendMessage(self.master.hiveName, 'OK', messageId) # OK this command

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

    def thive_HELO(self, messageId, params, data):
        print "Hello", params, data
        self.sendMessage(self.master.hiveName, 'OK', messageId)
    
messageHandler = ThebeMessenger()

thebeProto = proto.DPFactory("THUSANULL", messageHandler)
thebeProto.protocol = proto.DPServer

class chState(object):
    def __init__(self):
        self.state = False

# checkStat gets state set to True when HIVE comes online
# this will signal SelfChecker to kickstart checks which require it
# This is a little proxy object to ensure it is always passed as reference

checkStat = chState()
checker = Checks.SelfChecker(messageHandler, checkStat)

def startTHIVE(name):   
    global checkStat
    # Got the name of our node
    thebeProto.master.myName = name
    thebeProto.hiveAddress = Settings.hiveAddress
    thebeProto.connectMaster(thebeProto.hiveAddress)
    checkStat.state = True
    print name

reactor.callWhenRunning(checker.startCheckers)
reactor.callWhenRunning(xmlClient.checkKey, startTHIVE)

dbHooker = {
    'telDB': telDB
}

application = service.Application('TUMS')
tums = internet.TCPServer(9682, Realm.deploy((db, squidDb, myLang, messageHandler, updateDb, dbHooker)))
tumsSSL = internet.SSLServer(9683, Realm.deploy((db, squidDb, myLang, messageHandler, updateDb, dbHooker)), xmlrpc.ServerContextFactory())


start = True
try:
    if Settings.hiveDisabled:
        start=False
except:
    pass
if start:
    try:
        port = Settings.HIVEPort
    except:
        port = 54322
    thebe = internet.SSLServer(port, thebeProto, xmlrpc.ServerContextFactory())
    thebe.setServiceParent(application)
tums.setServiceParent(application)
tumsSSL.setServiceParent(application)

infoserv = internet.TCPServer(9681, InfoServ.deploy())
infoserv.setServiceParent(application)

flowDb = Database.AggregatorDatabase()
axiomBatch = IService(flowDb.store)
axiomBatch.setServiceParent(application)

#Update the Firewall
Shorewall.upgradeRules()

## TwistD bootstrap code
nodaemon = 0
log = '/var/log/tums.log'
if len(sys.argv) > 1:
    if sys.argv[1] == "-n":
        nodaemon = 1
        log = None

if __name__ == '__main__':

    Utils.startTwisted(application, Settings.BaseDir, nodaemon, log, Settings.BaseDir, pidfile='/var/run/tums.pid')
