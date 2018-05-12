from enamel import pages, deferreds, tags, form, url

from pages import * 

import utils

class Page(pages.Standard):
    """ License page """

    def form_license(self, data):
        f = form.Form()

        f.addField('key', form.String(), label = "Key")

        f.addAction(self.addKey)
        return f

    def addKey(self, c, f, data):
        self.enamel.setup['key'] = data['key'] or ""
        
        def ok(_):
            print _
            return url.root.child('Disks')

        return utils.system('ntpdate -u pool.ntp.org').addBoth(ok)

    def document(self):
        return pages.template('license.xml', templateDir = '/home/installer/templates')
