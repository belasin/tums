from enamel import pages, deferreds, tags, form, url

from pages import * 

import utils

class Page(pages.Standard):

    def form_raidConfig(self, data):
        def gotDisks(disks):
            f = form.Form()

            # Decide how many raid sets we can create from numbers of even partitions

            raidDisks = {}
            
            # Split on new lines, and remove the * that signifies bootable partitions
            for n in disks.replace('*','').split('\n'):
                if not n.strip():
                    continue
                parts = n.split()
                device = parts[0].strip('/dev/')
                cyls = int(parts[3].strip('-').strip('+'))
                raidDisks[device] = cyls

            # Find congruency 

            raidSets = {}

            used = []
            
            for k, v in raidDisks.items():
                if k in used:
                    continue 

                raidSets[k] = [k]

                used.append(k)

                # one partition per drive only
                usedHere = [k[:-1]]

                for otherk, otherv in raidDisks.items():
                    # Never check disks twice
                    if otherk in used:
                        # Already got this
                        continue

                    if otherk[:-1] in usedHere:
                        # Make sure we only check different drives
                        continue

                    if otherv == v:
                        # Same size
                        raidSets[k].append(otherk)
                        used.append(otherk)
                        usedHere.append(otherk[:-1])

            print raidSets

            sets = [v for k,v in raidSets.items()]

            self.raidSets = {}

            for raidNum, set in enumerate(sets):
                size = (int(raidDisks[set[0]]) * 8225280)/(1024*1024)

                # Store it.
                self.raidSets["md%s" % raidNum] = set

                f.addField('md%s' % raidNum, form.String(),
                    form.widgetFactory(form.SelectChoice, 
                        options=(
                            ('/', '/'), 
                            ('/var', '/var'), 
                            ('/storage', '/storage')
                        )
                    ),
                    label = [tags.strong["md%s" % (raidNum)], " (%sMB)" % size]
                )

            f.data = {
                'md0': '/',
                'md1': '/var',
                'md2': '/storage',
            }
 
            # If more than one drive exists..
                
            f.addAction(self.next)
            
            # Time to find some disks

            return f
        
        return utils.system('sfdisk -R -l 2>&1| grep "^/dev/" | grep "Linux raid"').addBoth(gotDisks)

    def form_singleConfig(self, data):
        def gotDisks(disks):
            print "HERE"
            print disks
            f = form.Form()
            myDisks = {}
            # Split on new lines, and remove the * that signifies bootable partitions
            for n in disks.replace('*','').split('\n'):
                if not n.strip():
                    continue
                parts = n.split()
                device = parts[0].strip('/dev/')

                cyls = int(parts[3].strip('-').strip('+'))

                myDisks[device] = cyls

            self.disks = []

            cnt = 0

            for dev, cyls in myDisks.items():
                cnt += 1 
                size = (int(cyls) * 8225280)/(1024*1024)
                self.disks.append(dev)

                f.addField(dev, form.String(),
                    form.widgetFactory(form.SelectChoice, 
                        options=(
                            ('/', '/'), 
                            ('/var', '/var'), 
                            ('/storage', '/storage')
                        )
                    ),
                    label = [tags.strong[dev], " (%sMB)" % size]
                )

                if cnt == 1:
                    f.data[dev] = '/'
                if cnt ==2:
                    f.data[dev] = '/var'
                if cnt ==3:
                    f.data[dev] = '/storage'

            # If more than one drive exists..
                
            f.addAction(self.nextSingle)
            
            return f

        return utils.system('sfdisk -R -l 2>&1| grep "^/dev/" | grep "Linux$"').addBoth(gotDisks)

    def nextSingle(self, c, f, data):
        runChain = ['mkdir -p /mnt/target']
        self.enamel.setup['mountpoints']={}

        self.enamel.setup['runmounts'] = []

        root = ""
        for k,v in data.items():
            if u"/" == v:
                root= k
        if not root:
            # We NEED a root mount!
            return url.root.child('DiskMounts')

        rootChain = []
        lateChain = []

        for disk in self.disks:
            runChain.append("mkfs.ext3 -j -F -q /dev/%s" % disk)
            runChain.append("sync")

            if data[disk]:
                self.enamel.setup['mountpoints'][data[disk]] = disk
                thisChain = []
                thisChain.append('mkdir -p /mnt/target%s' % data[disk])

                self.enamel.setup['runmounts'].append('mount /dev/%s /mnt/target%s' % (disk, data[disk]))

                if data[disk] == u"/":
                    rootChain.extend(thisChain)
                else:
                    lateChain.extend(thisChain)

        runChain.extend(rootChain)
        runChain.extend(lateChain)
        runChain.append('sync')

        self.enamel.setup['formatcoms']= runChain

        return url.root.child('FormatDisks')

    def next(self, c, f, data):
        runChain = ['mkdir -p /mnt/target']
        self.enamel.setup['mountpoints']={}
        self.enamel.setup['raidsets'] = self.raidSets

        self.enamel.setup['runmounts'] = []
        root = ""
        for k,v in data.items():
            if u"/" == v:
                root= k
        if not root:
            # We NEED a root mount!
            return url.root.child('DiskMounts')

        # http://wiki.archlinux.org/index.php/Reinstalling_GRUB
        # Ubuntu put the inode size to 256 post 8.10 - our grub version does not like this!
        rootChain = ['cp /root/mke2fs.conf /etc/']
        lateChain = []
        for raidDev, set in self.raidSets.items():
            runChain.append("yes | mdadm --create /dev/%s -f -l 1 -n %s -x 0 %s" % (
                raidDev,
                len(set), 
                ' '.join(['/dev/'+i for i in set])
            ))

            # Do some serious sync bashing to make sure our partition table is all synced and ready to go
            runChain.append('sync')
            runChain.append('sfdisk -R -l')
            runChain.append('sync')
            runChain.append('sleep 5')
            runChain.append("mkfs.ext3 -j -F -q /dev/%s" % raidDev)
            runChain.append('sync')

            if data[raidDev]:
                thisChain = []
                # Mount point was specified for this set
                self.enamel.setup['mountpoints'][data[raidDev]] = raidDev
                thisChain.append('mkdir -p /mnt/target%s' % data[raidDev])
                self.enamel.setup['runmounts'].append('mount /dev/%s /mnt/target%s' % (raidDev, data[raidDev]))

                if data[raidDev] == u"/":
                    rootChain.extend(thisChain)
                else:
                    lateChain.extend(thisChain)

        runChain.extend(rootChain)
        runChain.extend(lateChain)
        runChain.append('sync')

        self.enamel.setup['formatcoms']= runChain

        return url.root.child('FormatDisks')

    def document(self):
        if self.enamel.setup.get('disktype') == 'single':
            return pages.template('diskmounts-s.xml', templateDir = '/home/installer/templates')

        return pages.template('diskmounts-r.xml', templateDir = '/home/installer/templates')
            

