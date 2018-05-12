#!/usr/bin/python
import Settings, sys, os, config

l = open(Settings.BaseDir + '/backup.dat')
backups = {}
for i in l:
    line = i.strip('\n')
    if line:
        b = line.split('|')
        backups[b[0]] = b[1:]
        
try:
    set = backups[sys.argv[1]]
except:
    print "No backup set by that id"
    sys.exit(1)

try:
    # Start by making sure that /mnt/backup is not mounted
    if os.path.ismount('/mnt/backup'):
        os.system("umount /mnt/backup 2>/dev/null")
    # Try find the device matching that ID 
    lp = os.listdir('/dev/disk/by-id/')
    device = ""
    for disk in lp:
        if set[2] in disk and "part" in disk:
            device = disk
    if not device:
        for e in set[1].split(';'):
            os.system("echo \"I cannot find a device node to mount\" | mail -s \"%s: Backup Ended Error! \" %s" % (config.CompanyName, e))
        sys.exit(1)

    os.system('mkdir /mnt/backup >/dev/null 2>&1 ') # Make it or don't care
    
    mount = "mount /dev/disk/by-id/%s /mnt/backup 2>&1; rm /mnt/backup/BackupLog.txt 2>&1" % (device,) 

    email = [
        """echo -e "Backup \\\'%s\\\' completed at `date`
    Log:" | cat - /mnt/backup/BackupLog.txt | tail -n 3 | grep -E "(Backup|total|sent)" | mail -s "%s: Backup Ended Successful" %s""" % (set[0], config.CompanyName, i) 
        for i in set[1].split(';')]
    
    backups = [
        "/usr/bin/rsync -pravv --delete %s /mnt/backup/%s >> /mnt/backup/BackupLog.txt 2>&1" % (fold, set[4])
    for fold in set[3].split(';')]

    mounted = os.popen(mount).read()
    if "not exist" in mounted or "error" in mounted:
        for e in set[1].split(';'):
            os.system("echo \"You have not connected the device!\" | mail -s \"%s: Backup Ended Error! \" %s" % (config.CompanyName, e))
    else:
        for b in backups:
            os.system(b)
        for e in email:
            os.system(e)

    # Unmount the backup device!
    os.system('umount /mnt/backup')

except:
    print "Backup failed"
