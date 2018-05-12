from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, twcgi
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan, compression
from nevow.taglibrary import tabbedPane
import Tree, Settings, LDAPDir, time, os
from Core import PageHelpers, Auth, WebUtils, confparse, Utils

class RefreshTo(rend.Page):
    def __init__(self, url=None, *a):
        rend.Page.__init__(self, *a)
        self.url = url.replace('Sx63', '?')
        print self.url
        if not self.url.strip('http://'):
            self.url = "http://www.vulani.net"

    def render_head(self, ctx, data):
        return ctx.tag[
            tags.xml('<meta http-equiv="Pragma" content="no-cache"/><meta http-equiv="Expires" content="-1"/><meta http-equiv="refresh" content="1;url=%s"/>' % self.url)
        ]

    docFactory = loaders.stan([
        tags.html[
            tags.head[
                tags.invisible(render=tags.directive("head"))
            ]
        ]
    ])

class Portal(rend.Page):
    addSlash    = True
    docFactory  = loaders.xmlfile('captive.xml', templateDir=Settings.BaseDir+'/templates')
    
    def __init__(self, host=None, url=[], error=None, *a):
        self.radauth = Auth.RadiusLDAPAuthenticator()
        rend.Page.__init__(self, *a)
        self.host = host
        self.url = url
        self.error = error
        self.sysconf = confparse.Config()

    def render_error(self, ctx, data):
        return ctx.tag[tags.div(style="color: #ff0000")[self.error or ""]]

    def render_form(self, ctx, data):
        """Renders our login form"""
        newurl = "/myvulani/login/%s" % ('/'.join(self.url))
        return ctx.tag(action=newurl)

    def locateChild(self, ctx, segments):
        req = inevow.IRequest(ctx)

        headers = req.received_headers
        print headers, req.client
        # Lets play find the host!
        host = headers.get('x-forwarded-for', req.client.host)
        detail = req.args

        if segments[0] == "login":
            if not detail.get('username'):
                return Portal(self.host, self.url, "Username not provided"), ()
            if not detail.get('password'):
                return Portal(self.host, self.url, "Password not provided"), ()

            user = detail['username'][0]
            passw = detail['password'][0]

            def returnAuth(res):
                # Trace back our topology and find our closest interface to this host
                iface, zone, network, routed = Utils.traceTopology(self.sysconf, host)
                ipserv = self.sysconf.EthernetDevices[iface]['ip'].split('/')[0]
                print res, user, passw, ipserv, iface, zone, network, routed, host
                if res: 
                    print "Ok bitch"
                    # Add our record to the zone
                    def done(mac):
                        print "User has this MAC", mac
                        l = open('/tmp/caportal/%s' % host, 'wt')
                        l.write("%s|%s|%s" % (time.time(), mac.strip('\n'), user))
                        l.close()
                        os.chmod('/tmp/caportal/%s' % host, 0777)
                        print "Resturning person to ", segments
                        #return url.URL.fromString('http://%s' % ('/'.join(segments[1:])))
                        return RefreshTo(url='http://%s' % ('/'.join(segments[1:])))
                    def next(_):
                        print "Added shorewall, going to ARP check"
                        return WebUtils.system("arp -n | grep %s | awk '{print $3}'" % host).addBoth(done)
                    return WebUtils.system('shorewall add %s:%s c%s' % (iface, host, zone)).addBoth(next), ()

                print "Invalid authentication from", user, ":", repr(res)

                return Portal(self.host, self.url, "Invalid username or password."), ()
                #return url.URL.fromString('http://%s:9682/myvulani/%s' % (ipserv, '/'.join(segments[1:]))), ()

            # Check for active directory 
            def gotADAuth(res):
                return returnAuth("OK" in res)
            
            if self.sysconf.ProxyConfig.get('adauth'):
                return WebUtils.system("echo %s %s | /usr/lib/squid/msnt_auth" % (user, passw)).addBoth(gotADAuth)
            else:
                auth = self.radauth.authenticateUser(user, passw)
                return returnAuth(auth)

        if not self.url:
            return Portal(None, segments), ()
        
        return Portal(self.host, self.url), ()

    def renderHTTP_notFound(self, ctx):
        return url.root

class PortalRedirector(rend.Page):
    def locateChild(self, ctx, segments):
        sysconf = confparse.Config()
        req = inevow.IRequest(ctx)
        host = req.received_headers.get('x-forwarded-for', req.client.host)

        # Trace back our topology and find our closest interface to this host
        iface, zone, network, routed = Utils.traceTopology(sysconf, host)
        ipserv = sysconf.EthernetDevices[iface]['ip'].split('/')[0]

        return url.URL.fromString('http://%s:9682/myvulani/%s' % (ipserv, '/'.join(segments))), ()

    docFactory = loaders.xmlfile('captive.xml', templateDir=Settings.BaseDir+'/templates')

class chartResource(rend.Page):
    def renderHTTP(self, ctx):
        request = inevow.IRequest(ctx)

        def outputData(fi):
            request.setHeader("content-type", "image/png")
            request.setHeader("content-length", str(len(fi)))

            return fi

        getArgs = request.args

        chart = WebUtils.createChart(getArgs)

        if chart:
            return outputData(chart.read())
        
        return "Invalid type"

class SafePage(rend.Page):
    """ SafePage renderer"""
    db = None

    def __init__(self, db=None, *a , **kw):
        rend.Page.__init__(self, *a, **kw)

        self.db = db
    
    def childFactory(self, ctx, seg):
        # URL is encoded in seg.

        return SafePage(db=seg)

    docFactory = loaders.stan(
        tags.html[
            tags.head[
                tags.title["Vulani SafePage Advisory: Malicious content detected!"],
            ],
            tags.body[
                tags.invisible(render=tags.directive('header')),
                #tags.
            ]
        ]
    )
    
class ThebeName(rend.Page):
    def __init__(self, thebe=None, *a, **kw):
        rend.Page.__init__(self, *a, **kw)
        self.thebe = thebe

    def renderHTTP(self, ctx):
        me = self.thebe.master.myName
        return me

class Page(rend.Page):
    db = None

    def __init__(self, db, *a, **kw):
        rend.Page.__init__(self, *a, **kw)
        self.db = db

    addSlash = True
    child_css = compression.CompressingResourceWrapper(static.File(Settings.BaseDir+'/css/'))
    child_scripts = compression.CompressingResourceWrapper(static.File(Settings.BaseDir+'/scripts/'))
    child_images = compression.CompressingResourceWrapper(static.File(Settings.BaseDir+'/images/'))
    child_sandbox = compression.CompressingResourceWrapper(static.File(Settings.BaseDir+'/sandbox/'))
    child_php = static.File('/var/www/localhost/htdocs/')
    child_packs = static.File(Settings.BaseDir+'/packages/')
    child_updates = static.File('/var/lib/samba/updates/')
    child_chart = chartResource()
    child_myvulani = Portal()
    child_portal = PortalRedirector()
    child_topology = PageHelpers.Topology()

    def childFactory(self, ctx, seg):
        if seg == "favicon.ico":
            return static.File(Settings.BaseDir+'/images/favicon.ico')
        if seg == "whoami":
            return ThebeName(self.db[-1])
        return rend.Page.childFactory(self, ctx, seg)
    
    def render_content(self, ctx, data):
        return ctx.tag[
            tags.a(href="/auth/")["Login"]
        ]

    def render_head(self, ctx, data):
        return ctx.tag[
            tags.xml('<meta http-equiv="refresh" content="0;url=auth/"/>')
        ]

    docFactory = loaders.stan(
        tags.html[
            tags.head[
                tags.title["Vulani"],
                tags.invisible(render=tags.directive('head'))
            ],
            tags.body[
                tags.invisible(render=tags.directive('content'))
            ]
        ]
    )

