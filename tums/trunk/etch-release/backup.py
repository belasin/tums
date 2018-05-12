#!/usr/bin/python
#  Exit codes:
#	1  Version mismatch
#	3  No device configured
#	4  Device not connected
#       5  Filesystem not valid

# Import sys, os, time, config
import config, sys, os, logging
from plugins import Backup

# Built-ins
logFull = "/var/log/backup/full.log"
logSummary = "/var/log/backup/summary.log"
os.path.isdir('/var/log/backup') or os.mkdir('/var/log/backup')
os.system('touch %s' % logFull)
os.system('touch %s' % logSummary)

# Logging setup
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%F %T')

full = logging.getLogger('full')
fullhdlr = logging.FileHandler('/var/log/backup/full.log')
fullhdlr.setFormatter(formatter)
full.addHandler(fullhdlr)
full.setLevel(logging.INFO)

summary = logging.getLogger('summary')
summaryhdlr = logging.FileHandler('/var/log/backup/summary.log')
summaryhdlr.setFormatter(formatter)
summary.addHandler(summaryhdlr)
summary.setLevel(logging.INFO)

class Destination(object):
    def mount(self):    #change method to "preBackup"
        """ Handles the mounting of the destination filesystem. """

        # Make mountpoint on local filesystem
        if not os.path.isdir(self.mountPoint):
            os.makedirs(self.mountPoint)

        # Rotate logs
        if os.path.exists('/etc/logrotate.d/backup'):
            rotate = os.system("/usr/sbin/logrotate -f /etc/logrotate.d/backup")

        # Mount destination
        if not os.path.ismount(self.mountPoint):

            mount = os.popen(self.mountCmd).read()
            if "not exist" in mount or "error" in mount:
                notify("External drive not connected. Cannot continue with backup.", "Backup Failure!")
                sys.exit(4)
            elif "specify the filesystem" in mount:
                notify("External drive does not have a valid filesystem. Cannot continue with backup.", "Backup Failure!")
                sys.exit(5)
            elif "already mounted" in mount:
                full.info('External drive already mounted, continuing...')

        ## Create destination directory
        #d = self.makeDir()
        #if d != 0:
        #    print "FAILED"
        #    notify("Destination directory not found. Unable to create.\n\nPlease contact support@thusa.co.za for assistance.", "Backup Failure!")

    def umount(self):   #change method to "postBackup"
        """ Handles unmounting of destination filesystem. """
        if os.path.ismount(self.mountPoint):
            try:
                os.system("umount %s 2&>/dev/null" % (self.mountPoint))
            except:
                notify("Unable to unmount destination. Please contact support@thusa.co.za for assistance.", "Backup Warning")

    def transfer(self):     #change method to "runBackup"
        """ Handles transferring of files during backup. """
        status = 0

        for dir in self.config['fileset']:

            transfer = os.WEXITSTATUS(os.system("""
            /usr/bin/rsync %(exclude)s -%(opts)s --delete --delete-excluded %(dir)s %(mount)s/%(dest)s >> %(log)s 2>> %(log)s 
            """ % {
                'exclude': " ".join(['--exclude "%s"' % pat for pat in self.config['exclude']]), 
                'opts': self.mountOpts, 
                'mount': self.mountPoint, 
                'dest': self.config['dest'], 
                'dir': dir,
                'log': logFull 
                }))
            #error = os.popen("tail -n 1 %s | grep rsync" % (logFull)).read()
            error = os.popen("grep rsync %s | tail -n 1" % (logFull)).read() 	#broken

            if transfer == 0:
                summary.info('%s -> %s:\t\t\tSuccessful' % (dir, self.config['dest']))
                print '%s -> %s:\t\t\tSuccessful' % (dir, self.config['dest'])	#testing
            elif transfer == 24:
                summary.warning('%s -> %s:\t\t\tWarning!' % (dir, self.config['dest']))
                summary.warning('\t %s' % (error))
                print '%s -> %s:\t\t\tWarning!' % (dir, self.config['dest'])	#testing
                status = 10
            else:
                summary.error('%s -> %s:\t\t\tFailed!' % (dir, self.config['dest']))
                summary.error('\t %s' % (error))
                print '%s -> %s:\t\t\tFailed!' % (dir, self.config['dest'])	#testing
                status = 20

        return transfer
        #return status

class DestinationUSB(Destination):
    def __init__(self, *a):	

        #self.mountPoint = str(mountPoint)
        #self.fileset = fileset
        #self.exclude = exclude or []
        #self.dest = dest

        self.mountPoint = "/mnt/backup"
        self.mountOpts = "avp"
        self.config = conf

        # Look for device ID to use
        disks = os.listdir('/dev/disk/by-id/')
        for disk in disks:
            if self.config['usbDev'] in disk and "part" in disk:
                self.device = disk

        # If the device is not found, exit gracefully
        try:
            self.mountCmd = 'mount /dev/disk/by-id/%s %s 2>&1' % (self.device, self.mountPoint)
        except AttributeError:
            notify("I cannot find a device node to mount. Cannot continue.", "Backup Failure!")
            sys.exit()


class DestinationSMB(Destination):
    def __init__(self, *a):

        # Assign some configuration values
        self.mountPoint = "/mnt/backup"
        #self.mountPoint = str(mountPoint[0])

        self.mountOpts = "rvz"

        self.config = conf

        #print self.config['exclude']
        #print self.config['time']
        #print self.config['mailto']
        #print self.config['smbHost'], self.config['smbShare'], self.config['smbUser'], self.config['smbPass']

        self.mountCmd = 'smbmount //%(host)s/%(share)s %(mnt)s -o username=%(user)s%%%(pass)s' % {
            'mnt': self.mountPoint, 
            'host': self.config['smbHost'], 
            'share': self.config['smbShare'], 
            'user': self.config['smbUser'], 
            'pass': self.config['smbPass']
        }

    def makeDir(self, *a):
        """ Checks and creates destination backup directory. """


        #Check if dest dir exists
        o = os.popen('smbclient //%(host)s/%(share)s -U %(user)s%%%(pass)s -c "ls %(dest)s"' % {
            'host': self.config['smbHost'],
            'share': self.config['smbShare'],
            'user': self.config['smbUser'] or '',
            'pass': self.config['smbPass'] or '',
            'dest': self.config['dest']
        })

        #Make SMB dest dirs
        if 'NO_SUCH_FILE' in o.read():
            print "TRYING TO MAKE REM DIR..."
            try:
                os.system('smbclient //%(host)s/%(share)s -U %(user)s%%%(pass)s -c "mkdir %(dest)s" >/dev/null 2>/dev/null' % {
                    'host': self.config['smbHost'],
                    'share': self.config['smbShare'],
                    'user': self.config['smbUser'] or '',
                    'pass': self.config['smbPass'] or '',
                    'dest': self.config['dest']
                })
            except:
                print "FAILED"
                return 1
            else:
                return 0
        

def notify(msg, status):
	""" Simple notification system for backups. """
        addrs = config.Backup[set].get('mailto')
        for addr in addrs:
            os.system("echo \"%s\" | mail -s \"%s: %s\" %s" % (msg, config.CompanyName, status, addr))
    ## NOTE: Move under reporting class

def cleanup(result):
    """ Cleans up logs etc. """

    # Send backupStatus notification
    if result == 24:
        notify("`cat %s`" % (logSummary), "Backup OK (with warnings)")
    elif result == 0:
        notify("`cat %s`" % (logSummary), "Backup OK")
    else:
        notify("`cat %s`" % (logSummary), "Backup Failure!")
    ## NOTE: move under reporting class

handlers = {
    'usb': DestinationUSB,
    'smb': DestinationSMB
}

#data = {
#    'usb': ['/mnt/backup'],
#    'smb': ['/mnt/backup']
#}
if __name__ == '__main__':
    # Assign backup set to conf dict
    if len(sys.argv) > 1:
        set = int(sys.argv[1])
    else:
        usage = """No backup set specified. Please run again with the relevant argument. Check config.py for configured backup sets.
        usage: ./backup.py <backup set>"""
        print usage

        sys.exit()

    conf = config.Backup[set]

    # Sort out optional values
    for key in ['exclude', 'mailto']:
        try:
            conf[key]
        except KeyError:
            conf[key] = []

    # Remove unnecessary values
    try:
        del conf['time']
    except:
        pass


    # Create instance of backup to run
    type = conf['type']
    d = handlers[type](conf)

    # Perform backup
    d.mount()

    result = d.transfer()

    cleanup(result)

    d.umount()

