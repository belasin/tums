from enamel import pages, deferreds, tags, form, url

from pages import * 

import utils, sha, time


class Page(pages.Standard):
    def form_pageForm(self, data):
        f = form.Form()

        f.addField('NTP', form.String(required=True), label = "Time server", description = "Network time server")
        f.addField('SMTPRelay', form.String(), label = "SMTP Relay", description = "SMTP relay server. Sometimes called a smart-host. This is the mailserver your ISP gave you. Leave blank for direct delivery.")
        f.addField('ForwardingNameservers', form.String(), label = "DNS Servers", description = "Comma separated list of DNS servers to forward queries to.")

        f.data = {
            'NTP': 'pool.ntp.org', 
            'SMTPRelay': '',
            'ForwardingNameservers': ''
        }

        f.addAction(self.next)

        return f


    def next(self, c, f, data):
        self.enamel.config['NTP'] = data['NTP'].encode()
        self.enamel.config['SMTPRelay'] = data['SMTPRelay'] or ""
        ns = data['ForwardingNameservers']

        if ns:
            self.enamel.config['ForwardingNameservers'] = ns.replace(' ', '').split(',')
        else:
            self.enamel.config['ForwardingNameservers'] = []
            

        return url.root.child('NetConfig')

    def render_detail(self, ctx, data):
        return ctx.tag[
            tags.h3["Network Details"]
        ]

    def document(self):
        return pages.template('formpage.xml', templateDir = '/home/installer/templates')
            

