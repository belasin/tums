from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
import time, formal, LDAP, os
import Tree, Settings
from Core import PageHelpers, confparse, Utils, WebUtils
from Pages import Tools

from twisted.python import log

class BackupSets(PageHelpers.DataTable):
    def getTable(self):
        headings = [
            ('Description', 'desc'),
            ('Source', 'fileset'),
            ('Excluded', 'exclude'),
            ('Notifications', 'mailto'),
            ('Type', 'type'),
            ('Destination', 'dest'),
            ('Options', 'opts')
        ]
        backupconf = self.sysconf.Backup

        backups = []

        for backup in backupconf.keys():
            row = [backupconf[backup].get('desc')]
            for i in ['fileset', 'exclude', 'mailto', 'type', 'dest']:
                bdata = backupconf[backup].get(i, "")

                row.append(bdata)

            backups.append(row)

        return headings, backups

    def addForm(self, form):
        form.addField('desc', formal.String(required=False), label = "Description")
        form.addField('fileset', formal.String(required=True), label = "Source Path(s)", description = "Paths to backup, separated by a semicolon.")
        form.addField('exclude', formal.String(required=False), label = "Exclude", 
                description = "List of patterns to exclude from backup (eg: *.mp3, *.avi), seperated by semicolon")
        form.addField('mailto', formal.String(required=False), label = "Notifications", 
                description = "Email address(es) to be notified once backup has been completed, separated by semicolon")

#        form.addField('type', formal.String(required=True),
#                formal.widgetFactory(formal.SelectChoice, options = ['USB','Windows Share']), label = "Backup Type")

        try:
            storageNodes = os.listdir('/proc/scsi/usb-storage/')
        except:
            storageNodes = []
        AvailLetters = []
        usbStorage = {}
        for s in storageNodes:
            l = open('/proc/scsi/usb-storage/%s' % s)
            for i in l:
                ln = i.strip()
                if "Vendor" in ln:
                    vendor = ln.split(':')[-1].strip()
                if "Serial Number" in ln:
                    sn = ln.split(':')[-1].strip().split()[0]

            usbStorage[sn] = vendor
        #    AvailLetters.append((sn, vendor))
            
        AvailLetters = [('sn1', 'disk1'), ('disk2', 'sdb1')] #testing usbDev field

        form.addField('usbDev', formal.String(required=False),
                formal.widgetFactory(formal.SelectChoice, options = AvailLetters), label = "USB Device")

#    def addAction(self, data):
#        if "/" in data['path']:
#            if data['path'][0] == "/": # Starts with a /
#                path = data['path']
#            else:
#                path = "/var/lib/samba/data/%s" % data['path']
#        else:
#            path = '/var/lib/samba/data/%s' % data['path']
#            
#        backup = {} #[%s]\n" % (data['share'],)
#        backup["desc"] = data['desc']
#        share["path"] = path
#        share["comment"] = data['comment']
#        share["create mode"] = '664'
#        share["directory mode"] = '775'
#        share["nt acl support"] = 'yes'
#        WebUtils.system('mkdir -p %s' % path)
#        
#        if data['public']:
#            share["public"] = "yes"
#
#        if data['writable']:
#            share["writable"] = "yes"
#
#        if data['group']:
#            share["valid users"] = '@"%s",root' % data['group']
#            WebUtils.system('chown -R root:"%s" %s' % (data['group'], path))
#
#        WebUtils.system('chmod a+rwx %s' % path)
#        WebUtils.system('chmod -R a+rw %s' % path)
#
#        shares = self.sysconf.SambaShares
#        shares[data['share'].encode()] = share
#        self.sysconf.SambaShares = shares
# 
    def deleteItem(self, item):
        backups = self.getTable()[1]

        target = backups[item]

        name = target[0]

        backups = self.sysconf.Backup
        del backups[name]
        self.sysconf.Backup = backups

#    def returnAction(self, data):
#        log.msg('%s added backup %s' % (self.avatarId.username, repr(data)))
#        return reloadSamba().addBoth(lambda _: url.root.child('Samba')), ()

class Page(Tools.Page):
    def __init__(self, *a, **kw):
        Tools.Page.__init__(self, *a, **kw)
        self.backupTable = BackupSets(self, 'BackupSets', 'backup')

    def render_content(self, ctx, data):
   
        return ctx.tag[
            tags.h2[tags.img(src="/images/netdrive.png"), "Backups"],
            self.backupTable.applyTable(self)
        ]
