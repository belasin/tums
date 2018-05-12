import config, os, time, sys
from Core import Utils

class Plugin(object):
    parameterHook = "--backup"
    parameterDescription = "Reconfigure Backups"
    parameterArgs = ""
    autoRun = True
    configFiles = []

    def reloadServices(self):
        pass

    def usbDir(self,data):
        for set in data:
            self.dest = set['dest']

    def localPath(self, data):
        print data

    def smbDir(self,data):
        for set in data:
            self.dest = set['dest']
            self.host = set['smbHost']
            self.share = set['smbShare']
            self.user = set['smbUser']
            self.passwd = set['smbPass']

            # Check if dest dir exists
            o = os.popen('smbclient //%(host)s/%(share)s -U %(user)s%%%(pass)s -c "ls %(dest)s" >/dev/null 2>/dev/null' % {
                'host': self.host,
                'share': self.share,
                'user': self.user or '',
                'pass': self.passwd or '',
                'dest': self.dest
            }).read()

            # Make SMB dest dirs
            if 'NO_SUCH_FILE' in o:
                os.system('smbclient //%(host)s/%(share)s -U %(user)s%%%(pass)s -c "mkdir %(dest)s" >/dev/null 2>/dev/ull' % {
                    'host': self.host,
                    'share': self.share,
                    'user': self.user or '',
                    'pass': self.passwd or '',
                    'dest': self.dest
                })

    def writeConfig(self):
        areSets = False
        # Write cron.d jobs
        for set in config.Backup.keys():
            areSets = True
            t = config.Backup[set].get('time')

            if t:
                self.time = time.strptime(str(t), "%H:%M:%S")

                cron = "%s %s  * * *      root    /usr/local/tcs/tums/backup.py %s\n" % (
                    self.time.tm_min,
                    self.time.tm_hour,
                    set
                )   
                file = '/etc/cron.d/backup%s' % set

                # write to cron file using Utils.writeConf
                Utils.writeConf(file, cron, '#')
        if not areSets:
            # Term here if there are no backups to look at
            return
                
        # Maintain cron jobs
        jobs = [cron
                for cron in os.listdir('/etc/cron.d')
                if 'backup' in cron]
        for i in jobs:
            if i:
                if not i.lstrip('backup') and not int(i.lstrip('backup')) in config.Backup.keys():
                    os.remove('/etc/cron.d/%s' % i)

        # Create logfile directory
        if not os.path.isdir('/var/log/backup'):
            os.makedirs('/var/log/backup')

        # Write logrotate conf
        if not os.path.exists('/etc/logrotate.d/backup'):
            content = """/var/log/backup/*.log {
            daily
            rotate 30
            missingok
            notifempty
            compress
            nocreate
            }""" 
            
            file = '/etc/logrotate.d/backup'

            Utils.writeConf(file, content, '#')
            if not os.path.exists('/var/log/backup/'):
                os.mkdir('/var/log/backup')

        # Create a store for each type
        types = {
            'usb': [],
            'smb': [], 
            'path': []
        }

        # Map types to their handler functions
        handlers = {
            'usb': self.usbDir,
            'smb': self.smbDir,
            'path': self.localPath
        }

        # reprocess the configuration
        for set, conf in config.Backup.items():
            cnf = conf
            types[str(cnf['type'])].append(cnf)

        # Call the handler functions with the stores
        for k,v in types.items():
            if v:
                v.sort()
                handlers[k](v)

