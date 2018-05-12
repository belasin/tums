from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
import datetime, time, formal, LDAP, os
import Tree, Settings
from Core import PageHelpers, confparse, Utils, WebUtils
from Pages import Tools

from twisted.python import log


def findDisks():
    try:
        storageNodes = os.listdir('/proc/scsi/usb-storage/')
    except:
        storageNodes = []

    disks = []
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
        disks.append((sn, '%s (%s)' % (vendor, sn)))

    return disks
        
def createForm(self, form):
    AvailLetters = findDisks()

    form.addField('desc', formal.String(required=False), label = "Description")
    form.addField('fileset', formal.String(required=True), label = "Source Path(s)", description = "Paths to backup, separated by a comma.")
    form.addField('exclude', formal.String(required=False), label = "Exclude", 
            description = "List of patterns to exclude from backup (eg: *.mp3, *.avi), seperated by comma")
    form.addField('mailto', formal.String(required=False), label = "Notifications", 
            description = "Email address(es) to be notified once backup has been completed, separated by comma")
    form.addField('dest', formal.String(required=True), label = "Destination", 
            description = "Destination directory.")

    form.addField('config', formal.Boolean(), label = "Configuration", 
        description = "Include system configuration in backup")

    form.data['dest'] = 'backup'

    form.addField('type', formal.String(required=True),
        formal.widgetFactory(formal.SelectChoice, options = [
                ('usb', 'USB'), 
                ('smb', 'Windows Share'), 
                ('path', 'Local path')
        ]
    ), label = "Backup Type")

    #Local path
    form.addField('pathPath', formal.String(), label = "Destination Path")

    #USB fields
    form.addField('usbDev', formal.String(),
            formal.widgetFactory(formal.SelectChoice, options = AvailLetters), label = "USB Device")

    if AvailLetters:
        form.data['usbDev'] = AvailLetters[0][0]

    #SMB fields
    form.addField('smbHost', formal.String(required=True), label = "Remote Host", description = "Server where file share is hosted.")
    form.data['smbHost'] = 'server'
    form.addField('smbShare', formal.String(required=True), label = "Share", description = "Name of share on server.")
    form.data['smbShare'] = 'public'
    form.addField('smbUser', formal.String(), label = "Username")
    form.addField('smbPass', formal.String(), label = "Password")

    form.addField('time', formal.Time(), label = "Scheduled Time", 
        description = "The time to run the backup if scheduled.")


class EditSet(Tools.Page):
    def __init__(self, avatarId, db, set=None, *a, **kw):
        Tools.Page.__init__(self, avatarId, db, *a, **kw)
        
        self.set = set

    def form_addSet(self, c):
        form = formal.Form()
        createForm(self, form)
        
        if self.set in self.sysconf.Backup.keys():
            thisSet = self.sysconf.Backup.get(self.set, {})
        else:
            thisSet = self.sysconf.Backup.get(int(self.set), {})

        if thisSet:
            form.data = thisSet

            #Add required fields if they do not exist
            if form.data['type'] != 'smb':
                form.data['smbHost'] = 'server'
                form.data['smbShare'] = 'public'

            if form.data['type'] != 'usb':
                AvailLetters = findDisks()
                if AvailLetters:
                    form.data['usbDev'] = AvailLetters[0][0]

            #Format time value
            try:
                t = time.strptime(form.data['time'], "%H:%M:%S")
                h,m = t.tm_hour,t.tm_min
                form.data['time'] = datetime.time(h, m)
            except:
                pass

            form.data['fileset'] = ','.join(thisSet.get('fileset', [])), 
            form.data['exclude'] = ','.join(thisSet.get('exclude', [])), 
            form.data['mailto'] = ','.join(thisSet.get('mailto', [])), 

            form.data['config'] = thisSet.get('backupConfig', False)
    
        form.addAction(self.submitForm)

        return form

    def submitForm(self, ctx, f, data):
        #Assign generic values
        backup = {}
        backup["backupConfig"] = data['config']
        backup["desc"] = data['desc']
        backup["type"] = data['type']
        backup["fileset"] = [i.lstrip().rstrip() for i in data['fileset'].split(',')]
        backup["dest"] = data['dest']
        if data['time']:
            backup["time"] = str(data['time'])
        if data['mailto']:
            backup["mailto"] = [i.lstrip().rstrip() for i in data['mailto'].split(',')]
        if data['exclude']:
            backup["exclude"] = [i.lstrip().rstrip() for i in data['exclude'].split(',')]

        #Assign specific backup type values
        if data['type'] == "usb":
            backup["usbDev"] = data['usbDev']

        if data['type'] == "smb":
            backup["smbHost"] = data['smbHost']
            backup["smbShare"] = data['smbShare']
            backup["smbUser"] = data['smbUser']
            backup["smbPass"] = data['smbPass']

        if data['type'] == "path":
            backup['pathPath'] = data['pathPath']

        backups = self.sysconf.Backup

        try:
            if backups[int(self.set)]:
                backups[int(self.set)] = backup
        except KeyError:
            backups[self.set] = backup

        self.sysconf.Backup = backups

        Utils.log.msg('%s edited backup %s' % (self.avatarId.username, repr(data)))

        def returnPage(_):
            return url.root.child('Backup')

        return WebUtils.system(
            '/usr/local/tcs/tums/configurator --backup'
        ).addCallback(returnPage)

   
    def childFactory(self, ctx, seg):
        return EditSet(self.avatarId, self.db, set=seg)

    def render_content(self, ctx, data):
        return ctx.tag[
            tags.h3[tags.img(src="/images/netdrive.png"), " Backups"],
            tags.directive('form addSet'), 
        ]

class Page(Tools.Page):
    def form_addSet(self, c):
        form = formal.Form()
        createForm(self, form)
        form.addAction(self.submitForm)
        return form

    def submitForm(self, ctx, f, data):
        #Assign generic values
        backup = {}
        backup["backupConfig"] = data['config']
        backup["desc"] = data['desc']
        backup["type"] = data['type']
        backup["fileset"] = [i.lstrip().rstrip() for i in data['fileset'].split(',')]
        backup["dest"] = data['dest']
        if data['time']:
            backup['time'] = str(data['time'])
        if data['mailto']:
            backup["mailto"] = [i.lstrip().rstrip() for i in data['mailto'].split(',')]
        if data['exclude']:
            backup["exclude"] = [i.lstrip().rstrip() for i in data['exclude'].split(',')]

        #Assign specific backup type values
        if data['type'] == "usb":
            backup["usbDev"] = data['usbDev']

        if data['type'] == "smb":
            backup["smbHost"] = data['smbHost']
            backup["smbShare"] = data['smbShare']
            backup["smbUser"] = data['smbUser']
            backup["smbPass"] = data['smbPass']

        if data['type'] == "path":
            backup['pathPath'] = data['pathPath']

        backups = self.sysconf.Backup

        #Find available backup ID
        maxid = 0
        for id in backups:
            if id > maxid:
                maxid = int(id)
        current = maxid + 1

        #Add backup set by id
        backups[current] = backup
        self.sysconf.Backup = backups

        Utils.log.msg('%s added backup %s' % (self.avatarId.username, repr(data)))

        def returnPage(_):
            return url.root.child('Backup')

        return WebUtils.system(
            '/usr/local/tcs/tums/configurator --backup'
        ).addCallback(returnPage)

    def childFactory(self, ctx, seg):
        if seg == "Edit":
            return EditSet(self.avatarId, self.db)

        return Tools.Page.childFactory(self, ctx, seg)

    def locateChild(self, ctx, segs):
        def returnMe(_):
            return url.root.child('Backup')


        if segs[0]=="Execute":
            Utils.log.msg('%s executed backup %s' % (self.avatarId.username, segs[1]))
            #utils.getProcessOutput(Settings.BaseDir+'/backup.py', [segs[1]], errortoo=1) #.addCallbacks(self.care, self.care)
            
            # Fork this so we return immediately
            WebUtils.system(Settings.BaseDir+'/backup.py %s' % (segs[1]))
            return returnMe(1), ()

        if segs[0] == "Delete":
            B = self.sysconf.Backup
            try:
                del B[segs[1]]
            except KeyError:
                del B[int(segs[1])]
            self.sysconf.Backup = B

            Utils.log.msg('%s deleted backup %s' % (self.avatarId.username, segs[1]))

            return WebUtils.system('/usr/local/tcs/tums/configurator --backup').addBoth(returnMe), ()

        return Tools.Page.locateChild(self, ctx, segs)

    def render_content(self, ctx, data):
        headings = [
            ('Set', 'set'), 
            ('Description', 'desc'),
            ('Type', 'type'),
            ('Destination', 'dest'),
            ('Source', 'fileset'),
            ('Excluded', 'exclude'),
            ('Notifications', 'mailto'),
            ('', 'options')
        ]

        backups = self.sysconf.Backup
        backupRows = []

        remap = {
            'smb': 'Windows Share',
            'usb': 'USB Drive',
            'path': 'Local path'
        }

        for k,v in backups.items():
            backupRows.append([
                k, 
                v['desc'],
                remap[v['type']],
                v['dest'], 
                ','.join(v.get('fileset', [])), 
                ','.join(v.get('exclude', [])), 
                ','.join(v.get('mailto', [])),
                [
                    tags.a(
                            href="Delete/%s/" % k,
                            onclick="return confirm('Are you sure you want to delete this backup set?');"
                    )[tags.img(src='/images/ex.png')], 
                    " ",
                    tags.a(href="Edit/%s/" % k)[tags.img(src='/images/edit.png')], 
                    " ",
                    tags.a(href="Execute/%s/" % k)[tags.img(src='/images/start.png')],
                ]
            ])
   
        return ctx.tag[
            tags.h3[tags.img(src="/images/netdrive.png"), " Backups"],
            PageHelpers.dataTable([h[0] for h in headings], backupRows), 
            tags.h3['Add Backup'], 
            tags.directive('form addSet'), 
        ]
