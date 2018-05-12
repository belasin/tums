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

class ClusterFragment(athena.LiveFragment):
    jsClass = u'cluster.PS'

    docFactory = loaders.xmlfile('cluster.xml', templateDir = Settings.BaseDir + '/templates')

    def __init__(self, *a, **kw):
        super(ClusterFragment, self).__init__(*a, **kw)
        self.sysconf = confparse.Config()

    def initialTable(self):
        ha = self.sysconf.General.get('ha', {})
        
        servers = [ map(unicode, [v['name'], v['topology'], '?', k]) for k,v in ha.items() ]
        servers.sort()

        if not servers:
            servers = [[u'Searching...', u'', u'', u'']]

        return servers
    athena.expose(initialTable)

    def lanTest(self):
        ha = self.sysconf.General.get('ha', {})

        flan = Utils.getLans(self.sysconf)[0]
        lanIP = self.sysconf.EthernetDevices[flan].get('network', '192.168.0.0/24')
        myIP = self.sysconf.EthernetDevices[flan].get('ip', '192.168.0.0/24').split('/')[0]
        print lanIP, myIP
        def lanScan(res):
            print res
            for i in res.split('\n'):
                if i[:5] != "Host:":
                    continue
                
                n = i.split()
                ip = n[1]
                host = n[2][1:-1]
                
                if ip in ha.keys():
                    ha[ip]['status'] = 'Online'
                else:
                    ha[ip] = {
                        'status': 'Online',
                        'topology': "Not Configured",
                        'name': host or ip,
                    }
                if ip == myIP:
                    ha[ip]['status'] = "Me"
                    ha[ip]['name'] = ""

            servers = [ map(unicode, [v['name'], v['topology'], v.get('status', 'Offline'), k]) for k,v in ha.items() ]

            return servers

        loc = 'nmap -sS -p 9682,54322 -oG - %s 2>&1 | grep "9682/open/tcp" | grep "54322/open/tcp"' % (lanIP.encode())
        print loc
        return WebUtils.system(loc).addBoth(lanScan)
    athena.expose(lanTest)

class ClusterConfig(Tools.Page):
    def __init__(self, avatarId = None, db = None, ip="", *a, **kw):
        self.ip = ip
        Tools.Page.__init__(self,avatarId, db, *a, **kw)

    def locateChild(self, ctx, segs):
        print segs, "SEGSVVV"
        if len(segs) > 1:
            return ClusterConfig(self.avatarId, self.db, segs[0]), ()
        return Tools.Page.locateChild(self, ctx, segs)

    def populateForm(self):
        ha =  self.sysconf.General.get('ha', {})

        if ha.get(self.ip):
            vals = ha[self.ip]
            ans = {}
            for k,v in vals.items():
                if k =='name':
                    k = 'topology.name'

                elif k == 'topology':
                    k = 'topology.topology'

                elif k == 'ipoverride':
                    k = 'topology.ipoverride'

                elif k == 'wanoverride':
                    k = 'topology.wanoverride'

                ans[k] = str(v)
            return ans
        else:
            return {}

    def form_config(self, ctx):
        form = formal.Form(self.submitForm)[
            formal.Group('topology')[
                tags.div[
                    tags.h3["Topology configuration"]
                ],
                formal.Field('name', formal.String(), label = "Name"),
                formal.Field('topology', formal.String(),  formal.widgetFactory(formal.SelectChoice, options = [
                        ('master', 'Master'),
                        ('slave', 'Slave')
                    ]), label = "Topology"),
                formal.Field('ipoverride', formal.Boolean(), label = "Take over LAN", 
                    description = "Take over the LAN settings of this server on failure."), 
                formal.Field('wanoverride', formal.Boolean(), label = "Take over WAN", 
                    description = "Take over the WAN settings of this server on failure."),
                #formal.Field('key', formal.String(), label = "Access Key", 
                #    description = "On the slave system, configure it to accept HA connections and generate a key which is pasted here")
            ],
            formal.Group('failover')[
                tags.div[
                    tags.h3["Failover services"]
                ],
                formal.Field('dhcp', formal.Boolean(), label = "DHCP", 
                    description = "This server will act as a backup DHCP server"),

                formal.Field('smtp', formal.Boolean(), label = "SMTP", 
                    description = "This server will provide backup SMTP routing - NOT POP3/IMAP DELIVERY."),

                formal.Field('routing', formal.Boolean(), label = "Internet Gateway", 
                    description = "This server may act as a backup internet gateway in the event that the master goes offline"),

                formal.Field('dns', formal.Boolean(), label = "DNS Server", 
                    description = "This server may act as a backup DNS server for all zones"),

                formal.Field('pdc', formal.Boolean(), label = "Domain controller", 
                    description = "This server may act as the primary domain controller")
            ],
            formal.Group('loadbalance')[
                tags.div[
                    tags.h3["Load sharing services"]
                ],
                formal.Field('dhcp', formal.Boolean(), label = "DHCP"),
                formal.Field('smtp', formal.Boolean(), label = "SMTP")
            ],
        ]
        
        form.data = self.populateForm()
        form.addAction(self.submitForm)
        return form

    def submitForm(self, ctx, f, data):
        G =  self.sysconf.General
        if 'ha' not in G:
            G['ha'] = {}

        ans = {}
        for k,v in data.items():
            ans[k.replace('topology.', '')] = str(v)

        G['ha'][self.ip] =  ans
        
        self.sysconf.General = G

        return url.root.child('HA')

    def render_content(self, ctx, data):
        heading = " Configure cluster relationship with %s" % self.ip

        return ctx.tag[
            tags.h3[tags.img(src="/images/networking_section.png"), heading],
            PageHelpers.TabSwitcher([
                ('Topology', 'config-topology'), 
                ('Failover', 'config-failover'), 
                ('Load Sharing', 'config-loadbalance')
            ]),
            tags.directive('form config'),
            PageHelpers.LoadTabSwitcher()
        ]

class Page(PageHelpers.DefaultAthena):
    moduleName = 'cluster'
    moduleScript = 'cluster.js' 
    docFactory = loaders.xmlfile('ha.xml', templateDir = Settings.BaseDir + '/templates')

    addSlash = True

    childPages = {
        'Configure': ClusterConfig,
    }
    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2[tags.img(src='/images/tools-lg.png'), " Tools"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Tools.Page.sideMenu(Tools.Page(None, self.db), ctx, data)]

    def render_thisFragment(self, ctx, data):
        """ Renders ClusterFragment instance """
        f = ClusterFragment()
        f.setFragmentParent(self)
        return ctx.tag[f]

    def form_masterKey(self, ctx):
        form = formal.Form()

        form.addField('key', formal.String(), label = "Master Key", 
            description="If this is a slave node, enter the masters key here")

        form.data['key'] = self.sysconf.General.get('haconf', {}).get('masterkey', '')

        form.addAction(self.submitMaster)
        return form
        
    def submitMaster(self, c, f, data):
        G = self.sysconf.General
        
        if not G.get('haconf'):
            G['haconf'] = {
                'masterkey': data['key'].encode()
            }
        else:
            G['haconf']['masterkey'] = data['key'].encode()
        self.sysconf.General = G 
        
        return url.root.child('HA')

    def locateChild(self, ctx, segs):
        if segs[0] == "Sync":
            return WebUtils.system('/usr/local/tcs/tums/configurator --ha').addBoth(lambda _: url.root.child('HA')), ()
        
        return PageHelpers.DefaultAthena.locateChild(self, ctx, segs)

    def form_genKey(self, ctx):
        form = formal.Form()

        form.addField('key', formal.String(), label = "Access Key",
            description="This key is generated on submit. Paste this key into the section below on the slave server")
        
        try:
            l = open('/root/.ssh/identity.pub')
            form.data['key'] = l.read()
            l.close()

        except Exception, e:
            print "No key found", e

        form.addAction(self.submitKey)
        return form

    def submitKey(self, ctx, f, data):
        # Generate an SSH key 
        return WebUtils.system('rm /root/.ssh/identity; rm /root/.ssh/identity.pub; ssh-keygen -b 1024 -t rsa -N "" -C v2 -f /root/.ssh/identity').addBoth(
            lambda _: url.root.child('HA')
        )

    def getEthernets(self):
        f = open('/proc/net/dev')
        devs = []
        for i in f:
            l = i.strip()
            if 'eth' in l:
                devs.append(l.split(':')[0])
        return devs

    def form_clusterPort(self, ctx):
        form = formal.Form()
        form.addField('port', formal.String(required=True),
            formal.widgetFactory(formal.SelectChoice, options = [(i,i) for i in self.getEthernets() ]), label = "Ethernet Port", 
            description = "Choose an Ethernet port which will be used to monitor cluster peers")

        form.data['port'] = self.sysconf.General.get('haconf', {}).get('port', '')

        form.addAction(self.submitPort)
        return form
           
    def submitPort(self, ctx, f, data):
        G = self.sysconf.General
        if not G.get('haconf'):
            G['haconf'] = {}
        
        G['haconf']['port'] = data['port']

        self.sysconf.General = G 
        
        return WebUtils.system('/usr/local/tcs/tums/configurator --ha').addBoth(lambda _: url.root.child('HA'))

    def render_content(self, ctx, data):
        return ctx.tag[
            tags.h3[tags.img(src="/images/networking_section.png"), " Cluster"],
            PageHelpers.TabSwitcher([
                ('Configuration', 'config-me'),
                ('Cluster', 'config-cluster')
            ]),
            tags.div(id='config-me', _class='tabPane')[
                tags.h3["Cluster port"], 
                tags.directive('form clusterPort'),
                tags.h3["Generate access key"],
                tags.directive('form genKey'),
                tags.h3["Master key"],
                tags.directive('form masterKey')
            ],
            tags.div(id='config-cluster', _class='tabPane')[
                tags.div[
                    tags.invisible(render=tags.directive('thisFragment')),
                    tags.a(href="Sync/")['Synchronise Cluster']
                ]
            ],
            PageHelpers.LoadTabSwitcher()
        ]

