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

def getNetwork(ip):
    """ Returns the network address and CIDR for a given CIDR IP"""
    wmask = '.'.join(ip.split('/')[0].split('.')[:3])
    sadr = ip.split('.')[-1].split('/')[0]
    mask = ip.split('/')[-1]
    naddr = int(sadr) & ~((1 << (32 - int(mask))) - 1)
    return '%s.%s/%s' % (wmask, naddr, mask)


class Page(pages.Standard):
    def form_pageForm(self, data):
        f = form.Form()
        
        lans = []
        for k, n in self.enamel.setup['nets'].items():
            if n == "LAN":
                lans.append(k)
        
        cnt = 0
        for l in lans:
            f.addField(l, form.String(), label = "%s IP" % l,
                description = "IP address (CIDR format v.w.x.y/z) or blank for DHCP")

            f.addField(l+'dhcp', form.Boolean(), label = "%s DHCP Server" % l, 
                description = "Enable DHCP server on ths interface")

            if cnt == 0:
                f.data[l+'dhcp'] = True
            cnt += 1
        
        f.addAction(self.next)
        
        return f
    
    def next(self, c, f, data):
        lans = []

        for k, n in self.enamel.setup['nets'].items():
            if n == "LAN":
                lans.append(k)
        
        for l in lans:
            ip = data[l] or ""
            
            if ip:
                if '/' not in ip:
                    ip = ip + '/24'
                self.enamel.config['EthernetDevices'][l] = {
                    'ip': ip.encode(), 
                    'type': 'static', 
                    'network': getNetwork(ip.encode()), 
                    'dhcpserver': data[l+'dhcp']
                }
            else:
                self.enamel.config['EthernetDevices'][l] = {
                    'type':'dhcp',
                    'network': '192.168.0.0/24'
                }

        # Ensure we set these interfaces into the LOC zone
        self.enamel.config['Shorewall']['zones']['loc'] = {
            'policy': 'ACCEPT',
            'interfaces': ['%s detect dhcp,routeback' % i for i in lans ],
            'log': ''
        }

        self.enamel.config['LANPrimary'] = lans
        
        return url.root.child('WanConfig')

    def render_detail(self, ctx, data):
        return ctx.tag[
            tags.h3["LAN Port Details"], 
            tags.p["All ports will be added to the 'loc' zone. You may change the zone assignment after installation"]
        ]

    def document(self):
        return pages.template('formpage.xml', templateDir = '/home/installer/templates')
            

