from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP
from Core import PageHelpers, AuthApacheProxy, confparse, Utils, WebUtils
from Pages import Tools
import formal

from twisted.python import log

class EditWebserver(Tools.Page):
    def __init__(self, avatarId = None, db = None, domain="", *a, **kw):
        self.domain = domain
        self.location = url.root.child('Webserver').child('Edit').child(domain)
        PageHelpers.DefaultPage.__init__(self,avatarId, db, *a, **kw)

    def form_location(self, data):
        form = formal.Form()
        
        form.addField('Domain', formal.String(required = True), label = "Domain")

        form.addField('DocumentRoot', formal.String(required=True), label = "Path",
            description = "Location of files to be served for this domain")

        form.addField('ServerAlias', formal.String(required=True), label = "Domain Alias",
            description = "Comma separated list of extra domains to be served")

        form.addField('Administrator', formal.String(required=True), label = "Administrator", 
            description = "Email address of any extra administrators to be added, comma separated if more than one")

        form.addField('ScriptAlias', formal.String(required=True), label = "cgi-bin Location")

        if self.domain == "DEFAULT":
            zn = self.sysconf.General['http']['defaults']
        else:
            zn = self.sysconf.General['http']['vhosts'][self.domain]

        form.data = {
            'Domain': self.domain,
            'DocumentRoot':     zn['DocumentRoot'],
            'ServerAlias':      ', '.join(zn.get('ServerAlias', [])),
            'Administrator':    ', '.join(zn.get('#ServerAdmin', [])),
            'ScriptAlias':      zn.get('ScriptAlias', ' ').split()[-1]
        }
        
        form.addAction(self.submitLocation)
        return form

    def submitLocation(self, ctx, form, data):
        
        return self.location
    
    """ Stub
    def form_location(self, data):
        form = formal.Form()
        
        form.addField('', formal.String(required=True), label = "Domain")
        
        form.addAction(self.submitLocation)
        return form

    def submitLocation(self, ctx, form, data):
        
        return self.location"""


    def render_content(self, ctx, data):
        
        options = []

        if self.domain == "DEFAULT":
            zn = self.sysconf.General['http']['defaults']
        else:
            zn = self.sysconf.General['http']['vhosts'][self.domain]
            
        for opt, val in zn.items():
            if isinstance(val, list):
                options.append((opt, [[i, tags.br] for i in val], ''))
            elif isinstance(val, dict):
                options.append((opt, '', ''))
            else:
                options.append((opt, val, ''))

        return ctx.tag[
            tags.h3[tags.img(src="/images/networking_section.png"), " Editing virtual host %s" % self.domain],
            PageHelpers.TabSwitcher((
                ('Location',        'pannelLoc'),
                ('Proxy',           'pannelProx'),
                ('Rewrite',         'pannelRewrite'),
                ('Authentication',  'pannelAuth'),
                ('Directories',     'pannelDir'),
                ('Logging',         'pannelLog')
            )),
            tags.div(id="pannelLoc", _class="tabPane")[
                tags.directive('form location')
            ],
            tags.div(id="pannelProx", _class="tabPane")[
                tags.h3["Add Reverse Proxy"],
                #tags.directive('form addProxy')
            ],
            tags.div(id="pannelRewrite", _class="tabPane")[
                tags.h3["Add Rewrite Rule"],
                #tags.directive('form addRewrite')
            ],
            tags.div(id="pannelAuth", _class="tabPane")[
                tags.h3["Add Authentication"],
                #tags.directive('form addAuth')
            ],
            tags.div(id="pannelDir", _class="tabPane")[
                tags.h3["Add Directory"],
                #tags.directive('form addDir')
            ],
            tags.div(id="pannelLog", _class="tabPane")[
                ""
            ],
            PageHelpers.LoadTabSwitcher()
        ]


class Page(Tools.Page):
    addSlash = True
    
    childPages = {
        'Edit': EditWebserver
    }
    
    def childFactory(self, ctx, seg):
        if seg in self.childPages.keys():
            return self.childPages[seg](self.avatarId, self.db)
        else:
            return PageHelpers.DefaultPage.childFactory(self, ctx, seg)
        
    def form_addVhost(self, data):
        form = formal.Form()
        
        form.addField('zone', formal.String(required=True), label = "Domain")
        
        form.data['master'] = True
        
        form.addAction(self.submitVhost)
        return form

    def submitVhost(self, ctx, form, data):
        D = self.sysconf.General
        
        self.sysconf.General = D

        def res(_):
            return url.root.child('Webserver')
        return WebUtils.restartService('bind').addCallbacks(res, res)

    def render_content(self, ctx, data):
        Utils.log.msg('%s opened Tools/Webserver' % (self.avatarId.username))
    
        H = self.sysconf.General.get('http', {})
        hosts = []

        #hosts.append(('[default]', H.get('defaults',{}).get('DocumentRoot', "/var/www/localhost/htdocs/")))

        for host, v in H.get('vhosts', {}).items():
            hosts.append((host, v.get('DocumentRoot', '<Misconfigured>'), tags.a(href="Edit/%s/"%host)["Edit"]))

        return ctx.tag[
            tags.h3[tags.img(src="/images/networking_section.png"), " Webserver"],
            PageHelpers.TabSwitcher((
                ('Webserver Vhosts', 'panelVhost'),
                ('Webserver Default', 'panelDefault'),
            )),
            tags.div(id="panelVhost", _class="tabPane")[
                tags.h3["Webserver Vhosts"],
                PageHelpers.dataTable(["Domain", "Content Directory", ''], hosts, sortable = True),
                tags.h3["Add Vhost"],
                tags.directive('form addVhost')
            ],
            tags.div(id="panelDefault", _class="tabPane")[
                tags.h3["Default vhost"],
            ],
            PageHelpers.LoadTabSwitcher()
        ]
        
