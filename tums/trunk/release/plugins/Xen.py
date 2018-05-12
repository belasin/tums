import config, os
from Core import Utils


class Plugin(object):
    parameterHook = "--xen"
    parameterDescription = "Reconfigure Xen"
    parameterArgs = ""
    autoRun = True
    configFiles = [ 
        "/etc/xen/xend-config.sxp",
    ]

    def reloadServices(self):
        os.system('/etc/init.d/ddclient restart')

    def writeConfig(self, *a):
        if not config.General.get('xen'):
            # No Xen config
            return 

        if not config.General['xen'].get('enabled'):
            # Disabled
            return 

        self.checkInstall()

        XenConf = config.General['xen'].get('config', {})

        conf = """
# -*- sh -*-
# Vulani Xen configuration

(network-script 'network-bridge netdev=%(lanPrimary)s')
(network-script network-dummy)
(vif-script vif-bridge)
(dom0-min-mem 196)
(dom0-cpus 0)
(vnc-listen '%(lanPrimaryIp)s'
""" % {
        'lanPrimaryIp': Utils.getLanIPs(config)[0],
        'lanPrimary': Utils.getLans(config)[0]
      }
        
        # Seek out our latest Xen kernel

        lines = os.open('ls /boot/ | grep xen-vserver | grep -v ".bak$"')

        kern = "vmlinuz-2.6.18-6-xen-vserver-686"
        init = "initrd.img-2.6.18-6-xen-vserver-686"
        knum = 2*6*18*6
        inum = 2*6*18*6
        for n in lines.read():
            line = n.strip('\n')
            if not ('vmlinuz' in line or 'initrd' in line):
                # avoid things that might break this logic
                continue 
            p = line.split('-')
            # Make a big number from the version 
            ver = reduce(lambda x,y: x*y, [int(i) for i in p[1].split('.')]) * int(p[2])

            # Make sure this is the biggest version 
            if "vmlinuz" in line:
                if ver > knum:
                    kern = line
                    knum = ver

            if "initrd" in line:
                if ver > knum:
                    init = line
                    inum = ver

        toolconf = """
# Vulani Xen-tools configuration

dir = /storage/virtual_machines

size = 10Gb
memory = 128Mb
swap = 128Mb
fs = ext3
dist = etch
image = sparse

dhcp = 1 

passwd = 1 

kernel = /boot/%(xenKern)s
initrd = /boot/%(xenInit)s

mirror = http://debian.mirror.ac.za/debian/

""" % {'xenKern': kern, 'xenInit': init}

        defaults = """
# Vulani Xen defaults
XENDOMAINS_SYSRQ=""
XENDOMAINS_USLEEP=100000
XENDOMAINS_CREATE_USLEEP=5000000
XENDOMAINS_MIGRATE=""
XENDOMAINS_SAVE=/var/lib/xen/save
XENDOMAINS_SHUTDOWN="--halt --wait"
XENDOMAINS_SHUTDOWN_ALL="--all --halt --wait"
XENDOMAINS_RESTORE=true
XENDOMAINS_AUTO=/etc/xen/auto
XENDOMAINS_AUTO_ONLY=false
XENDOMAINS_STOP_MAXWAIT=300
"""
    
    
        Utils.writeConf('/etc/xend-config.sxp', conf, None)

        Utils.writeConf('/etc/xen-tools/xen-tools.conf', toolconf, None)

        Utils.writeConf('/etc/default/xendomains', defaults, None)
    def checkInstall(self):
        l = os.popen('aptitude search xen-hypervisor | grep "^i"')
        if 'xen-hyper' in l:
            # We have some xen stuff installed - assume the rest is as well and exit
            return 

        os.system('apt-get install linux-image-2.6-xen-vserver-686 xen-hypervisor-3.0 xen-tools xen-linux-system-2.6.18-6-xen-vserver-686 linux-headers-2.6-xen-vserver-686 libc6-xen bridge-utils xen-ioemu-3.0.3-1')
        
