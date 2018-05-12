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


from Core import Auth, PageHelpers, confparse
import formless
from formless import webform as freeform
from formless import annotate, iformless
from twisted.trial import unittest

import lang
import testUtils


class TestDuplicateGateways(testUtils.TestTums):
    def test_duplicates(self):
        c = confparse.Config()
        eth = c.EthernetDevices.items()

        routeStack = None
        for dev, configs in eth:
            for dst, gw in configs.get('routes', []):
                if dst == "default": 
                    assert(routeStack == None)
                    routeStack = dev

        return True

