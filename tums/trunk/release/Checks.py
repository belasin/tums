from Core import WebUtils, Utils, confparse, PageHelpers
import LDAP, Settings
from twisted.internet import task, reactor, defer

from twisted.web import client

import os, cPickle, time, datetime

class SelfChecker(object):
    checkers = [
        (5*60, 'branchmail', 0), 
        (5*60, 'perfdata', 1),
        (5*60, 'eximstats', 1),
        (5*60, 'clam', 1),
        (5*60, 'mailq', 1),
        (5*60, 'df', 1),
        (5*60, 'version', 1),
        (60*60, 'profiles', 1),
        (60*60, 'users', 1),
        #(12*60*60, 'updates'),
        (12*60*60, 'disks', 1),
        (24*60*60, 'system', 1),
        (24*60*60, 'mysql', 0),
        (5*60, 'fprobe', 0),
        (5*60, 'iftraf', 0),
        (5*60, 'ndrkiller', 0), 
        (5*60, 'maildiversity', 1), 
        (24*60*60, 'logrotate', 0), 
        (1*60*60, 'vacations', 0)
    ]

    def __init__(self, handler, tstat):
        self.loops = {}
        self.tstat = tstat 
        self.handler = handler
        self.alerts = {}
        self.lastClam = ""
        self.sysconf = confparse.Config()
        self.thivechecker = None

        self.iftraf = {} # Running totals
        self.ifdisp = {} # Last value

    def check_vacations(self):
        validities = [v for v in os.listdir('/var/mail/vacation') if v[-9:] == '.validity']

        today = datetime.date.today()

        for k in validities:
            nportion = k[:-9]
            vdate = open('/var/mail/vacation/%s' % k).read().strip('\n')
            d = datetime.date(*[int(i) for i in vdate.split('-')])

            if d == today:
                # Disable vacation note
                try:
                    os.rename('/var/mail/vacation/%s.txt' % nportion, '/var/mail/vacation/DISABLED%s.txt' % nportion)
                    os.remove('/var/mail/vacation/%s.log' % nportion)
                    os.remove('/var/mail/vacation/%s.db' % nportion)
                    os.remove('/var/mail/vacation/%s' % k)
                except Exception, e:
                    print "Problem", e
                print "[CHECKERS] Disabled vacation note for", nportion 

    def check_logrotate(self):
        rotators = os.listdir('/etc/logrotate.d')

        for rotator in rotators:
            if "ucf-dist" in rotator:
                print "[CHECKERS] Clearing bad log rotator", rotator
                os.remove(os.path.join('/etc/logrotate.d', rotator))
            if "exim4-paniclog" in rotator:
                print "[CHECKERS] Clearing bad log rotator", rotator
                os.remove(os.path.join('/etc/logrotate.d', rotator))

    def check_ndrkiller(self):
        def dumpOutput(_):
            if _.strip('\n'):
                print _
        return WebUtils.system('mailq | grep "<> \\*\\*\\* frozen \\*\\*\\*" | awk \'{print $3}\' | xargs exim -Mrm 2>/dev/null').addCallback(dumpOutput)
        
    def check_iftraf(self):
        """ Gets interface traffic """
        def ifck(iface):
            return "%s-%s" % (datetime.datetime.now().day, iface)

        # Clean keys to prevent memory leaks
        day = datetime.datetime.now().day

        keySet = self.iftraf.keys()
        for key in keySet:
            d, iface = key.split('-')
            if int(d) != day:
                del self.iftraf[key]

        for iface, vals in Utils.getIFStat().items():
            ifchk = ifck(iface)
            if ifchk not in self.iftraf:
                try:
                    datee = datetime.datetime.now()
                    l = open('/usr/local/tcs/tums/rrd/iface_%s_%s-%s-%s-total.nid' % (iface, datee.day, datee.month, datee.year))
                    vi, vo = l.read().strip('\n').split(':')
                    self.iftraf[ifchk] = [float(vi), float(vo)]
                except Exception, e:
                    print e, "no NID"
                    self.iftraf[ifchk] = [0,0]

            tin, tout = vals

            if self.ifdisp.get(iface):
                oin, oout = self.ifdisp[iface]
               
                if (tin+tout) >= (oin+oout):
                    nin = tin - oin
                    nout = tout - oout
                else:
                    # Counter reset
                    nin = tin
                    nout = tout

                if (nin+nout) > 0:
                    self.iftraf[ifchk][0] += nin
                    self.iftraf[ifchk][1] += nout

                    datee = datetime.datetime.now()
                    l = open('/usr/local/tcs/tums/rrd/iface_%s_%s-%s-%s-total.nid' % (iface, datee.day, datee.month, datee.year), 'wt')
                    l.write('%s:%s' % (self.iftraf[ifchk][0], self.iftraf[ifchk][1]))
                    l.close()
 
            self.ifdisp[iface] = (tin, tout)
            
            
    def check_branchmail(self):
        """ Does a branch-mail merge"""
        return WebUtils.refreshBranches(self.sysconf)

    def check_disks(self):
        """ Checks the raid status and reports back to Thebe """
        try:
            mdstat = open('/proc/mdstat')
        except IOError:
            mdstat = []
            #do some warning!
            pass
        pers = []
        thismd = ""
        mds = {}
        for i in mdstat:
            if "Personalities" in i:
                pers = i.split(':')[-1].replace('[', '').replace(']', '').split()
            elif "md" in i:
                # New md 
                thismd = i.split(':')[0].strip()
                b = i.split(':')[-1].split()
                mds[thismd] = {
                    'state': b[0],
                    'type' : b[1],
                    'disks' : b[2:]
                }
            elif "unused devices" in i:
                pass
            elif i.strip(): # non blank undecided line
                if 'blocks' in i:
                    state = []
                    for j in i.strip().split()[3].replace('[', '').replace(']', ''): # [UU]
                        if j == 'U':
                            state.append(True)
                        else:
                            state.append(False)
                    mds[thismd]['online'] = state
                elif 'speed' in i:
                    # A rebuild...
                    l = i.strip().split()
                    state = l[1]
                    fin = l[3]
                    mds[thismd]['state'] = "%s %s" % (state, fin)
                    
        self.handler.sendMessage(self.handler.master.hiveName, "raids::%s" % repr(mds))

    def check_version(self):
        """ Update our version with Thebe """
        ver = PageHelpers.VERSION
        self.handler.sendMessage(self.handler.master.hiveName, "tumsversion:%s:1" % (ver))

    def sendPerfdata(self, rectype, recdata):
        now = int(time.time())
        self.handler.sendMessage(self.handler.master.hiveName, "perfdat:%s %s:%s" % (rectype, now, recdata))

    def check_perfdata(self):
        """ Check performance data (Load average, IO and interface rates) """
        def continueParse(vmstat):
            # Read off /proc/net/dev
            it = Utils.getIFStat()
            str = ','.join(["%s:%s:%s" % (i[0], i[1][0], i[1][1]) for i in it.items()])
            self.sendPerfdata('ifaces', str)
            # Read off uptime and IO

            l = open('/proc/loadavg').read()
            loads = l.split()

            # Proccess our vmstat output
            vms = vmstat.split('\n')[2].split()

            str = "%s:%s:%s:%s:%s" % (loads[0], loads[1], loads[2], vms[8], vms[9])
            self.sendPerfdata('ioload', str)
        return WebUtils.system('vmstat').addCallback(continueParse)

    def check_mysql(self):
        # Scratch around for dead MySQL tables and automaticaly repair them 
        # (probably reasonable to just auto repair all tables we need)
        pass

    def check_fprobe(self):
        """ Checks to see that fprobe is running """

        def checkproc(ps):
            if "/usr/sbin/fprobe-ulog" in ps:
                return True

            else:
                return WebUtils.system('/etc/init.d/fprobe-ulog start').addBoth(checkproc)

        return WebUtils.system('ps aux | grep fprobe-ulog | grep -v grep').addBoth(checkproc)

    def check_eximstats(self):
        """ Build exim mail rate stats and send to Thebe"""
        def continueParse(eximstat):
            st = eximstat.split('\n')
            received = 0 
            deliver = 0 
            reject = 0 

            try:
                received = int(st[1].split()[2])
                deliver = int(st[2].split()[2])
                reject = int(st[3].split()[1])
            except:
                # some hosts do not provide reject stats or are not busy enough
                pass

            str = "%s:%s:%s" % (received, deliver, reject)
            self.sendPerfdata('eximstat', str)

        return WebUtils.system('eximstats -txt -nr -ne -nt /var/log/exim4/mainlog | head -n 11 | tail -n 5'
                ).addCallback(continueParse)

    def sendAlert(self, text, t=None, sub= ""):
        if t:
            if self.alerts.get(t):
                return 
            else:
                self.alerts[t] = True
        mailto = self.sysconf.General.get('notify', ['alert@thusa.co.za'])

        if sub:
            subject = "%s from %s" % (sub, self.sysconf.ExternalName)
        else:
            subject = "Vulani critical alert from %s" % self.sysconf.ExternalName

        print mailto

        for to in mailto:
            Utils.sendMail('notify@%s' % self.sysconf.Domain, [to], subject, text, server='mx3.thusa.net', importance = 'high')

        # Log it 
        l = open('/var/log/tums-eventlog.log', 'at')
        l.write("[%s] %s\n" % (time.ctime(), text))
        l.close()

    def sendThebeAlert(self, rectype, recdata):
        if self.alerts.get(rectype):
            return 
        else:
            self.alerts[rectype] = True
        now = int(time.time())
        self.handler.sendMessage(self.handler.master.hiveName, "alertlog:%s %s:%s" % (rectype, now, recdata))

    def clearThebeAlert(self, rectype, recdata):
        now = int(time.time())
        self.handler.sendMessage(self.handler.master.hiveName, "alertlog:%s_cleared %s:%s" % (rectype, now, recdata))

    def check_clam(self):
        """ Checker for clamav errors in mail log """
        def parse(main):
            if "clamd: unable to connect to UNIX socket" in main:
                # Have exception
                # Store the last occurrence
                lastClam = self.lastClam
                for i in main.split('\n'):
                    if "socket" in i:
                        lastClam = i[:19] # store the date

            if "clamd: unable to connect to UNIX socket" in main:
                # Trigger the event on first time.
                if not self.alerts.get('clam'):
                    #self.lastClam = lastClam # Store this checkpoint
                    def checkproc(ps):
                        if 'clamd' in ps:
                            # Clamd was always running... 
                            self.alerts['clamrun'] = True
                            self.sendAlert("A critical failure has occurred in the mail system. ClamAV is running but Exim can't find the socket. I can't recover from this error on my own.",'clam')
                            self.sendThebeAlert('clamrun', '1')
                        else:
                            self.alerts['clamrun'] = False
                            # Alert is new, clamd is dead - disable clamav
                            self.sendAlert("A critical failure has occured in the mail system. ClamAV appears to be broken!",'clam')
                            self.sendThebeAlert('clamrun', '2')

                    WebUtils.system('ps aux | grep clamd | grep -v grep').addBoth(checkproc)
            elif self.alerts.get('clam'):
                # Check our status
                def restart(ps):
                    if 'clamd' in ps:
                        self.sendAlert("ClamAV appears to have been restored.", t=None,sub = "ClamAV restored")
                        self.clearThebeAlert('clamrun', '')
                
                if self.alerts.get('clamrun'):
                    # This error clears if mail is delivering ok
                    self.alerts['clam'] = False
                    self.sendAlert("ClamAV appears to have been fixed - error state cleared.", t=None,sub = "ClamAV restored")
                    self.clearThebeAlert('clamrun', '')
                else:
                    # This error only clears when clamd is back
                    self.alerts['clam'] = False
                    WebUtils.system('ps aux | grep clamd | grep -v grep').addBoth(restart)
 
        return WebUtils.system('tail -n 10 /var/log/exim4/mainlog | grep "clamd: unable to connect to UNIX socket"').addBoth(parse)

    def check_mailq(self):
        """ Checker for ludicrous mail queues """
        def parse(queue):
            try:
                vol, size = queue.replace('\n', '').strip().split()[:2]
                if size[:-2] != '': 
                    bsize = int(size[:-2])
                else:
                    bsize = 0 
            except:
                self.sendAlert("System PERM_EXTRASPECIAL error. Server has no exim!", 'vol3')
                return
            if int(vol) > 400:
                self.sendAlert("Large mail backlog detected. %s messages await delivery with a volume of %s" % (vol, size), 'vol1', sub="Vulani notice mq=%s " % vol)
                return 
            if size[-2:] == "KB":
                bsize = bsize * 1024
            if size[-2:] == "MB":
                bsize = bsize * 1024 * 1024
            if size[-2:] == "GB":
                bsize = bsize * 1024 * 1024 *1024
            else:
                bsize = bsize
            
            self.sendPerfdata('mailqueue', "%s %s" % (bsize, vol))
            if bsize > 104857600: # 100 MB.
                self.sendAlert("Large mail backlog detected. Queue size has reached %s with %s messages" % (size, vol), 'vol2', sub="Vulani notice mqs=%s " % size)
                return
            self.alerts['vol1'] = False
            self.alerts['vol2'] = False

        return WebUtils.system('mailq | exiqsumm | tail -n 2').addBoth(parse)

    def check_maildiversity(self):
        def parse(queue):
            n = queue.split('\n')
            doms = len(n)
            
            if doms > 100:
                self.sendAlert("Large queue diversity detected. %s domains await delivery" % doms, 'vol6', sub="Vulani alert - queue diversity %s > 100" % doms)
            else:
                self.alerts['vol6'] = False

        return WebUtils.system('mailq | exiqsumm | head -n -3 | tail -n +5').addBoth(parse)

    def check_df(self):
        def continueParse(df):
            devs = []
            err = False
            for i in df.split('\n'):
                try:
                    l = i.split()
                    if self.sysconf.General.get('diskalert', None):
                        if l[5] in self.sysconf.General['diskalert']:
                            level = self.sysconf.General['diskalert'][l[5]]
                            if type(level) is int:
                                # Use a percentage use
                                if int(l[4].strip('%')) > level:
                                    self.sendAlert("Disk utilisation on %s has exceeded threshold of %s%% - current usage is %s" % (l[5], level, l[4]), 'df')
                                    err = True
                            else:
                                lev = level[:-1]
                                unit = level[-1].upper()
                                if unit == "M":
                                    level = lev * 1024
                                elif unit == "G":
                                    level = lev * 1024 * 1024

                                if int(l[3]) < level:
                                    self.sendAlert("Disk freespace on %s has gone below %sK - current space is %sK" % (l[5], level, l[3]),'df')
                                    err=True
                            
                    devs.append("%s:%s:%s:%s" % (l[0], l[5], l[1], l[3]))
                except:
                    pass # Not the right type of line..

            self.alerts['df'] = err
            str = ';'.join(devs)
            self.sendPerfdata('diskstat', str)
        return WebUtils.system('df | grep "^/dev/"').addCallback(continueParse)

    def check_system(self):
        # Tells HIVE what system we are every now and then
        systype = "Debian"
        
        self.handler.sendMessage(self.handler.master.hiveName, "systype::%s" % (systype))

    def check_users(self):
        """ Push all our users into Thebe """
        l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
        dc = "o=%s" % (Settings.LDAPBase)

        d, v = 0, None
        while (not v and d < 3):
            v = LDAP.searchTree(l, dc, 'uid=*', [])
            d += 1

        # Get the count of useful entries to pass with burst header
        num = 0
        for i in v:
            path, detail = i[0]
            if "ou=People" in path:
                num += 1

        print "[CHECKERS] New burst"
        def Burst(_):
            print "[CHECKERS] Burst start", _
            for i in v:
                path, detail = i[0]
                if "ou=People" not in path:
                    continue
                dom = path.split(',o=')[0].split('ou=People,dc=')[-1].replace(',dc=', '.')

                x = WebUtils.serialiseUser(detail, dom)
                    
                # create a mail resource locator
                mail = "%s@%s" % (detail['uid'][0], dom)
                print "[CHECKERS] User check:", mail
                self.handler.sendMessage(self.handler.master.hiveName, "user:%s:%s" % (mail, x))

            # soften this
            reactor.callLater(2, self.handler.sendMessage, self.handler.master.hiveName, "usernoburst:+:+")

        d = self.handler.callRemote(self.handler.master.hiveName, "userburst:%s:+" % num)
        return d.addCallback(Burst)

    def check_updates(self):
        print "[CHECKERS] Checking updates"
        WebUtils.system('aptitude update')

        def sendPackageNames(names):
            for name in names.replace('\n', ' ').split():
                self.handler.sendMessage(self.handler.master.hiveName, 
                    "newupdate:%s:--" % (name))
        
        r = WebUtils.system(
                'debsecan --only-fixed --suite etch --format packages'
        )

        return r.addCallback(sendPackageNames)


    def check_profiles(self):
        # Sends our current profiles to the server ever few hours...
        params  = "CompanyName ExternalName Hostname Domain SambaDomain LDAPBase LDAPPassword LANPrimary WANPrimary "
        params += "ThusaDNSUsername ThusaDNSPassword ThusaDNSAddress NTP SMTPRelay LocalRoute "
        params += "EthernetDevices WANDevices Shorewall SambaConfig SambaShares ProxyConfig Mail Shaping DHCP Failover Tunnel BGP FTP RADIUS "
        params += "ForwardingNameservers TCSAliases LocalDomains ShorewallBalance ShorewallSourceRoutes "
        params += "ProxyAllowedHosts ProxyAllowedDestinations ProxyAllowedDomains ProxyBlockedDomains ShaperRules Backup"

        paramL = params.split()

        for conf in os.listdir('profiles'):
            if conf[-3:] == ".py":
                l = open('profiles/' + conf).read()
                    
                myLocals = {}
                confDict = {}
                exec l in myLocals

                for i in paramL:
                    confDict[i] = myLocals[i]

                pickle = cPickle.dumps(confDict)
                self.handler.sendMessage(self.handler.master.hiveName, "config:%s:%s" % (conf[:-3],pickle))

    def recheckChecker(self):
        if self.tstat.state:
            for checkDelay, checker, reqThive in self.checkers:
                if reqThive:
                    fn = getattr(self, 'check_%s' % checker)
                    self.loops[checker] = task.LoopingCall(fn)
                    self.loops[checker].start(checkDelay, now=True)
            print "[CHECKERS] Started THIVE checkers"    
            self.thivechecker.stop()

    def startCheckers(self):
        print "[CHECKERS] Starting checkers"
        for checkDelay, checker, reqThive in self.checkers:
            if reqThive:
                # Requires thive to be running
                continue
            fn = getattr(self, 'check_%s' % checker)
            self.loops[checker] = task.LoopingCall(fn)
            self.loops[checker].start(checkDelay, now=True)

        self.thivechecker = task.LoopingCall(self.recheckChecker)
        self.thivechecker.start(60, now=True)
