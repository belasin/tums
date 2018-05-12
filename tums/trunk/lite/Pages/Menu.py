from nevow import rend, loaders, tags, athena
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from twisted.internet import utils, reactor
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
from twisted.internet.defer import deferredGenerator, waitForDeferred as wait

# Root modules
import Tree, Settings, os, Database, formal

# TUMS Core imports
from Core import PageHelpers, AuthApacheProxy, Utils, WebUtils

# Page hooks
from Pages import Users, Log, Tet, Stats, Shorewall, Mail, MailQueue, Samba, Reports, Tools
from Pages import VPN, Netdrive, Network, Backup, Dhcp, UserSettings, Computers, Squid
from Pages import Firewall, PermissionDenied, GroupMatrix, Traffic, Exim, Overview
from Pages import NetworkStats, System, Graph, MySQL, Existat, About, Ppp, Sar, SambaConfig
from Pages import FileBrowser, Qos, Policy, Profiles

def nullCB(_):
    print _

class ProcPage(PageHelpers.DefaultPage):
    def locateChild(self, ctx, seg):
        if self.avatarId.isAdmin:
            if "stop" in seg[1]:
                if os.path.exists('/etc/debian_version'):
                    WebUtils.system('update-rc.d -f %s remove' % seg[0])
                else:
                    WebUtils.system('rc-update -d %s' % seg[0])
            elif "start" in seg[1]:
                if os.path.exists('/etc/debian_version'):
                    WebUtils.system('update-rc.d %s defaults' % seg[0])
                else:
                    WebUtils.system('rc-update -a %s default' % seg[0])
            # Use deferred execution to make everything carry on as normal.
            utils.getProcessOutput('/etc/init.d/%s' % seg[0], [seg[1]], errortoo=1).addCallbacks(nullCB, nullCB)
        return url.root, ()

class liveGraphFragment(athena.LiveFragment):
    jsClass = u'statusGraphs.PS'

    kicks = ['renderGraphs', 'renderTables'] 

    docFactory = loaders.xmlfile('statusGraphs.xml', templateDir = Settings.BaseDir + '/templates')

    loadAve = []
    networkStats = {}
    last = {}

    def __init__(self, *a, **kw):
        super(liveGraphFragment, self).__init__(*a, **kw)
        reactor.callLater(2, self.kickEvents)
        self.loadAve = [[0.0, 0.0, 0.0] for i in xrange(20)]

    def render_interfaces(self, ctx, data):
        ifaces = self.getIFStat().keys()
        ifaces.sort()
        return ctx.tag[
            [
                [
                    tags.h3['Network Load:', iface],
                    tags.div[
                        tags.xml('<canvas id="graph%s" height="128" width="256"/>' % iface)
                    ]
                ]
            for iface in ifaces ]
        ]
    def render_load(self, ctx, data):
        return ctx.tag[
            tags.h3["System Load"],
            tags.div[
                tags.xml('<canvas id="graphload" height="128" width="256"/>')
            ]
        ]

    def getIFStat(self):
        ps = open("/proc/net/dev")

        results = {}

        for ln in ps:
            line = ln.strip()
            if "ppp" in line or "eth" in line:
                bits = line.split(':')[-1].split()
                ipin = float(bits[0])
                ipout = float(bits[8])
                iface = line.split(':')[0]
                if "eth" in iface:
                    num = iface.strip('eth')
                    iface = "Port "+num
                if "ppp" in iface:
                    num = iface.strip('ppp')
                    iface = "PPPoE "+num
                if iface!="lo":
                    results[iface] = (ipin, ipout)

        ps.close()

        return results

    def processCall(self, name, args=[]):
        return utils.getProcessOutput(name, args, errortoo=1)

    def systemCalls(self):
        # EMAIL
        if os.path.exists('/etc/debian_version'):
            debianMode = True
        else:
            debianMode = False
        proclist = ["dhcpd", "squid", "apache2", "openvpn.vpn", "samba", "courier-imapd", "sshd"]
        namelist = {
                    "dhcpd": u"DHCP Server",
                    "dhcp3-server": u"DHCP Server",
                    "squid": u"Web Proxy",
                    "squid3": u"Web Proxy",
                    "apache2": u"Web Server",
                    "openvpn.vpn": u"VPN Server",
                    "openvpn": u"VPN Server",
                    "samba": u"File Server",
                    "courier-imapd": u"IMAP Mail Server",
                    "courier-imap": u"IMAP Mail Server",
                    "sshd": u"Secure Shell"
                }

        if Settings.Mailer == "exim":
            mq = utils.getProcessOutput(Settings.BaseDir+'/syscripts/mailQueue.sh', [], errortoo=1)
            res = wait(mq)
            yield res
            mq = res.getResult()
            mq = unicode(mq.strip('\n')).split()
            proclist.append('exim')
            namelist['exim'] = "Mail Server"
            namelist['exim4'] = "Mail Server"

        else:
            mq = utils.getProcessOutput(Settings.BaseDir+'/syscripts/postQueue.sh', [], errortoo=1)
            res = wait(mq)
            yield res
            mq = res.getResult()
            if not "is empty" in mq:
                post = mq.strip('\n').split()
                mq = [unicode(post[4]), u"%s %s" % (post[1], post[2])]
            else:
                mq = [u"0", u"0"]
            proclist.append('postfix')
            namelist['postfix'] = u"Mail Server"

        # PROCESS LISTS 
        procstatus = []
        for proc in proclist:
            if debianMode:
                # Remap package names for Debian
                if proc == "openvpn.vpn":
                    checkproc = "openvpn"
                    proc = "openvpn"
                elif proc == "courier-imapd":
                    checkproc = "couriertcpd"
                    proc = "courier-imap"
                elif proc == "samba":
                    checkproc = "smbd"
                elif proc == "dhcpd":
                    checkproc = "dhcpd"
                    proc = "dhcp3-server"
                elif proc == "exim":
                    proc = "exim4"
                    checkproc = "exim"
                elif proc == "squid":
                    proc = "squid3"
                    checkproc = "squid"
                else:
                    checkproc = proc
                stat = self.processCall(Settings.BaseDir+'/syscripts/debInitStat.sh', [checkproc])
            else:
                stat = self.processCall(Settings.BaseDir+'/syscripts/initStat.sh', [proc])
            res = wait(stat)
            yield res
            stat = res.getResult()
            if "started" in stat:
                procstatus.append((
                    u'/images/green.gif', 
                    unicode(namelist[proc]), 
                    (u'Running. Click to stop this service', url.root.child('Proc').child(proc).child('stop'), u'Running')
                ))
            elif "stop" in stat:
                procstatus.append((
                    u'/images/red.gif',
                    unicode(namelist[proc]),
                    (u'Not running. Click to start this service', url.root.child('Proc').child(proc).child('start'), u'Stopped')
                ))

            else:
                procstatus.append((
                    u'/images/horange.gif',
                    unicode(namelist[proc]),
                    (u'Can\'t tell the status. Click to force a restart', url.root.child('Proc').child(proc).child('restart'), u'Unknown')
                ))

        # DISK UTILL 
        d = self.processCall(Settings.BaseDir+'/syscripts/diskUtil.sh')
        res = wait(d) 
        yield res
        d = unicode(res.getResult())
        filesystem = []

        for i in d.split('\n'):
            f = unicode(i.strip('\n')).split()
            filesystem.append(f)

        d = self.processCall(Settings.BaseDir+'/syscripts/raidStat.sh')
        res = wait(d)
        yield res
        d = unicode(res.getResult())
        raids = {}
        if not "No such file" in d: # Don't try if the raid doesn't exist...
            thisRaid = ""
            for i in d.split('\n'):
                l = i.strip().strip('\n')
                if l:
                    line = l.split()
                    if "md" in line[0]:
                        thisRaid = line[0]
                        raids[thisRaid] = [line[2], line[3], line[4:]]
                    else:
                        raids[thisRaid].append(line[3])
        raidstat = []
        for i in raids.keys():
            thisRaid = [unicode(i), unicode(raids[i][1]), u"%s %s" % (raids[i][0], raids[i][3])]
            smart = []
            for i in raids[i][2]:
                s = self.processCall(Settings.BaseDir+'/syscripts/smartStat.sh', [i[:3]])
                res = wait(s) 
                yield res
                s = res.getResult()
                smart.append(u"%s: %s" % (i, s.strip('\n').replace('=== START OF READ SMART DATA SECTION ===','')))

            thisRaid.append(smart)
            
            raidstat.append(thisRaid)
        # SAMBA SESSIONS
        s = self.processCall('/usr/bin/net', ['status', 'shares', 'parseable'])
        res = wait(s) 
        yield res
        s = res.getResult()
        shares = {}
        for i in s.split('\n'):
            if i:  
                l = unicode(i).split('\\')
                if not shares.get(l[3], None):
                    shares[l[3]] = []
                shares[l[3]].append(l[0])
        del s

        s =  self.processCall('/usr/bin/net', ['status', 'sessions', 'parseable'])
        res = wait(s) 
        yield res
        s = res.getResult()
        sessions = []
        for i in s.split('\n'):  
            if i:  
                l = i.split('\\')
                if shares.get(l[1], None):
                    shareopen = [u'%s' % k for k in shares[l[1]] ]
                else:
                    shareopen = [u""]
                sessions.append([unicode(l[1]), unicode(l[2]), u"%s (%s)" % (l[3], l[4]),shareopen])
        del s 

        uptime = self.processCall('/usr/bin/uptime')
        res = wait(uptime)
        yield res
        s = res.getResult()
        uptime = s.strip('\n').split(',')
        time = unicode(uptime[0].split()[0])
        up = unicode(' '.join(uptime[0].split()[2:4]))
        users = unicode(uptime[2].split()[0])
        yield mq, procstatus, filesystem, raidstat, shares, sessions, time, up, users 
    systemCalls = deferredGenerator(systemCalls)


    def getSystemDetails(self):
        def returnTup(_):   
            return _
        def error(_):
            print "---------------------------------------------"
            print "Failure", _
            print "---------------------------------------------"
            return ((0,0), (), (), (), (), (), 0,0,0)
        return self.systemCalls().addCallbacks(returnTup, error)
    athena.expose(getSystemDetails)

    def kickEvents(self):
        for kick in self.kicks:
            self.callRemote(kick)

    def getLoadAve(self):   
        def processDeferredResult(stdout):
            # Load averages
            del self.loadAve[0]
            self.loadAve.append([float(i) for i in stdout.replace(',','').split()[-3:]])
            zipped = [[],[],[]]
            for cnt, i in enumerate(self.loadAve):
                k = 0 
                for j in i:
                    zipped[k].append((cnt,j))
                    k+=1
            # Network stats
            
            latest = self.getIFStat()
            statsNow = {}
            for iface, bits in latest.items():
                # if this is the first run, clear the stats with stuff
                if not self.networkStats.get(iface, False):
                    self.networkStats[iface] = [(0.0, 0.0) for i in xrange(20)]

                rate = (0, 0)
                if self.last.get(iface, False):
                    tel = zip(self.last[iface], bits)
                    rate = [((i[1]-i[0])*8)/(2000) or 1.0 for i in tel]

                if len(self.networkStats[iface]) > 19:
                    del self.networkStats[iface][0]

                self.networkStats[iface].append(rate)

                statzip = [[],[]]
                for cnt, i in enumerate(self.networkStats[iface]):
                    k = 0
                    for j in i:
                        statzip[k].append((cnt, j))
                        k+=1
               
                statsNow[unicode(iface)] = statzip

            self.last = latest
            skeys = statsNow.keys()

            return zipped, statsNow, skeys
        return utils.getProcessOutput('/usr/bin/uptime', [], errortoo=1).addCallback(processDeferredResult)
    athena.expose(getLoadAve)

class StatusPage(PageHelpers.DefaultAthena):
    moduleName = 'statusGraphs'
    moduleScript = 'statusGraphs.js'
    docFactory = loaders.xmlfile('livepage.xml', templateDir = Settings.BaseDir + '/templates')

    def __init__(self, avatarId, db, *a, **kw):
        PageHelpers.DefaultAthena.__init__(self, avatarId, db, *a, **kw)

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Dashboard"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[""]

    def render_thisFragment(self, ctx, data):
        """ Renders liveGraphFragment instance """
        f = liveGraphFragment()
        f.setFragmentParent(self)
        return ctx.tag[f]

    def dataTable(self, headings, content):
        return tags.table(cellspacing=0,  _class='listing')[
            tags.thead(background="/images/gradMB.png")[
                tags.tr[
                    [ tags.th[i] for i in headings ]
                ]
            ],
            tags.tbody[
            [
                tags.tr[ [tags.td[col] for col in row] ]
            for row in content],
            ]
        ]

    def form_selectProfile(self, data):
        form = formal.Form()

        profiles = []
        for il in os.listdir('/usr/local/tcs/tums/profiles/'):
            if il[-3:] == '.py':
                name = il[:-3].replace('_', ' ').capitalize()
                profiles.append((il, name))
        
        form.addField('profile', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = profiles), label = "Switch Profile")
        form.addAction(self.switchProfile)
        return form

    def switchProfile(self, ctx, form, data):
        l = open('/usr/local/tcs/tums/currentProfile', 'wt')
        l.write(data['profile'].encode())
        l.close()
        return url.root.child('Status')

    def render_content(self, ctx, data):
        """ Function is deffered to make less blocking on system calls"""
        
        if not self.avatarId.isAdmin:
            return ctx.tag[""]

        # Fetch running profile
        thisProfile = Utils.currentProfile()

        runningProfile = Utils.runningProfile()[0]

        if thisProfile[0] != runningProfile:
            thisProfile = [thisProfile[0]," [", tags.a(href=url.root.child("Profiles").child("switch").child(thisProfile[1]))["Activate"]], "]"
        else:
            thisProfile = thisProfile[0]

        return ctx.tag[
            tags.table(width="100%", cellspacing="10")[
                tags.tr[
                    tags.td(colspan=2)[
                        tags.div(id="ProfileBlock")[
                            tags.div(_class="roundedBlock")[
                                tags.h1["Profile"],tags.div(id="123")[
                                    "Current profile: ",thisProfile,tags.br,
                                    "Running profile: ",runningProfile,tags.br,
                                    tags.directive('form selectProfile'),
                                    tags.a(href=url.root.child("Profiles"))["Manage Profiles"]
                                ]
                            ],
                        ],
                    ]
                ],
                tags.tr[
                    tags.invisible(render=tags.directive('thisFragment'))
                ]
            ]
        ]

class Page(PageHelpers.DefaultPage):
    addSlash = True

    docFactory = loaders.stan(
        tags.html[
            tags.head[
                tags.title["TUMS"],
                tags.xml('<meta http-equiv="refresh" content="0;url=Status/"/>')
            ],
            tags.body[
                ""
            ]
        ]
    )

    childPages = {
        'About': About,
        'Users': Users,
        'Logs':Log,
        'Tet':Tet,
        'Stats':Stats,
        'Shorewall':Shorewall,
        'Mail':Mail,
        'MailQueue': MailQueue,
        'Samba': Samba,
        'SambaConfig': SambaConfig,
        'Reports': Reports,
        'Tools': Tools,
        'VPN' : VPN,
        'Netdrive' : Netdrive,
        'Network' : Network,
        'Backup' : Backup,
        'Settings' : UserSettings,
        'Computers' : Computers,
        'Squid' : Squid,
        'Firewall' : Firewall,
        'GroupMatrix': GroupMatrix,
        'Bandwidth' : Traffic,
        'Mailserver' : Exim,
        'Existat' : Existat,
        'Overview' : Overview,
        'NetworkStats' : NetworkStats,
        'System': System,
        'Graphs': Graph,
        'MySQL': MySQL,
        'PPP': Ppp,
        'Policy': Policy,
        'ProxyUse': Sar,
        'FileBrowser': FileBrowser,
        'Qos': Qos,
        'Dhcp': Dhcp,
        'Profiles':Profiles,
    }


    def __init__(self, avatarId=None, db=None, *a, **kw):
        rend.Page.__init__(self, *a, **kw)
        self.db = db
        self.avatarId = avatarId
        self.child_local = AuthApacheProxy.AuthApacheProxy('localhost', 80, '/', avatarId.username, avatarId.password)
        self.child_Proc = ProcPage(avatarId, db)

    def childFactory(self, ctx, seg):
        if seg == "Settings":
            return self.childPages[seg].Page(self.avatarId, self.db)

        if seg =="Status":
            return StatusPage(self.avatarId, self.db)

        if self.avatarId.reports:
            if seg in ["Overview", "NetworkStats", "Mail", "Reports", "Stats"]:
                return self.childPages[seg].Page(self.avatarId, self.db)

        if not self.avatarId.isAdmin and not self.avatarId.isUser:
            if seg in ["Users", "Tet", "Reports", "Tools", "Stats"]:
                return self.childPages[seg].Page(self.avatarId, self.db)
            else:
                return PermissionDenied.Page(self.avatarId, self.db)

        if self.avatarId.isUser:
            if seg in ["Settings"]:
                return self.childPages[seg].Page(self.avatarId, self.db)
            else:
                return PermissionDenied.Page(self.avatarId, self.db)

        if seg in self.childPages.keys():
            return self.childPages[seg].Page(self.avatarId, self.db)

