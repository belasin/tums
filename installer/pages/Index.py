from enamel import pages, deferreds, tags, form, url

from pages import License, Disks, DiskSelect, DiskMounts, Install, CompDetails, InternetDetails, NetConfig
from pages import LanConfig, WanConfig, PppConfig, ServiceConfig, PrepSystem, Management, FormatDisks

class Page(pages.Standard):
    """ Index page """

    childPages = {
        'License': License.Page,
        'Disks': Disks.Page,
        'DiskSelect': DiskSelect.Page,
        'DiskMounts': DiskMounts.Page,
        'FormatDisks': FormatDisks.Page,
        'Install': Install.Page,
        'CompDetails': CompDetails.Page,
        'Management': Management.Page, 
        'InternetDetails': InternetDetails.Page, 
        'NetConfig': NetConfig.Page, 
        'LanConfig': LanConfig.Page,
        'WanConfig': WanConfig.Page, 
        'PppConfig': PppConfig.Page, 
        'ServiceConfig': ServiceConfig.Page, 
        'PrepSystem': PrepSystem.Page,
    }

    child_css = pages.static.File('/home/installer/templates/css/')
    child_static = pages.static.File('/home/installer/static/')

    def document(self):
        return pages.template('index.xml', templateDir = '/home/installer/templates')
