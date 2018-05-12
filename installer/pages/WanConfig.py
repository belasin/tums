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
    if not '/' in ip:
        ip+= '/29'
    wmask = '.'.join(ip.split('/')[0].split('.')[:3])
    sadr = ip.split('.')[-1].split('/')[0]
    mask = ip.split('/')[-1]
    naddr = int(sadr) & ~((1 << (32 - int(mask))) - 1)
    return '%s.%s/%s' % (wmask, naddr, mask)

class Page(pages.Standard):

    def getWan(self):
        wans = []
        for k, n in self.enamel.setup['nets'].items():
            if n == "WAN":
                wans.append(k)

        return wans
    def getLan(self):
        lans = []

        for k, n in self.enamel.setup['nets'].items():
            if n == "LAN":
                lans.append(k)

        return lans

    def form_pageForm(self, data):
        f = form.Form()

        wans = self.getWan()
        
        for l in wans:
            f.addField(l, form.String(), label = "%s IP" % (l.replace('eth', 'Port ')),
                description = "IP address (CIDR format v.w.x.y/z) or blank for DHCP")

            f.addField('gw%s' % l, form.String(), label = "%s Gateway" % (l.replace('eth', 'Port ')),
                description = "IP address or blank for no default route")
        
        f.addAction(self.next)
        
        return f
    
    def next(self, c, f, data):
        ifaces = getNetInterfaces()
        wans = self.getWan()
        cnt = 0 
        default = ""
        for l in wans:
            cnt += 1
            gw = data['gw%s' % l] or ""
            ip = data[l] or u""
            if ip:
                network = getNetwork(ip)
            else:
                network = ""


            defn = {
                'type': ip and 'static' or 'dhcp', 
                'ip': ip.encode(), 
                'network': str(network)
            }

            if (not default) and gw:
                default = l # interface name
                defn['routes'] = [('default', gw)]

            self.enamel.config['Shorewall']['masq'][l] = self.getLan()

            if len(wans) > 1:
                if cnt == 1:
                    zone = 'net'
                else:
                    zone = "net%s" % cnt
                self.enamel.config['Shorewall']['zones'][zone] = {
                    'policy': 'DROP', 
                    'interfaces': [
                        '%s detect' % l 
                    ], 
                    'log': '$LOG'
                }
                
                # Add a provider instance for this 
                self.enamel.config['ShorewallBalance'].append([
                    zone, gw.encode() or '-', 'track,balance'
                ])
            else:
                self.enamel.config['Shorewall']['zones']['net'] = {
                    'policy': 'DROP', 
                    'interfaces': [
                        '%s detect' % l 
                    ], 
                    'log': '$LOG'
                }
            
            self.enamel.config['EthernetDevices'][l] = defn
        
        if default:
            self.enamel.config['WANPrimary'] = default
        else:
            self.enamel.config['WANPrimary'] = wans[0]
        
        return url.root.child('PppConfig')

    def render_detail(self, ctx, data):
        wans = self.getWan()
        if len(wans) > 1:
            detail = "Since there are multiple WAN interfaces they will automatically be configured to load balance. This can be adjusted later."
        else:
            detail = ""

        return ctx.tag[
            tags.h3["Network Details"], 
            tags.p[detail]
        ]

    def document(self):
        if len(self.getWan()) == 0:
            # Ask if a PPPoE connection should be created, otherwise map the LAN as our route and ask for a default gateway
            #return url.root.child('/??')
            self.enamel.config['WANPrimary'] = 'ppp0'
            return pages.stan(
                tags.html[
                    tags.head[
                        tags.title["Vulani"],
                        tags.xml('<meta http-equiv="refresh" content="0;url=/PppConfig/"/>')
                    ],
                    tags.body[
                        ""
                    ]
                ]
            )
        return pages.template('formpage.xml', templateDir = '/home/installer/templates')
            

