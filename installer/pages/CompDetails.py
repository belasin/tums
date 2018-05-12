from enamel import pages, deferreds, tags, form, url

from pages import * 

import utils, sha, time


class Page(pages.Standard):
    def form_pageForm(self, data):
        f = form.Form()

        f.addField('CompanyName', form.String(required=True), label = "Company Name")

        f.addField('ExternalName', form.String(required=True), label = "External Name", description = "Fully qualified hostname by which this server will be reachable")

        f.addField('Hostname', form.String(required=True), label = "Hostname", description = "The short hostname for this server")

        f.addField('Domain', form.String(required=True), label = "Domain", description = "The DNS domain for this server")

        f.addField('SambaDomain', form.String(), label = "Windows Domain", description = "The Windows domain this server will provide")


        fi = open('/home/installer/tzs')

        zones = []

        for i in fi:
            ln = i.strip('\n').strip('/')

            if ln:
                zones.append(ln)

        zones.sort()

        timezones = [(i,i) for i in zones]

        f.addField('timezone', form.String(required=True), form.widgetFactory(form.SelectChoice, options=timezones), label = "Timezone")

        f.data = {
            'CompanyName':'My Company',
            'ExternalName':'vulani-gw.yourdomain.co.za',
            'Hostname':'vulani',
            'Domain':'yourdomain.co.za',
            'SambaDomain': ''
        }

        f.addAction(self.next)

        return f


    def next(self, c, f, data):
        l = ['CompanyName', 'ExternalName', 'Hostname', 'Domain', 'SambaDomain']

        if not data['SambaDomain']:
            data['SambaDomain'] = data['Domain'].split('.')[0].upper()
        else:
            data['SambaDomain'] = data['SambaDomain'].upper()

        for n in l:
            self.enamel.config[n] = data[n].encode()

        self.enamel.config['LocalDomains'] = [data['Domain'].encode()]

        self.enamel.config['LDAPBase']   = self.enamel.config['SambaDomain']
        self.enamel.config['LDAPPassword'] = sha.sha(self.enamel.config['SambaDomain'].lower() + str(time.time())).hexdigest()

        l = open('/mnt/target/etc/hostname', 'wt')
        l.write(data['Hostname'] + '\n')
        l.close()

        l = open('/mnt/target/etc/timezone', 'wt')
        l.write(data['timezone'] + '\n')
        l.close()

        try:
            i = open('/mnt/target/usr/share/zoneinfo/%s' % data['timezone'])
            o = open('/mnt/target/etc/localtime', 'w')
            o.write(i.read())
            o.close()
            i.close()
        except Exception, e:
            print "Error writing /etc/localtime: ", e

        print self.enamel.config
        return url.root.child('Management')

    def render_detail(self, ctx, data):
        return ctx.tag[
            tags.h3["Company Details"]
        ]

    def document(self):
        return pages.template('formpage.xml', templateDir = '/home/installer/templates')
            

