from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP, sys
from Core import PageHelpers, AuthApacheProxy, confparse, Utils, WebUtils
from Pages import Tools
import formal

from Core.Configurator import Xen

from twisted.python import log


class EditXen(Tools.Page):
    """ Form for editing a Xen domain """
    def __init__(self, avatarId = None, db = None, name="", *a, **kw):
        self.name = name
        Tools.Page.__init__(self,avatarId, db, *a, **kw)

    def form_editDomain(self, data):
        form = formal.Form()

        form.addField('name', formal.String(required=True), label = "Server name",
            description = "Server Name")

        form.addField('memory', formal.Integer(), label = "Memory", description = "Amount of reserved memory in MB (swap is always equal to this)")

        form.addField('ip', formal.String(strip=True, validators=[PageHelpers.IPValidator()]), label = "IP", description = "IP address (leave blank to use DHCP).")

        form.data = self.sysconf.General.get('xen', {}).get('images', {}).get(self.name, {})
        form.data['name'] = self.name

        form.addAction(self.submitDomain)
        return form

    def submitDomain(self, ctx, form, data):
        # Grab current data
        gen = self.sysconf.General
        xen = gen.get('xen', {}).get('images', {})
        current = xen.get(self.name, {})
        name = data['name'].encode()

        # Set changes
        current['memory'] = data['memory']

        current['ip'] = data['ip']
        
        # Name change
        if name != self.name:
            xen[name] = current
            del xen[self.name]
        else:
            xen[self.name] = current

        # Save data
        gen['xen']['images'] = xen
        self.sysconf.General = gen
        
        # Save configs
        if name != self.name:
            Xen.reconfigure_xen(self.sysconf, self.name, rename=name)
        else:
            Xen.reconfigure_xen(self.sysconf, self.name)
            
        return url.root.child('Xen')

    def locateChild(self, ctx, segs):
        if len(segs) > 1:
            return EditXen(self.avatarId, self.db, segs[0]), ()
        else:
            return url.root.child('Xen'), ()

    def render_content(self, ctx, data):
        
        return ctx.tag[
            tags.h3[tags.img(src="/images/networking_section.png"), " Editing instance %s" % self.name],
            tags.directive('form editDomain')
        ]

class BuildXen(PageHelpers.DefaultAthena):
    def __init__(self, avatarId = None, db = None, name="", *a, **kw):
        self.name = name
        Tools.Page.__init__(self,avatarId, db, *a, **kw)

    def form_editZone(self, data):
        form = formal.Form()

        form.addAction(self.submitZone)
        return form

    def submitZone(self, ctx, form, data):

        return url.root.child('Xen')

    def locateChild(self, ctx, segs):
        if len(segs) > 1:
            return EditXen(self.avatarId, self.db, segs[0]), ()
        else:
            return url.root.child('Xen'), ()

    def render_content(self, ctx, data):
        
        return ctx.tag[
            tags.h3[tags.img(src="/images/networking_section.png"), " Building xen %s" % self.name],
        ]

class Page(Tools.Page):
    addSlash = True
    
    childPages = {
        'Edit': EditXen,
        'Build': BuildXen
    }
    
    def childFactory(self, ctx, seg):
        if seg in self.childPages.keys():
            return self.childPages[seg](self.avatarId, self.db)
        else:
            return Tools.Page.childFactory(self, ctx, seg)
        
    def form_xenConf(self, data):
        form = formal.Form()
        
        form.addField('enable', formal.Boolean(), label = "Xen enabled", description = "Enable Xen support")
        
        form.data['enable'] = self.sysconf.General.get('xen', {}).get('enabled')

        form.addAction(self.submitXenConf)
        return form

    def submitXenConf(self, ctx, f, data):
        
        G = self.sysconf.General

        if not G.get('xen'):
            G['xen'] = {
                'config': {},
                'images': {}
            }
        G['xen']['enabled'] = data['enable']
        
        WebUtils.system('/usr/local/tcs/tums/configurator --xen').addBoth(lambda _: url.root.child('Xen'))

    def form_newXen(self, data):
        form = formal.Form()
        if os.path.exists("/usr/lib/xen-tools"):

            tools = os.listdir("/usr/lib/xen-tools/")
            dists = ['hvm']
            for n in tools:
                if n[-2:] == '.d':
                    dists.append(n.split('.')[0])

            distSelect = [(i, i.capitalize()) for i in dists]
        else:
            distSelect = [("ERROR", "Xen not active!")]
        
        form.addField('name', formal.String(required=True), label = "Server name",
            description = "Server Name")

        #form.addField('lva', formal.String(), label = "Volume Group", description = "The LVM VG to use (blank to use an image)")

        form.addField('distribution', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = distSelect),
            label = "Distribution", description = "Xen image type")

        form.addField('memory', formal.Integer(required=True), label = "Memory", description = "Amount of reserved memory in MB (swap is always equal to this)")

        form.addField('disk', formal.Integer(required=True), label = "Disk", description = "Amount of disk space in GB")

        form.addField('ip', formal.String(strip=True, validators=[PageHelpers.IPValidator()]), label = "IP", description = "IP address (leave blank to use DHCP).")

        form.addField('password', formal.String(), label = "Password", description = "A root password for the machine (leave blank on HVM).")

        form.data['distribution'] = 'etch'
        
        form.addAction(self.submitNewXen)
        return form

    def submitNewXen(self, ctx, form, data):
        
        xenConfig = {
            'lva' : False, #data['lva'].encode(),
            'dist' : data['distribution'].encode(),
            'memory' : data['memory'],
            'disk' : data['disk'],
            'ip' : data['ip']
        }
        gen = self.sysconf.General
        if not gen.get('xen'):
            gen['xen'] = {'images':{}}
        gen['xen']['images'][data['name'].encode()] = xenConfig
        self.sysconf.General = gen

        if data['distribution'] != 'hvm':
            Xen.xen_create_linux(self.sysconf, data)
        else:
            Xen.xen_create_hvm(self.sysconf, data)
        
        return url.root.child('Xen')

    def render_content(self, ctx, data):
        Utils.log.msg('%s opened Tools/Xen' % (self.avatarId.username))
        gen = self.sysconf.General
        xen = gen.get('xen', {}).get('images', {})
        xenconf = gen.get('xen', {}).get('config', {})
        xenServers = []

        # Try get our domain info XXX - put into try -catch later
        sys.path.append('/usr/lib/xen-default/lib/python')

        doms = {}
        try:
            from xen.xend.XendClient import server
        
            ddata = server.xend.domains(1)
            for n in ddata:
                if n[0] == "domain":
                    thisdom = dict(n[1:])
                    print thisdom['name'], thisdom
                    doms[thisdom['name']] = thisdom

        except Exception, e:
            print e
            pass

        def renderer(ps):
            for k, v in xen.items():
                if v['lva']:
                    disk = "%sGB in %s/%s-disk" % (v['disk'], v['lva'], k)
                else:
                    disk = "%sGB in %s" % (v['disk'], os.path.join(xenconf.get('home', '/home/xen/'), 'domains', k, 'disk.img'))

                if k in doms:
                    status = "Running"
                else:
                    if k in ps:
                        status = "Building..."
                    else:
                        status = "Stopped"
                xenServers.append((
                    k,
                    status,
                    v['memory'],
                    disk,
                    v['dist'],
                    v['ip'] or 'DHCP',
                    tags.a(href="Edit/%s/" % k)["Edit"]
                ))

            return ctx.tag[
                tags.h3[tags.img(src="/images/networking_section.png"), " Xen"],
                PageHelpers.TabSwitcher((
                    ('Xen Servers', 'panelXenServ'),
                    ('Xen Configuration', 'panelXenConf'),
                )),
                tags.div(id="panelXenServ", _class="tabPane")[
                    tags.h3["Xen Servers"], 
                    PageHelpers.dataTable(['Name', 'Status', 'Memory', 'Disk', 'Distribution', 'IP', ''],
                        xenServers,
                        sortable = True
                    ),
                    tags.h3["Create new image"],
                    tags.directive('form newXen'),
                    tags.p["Note that images will take a long time to create. The status will read 'Building...' until it is completed"]
                ], 
                tags.div(id="panelXenConf", _class="tabPane")[
                    tags.h3["Xen Configuration"],
                    tags.directive('form xenConf')
                ],
                PageHelpers.LoadTabSwitcher()
            ]

        return WebUtils.system('ps axg -www').addBoth(renderer)
