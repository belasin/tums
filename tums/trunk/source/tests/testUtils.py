import sys

sys.path.append('/usr/local/tcs/tums')
sys.path.append('/usr/local/tcs/tums/lib')
sys.path.append('/usr/local/tcs/tums/tests')
from zope.interface import implements, Interface
import lang
from twisted.internet import defer
from twisted.trial import unittest
from nevow import testutil, stan
from nevow import livetest, url, util, appserver, inevow, context, flat, rend, loaders


import os

from Core import Auth

class FakeBooty:
    def integrateTools(self, *a):
        return 

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
        self.db = [dbFaker(), dbFaker(), lang.Text('en'), dbFaker(), dbFaker(), FakeBooty()]
        self.testSambaDomain = 'netlink.za.net'
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

def treeDict(d, ind = 0):
    indChars = " " * ind
    if type(d) == dict:
        for k,v in d.items():
            if type(v) == dict:
                print indChars,k
                treeDict(v, ind+4)
            else:
                print indChars, k, ":", v
    else:
        print indChars,d
