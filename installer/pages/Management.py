from enamel import pages, deferreds, tags, form, url

from pages import * 

import utils, sha, time


class Page(pages.Standard):
    def form_pageForm(self, data):
        f = form.Form()

        f.addField('rootpw', form.String(required=True), form.CheckedPassword,label = "Root Password", 
            description = "Enter a root password for the installation")

        f.addField('adminpw', form.String(required=True), form.CheckedPassword, label = "Administrator Password", 
            description = "Enter a password for the administrator account")

        f.addField('thusam', form.Boolean(), label = "Thusa Managed", 
            description = "Tick this option to grant THUSA (http://thusa.net) permission to provide remote management and support services to this Vulani server. " +
                          "If you have purchased a maintenance or remote support agreement from THUSA, you must tick this box.")

        f.addAction(self.next)

        return f


    def next(self, c, f, data):
        self.enamel.setup['rootpw'] = data['rootpw'].encode()
        self.enamel.setup['adminpw'] = data['adminpw'].encode()
        self.enamel.setup['thusam'] = data['thusam']

        return url.root.child('InternetDetails')

    def render_detail(self, ctx, data):
        return ctx.tag[
            tags.h3["Management"]
        ]

    def document(self):
        return pages.template('formpage.xml', templateDir = '/home/installer/templates')
            

