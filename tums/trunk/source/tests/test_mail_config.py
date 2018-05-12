import sys, os
sys.path.append('/usr/local/tcs/tums')
sys.path.append('/usr/local/tcs/tums/lib')
sys.path.append('/usr/local/tcs/tums/tests')
from zope.interface import implements, Interface

from twisted.internet import defer
from twisted.trial import unittest

from nevow import testutil, stan
from nevow import livetest, url, util, appserver, inevow, context, flat, rend, loaders

from Pages import Mail, MailQueue, Exim


from Core import Auth, PageHelpers
import formless
from formless import webform as freeform
from formless import annotate, iformless
from twisted.trial import unittest

import lang
import testUtils


class TestExim(testUtils.TestTums):
    def test_exim(self):
        page = Exim.Page(self.avatarId, self.db)
        
        U = page.submitForm(self.aContext, None, {
            'maxsize':      '100M',
            'blockedFiles': '.mp3',
            'blockMovies':  True,
            'blockHarm':    True,
            'smtprelay':    '172.31.0.1',
            'copyall': '',
            'spamscore': 70,
            'greylisting': True,
            'relayfrom': '',
            'rpfilter': True, 
            'ratelimit': False,
            'smtpinterface': None
        })
        
        U.addCallback(self._urlTest, page, '/Mailserver')
        return U

    def test_render(self):
        page = Exim.Page(self.avatarId, self.db)
        page.addSlash = False
        return testutil.renderPage(page)
