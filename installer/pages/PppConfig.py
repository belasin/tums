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

    def getWan(self):
        wans = []
        for k, n in self.enamel.setup['nets'].items():
            if n == "PPPoE":
                wans.append(k)

        return wans

    def getWanNP(self):
        wans = []
        for k, n in self.enamel.setup['nets'].items():
            if n == "WAN":
                wans.append(k)

        return wans
 
    def form_pageForm(self, data):
        f = form.Form()

        wans = self.getWan()
        
        for l in wans:
            f.addField(l, form.String(), label = "%s Username" % (l.replace('eth', 'Port ')),
                description = "Username for PPPoE conection")

            f.addField('pass%s' % l, form.String(), label = "%s Password" % (l.replace('eth', 'Port ')),
                description = "Password for PPPoE connection")
        
        f.addAction(self.next)
        
        return f
    
    def next(self, c, f, data):
        ifaces = getNetInterfaces()
        wans = self.getWan()
        nothere = self.getWanNP()
        cnt = len(nothere)
        default = ""
        ifcnt = 0 
        for l in wans:
            cnt += 1
            iface = 'ppp%s' % ifcnt 

            defn = {
                'link': l , 
                'password': data['pass%s' % l] or "", 
                'username': data[l] or "",
                'plugins': 'pppoe', 
                'pppd': [], 
            }

            if (len(nothere) > 1) or (len(wans) > 1):
                if cnt == 1:
                    zone = 'net'
                else:
                    zone = "net%s" % cnt
                self.enamel.config['Shorewall']['zones'][zone] = {
                    'policy': 'DROP',
                    'interfaces': [
                        '%s detect' % iface
                    ],
                    'log': '$LOG'
                }

                # Add a provider instance for this 
                self.enamel.config['ShorewallBalance'].append([
                    zone, gw.encode() or '-', 'track,balance' 
                ])
            else:
                # We really have just this interface
                defn['pppd'] = ['defaultroute']
                self.enamel.config['Shorewall']['zones']['net'] = {
                    'policy': 'DROP',
                    'interfaces': [
                        '%s detect' % iface
                    ],
                    'log': '$LOG'
                }
 
            self.enamel.config['WANDevices'][iface] = defn

            ifcnt += 1
        
        if len(nothere) > 0:
            # Just assume wildly here.. We have no default route at this point really
            self.enamel.config['WANPrimary'] = 'ppp0'
        
        return url.root.child('ServiceConfig')

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
        # Ensure we have some interfaces to work with 
        if len(self.getWan()) == 0:
            # Check now whether or not we will us LAN as the default WAN (ie LAN==WAN)
            if not self.enamel.config['WANPrimary']:
                self.enamel.config['WANPrimary'] = self.enamel.config['LANPrimary'][0]
            
            return pages.stan(
                tags.html[
                    tags.head[
                        tags.title["Vulani"],
                        tags.xml('<meta http-equiv="refresh" content="0;url=/ServiceConfig"/>')
                    ],
                    tags.body[
                        ""
                    ]
                ]
            )
        return pages.template('formpage.xml', templateDir = '/home/installer/templates')
            

