import sys, os
sys.path.append('/root/dev/source/')
from zope.interface import implements, Interface

from twisted.internet import defer
from twisted.trial import unittest

from nevow import testutil, stan
from nevow import livetest, url, util, appserver, inevow, context, flat, rend, loaders

from Pages import Log, Tet, Mail, MailQueue, Samba, Reports, Tools
from Pages import VPN, Network, Backup, Dhcp, UserSettings, Squid, Xen
from Pages import Firewall, PermissionDenied, GroupMatrix, Traffic, Exim, Apache
from Pages import NetworkStats, System, Graph, MySQL, Existat, About, Ppp, Sar
from Pages import FileBrowser, Profiles, Routing, DNS, InterfaceStats, Diagnose
from Pages import HA, Dashboard, WindowsDomain, UpdateCache, SSH, Menu
from Pages.Users import Start

from Pages.Users import Start, Add, Edit, Group, Domains, Delete


from Core import Auth, PageHelpers
import formless
from formless import webform as freeform
from formless import annotate, iformless
from twisted.trial import unittest

import lang

class masterFaker:
    hiveName = 'TEST'

class dbFaker:
    master = masterFaker()
    def getMailQueue(self, *a, **kw):
        def deferer():
            return []
        return defer.maybeDeferred(deferer)

    def getLastMessages(self, *a, **kw):
        def deferer():
            return []
        return defer.maybeDeferred(deferer)

    def getMonths(self, *a, **kw):
        return self.getLastMessages()
    def sendMessage(self, *a, **kw):
        pass

class TestTums(unittest.TestCase):
    def _urlTest(self, U, page, urlLoc):
        return self.assertIn(urlLoc, self.flattenUrl(U, page))

    def setUp(self):
        self.db = [dbFaker(), dbFaker(), lang.Text('en'), dbFaker()]
        self.testSambaDomain = 'thusa.co.za'
        self.testUser = 'test'
        self.avatarId = Auth.UserAvatar('test', 'test', 1, 1, True, [])
        self.aContext = None

        # Backup the profile
        try:
            os.system('cp /usr/local/tcs/tums/profiles/default.py /usr/local/tcs/tums/profiles/testbackup.py')
            os.system('cp -a /etc/exim4 /root/')
        except:
            pass

    def tearDown(self):
        # restore the profile
        os.system('cp /usr/local/tcs/tums/profiles/testbackup.py /usr/local/tcs/tums/profiles/default.py')
        os.system('cp -a /root/exim4/* /etc/exim4/')
        os.system('rm /etc/cron.d/backup* > /dev/null 2>&1')
    
    def flattenUrl(self, urlObj, page):
        ctx = context.WebContext(tag=page)
        ctx.remember(testutil.AccumulatingFakeRequest())
        return ''.join([i for i in url.URLOverlaySerializer(urlObj, ctx).next()])

class TestUsers(TestTums):
    ########################
    # Users
    ########################
    def test_Users(self):
        page = Start.Page(self.avatarId, self.db)
        page.addSlash = False
        return testutil.renderPage(page)

    def test_addUser(self):
        page = Add.addPage(self.avatarId, self.db, self.testSambaDomain)
        page.addSlash = False
        testutil.renderPage(page)
        submitData = {
            'userSettings.uid': u'test01',
            'userPermissions.employeeType': True, 'userPermissions.tumsUser': None,
            'userSettings.userPassword': "test", 'mailSettings.vacation': None,
            'mailSettings.mailAlternateAddress0': None,
            'userPermissions.tumsAdmin': True,
            'mailSettings.mailForwardingAddress0': None,
            'userPermissions.accountStatus': True,
            'userPermissions.employeeType':True,
            'userSettings.sn': u'test', 
            'userSettings.givenName': u'test01',
            'userAccess.ftpEnabled': False,
            'userAccess.ftpGlobal': False,
            'userAccess.vpnEnabled': False,
            'userPermissions.copyto': '',
        }
        for i in range(10):
            submitData['mailSettings.mailAlternateAddress%s' % i] = None
            submitData['mailSettings.mailForwardingAddress%s' % i] = None
        form = None

        U = page.submitForm(self.aContext, form, submitData)

        U.addCallback(self._urlTest, page, '/Users/Edit/thusa.co.za/test01')
        return U

    def test_editUser(self):
        page = Edit.editPage(self.avatarId, self.db, 'root', self.testSambaDomain)
        page.addSlash = False
        testutil.renderPage(page)

        submitData = {
            'userPermissions.employeeType': False, 
            'uid': ['root'], 
            'objectClass': ['inetOrgPerson', 'sambaSamAccount', 'posixAccount', 'shadowAccount'], 
            'userAccess.ftpGlobal': False, 
            'uidNumber': ['0'], 
            'sambaAcctFlags': ['[U]'], 
            'sambaPrimaryGroupSID': ['S-1-5-21-3603831541-3007533189-3710063549-512'], 
            'mailSettings.mailAlternateAddress7': None, 
            'mailSettings.mailAlternateAddress6': None, 
            'mailSettings.mailAlternateAddress5': None, 
            'mailSettings.mailAlternateAddress4': None, 
            'userSettings.givenName': u'root', 
            'mailSettings.mailAlternateAddress2': None, 
            'mailSettings.mailAlternateAddress1': None, 
            'mailSettings.mailAlternateAddress0': None, 
            'sambaLogoffTime': ['2147483647'], 
            'mailSettings.vacation': None, 
            'sambaPwdCanChange': ['0'], 
            'cn': ['root root'], 
            'mailSettings.mailForwardingAddress6': None, 
            'employeeType': ['tumsAdmin'], 
            'mailSettings.mailForwardingAddress5': None, 
            'userPassword': ['{SHA}+GW1NiOxIf007lQmx5Llwzr4wic='], 
            'sambaPwdMustChange': ['1209377073'],
            'userPermissions.tumsReports': False, 
            'mailSettings.mailAlternateAddress9': None, 
            'sambaLogonTime': ['0'], 
            'sambaLMPassword': ['AC804745EE68EBEA1AA818381E4E281B'], 
            'mailSettings.mailAlternateAddress8': None, 
            'userAccess.ftpEnabled': False, 
            'mailSettings.mailForwardingAddress3': None, 
            'mailSettings.mailForwardingAddress2': None, 
            'mailSettings.mailForwardingAddress1': None, 
            'mailSettings.mailForwardingAddress0': None, 
            'mailSettings.mailForwardingAddress7': None, 
            'userPermissions.tumsAdmin': True, 
            'userSettings.uid': u'root', 
            'mailSettings.mailForwardingAddress4': None, 
            'loginShell': ['/bin/false'], 
            'mailSettings.mailForwardingAddress9': None, 
            'mailSettings.mailForwardingAddress8': None, 
            'gidNumber': ['0'], 
            'sambaKickoffTime': ['2147483647'], 
            'sambaPwdLastSet': ['1205489073'], 
            'sambaNTPassword': ['3008C87294511142799DCA1191E69A0F'], 
            'userPermissions.tumsUser': None, 
            'userSettings.sn': u'root', 
            'userAccess.vpnEnabled': False, 
            'userPermissions.accountStatus': False, 
            'userSettings.userPassword': None, 
            'mailSettings.vacen': False, 
            'sambaSID': ['S-1-5-21-3603831541-3007533189-3710063549-500'], 
            'gecos': ['Netbios Domain Administrator'], 
            'sn': ['root'], 'homeDirectory': ['/home/root'], 
            'mailSettings.mailAlternateAddress3': None, 
            'givenName': ['root'], 'userPermissions.copyto': None
        }   
        form = None

        for i in range(10):
            submitData['mailSettings.mailAlternateAddress%s' % i] = None
            submitData['mailSettings.mailForwardingAddress%s' % i] = None

        U = page.submitForm(self.aContext, form, submitData)
        self.assertIn("/Users/Edit/thusa.co.za/root/Completed", self.flattenUrl(U, page))

        return U 

    def test_deleteUser(self):
        page = Delete.deletePage(self.avatarId, self.db)
        page.addSlash = False
        testutil.renderPage(page)
        U = page.locateChild(None, ['thusa.co.za', 'test01'])
        self.assertIn("/Users", self.flattenUrl(U[0], page))

        return U 
        
    def test_addGroup(self):
        page = Group.addGroups(self.avatarId, self.testSambaDomain, self.testUser, self.db)
        page.addSlash = False
        testutil.renderPage(page)
        submitData = {'groupName':'test01'}
        U = page.submitForm(self.aContext, None, submitData)
        self.assertIn('/Users/Groups/thusa.co.za/test', self.flattenUrl(U, page))

        return U 

    def test_editGroupMembership(self):
        page = Group.editGroups(self.avatarId, self.db, self.testUser, self.testSambaDomain)
        page.addSlash = False
        return testutil.renderPage(page)

class TestRenders(TestTums):
    def test_pages(self):
        pages = [
            About,              Apache,
            Backup,             Computers,
            DNS,                Dhcp,
            Diagnose,           Exim,
            Existat,            FileBrowser,
            Firewall,           Graph,
            GroupMatrix,        InterfaceStats, 
            Log,                Mail,
            Menu,               MySQL,
            Netdrive,           Network,
            NetworkStats,       Overview,
            PermissionDenied,   Policy,
            Ppp,                Profiles,
            Qos,                Reports,
            Routing,            Samba,
            SambaConfig,        Sar,
            Shorewall,          Squid,
            System,             MailQueue,
            Tools,              Traffic,
            VPN,                Xen,
        ]
        renderInstances = []
        for pname in pages:
            page = pname.Page(self.avatarId, self.db)
            page.addSlash = False
            renderInstances.append(testutil.renderPage(page))
        return defer.DeferredList(renderInstances)

class TestDHCP(TestTums):

    def tearDown(self):
        # restore the profile
        os.system('cp /usr/local/tcs/tums/profiles/testbackup.py /usr/local/tcs/tums/profiles/default.py')
        os.system('/etc/init.d/dhcpd stop > /dev/null 2>&1')
        os.system('killall -9 dhcpd')

    def test_config(self):
        page = Dhcp.Page(self.avatarId, self.db)
        return page

class TestPPP(TestTums):
    def test_ppp(self):
        page = Ppp.Page(self.avatarId, self.db)
        pass

class TestBackup(TestTums):
    def test_backup(self):
        page = Backup.Page(self.avatarId, self.db)
        return True

class TestVPN(TestTums):

    def test_vpnWin(self):
        page = VPN.Page(self.avatarId, self.db)

        # Test the windows form
        U = page.submitWinForm(self.aContext, None, {
            'windows':True,
            'winip':u'172.31.0.2',
            'winextip':u'196.211.202.165'
        })
        return U

    def test_vpnWin2(self):
        page = VPN.Page(self.avatarId, self.db)
        # Turn it off...
        U = page.submitWinForm(self.aContext, None, {
            'windows':False,
            'winip':u'',
            'winextip':u''
        })
        
        return U

    def test_vpnTCS(self):
        page = VPN.Page(self.avatarId, self.db)
        # Setup a Vulani VPN
        U = page.submitForm(self.aContext, None, {
            'openvpn':True,
            'iprange1':'172.31.4.30',
            'iprange2':'172.31.4.50',
            'mtu':'1300',
            'WINS':'172.31.0.1',
            'DNS':'172.31.0.2',
            'DOMAIN':'thusa.co.za',
            'tcp':False,
            'routes':[]
        })

        # Add a user.

        return U

    def test_vpnCert(self):
        page = VPN.Page(self.avatarId, self.db)
        U = page.newCert(self.aContext, None, {
            'name':'colin alston',
            'mail':'colin@thusa.co.za',
            'ip':'172.31.4.35',
            'mailKey':True
        })

        # Revoke the test cert
        D = page.locateChild(self.aContext, ['Revoke', 'colinalston'])

        return defer.DeferredList([U, D[0]])

class TestFirewall(TestTums):
    def test_firewall(self):
        page = Firewall.Page(self.avatarId, self.db)
        # Try creating a zone
        U = [ 
            page.submitZone(self.aContext, None, {
                'zone':'test',
                'policy':'ACCEPT',
                'log':'',
                'interfaces':'eth1, eth0'
            }),
            # Try allowing a range in our test zone
            page.submitAllowRange(self.aContext, None, {
                'action': 'ACCEPT', 
                'sport': '32', 
                'dport': None,
                'sip':'172.31.0.1',
                'dip': None,
                'dzone': None,
                'proto': 'tcp',
                'szone': 'test',
            }),
            # Allow a port in our zone
            page.submitAllowPort(self.aContext, None, {
                'destport':'1994',
                'destip':'192.157.123.2',
                'proto':'udp',
                'zone':'test'
            }),
            # Forward a port.
            page.submitForwardPort(self.aContext, None, {
                'port':'24',
                'destip':'172.31.0.2',
                'dstport':'24',
                'sourceip':'',
                'proto':'tcp',
                'szone':'net',
                'dzone':'test',
                'source': None
            }),
            # create a transparent proxy
            page.submitTransProxy(self.aContext, None, {
                'sourceip':'172.31.0.0',
                'destip':'172.31.0.212',
                'srcport':'8080',
                'dstport':'3123',
                'proto':'tcp',
                'zone': 'test'
            }),

            # Create NAT entry
            page.submitNAT(self.aContext, None, {
                'dstif': 'eth0',
                'srcif': 'eth1',
                'destip': '172.31.0.212',
                'natip': '172.31.0.212',
                'proto': 'tcp',
                'srcport': '20',
                'srcip': None,
            }),

            page.submitSNAT(self.aContext, None, {
                'dstif': 'eth0',
                'dstip': '172.31.0.1', 
                'srcip': '172.31.0.212',
                'all': True,
                'local': False
            }),

            # Delete items
            page.locateChild(self.aContext, ['Delete', 'Zone', 'test'])[0],
            page.locateChild(self.aContext, ['Delete', 'AIP', '-1'])[0],
            page.locateChild(self.aContext, ['Delete', 'NAT', 'eth0', '-1'])[0],
            page.locateChild(self.aContext, ['Delete', 'SNAT', '-1'])[0]
        ]

        return U

class TestFileserver(TestTums):
    def test_samba(self):
        page = Samba.Page(self.avatarId, self.db)
        U = page.submitForm(self.aContext, None, {
            'share':'testshare',
            'path':'/foo/bar',
            'comment':'Test Share',
            'public':True,
            'writable':True,
            'group':'Domain Users'
        })

        U.addCallback(self._urlTest, page, '/Samba')
        Ul = page.locateChild(self.aContext, ['Delete', 'testshare'])
        
        return defer.DeferredList([U, Ul[0]])

    def test_netDrive(self):
        page = Netdrive.Page(self.avatarId, self.db)
        U = page.submitForm(self.aContext, None, {
            'sharepath': '\\\\foo\\bar',
            'loginGroup': 'Domain Users',
            'driveletter': 'X'
        })
        
        U.addCallback(self._urlTest, page, '/Netdrive')

        # Delete the thing we added
        Ul = page.locateChild(self.aContext, ['Delete', 'X'])

        return defer.DeferredList([U, Ul[0]])



class TestExim(TestTums):
    def test_exim(self):
        page = Exim.Page(self.avatarId, self.db)
        
        U = page.submitForm(self.aContext, None, {
            'maxsize':      '100M',
            'blockedFiles': '.mp3',
            'blockMovies':  True,
            'blockHarm':    True,
            'smtprelay':    '172.31.0.1',
            'hubbedHosts':  'foo.com   172.31.0.2',
            'localDomains': 'foo.net',
            'relayDomains': 'foo.org',
            'copyall': '',
            'spamscore': 70,
            'greylisting': True,
            'relayfrom': '',
            'rpfilter': True, 
        })
        
        U.addCallback(self._urlTest, page, '/Mailserver')
        return U

class TestSquid(TestTums):
    def test_squidAuth(self):
        page = Squid.Page(self.avatarId, self.db)
        # Change auth details..
        U = page.submitAuth(self.aContext, None, {
            'adauth': False,
            'adserv': u'',
            'addom': u'',
            'advanced': True,
            'captive': False,
            'captiveblock': False, 
            'contentfilter': False, 
            'bindaddr': ""
        })
        
        U.addCallback(self._urlTest, page, '/Squid')

        return U
