from nevow import rend, loaders, tags, athena, context, flat
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure, log
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
from zope.interface import implements
from Core import Utils, confparse
import Tree, Settings, formal
try:
    from twisted.web import http
except ImportError:
    from twisted.protocols import http

VERSION = '1.5.0'
CODENAME = "Chrome"

def progressBar(percent):
    length = 200.0
    percentText = "%s%%" % int(percent*100)
    return tags.div(style='border:1px solid black; width: %spx; height:16px;' % (length+2))[
        tags.div(style='float:left; margin-left: %spx;' % int((length/2)-15))[percentText],

        tags.div(style='margin-top:1px; margin-left:1px; width:%spx; height:14px; background: #EC9600;' % int(length*percent))[''],
    ]

def TabSwitcher(tabs):
    tabNames = [i for j,i in tabs]
    tabLables = [i for i,j in tabs]

    closeTabs = ';\n'.join(["    hideElement('%s'); getElement('tab%s').style.color='#666666';" % (i,i) for i in tabNames])

    switchFunc = """
        tabSwitcher = function (tab) {
            %s
            getElement('tab'+tab).style.color='#E710D8';
            showElement(tab);
            createCookie('tabOpen', tab);
        };
    """ % closeTabs

    return [
        tags.xml("""<script type="text/javascript">
        function createCookie(name,value) {
            var date = new Date();
            date.setTime(date.getTime()+(24*60*60*1000));
            var expires = "; expires="+date.toGMTString();
            document.cookie = name+"="+value+expires+"; path=/";
        }

        function readCookie(name) {
            var nameEQ = name + "=";
            var ca = document.cookie.split(';');
            for(var i=0;i < ca.length;i++) {
                var c = ca[i];
                while (c.charAt(0)==' ') c = c.substring(1,c.length);
                if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
            }
            return null;
        }

        createTabSwitcher = function() {
            %s
            var firstTab = '%s';
            showElement(firstTab);
            getElement('tab'+firstTab).style.color='#E710D8';
            try {
                var tab = readCookie('tabOpen');
                if (tab) {
                    %s
                    showElement(tab);
                    getElement('tab'+tab).style.color='#E710D8';
                }
            } catch(dontCare){
                showElement(firstTab);
                getElement('tab'+ firstTab).style.color='#E710D8';
            }
        };
        %s
        </script>""" % (closeTabs, tabNames[0], closeTabs, switchFunc)),
        tags.br, tags.br,
        tags.table(cellspacing=0, cellpadding=0)[tags.tr[
            [
                tags.td(_class = "tabTab", style="padding:0;background-image: url(/images/tabcenter.png); background-repeat: repeat-x;" ,
                    onclick = "tabSwitcher('%s');" % j)[
                        tags.img(src='/images/lefttab.png', align="absmiddle"), 
                        tags.a(
                            id="tab"+j, 
                            href="#",
                            style="color:#666666; text-decoration:none;", 
                            title="Switch to the tab: %s" % i
                        )[tags.strong[i]], 
                        tags.img(src='/images/righttab.png', align="absmiddle")
                ] for i,j in tabs]
        ]]
    ]
    
def LoadTabSwitcher():
    return tags.script(type="text/javascript")["createTabSwitcher();"]

def dataTable(headings, content):
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

class DefaultAthena(formal.ResourceMixin, athena.LivePage):
    addSlash = True
    moduleName = ''
    moduleScript = ''
    fragmentPage = None

    BOOTSTRAP_MODULES = ['Divmod', 'Divmod.Base', 'Divmod.Defer', 'Divmod.Runtime', 'Nevow', 'Nevow.Athena']

    docFactory  = loaders.xmlfile('default.xml', templateDir=Settings.BaseDir+'/templates')

    userMenu = [
         ('http://$ME$/roundcube/', '/images/webmailMB.png', None, "Web based email client"),
         ('/auth/Settings/', '/images/mysetMB.png',None, "Edit your personal account settings"),
         (url.root.child(guard.LOGOUT_AVATAR), "/images/logout.png",None, "Log out of TUMS"),
    ]
    pageMenu = []

    def __init__(self, avatarId = None, db = None, *a, **k):
        mods = athena.jsDeps.mapping
        mods[self.moduleName] = Settings.BaseDir+'/scripts/'+self.moduleScript
        athena.LivePage.__init__(self, jsModules = athena.JSPackage(mods) )
        self.avatarId = avatarId
        self.db = db

    def render_thisFragment(self, ctx, data):
        """ Render overviewFragment instance """
        f = self.fragmentPage(self.db)
        f.setFragmentParent(self)
        return ctx.tag[f]

    def render_footerBar(self, ctx, data):
        return ctx.tag[
            tags.a(href=url.root.child('About'))["TUMS ", VERSION]
        ]

    def render_topBar(self, ctx, data):
        l = [
            ('Status', 'Dashboard', 'View system status'),
            ('Users',  'Users',     'Manage user accounts'),
            ('Reports','Reports',   'View system reports'),
            ('Tools',  'Tools',     'Configure system settings')
        ]
        
        return ctx.tag[
            [ 
                tags.li[tags.h1[tags.a(href=url.root.child(base))[name]], description]
            for base, name, description in l]
        ]

    def render_userBar(self, ctx, data):
        return ctx.tag[
            "Logged in as: ", self.avatarId.username, 
            " | ",
            tags.a(href=url.root.child('Settings'), title="Personal account settings")["Account Settings"],
            " | ",
            tags.a(href=url.root.child(guard.LOGOUT_AVATAR), title="Logout of TUMS")["Logout"]
        ]   

    def render_version(self, ctx, data):
        return VERSION

    def render_content(self, ctx, data):
        return ctx.tag[
            tags.invisible(render=tags.directive('thisFragment'))
        ]

    def addedMenu(self):
        if self.pageMenu:
            return [
                tags.img(src="/images/blockMB.png"),
                [
                    tags.a(href=elm[0], title=elm[3])[tags.img(src=elm[1])]
                for elm in self.pageMenu]
            ]
        else:
            return []


    def render_menu(self, ctx, data):
        host = str(url.URL.fromContext(ctx)).split('//')[-1].split(':')[0]
        if self.avatarId.isUser:
            self.menu= []
        if self.avatarId.reports:
            try:
                del self.menu[3]
            except:
                pass
        if self.menu:
            newBlock = tags.img(src="/images/blockMB.png")
        else:
            newBlock = ""
        return ctx.tag[
            tags.img(src="/images/blockMB.png"),
            [
                tags.a(href=elm[0].replace('$ME$',host), title=elm[3])[tags.img(src=elm[1])]
            for elm in self.menu],
            newBlock,
            [
                tags.a(href=elm[0].replace('$ME$',host), title=elm[3])[tags.img(src=elm[1])]
            for elm in self.userMenu],
            self.addedMenu(),
        ]

    def logout(self):
        print "Logged out"

class TumsExceptionHandler:
    implements(inevow.ICanHandleException)

    def renderHTTP_exception(self, ctx, reason):
        log.err(reason)
        request = inevow.IRequest(ctx)
        request.setResponseCode(http.INTERNAL_SERVER_ERROR)
        request.write('<html><head><title>TUMS Error</title><link rel="stylesheet" type="text/css" href="/css/style.css"/></head><body>')
        request.write('<div id="pageTitle"><img src="/images/thusa.png" alt=""/><ul>')
        request.write('<li><h1><a href="/auth/Status/">Dashboard</a></h1>View system status</li>')
        request.write('<li><h1><a href="/auth/Users/">Users</a></h1>Manage user accounts</li>')
        request.write('<li><h1><a href="/auth/Reports/">Reports</a></h1>View system reports</li>')
        request.write('<li><h1><a href="/auth/Tools/">Tools</a></h1>Configure system settings</li></ul></div>')
        request.write('<div id="pageNote"><h2>Error</h2></div><div id="pageSide"></div>')
        request.write('<div id="pageContent">')
        request.write("<h3>An error has occured</h3><p>An error has occurred. We apologise for this inconvenience.</p>")
        request.write("<p><strong>Please don't panic!</strong> The explanation in the box below may contain a simple reason for the problem. ")
        request.write("<br/>This error has been automaticaly emailed to Thusa for analysis.")
        request.write('<div style="height:25em; width:50em; overflow: scroll;">')
        from nevow import failure
        result = ''.join(flat.flatten(failure.formatFailure(reason)))

        #Utils.sendMail("%s <tums@thusa.net>" % Settings.LDAPOrganisation, ["colin@thusa.co.za"], "TUMS Error", result, html=True)
        request.write(result)
        request.write('</div></div>')
        request.write("</body></html>")

        request.finishRequest( False )

    def renderInlineException(self, context, reason):
        from nevow import failure
        formatted = failure.formatFailure(reason)
        desc = str(reason)
        return flat.serialize([
            stan.xml("""<div style="border: 1px dashed red; color: red; clear: both" onclick="this.childNodes[1].style.display = this.childNodes[1].style.display == 'none' ? 'block': 'none'">"""),
            desc,
            stan.xml('<div style="display: none">'),
            formatted,
            stan.xml('</div></div>')
        ], context)

class DefaultPage(formal.ResourceMixin, rend.Page):
    addSlash = True

    docFactory  = loaders.xmlfile('default.xml', templateDir=Settings.BaseDir+'/templates')

    menu = [
            ('/auth/Status/', '/images/statusMB.png',None, "Current system status"),
            ('/auth/Users/', '/images/usersMB.png',None, "Add or Modify system users"),
            ('/auth/Reports/', '/images/reports.png',None, "View system reports"),
            ('/auth/Tools/', '/images/tools.png',None, "System configuration and tools"),
           ]
    userMenu = [
         ('http://$ME$/roundcube/', '/images/webmailMB.png', None, "Web based email client"),
         ('/auth/Settings/', '/images/mysetMB.png',None, "Edit your personal account settings"),
         (url.root.child(guard.LOGOUT_AVATAR), "/images/logout.png",None, "Log out of TUMS"),
    ]
    pageMenu = []

    def __init__(self, avatarId = None, db = None, *a, **k):
        formal.ResourceMixin.__init__(self, *a, **k)
        rend.Page.__init__(self, *a, **k)
        self.avatarId = avatarId
        self.db = db
        self.sysconf = confparse.Config()
        try:
            self.text = db[2]
            self.handler = db[3]
        except:
            print "Failed to get i18l module"

    def render_footerBar(self, ctx, data):
        return ctx.tag[
            tags.a(href=url.root.child('About'))["TUMS ", VERSION]
        ]

    def render_topBar(self, ctx, data):
        l = [
            ('Status', 'Dashboard', 'View system status'),
            ('Users',  'Users',     'Manage user accounts'),
            ('Reports','Reports',   'View system reports'),
            ('Tools',  'Tools',     'Configure system settings')
        ]
        
        return ctx.tag[
            [ 
                tags.li[tags.h1[tags.a(href=url.root.child(base))[name]], description]
            for base, name, description in l]
        ]

    def render_userBar(self, ctx, data):
        return ctx.tag[
            "Logged in as: ", self.avatarId.username, 
            " | ",
            tags.a(href=url.root.child('Settings'), title="Personal account settings")["Account Settings"],
            " | ",
            tags.a(href=url.root.child(guard.LOGOUT_AVATAR), title="Logout of TUMS")["Logout"]
        ]   

    def render_version(self, ctx, data):
        return VERSION

    def render_content(self, ctx, data):
        return ctx.tag[
            tags.p[""]
        ]

    def addedMenu(self):
        if self.pageMenu:
            return [
                tags.img(src="/images/blockMB.png"),
                [
                    tags.a(href=elm[0], title=elm[3])[tags.img(src=elm[1])]
                for elm in self.pageMenu]
            ]
        else:
            return []
        
    def render_menu(self, ctx, data):
        host = str(url.URL.fromContext(ctx)).split('//')[-1].split(':')[0]
        if self.avatarId.isUser:
            self.menu= []

        if self.avatarId.reports:
            try:
                del self.menu[3]
            except:
                pass

        if self.menu:
            newBlock = tags.img(src="/images/blockMB.png")
        else:
            newBlock = ""
        return ctx.tag[
            tags.img(src="/images/blockMB.png"),
            [
                tags.a(href=elm[0].replace('$ME$',host), title=elm[3])[tags.img(src=elm[1])]
            for elm in self.menu],
            newBlock,
            [
                tags.a(href=elm[0].replace('$ME$',host), title=elm[3])[tags.img(src=elm[1])]
            for elm in self.userMenu],
            self.addedMenu(),
        ]

    def logout(self):
        print "Logged out"

