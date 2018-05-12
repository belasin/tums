from nevow import rend, loaders, tags, athena
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP
from Core import PageHelpers, AuthApacheProxy, confparse, Utils, WebUtils
from Pages import Tools
import formal, socket, struct

class liveGraphFragment(athena.LiveFragment):
    jsClass = u'diagnostics.PS'

    docFactory = loaders.xmlfile('diagnostics.xml', templateDir = Settings.BaseDir + '/templates')

    def __init__(self, *a, **kw):
        super(liveGraphFragment, self).__init__(*a, **kw)
        self.sysconf = confparse.Config()

    def lanTest(self):
        def lanScan(res):
            hosts = {}
            lastIP = ""
            ipOrder = []
            for i in res.split('\n'):
                if "Host" in i:
                    if "(" in i:
                        host = i.split()[1]
                        ip = i.split()[2].replace('(', '').replace(')', '')
                    else:
                        ip = i.split()[1]
                        host = ip

                    hosts[ip] = [unicode(host), u"", u""]
                    ipOrder.append(ip)
                    lastIP = ip
                elif "MAC" in i:
                    mac = i.split()[2]
                    brand = i.split()[3].replace('(', '').replace(')', '')
                    hosts[lastIP][1] = unicode(mac)
                    hosts[lastIP][2] = unicode(brand)

            bundle = []

            for k in ipOrder:
                v = hosts[k]
                sortKey = [int(i) for i in k.split('.')]
                bundle.append((unicode(k), v[0], v[1], v[2]))
            
            return bundle
        
        loc = []
        for k,v in Utils.getLanNetworks(self.sysconf).items():
            loc.append('nmap -sP %s 2>&1 | grep -E "(be up|MAC)"' % (v))

        return WebUtils.system(';'.join(loc)).addCallback(lanScan)
    athena.expose(lanTest)

    def bandwidthTest(self):
        def updateIntl(intl):   
            if "saved" in intl:
                speed = intl.split('(')[-1].split(')')[0]
            else:
                speed = "Zero"

            self.callRemote('intlSpeed', unicode(speed))
            return

        def intlDl(local):
            if "saved" in local:
                speed = local.split('(')[-1].split(')')[0]
            else:
                speed = "Zero"
            self.callRemote('localSpeed', unicode(speed))
            intl =  "wget --progress=dot ftp://ftp.debian.org/debian/README.mirrors.txt 2>&1 | grep saved; rm README.mirrors.txt"
            return WebUtils.system(intl).addCallback(updateIntl)

        loc =  "wget --progress=dot ftp://mirror.ac.za/debian/debian/README.mirrors.txt 2>&1 | grep saved; rm README.mirrors.txt"

        return WebUtils.system(loc).addCallback(intlDl)
    athena.expose(bandwidthTest)

    def pingTest(self):
        def returnTup(d):
            # We get back 4 sets of data. The first two are international latency, the last two are local
            # We take the best of each set with lack of packet loss being preffered to latency
            intlLatency = 9999
            intlPacketloss = 101

            localLatency = 9999
            localPacketloss = 101
            cnt = 0 
            for i in d.split('\n'):
                if "packet loss" in i:
                    pl = int(i.split(', ')[2].split('%')[0])
                    if cnt < 3:
                        if pl < intlPacketloss:
                            intlPacketloss = pl
                    else:
                        if pl < localPacketloss:
                            localPacketloss = pl
                    if pl == 100:
                        # We won't get a latency count after this...
                        cnt +=1

                if "rtt" in i:
                    l = int(float(i.split(' = ')[-1].split('/')[1]))
                    if cnt < 4:
                        if l < intlLatency:
                            intlLatency = l
                    else:
                        if l < localLatency:
                            localLatency = l
                cnt += 1
            return intlLatency, intlPacketloss, localLatency, localPacketloss

        pings = [
            'ping -c 3 google.com 2>&1 | grep -E "(loss|rtt)"',
            'ping -c 3 yahoo.com 2>&1 | grep -E "(loss|rtt)"',
            'ping -c 3 igubu.saix.net 2>&1 | grep -E "(loss|rtt)"',
            'ping -c 3 smtp.isdsl.net 2>&1 | grep -E "(loss|rtt)"',
        ]

        return WebUtils.system(';'.join(pings)).addCallback(returnTup)
    athena.expose(pingTest)

class Page(PageHelpers.DefaultAthena):
    moduleName = 'diagnostics'
    moduleScript = 'diagnostics.js' 
    docFactory = loaders.xmlfile('livepage.xml', templateDir = Settings.BaseDir + '/templates')

    addSlash = True

    def render_thisFragment(self, ctx, data):
        """ Renders liveGraphFragment instance """
        f = liveGraphFragment()
        f.setFragmentParent(self)
        return ctx.tag[f]

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2[tags.img(src='/images/tools-lg.png'), " Tools"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Tools.Page.sideMenu(Tools.Page(None, self.db), ctx, data)]

    def render_content(self, ctx, data):
        return ctx.tag[
            tags.h3[tags.img(src="/images/networking_section.png"), " Network Diagnostics"],
            tags.div[
                tags.invisible(render=tags.directive('thisFragment'))
            ]
        ]

