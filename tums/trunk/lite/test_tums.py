#!/usr/bin/python
from zope.interface import implements, Interface

from twisted.internet import defer
from twisted.trial import unittest

import sys
sys.path.append('/root/dev/TUMS/trunk/source')

from nevow import testutil, stan
from nevow import livetest, url, util, appserver, inevow, context, flat, rend, loaders

from Pages import Users, Log, Tet, Stats, Shorewall, Mail, MailQueue, Samba, Reports, Tools
from Pages import VPN, Netdrive, Network, Backup, Dhcp, UserSettings, Computers, Squid
from Pages import Firewall, PermissionDenied, GroupMatrix, Traffic, Exim, Overview
from Pages import NetworkStats, System, Graph, MySQL, Existat, About, Menu, Ppp

from Core import Auth, PageHelpers
import formless
from formless import webform as freeform
from formless import annotate, iformless
from twisted.trial import unittest

class dbFaker:
    def getMailQueue(self, *a, **kw):
        def deferer():
            return []
        return defer.maybeDeferred(deferer)

    def getLastMessages(self, *a, **kw):
        def deferer():
            return []
        return defer.maybeDeferred(deferer)


class TestTums(unittest.TestCase):
    db = [dbFaker(), dbFaker()]
    testSambaDomain = 'thusa.co.za'
    testUser = 'test'
    avatarId = Auth.UserAvatar('test', 'test', 1, 1, True, [])
    aContext = None
    
    def flattenUrl(self, urlObj, page):
        ctx = context.WebContext(tag=page)
        ctx.remember(testutil.AccumulatingFakeRequest())
        return ''.join([i for i in url.URLOverlaySerializer(urlObj, ctx).next()])
    ########################
    # Users
    ########################
    def test_Users(self):
        page = Users.Page(self.avatarId, self.db)
        page.addSlash = False
        return testutil.renderPage(page)

    def test_addUser(self):
        page = Users.addPage(self.avatarId, self.db, self.testSambaDomain)
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
            'userSettings.sn': u'test', 'userSettings.givenName': u'test01'}
        for i in range(10):
            submitData['mailSettings.mailAlternateAddress%s' % i] = None
            submitData['mailSettings.mailForwardingAddress%s' % i] = None
        form = None

        U = page.submitForm(self.aContext, form, submitData)
        self.assertIn("/Users/Edit/thusa.co.za/test01", self.flattenUrl(U, page))
        return U

    def test_editUser(self):
        page = Users.editPage(self.avatarId, self.db, 'root', self.testSambaDomain)
        page.addSlash = False
        testutil.renderPage(page)

        submitData = {
            'userSettings.uid': u'root',
            'userPermissions.employeeType': True, 'userPermissions.tumsUser': None,
            'userSettings.userPassword': None, 'mailSettings.vacation': None,
            'mailSettings.mailAlternateAddress0': None,
            'userPermissions.tumsAdmin': True,
            'mailSettings.mailForwardingAddress0': None,
            'userPermissions.accountStatus': True,
            'userPermissions.employeeType':True,
            'userSettings.sn': u'root', 'homeDirectory': ['/home/colin'], 'userSettings.givenName': u'rooter'}
        form = None

        for i in range(10):
            submitData['mailSettings.mailAlternateAddress%s' % i] = None
            submitData['mailSettings.mailForwardingAddress%s' % i] = None

        U = page.submitForm(self.aContext, form, submitData)
        self.assertIn("/Users/Edit/thusa.co.za/root/Completed", self.flattenUrl(U, page))

        return U 

    def test_deleteUser(self):
        page = Users.deletePage(self.avatarId, self.db)
        page.addSlash = False
        testutil.renderPage(page)
        U = page.locateChild(None, ['thusa.co.za', 'test01'])
        self.assertIn("/Users", self.flattenUrl(U[0], page))

        return U 
        
    def test_addGroup(self):
        page = Users.addGroups(self.avatarId, self.testSambaDomain, self.testUser, self.db)
        page.addSlash = False
        testutil.renderPage(page)
        submitData = {'groupName':'test01'}
        U = page.submitForm(self.aContext, None, submitData)
        self.assertIn('/Users/Groups/thusa.co.za/test', self.flattenUrl(U, page))

        return U 

    def test_editGroupMembership(self):
        page = Users.editGroups(self.avatarId, self.db, self.testUser, self.testSambaDomain)
        page.addSlash = False
        return testutil.renderPage(page)

    ########################
    # All page renderers
    ########################
 
    def test_pageRenders(self):
        pages = [
            Log, Stats, Mail, MailQueue, Samba, Reports, 
            Tools, VPN, Netdrive, Network, Backup, Dhcp, 
            Computers, Squid, Firewall, PermissionDenied, 
            GroupMatrix, Traffic, Exim, Overview, NetworkStats, 
            System, Graph, MySQL, Existat, About, Menu, Ppp
        ]
        renderInstances = []
        for pname in pages:
            page = pname.Page(self.avatarId, self.db)
            page.addSlash = False
            renderInstances.append(testutil.renderPage(page))
        return renderInstances

    def test_dhcp(self):
        page = Dhcp.Page(self.avatarId, self.db)
        pass

    def test_ppp(self):
        page = Ppp.Page(self.avatarId, self.db)
        pass

    def test_backup(self):
        page = Backup.Page(self.avatarId, self.db)
        import datetime
        U = page.submitForm(self.aContext, None, {
            'descrip':      'Test',
            'backpath':     '/home',
            'destpath':     'foo',
            'notify':       'colin@thusa.co.za',
            'backupdrive':  'noDrive',
            'sched':        True,
            'time':         datetime.datetime.now(),
        })

        self.assertIn('/Backup', self.flattenUrl(U, page))

        return U

    def test_vpn(self):
        page = VPN.Page(self.avatarId, self.db)

        # Test the windows form
        U = page.submitWinForm(self.aContext, None, {
            'windows':True,
            'winip':u'172.31.0.2',
            'winextip':u'196.211.202.165'
        })
        # Turn it off...
        U = page.submitWinForm(self.aContext, None, {
            'windows':False,
            'winip':u'',
            'winextip':u''
        })
        
        # Setup a TCS VPN
        U = page.submitForm(self.aContext, None, {
            'openvpn':True,
            'iprange1':'172.31.4.30',
            'iprange2':'172.31.4.50',
            'mtu':'1300',
            'WINS':'172.31.0.1',
            'DNS':'172.31.0.2',
            'DOMAIN':'thusa.co.za',
            'routes':[]
        })

        # Add a user.

        U = page.newCert(self.aContext, None, {
            'name':'colin alston',
            'mail':'colin@thusa.co.za',
            'ip':'172.31.4.35',
            'mailKey':True
        })

        # Revoke the test cert
        page.locateChild(self.aContext, ['Revoke', 'colinalston'])

        return U 

    def test_firewall(self):
        page = Firewall.Page(self.avatarId, self.db)
        # Try creating a zone
        U = page.submitZone(self.aContext, None, {
            'zone':'test',
            'policy':'ACCEPT',
            'log':'',
            'interfaces':'eth1, eth0'
        })
        # Try allowing a range in our test zone
        U = page.submitAllowRange(self.aContext, None, {
            'sourceip':'172.31.0.1',
            'zone':'test'
        })
        # Allow a port in our zone
        U = page.submitAllowPort(self.aContext, None, {
            'destport':'1994',
            'destip':'192.157.123.2',
            'proto':'udp',
            'zone':'test'
        })
        # Forward a port.
        U = page.submitForwardPort(self.aContext, None, {
            'port':'24',
            'destip':'172.31.0.2',
            'dstport':'24',
            'sourceip':'',
            'proto':'tcp'
        })
        # create a transparent proxy
        U = page.submitTransProxy(self.aContext, None, {
            'sourceip':'172.31.0.0',
            'destip':'172.31.0.212',
            'srcport':'8080',
            'dstport':'3123',
            'proto':'tcp'
        })

        return U 

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

        page.locateChild(self.aContext, ['Delete', 'testshare'])
        return U 

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
            'relayDomains': 'foo.org'
        })

        self.assertIn('/Mailserver', self.flattenUrl(U, page))
        return U 

    def test_netDrive(self):
        page = Netdrive.Page(self.avatarId, self.db)
        U = page.submitForm(self.aContext, None, {
            'sharepath': '\\\\foo\\bar',
            'loginGroup': 'Domain Users',
            'driveletter': 'X'
        })
        self.assertIn('/Netdrive', self.flattenUrl(U, page))
        # Delete the thing we added
        Ul = page.locateChild(self.aContext, ['Delete', 'X'])
        self.assertIn('/Netdrive', self.flattenUrl(Ul[0], page))

        return U 

    def test_squid(self):
        page = Squid.Page(self.avatarId, self.db)
        # Change auth details..
        U = page.submitAuth(self.aContext, None, {
            'ldapauth': True,
            'adauth': False,
            'adserv': u'',
            'addom': u'',
        })
        self.assertIn('/Squid', self.flattenUrl(U, page))
        # Add a domain

        U = page.submitDomain(self.aContext, None, {
            'domain':'test.com'
        })
        self.assertIn('/Squid', self.flattenUrl(U, page))

        # Add an IP

        U = page.submitHost(self.aContext, None, {
            'ip' : '192.168.153.2'
        })
        
        self.assertIn('/Squid', self.flattenUrl(U, page))

        U = page.submitDest(self.aContext, None, {
            'ip' : '192.168.153.2'
        })

        self.assertIn('/Squid', self.flattenUrl(U, page))
        
        # Deletions
        page.locateChild(self.aContext, ['Delete', 'Domain', '-1'])
        page.locateChild(self.aContext, ['Delete', 'Destination', '-1'])
        page.locateChild(self.aContext, ['Delete', 'Host', '-1'])

        return U 

