from enamel import pages, deferreds, tags, form, url

from pages import * 

import utils, sha, time

class Page(pages.Standard):
    def form_pageForm(self, data):
        f = form.Form()
        
        f.addField('pdc', form.Boolean(), label = "PDC", description = "Should this server act as a primary domain controller")

        f.addField('proxy', form.Boolean(), label = "Proxy Authentication", description = "Should this server require authentication for the proxy?")

        f.addField('cf', form.Boolean(), label = "Content Filter", description = "Should content filtering be enabled?")

        f.addField('dhcp', form.Boolean(), label = "DHCP", description = "Should the DHCP service be enabled?")

        f.data = {
            'pdc': True, 
            'proxy': False, 
            'cf': True, 
            'dhcp': True
        }
        
        f.addAction(self.next)
        
        return f
    
    def next(self, c, f, data):
        if data['pdc']:
            self.enamel.config['SambaConfig']['domain logons'] = 'yes'
            self.enamel.config['SambaConfig']['domain master'] = 'yes'
            
        if data['proxy']:
            self.enamel.config['Shorewall']['rules'].append([1, 'REJECT loc   net   tcp   80'])

        else:
            for n,v in self.enamel.setup['nets'].items():
                if v == "LAN":
                    mask = self.enamel.config['EthernetDevices'][n].get('network', '0.0.0.0/0')
                    self.enamel.config['ProxyAllowedHosts'].append(mask)
        
        if data['cf']:
            self.enamel.config['ProxyConfig']['contentfilter'] = True

            # Create a reasonable filter set for the content filter
            self.enamel.config['ProxyConfig']['blockedcontent'] = [
                'p2p', 'games', 'dating', 'hacking', 'porn', 'gambling'
            ]

        if not data['dhcp']:
            self.enamel.config['General']['services'] = {
                'dhcp3-server': False
            }
        
        return url.root.child('PrepSystem')

    def render_detail(self, ctx, data):
        return ctx.tag[
            tags.h3["Default Services"]
        ]

    def document(self):
        return pages.template('formpage.xml', templateDir = '/home/installer/templates')
            

