from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
import time, formal, LDAP, os
import Tree, Settings
from Core import PageHelpers, Utils, WebUtils, confparse
from Pages import Tools

class Page(Tools.Page):
    def form_addQos(self, data):
        tos = [
            ('16', 'Minimize Delay'),
            ('8',  'Maximize Throughput'),
            ('4',  'Maximize Reliability'),
            ('2',  'Minimize Cost'),
            ('0',  'Normal Service')
        ]
        form = formal.Form()
        protocols = [('tcp', 'TCP'),
                     ('udp', 'UDP'),
                     ('47', 'PPTP')]
        form.addField('port', formal.String(required=True), label = "Port")
        form.addField('proto', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = protocols), label = "Protocol")
        form.addField('qos', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = tos), label = "Type of service")
        form.addAction(self.submitForm)

        return form

    def submitForm(self, ctx, form, data):
        conf = self.sysconf.Shorewall

        if conf.get('qos', None):
            conf['qos'].append((data['port'].encode(), data['proto'].encode(), data['qos'].encode()))
        else:
            conf['qos'] = [(data['port'].encode(), data['proto'].encode(), data['qos'].encode())]

        self.sysconf.Shorewall = conf
        WebUtils.system('/usr/local/tcs/tums/configurator --shorewall')
        return url.root.child('Qos')

    def locateChild(self, ctx, segs):
        if segs[0]=="Delete":
            index = int(segs[1])
            conf = self.sysconf.Shorewall
            try:
                del conf['qos'][index]
            except:
                print "Unable to delete ", index
            self.sysconf.Shorewall = conf
            WebUtils.system('/usr/local/tcs/tums/configurator --shorewall')
            return url.root.child('Qos'), ()
            
        return rend.Page.locateChild(self, ctx, segs)

    def render_content(self, ctx, data):
        toss = {
            '16':'Minimize Delay',
            '8':'Maximize Throughput',
            '4':'Maximize Reliability',
            '2':'Minimize Cost',
            '0':'Normal Service'
        }
        qosRules = []
        l = 0
        for port, proto, tos in self.sysconf.Shorewall.get('qos', []):
            qosRules.append([
                port, 
                proto, 
                toss[tos], 
                tags.a(href=url.root.child("Qos").child("Delete").child(l), onclick="return confirm('Are you sure you want to delete this entry?');")[tags.img(src="/images/ex.png")]
            ])
            l += 1
        
        return ctx.tag[
            tags.h3[tags.img(src="/images/compress.png"), "QOS"],
            PageHelpers.dataTable(['Port', 'Protocol', 'Type of service', ''], qosRules),
            tags.h3["Add Rule"],
            tags.directive('form addQos'),
        ]
