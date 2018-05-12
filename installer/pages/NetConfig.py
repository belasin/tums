from enamel import pages, deferreds, tags, form, url

from pages import * 

import utils, sha, time

def getNetInterfaces():
    l = open('/proc/net/dev')
    ifs = []
    for n in l:
        if not ":" in n:
            continue
        try:
            iface = n.split(':')[0].strip()
            if iface in ['sit0', 'lo']:
                continue
            ifs.append(iface)
        except:
            continue
    
    return ifs

class Page(pages.Standard):
    def form_pageForm(self, data):
        f = form.Form()
        
        ifaces = getNetInterfaces()
        for n in ifaces:
            print n
            f.addField(n, form.String(required=True),
                form.widgetFactory(form.SelectChoice,
                    options=(
                        ('Unused', 'Unused'),
                        ('LAN', 'LAN'),
                        ('WAN', 'WAN'),
                        ('PPPoE', 'PPPoE'),
                    )
                ),
            label = n.replace('eth', 'Port '))

            f.data[n] = 'Unused'
        
        f.data['eth0'] = 'LAN'
        f.data['eth1'] = 'WAN'
        
        f.addAction(self.next)
        
        return f
    
    def next(self, c, f, data):
        ifaces = getNetInterfaces()

        for n in ifaces:
            self.enamel.setup['nets'][n] = data[n].encode()

        return url.root.child('LanConfig')

    def render_detail(self, ctx, data):
        return ctx.tag[
            tags.h3["Network Details"]
        ]

    def document(self):
        return pages.template('formpage.xml', templateDir = '/home/installer/templates')
            

