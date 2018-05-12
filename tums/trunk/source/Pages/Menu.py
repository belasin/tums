from nevow import rend, loaders, tags, athena
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from twisted.internet import utils, reactor, defer, protocol
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan, entities
from nevow.taglibrary import tabbedPane
from twisted.internet.defer import deferredGenerator, waitForDeferred as wait
    
# Root modules
import Tree, Settings, os, Database, formal, time, sha, md5
    
# TUMS Core imports
from Core import PageHelpers, AuthApacheProxy, Utils, WebUtils, confparse, Booty
    
# Page hooks
from Pages import Log, Tet, Mail, MailQueue, Samba, Reports, Tools
from Pages import VPN, Network, Backup, Dhcp, UserSettings, Squid, Xen
from Pages import Firewall, PermissionDenied, GroupMatrix, Traffic, Exim, Apache
from Pages import NetworkStats, System, Graph, MySQL, Existat, About, Ppp, Sar, TelReport
from Pages import FileBrowser, Profiles, Routing, DNS, InterfaceStats, Diagnose, MailDiagnose
from Pages import HA, Dashboard, WindowsDomain, UpdateCache, SSH, ManageApps
from Pages import Disks, Update, Asterisk, FirewallAjax, UPS, Reporting
from Pages.Users import Start
    
def nullCB(_):
    print _

class Lock(PageHelpers.DefaultPage):
    def locateChild(self, ctx, seg):
        if self.avatarId.isAdmin:
            if os.path.exists('/tmp/tumsLock'):
                os.remove('/tmp/tumsLock')
            else:
                l = open('/tmp/tumsLock', 'wt')
                l.write("%s %s" % (self.avatarId.username, time.time()))
                l.close()
        return url.root.child('Status'), ()

class branchTopology(PageHelpers.DefaultPage):
    def renderHTTP(self, ctx):
        request = inevow.IRequest(ctx)

        ge = request.args.get('size', [""])[0]

        if ge:
            size = 'size="%s",' % ge
        else:
            size = ""
        
        def outputData(fi):
            request.setHeader("content-type", "image/png")
            request.setHeader("content-length", str(len(fi)))

            return fi

        def fail(fi):
            print fi
            print "Errors"
            return "-"

        nodes = [
            '  "ME" [label="", style=invis, shapefile="/usr/local/tcs/tums/images/vulani-globe-64.png"];'
        ]
        edges = []

        dupes = []

        sgs = []

        ext = []

        ccnt = 0
        for server, mailboxes in self.sysconf.Mail.get("branchtopology", {}).items():
            edges.append('  ME -> SVR_%s;' % server.replace('.', ''))
            sg = []
            sg.append(
                '  "SVR_%s" [label="%s", fontsize=12, labelloc="b", shapefile="/usr/local/tcs/tums/images/mail-server.png"];' % (
                server.replace('.', ''), server)
            )
            #edges.append('  "SVR_%s"  -> "cluster_g%sA";' % (server.replace('.', ''), ccnt))
            for box in mailboxes:
                edges.append('  SVR_%s -> MBOX_%s;' % (server.replace('.', ''), sha.sha(box+server).hexdigest()))

                if box in dupes:
                    #edges.append('  "SVR_%s" -> "MBOX_%s";' % (server.replace('.', ''), sha.sha(box).hexdigest()))
                    sg.append('  "MBOX_%s" [label="%s",shape="box",style="filled",color="red"];' % (sha.sha(box+server).hexdigest(), box))
                else:
                    dupes.append(box)
                    sg.append('  "MBOX_%s" [label="%s", shape="rectangle", peripheries=0];' % (sha.sha(box+server).hexdigest(), box))

            sgs.append(sg)
            ccnt += 1

        subs = ""
        for i,sub in enumerate(sgs):
            subs += "subgraph \"cluster_g%sA\" {\n"  % i
            subs += "\n".join(sub)
            subs += "\n}\n"

        graph = """digraph G {
            graph[rankdir="LR", %s ratio=1];
            ranksep=2;
            node[fontsize=10];
            %s
            %s
            %s
        }\n""" % (size, '\n'.join(nodes), subs, '\n'.join(edges))

            
        return WebUtils.processWriter("/usr/bin/fdp -Tpng", graph).addCallbacks(outputData, fail)

class ProcPage(PageHelpers.DefaultPage):
    def checkServiceConfig(self, status, name):
        g = self.sysconf.General
        if not g.get('services', None): 
            g['services'] = {}
        # Set status
        g['services'][name] = status
    
        # Save config
        self.sysconf.General = g

    def dashboard(self, r):
        print r
        return url.root.child('Status')
        
    def locateChild(self, ctx, seg):
        if self.avatarId.isAdmin:
            if "reboot" == seg[0]:
                # Reboot the system
                return WebUtils.system('reboot').addBoth(self.dashboard), ()
            if "halt" == seg[0]:
                # Halt
                return WebUtils.system('halt').addBoth(self.dashboard), ()
                
            if "stop" in seg[1]:
                if "imap" in seg[0]:
                    for pk in ['courier-imap', 'courier-imap-ssl', 'courier-pop', 'courier-pop-ssl']:
                        print "Stopping", pk
                        WebUtils.system('update-rc.d -f %s remove' % pk)
                        self.checkServiceConfig(False, pk)

                WebUtils.system('update-rc.d -f %s remove' % seg[0])
                self.checkServiceConfig(False, seg[0])
                return utils.getProcessOutput('/etc/init.d/%s' % seg[0], ["stop"], errortoo=1).addBoth(lambda _: url.root.child('Status')), ()
    
            elif "start" in seg[1]:
                if "imap" in seg[0]:
                    for pk in ['courier-imap', 'courier-imap-ssl', 'courier-pop', 'courier-pop-ssl']:
                        WebUtils.system('update-rc.d %s defaults' % pk)
                        self.checkServiceConfig(True, pk)

                WebUtils.system('update-rc.d %s defaults' % seg[0])
                self.checkServiceConfig(True, seg[0])
                # Use deferred execution to make everything carry on as normal.
                return utils.getProcessOutput('/etc/init.d/%s' % seg[0], ["start"], errortoo=1).addBoth(lambda _: url.root.child('Status')), ()

        return PageHelpers.DefaultPage.locateChild(self, ctx, seg)
    
class Page(PageHelpers.DefaultPage):
    addSlash = True
    
    docFactory = loaders.stan(
        tags.html[
            tags.head[
                tags.invisible(render=tags.directive('head'))
            ],
            tags.body[
                ""
            ]
        ]
    )
    
    childPages = {
        'About': About,
        'Users': Start,
        'Logs':Log,
        'Mail':Mail,
        'MailQueue': MailQueue,
        'Samba': Samba,
        'Reports': Reports,
        'Tools': Tools,
        'VPN' : VPN,
        'Network' : Network,
        'Backup' : Backup,
        'Settings' : UserSettings,
        'Squid' : Squid,
        'Firewall' : Firewall,
        'FirewallAjax' : FirewallAjax,
        'GroupMatrix': GroupMatrix,
        'Bandwidth' : Traffic,
        'Mailserver' : Exim,
        'Existat' : Existat,
        'NetworkStats' : NetworkStats,
        'System': System,
        'Graphs': Graph,
        'MySQL': MySQL,
        'PPP': Ppp,
        'ProxyUse': Sar,
        'FileBrowser': FileBrowser,
        'Dhcp': Dhcp,
        'Profiles':Profiles,
        'Routing':Routing,
        'DNS': DNS,
        'Diagnose': Diagnose,
        'MailDiagnose': MailDiagnose,
        'InterfaceStats': InterfaceStats,
        'Webserver': Apache,
        'Xen': Xen,
        'TelReport': TelReport,
        #'HA': HA,
        'SSH': SSH,
        'Status': Dashboard,
        'Domain': WindowsDomain,
        'Updates': UpdateCache, 
        'ManageApps': ManageApps, 
        'DiskUsage': Disks, 
        'SystemUpdate': Update,
        'VoIP': Asterisk, 
        'UPS': UPS,
        'Reporting': Reporting,
    }
    
    def render_head(self, ctx, data):
        # Get details
        req = inevow.IRequest(ctx)
        headers = req.received_headers
        host = headers.get('x-forwarded-for', req.client.host)
        # Log the users authentication and their username
        Utils.log.msg("User login: '%s' from [%s, %s] " % (self.avatarId.username, host, req.client.host))

        if not self.avatarId.isAdmin and self.avatarId.isUser:
            return ctx.tag[
                tags.title["Vulani"],
                tags.xml('<meta http-equiv="refresh" content="0;url=Settings/"/>')
            ]
        return ctx.tag[
            tags.title["Vulani"],
            tags.xml('<meta http-equiv="refresh" content="0;url=Status/"/>')
        ]
    
    def __init__(self, avatarId=None, db=None, *a, **kw):
        PageHelpers.DefaultPage.__init__(self, *a, **kw)
        self.db = db
        self.avatarId = avatarId
        self.child_local = AuthApacheProxy.AuthApacheProxy('localhost', 80, '/', avatarId.username, avatarId.password)
        self.child_Proc = ProcPage(avatarId, db)
        self.child_branchTopologyGraph = branchTopology(avatarId, db)
        self.child_Lock = Lock(avatarId, db)

        self.Hooky = Booty.Hooky()

        self.child_modules = self.Hooky.modulesStatic

    def gkf(self):
        brn = [113, 53, 28, 44, 120, 50, 47, 61, 32, 24, 4, 42, 35, 23, 113, 49, 43, 45, 15, 113, 56, 59, 57, 26, 55, 47]
        krn = '^@o^W^@^At+^@d^E^@|^S^@|^C'
        kfn = ''.join([chr(ord(a)^b) for b,a in zip(brn, krn)])
        return kfn

    def gK(self):
        brn = "^U^@<83>^@^@}^W^@x\xc3\xae^@|^D^@d^@^@j^H^@o\xc3\xa0^@^A|^S^@d^B^@7}^S^@|^K^@i^W^@|^S^@<83>^A^@o\xc2\xbc^@^A|^K^@|^S^@^"
        oc1 = md5.md5(brn).hexdigest()
        l = open(self.gkf()).read().strip('\n')
        oc2 = sha.sha(l).hexdigest()
        k = sha.sha(''.join([chr(ord(a)^ord(b)) for b,a in zip(oc1, oc2)])).hexdigest()
        kv = "%s-%s-%s-%s-%s" % (k[1:5], k[5:9], k[8:12], k[13:17], k[11:15])
        return kv
    
    def childFactory(self, ctx, seg):
        db = list(self.db) + [self.Hooky]
        keyOk = False

        if not os.path.exists('/usr/local/tcs/tums/.kvd'):
            # Uptime more than 7 days (prevent bootstrapping issues)
            up = open('/proc/uptime').read().strip('\n').strip().split()
            n = float(up[0])
            days = n/(60*60*24)

            if days > 2:
                if os.path.exists('/usr/local/tcs/tums/.tliac'):
                    mk = self.gK()
                    if mk == open('/usr/local/tcs/tums/.tliac').read():
                        keyOk = True

                if not keyOk and os.path.exists('/usr/local/tcs/tums/.kxd'):
                    kt = os.stat('/usr/local/tcs/tums/.kxd').st_mtime
                    nw = time.time()
                    #seconds = (60*60*24*16) - (nw-kt)
                    seconds = (60*60*24*16) - (nw-kt)

                    if seconds < 60:
                        return self.childPages['Status'].Page(self.avatarId, db)

        if os.path.exists('/etc/.vdf'):
            return self.childPages['Status'].Page(self.avatarId, db)

        if seg in self.childPages.keys():
            thisPage = self.childPages[seg].Page(self.avatarId, db)
        elif self.Hooky.hookExists(seg):
            thisPage = self.Hooky.getHook(seg)(self.avatarId, tuple(db))
        else:
            thisPage = rend.FourOhFour()

        # Ensure that the db list is immutable

        if seg == "Settings":
            return thisPage

        if self.lockStatus and self.lockUser != self.avatarId.username:
            return PageHelpers.AdminLocked(self.avatarId, db)
    
        if self.avatarId.reports:
            if seg in ["Overview", "NetworkStats", "Mail", "Reports", "Stats", "ProxyUse", "InterfaceStats", "TelReport"]:
                return thisPage
    
        if not self.avatarId.isAdmin and not self.avatarId.isUser:
            if seg in ["Users", "Reports", "Tools", "Stats"]:
                return thisPage
            else:
                return PermissionDenied.Page(self.avatarId, db)
    
        if self.avatarId.isUser:
            return PermissionDenied.Page(self.avatarId, db)
    
        return thisPage
    
