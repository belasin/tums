from enamel import pages, deferreds, tags, form, url
import re
from pages import * 

import utils

class partEditor(pages.AthenaFragment):
    def document(self):
        return pages.template('diskselect_fragment.xml', templateDir = '/home/installer/templates')

    @pages.exposeAthena
    def getPartitions(self):
        def diskstats(result):
            print result
            devs = {}

            self.dsizes = {}
            
            for n in result.split('\n'):
                if "dev/md" in n:
                    continue
                if n[:4] == "Disk":
                    dev = unicode(n.split()[1].strip(':').split('/')[-1])
                    size = int(n.split()[2])
                    print size
                    devs[dev] = []
                    self.dsizes[dev] = size
                    continue
                k = n.strip()
                bootable = False
                if not k:
                    continue 

                if '*' in k:
                    bootable = True
                    k = k.replace('*', ' ')
                
                devpath, start, end, crap, blocks, id = k.split()[:6]
                type = ' '.join(k.split()[6:])
                size = (int(blocks.replace('-', '').replace('+', ''))*1024)/(1000*1000.0)
                dev = unicode(re.sub(r'[0-9]', '', devpath.strip('/dev/')))
                devtot = devpath.strip('/dev/') # The actual partition full name (sda1, hdb2 or whatever)
                def unicodeOrSelf(p):
                    if isinstance(p, str):
                        return unicode(p)
                    return p
                part = map(unicodeOrSelf, [
                    int(start.replace('-', '').replace('+', '')), 
                    int(end.replace('-', '').replace('+', '')), 
                    size, 
                    id, 
                    type, 
                    devtot
                ])
                if devs.get(dev):
                    devs[dev].append(part)
                else:
                    devs[dev] = [part]
            
            # Add freespace to partition list and create a stack of sizes. 
            # This will help with the javascript construction of a bar graph
            newdevs = []
            for dev, devParts in devs.items():
                lastEnd = 0 
                parts = []
                cnt = 0
                for part in devParts:
                    cnt += 1
                    if part[0] > (lastEnd + 1):
                        # There is freespace before me
                        parts.append([
                            ((part[0] - lastEnd) * 8225280)/(1024*1024), # Size of free block
                            lastEnd+1, # Start (Sectors)
                            part[0]-1, # End
                            u"-1", # ID
                            u"Free space", # Type
                            u"", # Device handle
                            cnt  # Part number (for fdisk later)
                        ])
                    parts.append([
                        part[2], # Size of partition
                        part[0], # Start (Sectors)
                        part[1], # End
                        part[3], 
                        part[4],
                        part[5],
                        cnt # Part number
                    ])
                    lastEnd = part[1]
                
                difer = self.dsizes[dev] - (lastEnd+1)

                if difer > 1:
                    # Decent difference between last partition and disk back... (and it's not empty)
                    parts.append([
                        ((self.dsizes[dev]-lastEnd) * 8225280)/(1024*1024),
                        0, 
                        0,
                        u"-1",
                        u"Free space", 
                        u"", 
                        cnt
                    ])
                    
                newdevs.append((dev, parts))
            print newdevs
            return newdevs

        def cyls(result):
            tots = {}
            lastDisk = ""
            cylindersRe = re.compile(r'.*, (.*) cylinders$')
            sizeRe = re.compile(r'Disk /dev/(.*): (.*) (..), .*$')
            for n in result.split('\n'):
                k = n.strip()
                if not k:
                    continue 

                if "md" in k:
                    continue
                cylMatch = cylindersRe.match(k)
                sizeMatch = sizeRe.match(k)
                
                if sizeMatch:
                    disk, size, unit = sizeMatch.groups()

                    lastDisk = unicode(disk)
                    if unit == "GB":
                        size = float(size)*1000
                    elif unit == "TB":
                        size = float(size)*1000*1000
                    else:
                        size = float(size)
                        
                    tots[unicode(disk)] = [size, None]
                if cylMatch:
                    mcyls = cylMatch.groups()[0]
                    tots[lastDisk][1] = int(mcyls)
            print tots
            return tots
                
        def sendResult(list):
            return list[0][1], list[1][1]

        return deferreds.DeferredList([
            # Get partitions
            utils.system(
                'sfdisk -R -l 2>&1 | egrep "^(/dev|Disk)" | grep -v "Empty$"'
            ).addBoth(diskstats),
            utils.system("fdisk -l").addBoth(cyls)
        ]).addBoth(sendResult)

    @pages.exposeAthena
    def deletePartition(self, device, partnum):
        def ok(_):
            print _
            return True
        args = '\\n'.join(['','d', str(partnum), 'p', 'w', 'q', ''])
        return utils.system('mdadm --misc --zero-superblock /dev/%s%s ; echo -e "%s" | fdisk /dev/%s' % (
            device.encode(), 
            partnum, 
            args, device.encode()
        )).addBoth(ok)

    @pages.exposeAthena
    def createPartition(self, device, partnum, size, type):
        size = int(size)
        print type
        def ok(_):
            print _
            return True
        args = ['', 'n', 'p']

        args.append(partnum)

        args.append('')

        if size:
            args.append('+%sM' % size)
        else:
            args.append('')

        args.append('t')

        typeMapper = {
            'Vulani': '83', 
            'Vulani RAID': 'fd', 
            'Swap': '82'
        }

        if partnum > 1:
            args.append(partnum)

        args.append(typeMapper[type])

        args.extend(['w', 'q', ''])

        cmd = '\\n'.join([str(n) for n in args])
        print cmd
        return utils.system('echo -e "%s" | fdisk /dev/%s' % (cmd, device.encode())).addBoth(ok)

    def doAutoPart(self, device):
        def done(_):
            print _
            return True

        def doneSwap(_):
            print _

            # Look for raid and make the right partition type
            if self.enamel.setup.get('disktype') == 'single':
                return self.createPartition(device, 2, 0, 'Vulani').addBoth(done)
            else:
                return self.createPartition(device, 2, 0, 'Vulani RAID').addBoth(done)

        def makeParts(_):
            print _
            return self.createPartition(device, 1, 1024, 'Swap').addBoth(doneSwap)

        return utils.system('dd if=/dev/zero of=/dev/%s bs=512 count=1' % device.encode()).addBoth(makeParts)

    @pages.exposeAthena
    def autoPart(self, device):
        return self.doAutoPart(device)

    @pages.exposeAthena
    def getDisks(self):
        print "Fetching layout"
        def diskstats(result):
            devs = []
            for n in result.split('\n'):
                dev = n.strip()
                if not dev:
                    # Blank lines are the bane of my life
                    continue 
                if not (dev in ['ram', 'fd', 'sr', 'loop', 'md']):
                    devs.append(unicode(dev))

            print devs
            return devs
        return utils.system(
                "cat /proc/diskstats | awk '{{print $3}}' | sed 's/[0-9]//g' | uniq"
            ).addBoth(diskstats)
        

class Page(pages.Athena):
    elements = {'partEditor': (partEditor, 'partEditor.E', '/home/installer/athena/partEditor.js')}

    def form_diskConfig(self, data):
        f = form.Form()

        f.addField('', form.String(),
            form.widgetFactory(form.RadioChoice, 
                options=(
                    ('raid1', 'RAID 1'),
                    ('noraid', 'Single device')
                )
            ),
            label = "Setup"
        )
        
        # If more than one drive exists..
        f.data['setup'] = 'raid1'

        f.addAction(self.next)
        return f

    def next(self, c, f, data):
        return url.root.child('DiskSelect')

    def document(self):
        return pages.template('diskselect.xml', templateDir = '/home/installer/templates')

