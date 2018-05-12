from enamel import pages, deferreds, tags, form, url
import re
from pages import * 

import utils

class Installer(pages.AthenaFragment):
    
    def __init__(self, *a, **kw):
        self.progress = 0  # progress ticker. 
        self.files = {
            'vulani-var.tar.bz2':   8630.0,
            'vulani-base.tar.bz2':  15890.0,
            'vulani-usr.tar.bz2':   50683.0
        }
        pages.AthenaFragment.__init__(self, *a, **kw)
    
    def document(self):
        return pages.template('install_fragment.xml', templateDir = '/home/installer/templates')
    
    @pages.exposeAthena
    def grubInstall(self):
        """ Configure grub - wheee.. """
        
        # Read from self.enamel.setup for / mount
        rootdev = self.enamel.setup['mountpoints']['/']
        
        # Here comes the fucking mission
        # if raid, get the first member of /
        if 'md' in rootdev:
            disks = self.enamel.setup['raidsets'][rootdev]
            disks.sort()
            disk = disks[0]
        else:
            disks = [rootdev]
            disk = rootdev
        
        # ??
        partnum = int(disk[-1]) - 1 
        disknum = ord(disk[-2]) - 97
        
        # Rewrite menu hint for root device
        f = open('/mnt/target/boot/grub/menu.lst')
        newlines = ""
        for n in f:
            if '# kopt' in n:
                newlines += "# kopt=root=/dev/%s ro\n" % rootdev
            elif '# groot=' in n:
                newlines += "# groot=(hd%s,%s)\n" % (disknum, partnum)
            elif '# defoptions=' in n:
                newlines += "defoptions=vga=791\n"
            elif 'color ' in n:
                newlines += "color yellow/light-gray light-red/light-gray\n"
            else:
                newlines += n
        f.close()
        f = open('/mnt/target/boot/grub/menu.lst', 'wt')
        f.write(newlines)
        f.close()
        
        # First rewrite fstab too
        fstab = """# /etc/fstab: static file system information.
#
# <file system> <mount point>   <type>  <options>       <dump>  <pass>
proc            /proc           proc    defaults        0       0
"""
        mtab = ""
        for m, d in self.enamel.setup['mountpoints'].items():
            fstab += "/dev/%s        %s        ext3 acl     0       1\n" % (d, m)
            mtab += "/dev/%s %s ext3 rw,acl 0 0\n"  % (d, m)
        
        # And then mtab...
        mtab += """tmpfs /lib/init/rw tmpfs rw,nosuid,mode=0755 0 0
proc /proc proc rw,noexec,nosuid,nodev 0 0
sysfs /sys sysfs rw,noexec,nosuid,nodev 0 0
procbususb /proc/bus/usb usbfs rw 0 0
udev /dev tmpfs rw,mode=0755 0 0
tmpfs /dev/shm tmpfs rw,nosuid,nodev 0 0
devpts /dev/pts devpts rw,noexec,nosuid,gid=5,mode=620 0 0\n"""
            
        l = open('/mnt/target/etc/fstab', 'wt')
        l.write(fstab) 
        l.close()
        
        l = open('/mnt/target/etc/mtab', 'wt')
        l.write(mtab)
        l.close()
        
        # Find all / devices  - if / is md0 find its parent members.
        # then call grub-install on each

        sequence = []

        # Mark bootable
        for d in disks:
            sequence.append('/home/installer/makeBootable.py %s' % d)

        sequence.extend([
            "mount -o bind /dev /mnt/target/dev",
            "mount -t proc none /mnt/target/proc",
            "mount -t sysfs none /mnt/target/sys",
            "/home/installer/popSwap.py >> /mnt/target/etc/fstab",
            "/home/installer/initSwap.py"
        ])
        
        sequence.extend([
            'chroot /mnt/target /usr/sbin/update-initramfs -u',
            'chroot /mnt/target /usr/sbin/update-grub',
            'chroot /mnt/target /usr/sbin/grub-install --recheck --no-floppy "(hd1)"',
            'chroot /mnt/target /usr/sbin/grub-install --recheck --no-floppy "(hd0)"'
        ])
        
        
        for n in sequence:
            print n
        
        com = ';'.join(sequence)

        def ok(_):
            # Don't swallow the output
            print _
        
        return utils.system(com).addBoth(ok)
    
    @pages.exposeAthena
    def fileComplete(self, file):
        #self.callRemote('fileCompleted', unicode(file))
        if 'base' in file:
            utils.extractBz2(self, 'vulani-var.tar.bz2')
            self.callRemote('updateTicker', u"Installing variable data...")
        elif 'var' in file:
            utils.extractBz2(self, 'vulani-usr.tar.bz2')
            self.callRemote('updateTicker', u"Installing system data...")
        else:
            self.callRemote('updateTicker', u"Completing installation...")
            self.callRemote('installComplete')
    
    @pages.exposeAthena
    def progressUpdate(self, file, n):
        # Figure out the percentage
        percent = int((n/self.files[file])*100)
        
        # Soften the impact on Athena by preventing unnecessary hammering on the connection
        if percent != self.progress:
            self.callRemote('updateProgress', percent)
        self.progress = percent
    
    @pages.exposeAthena
    def startup(self):
        utils.extractBz2(self, 'vulani-base.tar.bz2')
        self.callRemote('updateTicker', u"Installing base system...")
        return True

class Page(pages.Athena):
    elements = {'installer': (Installer, 'installer.E', '/home/installer/athena/installer.js')}
    
    def document(self):
        return pages.template('install.xml', templateDir = '/home/installer/templates')

