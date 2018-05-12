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

class Page(Tools.Page):
    addSlash = True

    def reloadAndReturn(self):
        return WebUtils.system('/usr/local/tcs/tums/configurator --nut; /etc/init.d/nut restart').addBoth(
            lambda _: url.root.child('UPS')
        )

    def getSers(self):
        devs = []
        
        for dev in os.listdir('/dev/'):
            if "ttyS" == dev[:4]:
                devs.append((dev, dev.replace('ttyS', 'Serial ')))
            if "ttyUSB" == dev[:6]: 
                devs.append((dev, dev.replace('ttyUSB', 'USB ')))

        return devs

    def form_addUps(self, data):

        ports = self.getSers()

        drivers = [
            ('apcsmart', 'APC'), 
            ('belkin', 'Belkin'), 
            ('belkinunv', 'Belkin Universal UPS'), 
            ('mge-shut', 'MGE Ellipse/Esprit'),
            ('newmge-shut', 'MGE Ellipse/Esprit V2'), 
            ('mge-utalk', 'MGE Pulsar E/Comet'), 
            ('powercom', 'Powercom')
        ]
        
        form = formal.Form()
        form.addField('name', formal.String(required=True), label = "Name")
        form.addField('desc', formal.String(required=True), label = "Description")
        form.addField('driver', formal.String(required=True), 
            formal.widgetFactory(formal.SelectChoice, options = drivers), label = "Driver")
        form.addField('port', formal.String(required=True), 
            formal.widgetFactory(formal.SelectChoice, options = ports), label = "Port")
        form.addAction(self.submitForm)
        return form

    def submitForm(self, ctx, form, data):
        dao = {}
        
        for i in ['driver', 'port', 'desc']:
            dao[i] = data[i].encode('ascii', 'replace')
        
        G = self.sysconf.General
        
        if not G.get('ups'):    
            G['ups'] = {}
        
        G['ups'][data['name'].encode('ascii', 'replace')] = dao
        
        self.sysconf.General = G
        

        return self.reloadAndReturn()

    def render_status(self, ctx, data):
        def gotCb(dta):
            inv, inf, mdl = '','',''
            try:
                for ln in dta.split('\n'):  
                    if not ': ' in ln:
                        continue
                    k,v = ln.split(': ')
                    if k == 'input.frequency':
                        inf = v 
                    if k == 'input.voltage':
                        inv = v
                    if k == 'ups.model':
                        mdl = v
            except:
                return ctx.tag[dta.split(':')[-1]]

            return ctx.tag[
                "%s %sV@%sHz" % (mdl, inv, inf)
            ]

        return WebUtils.system('upsc %s@localhost' % (data)).addBoth(gotCb)

    def render_content(self, ctx, data):
        
        upslist = []
        
        for k,v in self.sysconf.General.get('ups', {}).items():
            upslist.append([
                k, 
                v.get('desc', ''), 
                v['port'].replace('/dev/ttyS', 'Serial '), 
                v['driver'], 
                tags.invisible(render=tags.directive('status'), data=k),
                tags.a(href='Delete/%s/' % k)['X']
            ])
        
        return ctx.tag[
            tags.h3[tags.img(src="/images/cluster.png"), " UPS"],
            PageHelpers.dataTable(['Name','Description','Port', 'Driver', 'Status', ''], upslist),
            tags.br, 
            tags.h3["Add UPS"],
            tags.directive('form addUps')
        ]

    def locateChild(self, ctx, segs):
        if segs[0] == "Delete":
            G = self.sysconf.General
            del G['ups'][segs[1]]
            self.sysconf.General = G
            return self.reloadAndReturn(), ()
        return rend.Page.locateChild(self, ctx, segs)

