from enamel import pages, deferreds, tags, form, url

from pages import * 

import utils, os

class Page(pages.Standard):
    def form_diskConfig(self, data):
        f = form.Form()

        f.addField('setup', form.String(),
            form.widgetFactory(form.RadioChoice, 
                options=(
                    ('raid1', 'RAID 1'),
                    ('noraid', 'Single device')
                )
            ),
            label = "Setup"
        )
        
        # If more than one drive exists..
        f.data['setup'] = 'raid1'

        f.addAction(self.next)
        return f

    def next(self, c, f, data):
        if data['setup'] == 'raid1':
            self.enamel.setup['disktype'] = 'raid'
        if data['setup'] == 'noraid':
            self.enamel.setup['disktype'] = 'single'

        def ret(*_):
            return url.root.child('DiskSelect')

        # Stop any existing raid devices (interferes with stuff)

        return utils.system('mdadm --stop --scan').addBoth(ret)

        #devs = [i for i in os.listdir('/dev/') if 'md' in i and i!= "md"]
        #if not devs:
        #    return url.root.child('DiskSelect')
        #return utils.system(';'.join(["mdadm --manage --stop %s" % i for i in devs])).addBoth(ret)

    def document(self):
        return pages.template('disks.xml', templateDir = '/home/installer/templates')

