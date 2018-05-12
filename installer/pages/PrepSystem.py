from enamel import pages, deferreds, tags, form, url

from pages import * 

import utils, sha, time

class Prep(pages.AthenaFragment):

    def document(self):
        return pages.template('prep_fragment.xml', templateDir = '/home/installer/templates')

    @pages.exposeAthena
    def progressUpdate(self, n):
        # Figure out the percentage
        self.callRemote('updateProgress', n)

    def reboot(self):
        # Setup over. Lets reboot
        def rebootDone(_):
            print "How did we get here?"
            return True
        return utils.system('reboot').addBoth(rebootDone)
    
    @pages.exposeAthena
    def startConfig(self):
        n = open('/mnt/target/usr/local/tcs/tums/config.py', 'w')
        for k, val in self.enamel.config.items():
            n.write('%s = %s\n' % (k, repr(val)))
        n.close()

        # We need to create the mysql databases in the fully running system. It cannot happen in chroot. 
        l = open('/mnt/target/etc/rc.local', 'wt')
        l.write("""#!/bin/sh -e
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
echo "Entering first time configuration..."
echo "Configuring Vulani databases..."
/usr/bin/mysqladmin create exilog || true
/usr/bin/mysql exilog < /usr/local/tcs/exilog-tums/doc/mysql-db-script.sql || true
cd /usr/local/tcs/tums
/usr/local/tcs/tums/configurator --mysar || true
/usr/local/tcs/tums/configurator --webmail || true
echo "Configuring graphs..."
/usr/local/tcs/tums/getGraph.py > /dev/null 2>&1 
echo "Restarting services..."
/usr/local/tcs/tums/syscripts/doDeploy.sh || true
sed 's/%s/admin123/' -i /usr/local/tcs/tums/plugins/PostPrep.py
killall -9 tums || true
/usr/local/tcs/tums/tums || true
echo "#!/bin/sh -e" > /etc/rc.local
echo "#rc.local" >> /etc/rc.local
echo "exit 0" >> /etc/rc.local
""" % self.enamel.setup['adminpw'])
        l.close()

        l = open('/mnt/target/usr/local/tcs/tums/keyfil', 'wt')
        l.write(self.enamel.setup['key'].replace('\r', '').replace('\n', ''))
        l.write('\n')
        l.close()

        l = open('/mnt/target/root/fillSettings','wt')

        cont = """#!/bin/sh
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
addgroup --system nvram
addgroup --system kvm
addgroup --system scanner
addgroup --system fuse
addgroup --system tss
addgroup --system rdma
adduser --system --no-create-home --home /bin --disabled-password --group tss
userdel -f deleteme
cat /etc/passwd | grep "^root:" | sed 's/^root:x:/root:%(rootpw)s:/' | newusers
""" %   { 
            'rootpw': self.enamel.setup['rootpw']
        }

        # Setup management options 

        if not self.enamel.setup['thusam']:
            cont += """
rm -rf /root/.ssh
echo 1 > /usr/local/tcs/tums/.nomng
"""

        l.write(cont)
        l.close()

        l = open('/mnt/target/root/prePrep','wt')

        cont = """#!/bin/sh
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
#/usr/bin/dpkg -i /root/libapt-pkg-perl_0.1.20_i386.deb
#/usr/bin/dpkg -i /root/apt-show-versions_0.10_all.deb  
/usr/bin/dpkg -i /root/*.deb
# Do some hacks
rm -rf /usr/local/tcs/tums/plugins/GentooNetwork.*
"""
        l.write(cont)
        l.close()

        fn = (
            'mkdir -p /mnt/target/var/lib/samba/data/public',
            'mkdir /mnt/target/usr/local/tcs/tums/profiles',
            'cp /mnt/target/usr/local/tcs/tums/config.py /mnt/target/usr/local/tcs/tums/profiles/default.py',
            'echo default.py > /mnt/target/usr/local/tcs/tums/runningProfile',
            'echo default.py > /mnt/target/usr/local/tcs/tums/currentProfile',
            'touch /mnt/target/usr/local/tcs/tums/packages/set',
            # Update the base image if need be
            'cp /root/*.deb /mnt/target/root',
            'chmod +x /mnt/target/root/prePrep',
            'chroot /mnt/target /root/prePrep',
            'touch /root/cdinst',
            'rm /mnt/target/etc/udev/rules.d/z25_*',
            'sed \'s/admin123/%s/\' -i /mnt/target/usr/local/tcs/tums/plugins/PostPrep.py' % self.enamel.setup['adminpw']
        )

        # Make doDeploy managed

        c = open('/mnt/target/usr/local/tcs/tums/syscripts/doDeploy.sh', 'wt')
        c.write("#!/bin/sh\n")
        c.write('export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"\n')
        c.write("cd /usr/local/tcs/tums\n")
        c.write('/usr/local/tcs/tums/configurator --upgrade\n')
        c.write("/usr/local/tcs/tums/configurator -D | tee /var/log/vinstall.log\n")
        c.close()

        def doReboot(_):
            print _
            self.progressUpdate(100)
            self.reboot()
            return True

        def doTidy(_):
            print _
            self.progressUpdate(90)
            fn = (
                'chmod +x /mnt/target/root/fillSettings',
                'chroot /mnt/target /root/fillSettings',
                'rm /mnt/target/root/fillSettings', 
                'cp /var/log/tuminstall.log /mnt/target/root/',
            )
            return utils.system(';'.join(fn)).addBoth(doReboot)

        def configDone(_):
            print _
            print "Lets go!"
            self.progressUpdate(70)
            return utils.system('chroot /mnt/target/ /usr/local/tcs/tums/syscripts/doDeploy.sh').addBoth(doTidy)

        self.progressUpdate(20)
        return utils.system(';'.join(fn)).addBoth(configDone)

class Page(pages.Athena):
    elements = {'prep': (Prep, 'prep.E', '/home/installer/athena/prep.js')}

    def render_detail(self, ctx, data):
        return ctx.tag[
            tags.h3["Default Services"]
        ]

    def document(self):
        # Burn our config 


        return pages.template('prep.xml', templateDir = '/home/installer/templates')
        
