from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure, log
from twisted.internet import defer
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan, entities
from nevow.taglibrary import tabbedPane
import formal

import Tree, Settings, time, os, sys, sha, md5
from Core import PageHelpers, AuthApacheProxy, WebUtils, Utils

## Beware dragons

class Informant:
    def mailqueue(self):
        def ret(r):
            r = r.replace('\n', '').strip().split()
            
            # Try parsing it
            try:
                count, volume, oldest, newest, _ = r
            except:
                count, volume, oldest, newest = ("0", "0KB", "0s", "0s")

            return count, volume
                    
        return WebUtils.system("mailq | exiqsumm | tail -n 2").addBoth(ret)

    def uptime(self):
        def ret(r):
            r = r.replace('\n', '').replace(',', '').strip().split()

            up = "%s %s %s" % (r[2], r[3], r[4])

            return up

        return WebUtils.system("uptime").addBoth(ret)

    def runningProcesses(self):
        def ret(r):
            status = {
                'dhcpd3': False,
                'squid': False,
                'openvpn': False,
                'exim4': False,
                'smbd': False,
                'sshd': False,
            }
            
            for n in status.keys():
                if n in r:
                    status[n] = True

            return status
        return WebUtils.system("ps axg -www").addBoth(ret)

    def getLoadOld(self):
        # Get old load average segments. 
        fn = "rrdtool fetch /usr/local/tcs/tums/rrd/%s AVERAGE -s -2h | tail -n 20"
        def ret(r):
            five = r[0][1].strip('\n').split('\n')
            ten = r[1][1].strip('\n').split('\n')
            fifteen = r[2][1].strip('\n').split('\n')

            data = []
            for seg in [five, ten, fifteen]:
                partition = []
                for n in seg:
                    if not n:
                        continue
                    val = n.split(': ')[-1]
                    if val == "nan":
                        val = 0
                    val = float(val)
                    partition.append(val)
                data.append(partition)

            if not data:
                data = [[0.0 for i in range(20)] for j in range(3)]

            return data
            
        return defer.DeferredList([
            WebUtils.system(fn % 'sysload-5.rrd'),
            WebUtils.system(fn % 'sysload-10.rrd'),
            WebUtils.system(fn % 'sysload-15.rrd')
        ]).addBoth(ret)

class Page(PageHelpers.DefaultAthena):
    moduleName = 'statusGraphs'
    moduleScript = 'statusGraphs.js'
    docFactory = loaders.xmlfile('dashboard.xml', templateDir = Settings.BaseDir + '/templates')

    def __init__(self, *a, **kw):
        self.informant = Informant()
        PageHelpers.DefaultAthena.__init__(self, *a, **kw)

    def form_selectProfile(self, data):
        form = formal.Form()

        profiles = []
        for il in os.listdir('/usr/local/tcs/tums/profiles/'):
            if il[-3:] == '.py':
                name = il[:-3].replace('_', ' ').capitalize()
                profiles.append((il, name))

        form.addField('profile', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = profiles), label = "Switch Profile")
        form.addAction(self.switchProfile)
        return form

    def render_selectProfile(self, ctx, data):
        # Renderer for the form (because formal rendering sucks piles)
        profiles = []
        for il in os.listdir('/usr/local/tcs/tums/profiles/'):
            if il[-3:] == '.py':
                name = il[:-3].replace('_', ' ').capitalize()
                profiles.append((il, name))

        return ctx.tag[
            tags.select(id="selectProfile-profile", name="profile")[
                [tags.option(value=k)[v] for k, v in profiles]
            ]
        ]

    def switchProfile(self, ctx, form, data):
        l = open('/usr/local/tcs/tums/currentProfile', 'wt')
        l.write(data['profile'].encode())
        l.close()
        return url.root.child('Status')


    def data_fileserver(self, ctx, n):
        def ret(r):
            shares, sessions = r
            shares = [ i.split('\\') for i in shares[1].strip('\n').split('\n') if i ]
            sessions = [ i.split('\\') for i in sessions[1].strip('\n').split('\n') if i]
            sharesd = {}
            for n in shares:
                try:
                    nam = n[2]
                    if nam in sharesd:
                        sharesd[nam].append(n[0])
                    else:
                        sharesd[nam] = [n[0]]
                except:
                    Utils.log.msg("Error processing share: %s" % n)
                    continue

            sessionsList = []
            # Restructure the insane session list 
            for n in sessions:
                try:
                    # If there are shares open, create a line for each share..
                    if n[1] in sharesd:
                        for k in sharesd[n[1]]:
                            sessionsList.append([
                                n[1], 
                                n[2], 
                                "%s (%s)" % (n[3], n[4]), 
                                k
                            ])
                    # Otherwise just place the session on the table
                    else:
                        sessionsList.append([
                            n[1], 
                            n[2], 
                            "%s (%s)" % (n[3], n[4]), 
                            ""
                        ])
                except:
                    Utils.log.msg("Error processing session: %s" % n)
                    continue
            return sessionsList
            
        return defer.DeferredList([
            WebUtils.system("net status shares parseable"),
            WebUtils.system("net status sessions parseable")
        ]).addBoth(ret)

    def data_profiles(self, ctx, data):
        # Fetch running profile
        thisProfile = Utils.currentProfile()

        runningProfile = Utils.runningProfile()[0]

        if thisProfile[0] != runningProfile:
            thisProfile = [thisProfile[0]," [", tags.a(href=url.root.child("Profiles").child("switch").child(thisProfile[1]))["Activate"]], "]"
        else:
            thisProfile = thisProfile[0]

        print thisProfile
        
        return {
            'current': thisProfile,
            'running': runningProfile, 
        }

    def data_status(self, ctx, n):
        def ret(r):
            mqueue, uptime = r
            return {
                'mailvol': mqueue[1][1],
                'mailcnt': mqueue[1][0],
                'time': time.ctime(),
                'uptime': uptime[1]
            }

        return defer.DeferredList([
            self.informant.mailqueue(),
            self.informant.uptime()
        ]).addBoth(ret)

    def render_thisFragment(self, ctx, data):
        """ Renders liveGraphFragment instance """
        f = liveGraphFragment()
        f.setFragmentParent(self)
        return ctx.tag[f]

    def render_services(self, ctx, data):
        def ret(p):
            service = {
                'dhcpd3':   ('DHCP server', 'dhcp3-server'),
                'squid':    ('Web proxy',   'squid'),
                'openvpn':  ('VPN server',  'openvpn'),
                'exim4':    ('Mail server', 'exim4'),
                'smbd':     ('File server', 'samba'),
                'sshd':     ('Secure shell','sshd'),
            }
            
            slist = []

            s_red   = "color:#bf0000; margin-left: 1em; margin-right: 2em"
            s_green = "color:#006b33; margin-left: 1em; margin-right: 2em"
            for k, v in service.items():
                status = p[k]
                name, init = v


                slist.append([
                    status and tags.img(src="/images/state-running.png") or tags.img(src="/images/state-stopped-whitebg.png"), 
                    [entities.nbsp, name],
                    status and tags.div(style=s_green)["Running"] or tags.div(style=s_red)["Stopped"],
                    [
                        tags.a(href="/auth/Proc/%s/start/" % init, onclick="return confirm('Are you sure you want to start the %s service?');" % name)[
                            tags.img(src='/images/service-start.png')
                        ],
                        entities.nbsp, 
                        entities.nbsp, 
                        entities.nbsp, 
                        tags.a(href="/auth/Proc/%s/stop/" % init, onclick="return confirm('Are you sure you want to stop the %s service?');" % name)[
                            tags.img(src='/images/service-stop.png')
                        ]
                    ]
                ])
                
            # Produce our trs
            return ctx.tag[
                [
                    tags.tr[
                        [ tags.td[j] for j in i]
                    ]
                for i in slist]
            ]

        return self.informant.runningProcesses().addBoth(ret)

    def render_fileserver(self, ctx, data):
        return ctx.tag[
            ""
        ]
    
    def data_storage(self, ctx, data):
        d = Utils.getDf()
        filesystem = []
        for i in d:
            l = [
                i[1],
                Utils.intToHBnormal(i[2]*1024.0, True),
                Utils.intToHBnormal(i[3]*1024.0, True),
                "%s%%" % i[5],
                i[0]
            ]
            filesystem.append([unicode(j) for j in l])
        
        return filesystem

    def render_raid(self, ctx, data):
        try:
            mdstat = open('/proc/mdstat')
        except:
            return ctx.tag[
                tags.tr[
                    tags.td(colspan='5')["No active RAID identities"]
                ]
            ]

        raidStat = {}
        allDisks = []
        lastDisk = ""
        diskHolder = []
        for n in mdstat:
            l = n.strip('\n').strip()
            if not l:
                continue
            if "Personalities" in l:
                continue
            if "unused"  in l:
                continue
            
            v = l.replace(':', '').split()

            if 'md' in l:
                lastDisk = v[0]
                disks = v[3:]
                diskHolder = [] #Reset the diskHolder (Used when defining the status of the drive)
                allDisks.extend(disks)
                raidStat[lastDisk] = {
                    'type': v[2], 
                    'disks': disks
                }
            
            elif len(diskHolder) < 1: #Check if we have already got the status of the drives
                state = v[-1][1:-1]
                disks = raidStat[lastDisk]['disks']
                spares = []

                state = list(state)
                
                for d in disks:
                    dname = d.split('[')[0]
                    if "(S)" in d:
                        # Is a spare
                        spares.append(dname)
                    else:
                        if state.pop(0) == "U":
                            diskHolder.append((0, dname))
                        else:
                            # Broken drive
                            diskHolder.append((1, dname))

                for d in spares:
                    diskHolder.append((2, d))

                raidStat[lastDisk]['disks'] = diskHolder
            else:
                pass

        # Draw the table
        imgs = {
            0: '/images/disk-good.png',
            1: '/images/disk-bad.png',
            2: '/images/disk-rebuild.png'
        }
        rows = []

        for k, v in raidStat.items():
            diskImages = []
            spares = 0
            state = 0
            for status, name in v['disks']:
                if status == 2:
                    spares += 1
                if status == 1:
                    state += 1
                diskImages.append(tags.img(src=imgs[status]))
            
            if spares:
                type = [v['type'], tags.br, "%s Spare(s)" % spares]
            else:
                type = v['type']
            
            if state > 0:
                state = "Degraded"
                stateImg = tags.img(src='/images/state-stopped-whitebg.png')
            else:
                state = "Active/OK"
                stateImg = tags.img(src="/images/state-running.png")
            
            rows.append([
                stateImg, 
                k,
                type,
                diskImages, 
                state
            ])

        return ctx.tag[
            [
                tags.tr[
                    [tags.td[i] for i in j]
                ]
            for j in rows]
        ]
        
    def render_load(self, ctx, data):
        def graph(r):
            s = "/chart?type=line2&layout=tight&width=300&height=160&ylab=Run+queue&xticks=10"
            sets = ["5min", "10min", "15min"]
            
            for i, set in enumerate(r):
                s += "&set=%s&data=%s" % (sets[i], '+'.join(["%0.2f" % j for j in set]))
            
            for c,i in enumerate(reversed(range(20))):
                if c%2 == 0:
                    i = " "
                else:
                    i = "%ss" % i
                s += "&lables=%s" % i

            return ctx.tag[
                tags.img(src=s)
            ]
        return self.informant.getLoadOld().addBoth(graph)

    def cleanRRData(self, data):
        nd = []
        for n in data:
            if not n:
                continue
            val = n.split(': ')[-1]
            if val == "nan":
                val = 0
            try:
                val = float(val)
            except:
                val = 0 
            nd.append(val)
        return nd

    def render_ethMedia(self, ctx, data):
        if isinstance(data, list):
            iface = data[0]
            doState = True
        else:
            iface = data
            doState = False

        def ret(ethtool):
            state = False
            rate = "Unknown"
            for n in ethtool.split('\n'):
                l = n.strip()
                if not ':' in l:
                    continue
                l = n.strip().split(':')
                 
                k = l[0].strip()
                v = l[1].strip()
                
                if k == 'Link detected': 
                    state = v == 'yes'
                if k == 'Speed':
                    rate = v

            if not state:
                rate = "Not Connected"
            
            if doState:
                green = "#29b25c"
                red   = "#bf0000"
                img = state and '/images/state-running.png' or '/images/state-stopped-whitebg.png'
                color = state and green or red
                return [
                    tags.td[
                        tags.img(src=img)
                    ],
                    tags.td(width="100%")[
                        entities.nbsp,
                        tags.span(style="color: %s" % color)["Ethernet connection (%s)" % (iface)]
                    ],
                ]
            return ctx.tag["%s" % rate]


        return WebUtils.system('ethtool %s | grep -v Settings' % iface).addBoth(ret)

    def render_ethIP(self, ctx, data):
        """ Render the IP addresses configured on this interface """
        iface = data
        
        def ret(ipadd):
            ips = []
            for i in ipadd.strip('\n').split('\n'):
                ln = i.strip('\n').strip()
                if not ln:
                    continue
                ips.append(i.split()[1])

            if ips:
                return ctx.tag[
                    [[ip, tags.br] for ip in ips]
                ]
            else:
                return ["None assigned"]
            
        return WebUtils.system('ip addr show dev %s | grep "inet "' % iface).addBoth(ret)

    def form_changeKey(self, data):
        form = formal.Form()
        form.addField('key', formal.String(required=True), label = "New Key", 
            description = "Enter a new license key here")

        form.addAction(self.newLicenseKey)
        return form

    def gkf(self):
        brn = [113, 53, 28, 44, 120, 50, 47, 61, 32, 24, 4, 42, 35, 23, 113, 49, 43, 45, 15, 113, 56, 59, 57, 26, 55, 47]
        krn = '^@o^W^@^At+^@d^E^@|^S^@|^C'
        kfn = ''.join([chr(ord(a)^b) for b,a in zip(brn, krn)])
        return kfn

    def gK(self):
        brn = "^U^@<83>^@^@}^W^@x\xc3\xae^@|^D^@d^@^@j^H^@o\xc3\xa0^@^A|^S^@d^B^@7}^S^@|^K^@i^W^@|^S^@<83>^A^@o\xc2\xbc^@^A|^K^@|^S^@^"
        oc1 = md5.md5(brn).hexdigest()
        l = open(self.gkf()).read().strip('\n')
        oc2 = sha.sha(l).hexdigest()
        k = sha.sha(''.join([chr(ord(a)^ord(b)) for b,a in zip(oc1, oc2)])).hexdigest()
        kv = "%s-%s-%s-%s-%s" % (k[1:5], k[5:9], k[8:12], k[13:17], k[11:15])
        return kv 
 
    def newLicenseKey(self, ctx, form, data):
        l = open(self.gkf(), 'wt')
        l.write(data['key'].encode() + '\n')
        l.close()
        n = data['key'].strip().split('-')
        if len(n) == 4:
            l = open('/usr/local/tcs/tums/.kxd', 'wt')
            l.write('\x01\x10\x10')
            l.close()

        return url.root.child('Status')
    
    def form_codeActivation(self,data):
        form = formal.Form()
        form.addField('code', formal.String(required=True), label = "Activation Code", 
            description = "Enter your offline activation code here")

        form.addAction(self.activatePhone)
        return form

       
    def activatePhone(self, ctx, form, data):
        mk = self.gK()
        if mk == data['code'].encode():
            # valid key
            n = open('/usr/local/tcs/tums/.tliac', 'wt')
            n.write(mk)
            n.close()
        return url.root.child('Status')

    def render_license(self, ctx, data):
        if os.path.exists('/usr/local/tcs/tums/.kvd'):
            return ctx.tag[""]
        
        # Uptime more than 7 days (prevent bootstrapping issues)
        up = open('/proc/uptime').read().strip('\n').strip().split()
        n = float(up[0])
        days = n/(60*60*24)
        print "System uptime is %s days" % days
        if days < 7:
            pass
            #return ctx.tag[""]

        if os.path.exists('/usr/local/tcs/tums/.tliac'):
            mk = self.gK()
            if mk == open('/usr/local/tcs/tums/.tliac').read():
                return ctx.tag[""]

        if os.path.exists('/usr/local/tcs/tums/.kxd'):
            kt = os.stat('/usr/local/tcs/tums/.kxd').st_mtime
            nw = time.time()
            invalid = open('/usr/local/tcs/tums/.kxd').read() == '\x11\x10\x10'

            seconds = (60*60*24*16) - (nw-kt)
            # Give a 2 day leeway to perform activation requirements
            if seconds > (60*60*24*14) and not invalid:
                return ctx.tag[""]

            timeSet = ""

            days = seconds//(60*60*24)
            seconds -= days*60*60*24

            hours = seconds//(60*60)
            seconds -= hours*60*60

            minutes = seconds//60
            seconds -= minutes

            if days:
                timeSet = "%d days and %d hours" % (days, hours)

            elif hours:
                timeSet = "%d hours and %d minutes" % (hours, minutes)

            elif minutes:
                timeSet = "%d minutes" % (minutes)

            return ctx.tag[
                tags.div(_class="roundedBlock")[
                    tags.img(src="/images/network-small.png"), 
                    tags.h1["Software License"], 
                    tags.div[
                        tags.h1["Vulani License Activation!"],
                        tags.h3[" Activation time remaining %s" % timeSet],

                        tags.p["Your Vulani license has not been activated. If this is in error it should resolve itself ", 
                        "automaticaly. If not, please contact Thusa at support@thusa.co.za for licensing details."], 
                        tags.p["Your Vulani management interface will continue to work for the time indicated above, after which time ", 
                        "it will no longer be accessible until activation. Your server will continue to work indefinitely with its ",
                        "current configuration"],
                        tags.div(id="enterNewLicense")[
                            tags.a(href="#", onclick="newLicenseClick();")["Enter new license key"], 
                            tags.br,
                            tags.a(href="#", onclick="activationClick();")["Enter activation code"]
                        ],
                        tags.div(id="NewLicense", style="display:none")[
                            tags.directive('form changeKey')
                        ], 
                        tags.div(id="ActivateCode", style="display:none")[
                            tags.directive('form codeActivation')
                        ]
                    ]
                ]
            ]
        else:
            return ctx.tag[""]

    def render_network(self, ctx, data):
        interfaces = []
        
        for i in Utils.getInterfaces():
            if i[:3] in ['eth', 'ppp']:
                interfaces.append(i)
        
        interfaces.sort()
        procs = []
        for i in interfaces:
            procs.append(
                WebUtils.system(';'.join([
                    'rrdtool fetch /usr/local/tcs/tums/rrd/iface_%s_in.rrd AVERAGE -s -2h | tail -n 20' % i,
                    'rrdtool fetch /usr/local/tcs/tums/rrd/iface_%s_out.rrd AVERAGE -s -2h | tail -n 20' % i
                ]))
            )

        def ret(r):
            story = []
            s = "/chart?type=line2&layout=tight&width=300&height=160&ylab=KB/s&xticks=10"

            green = "#29b25c"
            
            for c, i in enumerate(interfaces):
                iface = i
                # Grab two data sets and split them 
                data = r[c][1].strip('\n').split('\n')
                data_in = self.cleanRRData(data[:20])
                data_out = self.cleanRRData(data[20:])
                
                gra = s
                gra += "&set=In&data=%s" % '+'.join(["%0.2f" % (j/1024) for j in data_in])

                gra += "&set=Out&data=%s" % '+'.join(["%0.2f" % (j/1024) for j in data_out])
                
                for k,i in enumerate(reversed(range(20))):
                    if k%2 == 0:
                        i = " "
                    else:
                        i = "%ss" % i
                    gra += "&lables=%s" % i

                ctype = "Unknown"
                if 'eth' in iface:
                    media = tags.invisible(render=tags.directive('ethMedia'), data=iface)
                    state = tags.invisible(render=tags.directive('ethMedia'), data=[iface, 'state'])
                    netConfig = "/auth/Network/Edit/%s/" % iface
                if 'ppp' in iface:
                    media = "Link"
                    state = [
                        tags.td[
                            tags.img(src='/images/state-running.png')
                        ],
                        tags.td(width="100%")[
                            entities.nbsp,
                            tags.span(style="color: %s" % green)["PPP connection (%s)" % (iface)]
                        ],
                    ]
                    netConfig = "/auth/PPP/"

                if c < 1:   
                    scriptExtra = ""
                else:
                    scriptExtra = tags.script(type="text/javascript")[
                        "rollNet(\"%s\");" % iface
                    ]

                block =  tags.table(_class="interfaceTable", cellspacing="0", cellpadding="0")[
                    tags.tr[
                        state,
                        tags.td[
                            tags.img(src='/images/block-minus.png', id='roller%s' % iface, onclick="rollNet('%s')" % iface)
                        ]
                    ],
                    tags.tr[
                        tags.td(style="border-bottom:2px solid #999")[
                            ""
                        ],
                        tags.td(style="border-bottom:2px solid #999")[
                            entities.nbsp, 
                            tags.table[
                                tags.tr[
                                    tags.td['Media: '], tags.td[media]
                                ],
                                tags.tr[
                                    tags.td['IP Address: '], tags.td[tags.invisible(render=tags.directive('ethIP'), data=iface)]
                                ],
                            ]
                        ],
                        tags.td[""]
                    ],
                    tags.tr[
                        tags.td[""],
                        tags.td[
                            tags.div(id="con%s" % iface)[
                                tags.img(src=gra), 
                                tags.br,
                                tags.a(href=netConfig)[
                                    tags.img(src="/images/services-small.png"), " Configure"
                                ]
                            ]
                        ],
                        tags.td[""]
                    ]
                ]
                   
                story.append(block)
                story.append(scriptExtra)
                story.append(tags.br)

            return ctx.tag[
                story
            ]

        return defer.DeferredList(procs).addBoth(ret)
    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2[tags.img(src="/images/dashboard-lg.png")," Dashboard"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[
            ""
        ]

    def render_content(self, ctx, data):
        return ctx.tag[
            ""
        ]
