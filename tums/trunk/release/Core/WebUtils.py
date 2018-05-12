from twisted.internet.defer import deferredGenerator, waitForDeferred as wait
from twisted.internet import reactor, protocol, defer
from twisted.web import client

from twisted.mail import smtp
from Core import confparse
import pycha.pie, pycha.bar, pycha.line
import cairo
import StringIO
import os
import itertools
import time

@deferredGenerator
def system(e):
    from twisted.internet import utils
    #def procResult(e):
    #    return e
    path = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/tcs/tums"
    env = {'PATH':path, 'path':path, 'DEBIAN_FRONTEND':"noninteractive"}
    mq = utils.getProcessOutput('/bin/sh', ['-c', str(e)], env = env, errortoo=1)
    res = wait(mq) 
    yield res
    yield res.getResult()

class ProcessWriter(protocol.ProcessProtocol):
    def __init__(self, inputt):
        self.inputt = inputt
        self.data = ""
        self.error = ""

    def connectionMade(self):
        self.transport.write(self.inputt)
        self.transport.closeStdin()

    def outReceived(self, data):
        self.data += data

    def errReceived(self, err):
        print err
        self.error += err

    def processEnded(self, status):
        rc = status.value.exitCode
        if rc == 0:
            self.deferred.callback(self.data)
        else:
            self.deferred.errback(rc)

def processWriter(command, inputt):
    pw = ProcessWriter(inputt)
    pw.deferred = defer.Deferred()
    
    path = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/tcs/tums"
    env = {'PATH':path, 'path':path, 'DEBIAN_FRONTEND':"noninteractive"}
    cmd = ['/bin/sh', '-c', str(command)]

    p = reactor.spawnProcess(pw, cmd[0], cmd, env=env)

    return pw.deferred

def serviceMap(name):
    serviceMaps = {
        'dhcp':         'dhcp3-server',
        'bind':         'bind9',
        'ddclient':     'ddclient',
        'squid':        'squid',
        'shorewall':    'shorewall',
        'debnet':       'networking',
        'fprobe':       'fprobe-ulog'
    }

    print "Restarting", name
    return serviceMaps.get(name, name)

def restartService(name, either="", init=""):
    def restartNext(_, nserv):
        print _
        return system('/etc/init.d/%s restart' % serviceMap(nserv))

    print "Reconfiguring", name
    de=system('/usr/local/tcs/tums/configurator --%s' % name).addBoth(restartNext, name)

    if name == "debnet":
        return de.addBoth(lambda _: restartService('fprobe').addBoth(lambda _: restartService('dhcp')))
    else:
        return de


def restartNetworking(dhcp=False):
        reloadcmds = [
            '/usr/local/tcs/tums/configurator --bind',
            '/usr/local/tcs/tums/configurator --exim',
            '/usr/local/tcs/tums/configurator --dhcp',
            '/usr/local/tcs/tums/configurator --fprobe',
            '/etc/init.d/exim4 restart',
            '/etc/init.d/bind9 restart',
            '/etc/init.d/fprobe-ulog restart',
            'killall -9 tums-fc',
            '/usr/local/tcs/tums/tums-fc'
        ]

        if dhcp:
            reloadcmds.append('/etc/init.d/dhcp3-server restart')

        return restartService('debnet').addBoth(
            lambda _: restartService('shorewall')
        ).addBoth(
            lambda _: system(';'.join(reloadcmds))
        )


def runIter(run, iterable, padding=None):
    it = iter(iterable)
    while True:
        currentRun = list(itertools.islice(it, run))
        lcr = len(currentRun)
        if lcr == 0:
            break
        yield currentRun + [padding] * (run - lcr)

def serialiseUser(detail, dom):
    vacation = ""
    vacEnable = False
    user, domain = detail['uid'][0], dom
    try:
        vac = open("/var/spool/mail/vacation/%s@%s.txt" % (user, domain), 'r')
        vacation = vac.read()
        vacEnable = True
    except:
        pass # No vacation note

    try:
        vac = open("/var/spool/mail/vacation/DISABLED%s@%s.txt" % (user, domain), 'r')
        vacation = vac.read()
    except:
        pass # No disabled note either.

    sn = detail.get('sn')
    if sn:
        sn = sn[0]
    else:
        sn = ""

    serStruct = {
        'domain'        : dom,
        'name'          : detail['uid'][0],
        'uid'           : detail.get('uidNumber', [1000])[0],
        'gid'           : detail.get('gidNumber', [1000])[0],
        'cn'            : detail.get('cn', [''])[0],
        'sn'            : sn,
        'giveName'      : detail.get('givenName', [''])[0],
        'emp'           : '+'.join(detail.get('employeeType', [])), # Can have multiple values here.
        'password'      : detail.get('userPassword', [''])[0],
        'mail'          : detail.get('mail', [''])[0],
        'active'        : detail.get('accountStatus', [''])[0],
        'pgSid'         : detail.get('sambaPrimaryGroupSID', [''])[0],
        'samSid'        : detail.get('sambaSID', [''])[0],
        'ntPass'        : detail.get('sambaNTPassword', [''])[0],
        'lmPass'        : detail.get('sambaLMPassword', [''])[0],
        'mailForward'   : '+'.join(detail.get('mailForwardingAddress', [])),
        'mailAlias'     : '+'.join(detail.get('mailAlternateAddress', [])),
        'vacation'      : vacation,
        'vacEnable'     : vacEnable
    }

    # Construct our flags.
    flags = []
    # Order is important from here on
    thisFlag = False
    for i in os.listdir('/etc/openvpn/keys/'):
        if "%s.%s" % (serStruct['name'], dom) in i and "key" in i:
            thisFlag = True
    flags.append(thisFlag)

    # FTP Enabled
    thisFlag = False
    if detail.get('loginShell'):
        if '/bin/bash' in detail['loginShell'][0]:
            thisFlag = True
    flags.append(thisFlag)

    # We need a config parser
    sysconf = confparse.Config()
    thisFlag = False
    # FTP Global
    if  sysconf.FTP.get('globals'):
        if serStruct['name'] in sysconf.FTP['globals']:
            thisFlag = True
    flags.append(thisFlag)

    address = "%s@%s" % (serStruct['name'], dom)
    copyto = ""
    if sysconf.Mail.get('copys', []):
        for addr, dest in sysconf.Mail['copys']:
            if addr == address:
                copyto = dest
    flagSer = ""
    for i in flags:
        flagSer += i and '-' or '_'
    flagSer += "+" + copyto

    serStruct['flags'] = flagSer
    
    x = ""
    for k,v in serStruct.items():
        x += "%s:%s`" % (k,v)
    
    return x

def createChart(config):
    """ A generic method that returns a PDF file (as a StringIO object) 
        from a set of complicated config obtions """
    width = int(config['width'][0])
    height = int(config['height'][0])
    ok = False

    if config['type'][0] in ['pie', 'line', 'line2']:
        # Create our options
        options = {
            'axis': {
                'x': {
                    'ticks': [dict(v=i, label=d) for i,d in enumerate(config.get('lables', ['None']))],
                },
                'lineColor': '#999999',
                'lineWidth': 0.5
            },
            'padding': {
                'left': 25,
                'bottom': 25
            },
            'colorScheme': '#f47a07'
        }
        if config.get('xticks'):
            options['axis']['x']['tickCount'] = int(config['xticks'][0])

        if config.get('ylab'):
            options['axis']['y'] = {
                'label': config['ylab'][0],
                'rotate': 25,
                'tickCount': 8, 
                'tickPrecision': 0.1
            }
 
        # Right aligned legend
        if config.get('legright'):
            options['legend'] = {
                'position': {
                    'left':width+5
                },
            }
            options['padding']['right'] = 220
            width += 220


    if config['type'][0] == "pie":
        data = [
            (l, [[0, int(d)]])

        for l,d in zip(config.get('lables', ["None"]), config.get('data', ['1']))]

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        chart = pycha.pie.PieChart(surface, options)

        chart.addDataset(data)
        chart.render()

        ok = True

    if config['type'][0] == "line":
        sets = config.get('set', ["None"])
        setData = config.get('data', ['0'])

        data = []
        for set, setname in enumerate(sets):
            data.append((
                setname,
                [ (i, float(l)) for i,l in enumerate(setData[set].split()) ]
            ))

        options['axis']['x']['rotate'] = 25
        
        # Adjust padding for bar graph
        options['padding']['left'] = 50
        options['padding']['bottom'] = 50

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        chart = pycha.bar.VerticalBarChart(surface, options)

        chart.addDataset(data)
        chart.render()

        ok = True

    if config['type'][0] == "line2":
        if config.get('layout', [''])[0] == 'tight':
            options['padding'] = {
                'bottom':25, 
            }
            options['legend'] = {
                'hide': True
            }

        sets = config.get('set', ["None"])
        setData = config.get('data', ['0'])

        data = []
        for set, setname in enumerate(sets):
            data.append((
                setname,
                [ (i, float(l)) for i,l in enumerate(setData[set].split()) ]
            ))

        #options['axis']['x']['rotate'] = 25

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        chart = pycha.line.LineChart(surface, options)

        chart.addDataset(data)
        chart.render()

        ok = True
 
    if ok:
        out = StringIO.StringIO()
        surface.write_to_png(out)
        out.seek(0)
        return out
    
    return ok

def updateASCache(ipr, asn):
    l = open('/usr/local/tcs/tums/ascache', 'at')
    l.write('%s:%s\n' % (ipr, asn))
    l.close()

def getASn(ipr):
    pass

def updateNCache(ip, name):
    l = open('/tmp/ncache', 'at')
    now = time.time()
    l.write('%s:%s:%s\n' % (ip, name, now))
    l.close()

def logToEpoch(logtime):
    return time.mktime(time.strptime(logtime+time.strftime(' %Y'), '%b %d %H:%M:%S %Y'))

def getUsername(ip):
    # Get the username for a specific IP at an instantaneous time
    # This does NOT give back stats
    if ip == "0.0.0.0":
        return "0.0.0.0"

    # Cache 
    if os.path.exists('/tmp/ncache'):
        cache = open('/tmp/ncache')
        for i in cache:
            if ip in i:
                l = i.strip('\n').split(':')
                now = time.time()
                then = float(l[2])
                if now < (then + 3600):
                    return l[1]

    # Quickest, check CAPORTAL 
    if os.path.exists('/tmp/caportal/%s' % ip):
        # We do have this
        l = open('/tmp/caportal/%s' % ip).read().split('|')
        if '@' in l[-1]:
            n = l[-1]
        else:
            import Settings
            n = '%s@%s' % (l[-1], Settings.defaultDomain)

        updateNCache(ip, n)
        return n

    sysconf = confparse.Config()
    if sysconf.DHCP.get('leases', {}).get(ip):
        return sysconf.DHCP.get('leases', {}).get(ip)[0]

    def parseNmb(lookup):
        l = lookup.strip('\n').strip()
        name = ip
        if l:
            name = l
            updateNCache(ip, l)
        return name

    def checkMail(mail):
        l = mail.strip('\n').strip()
        name = None
        if l:
            now = time.time()
            then = logToEpoch(' '.join(l.split()[:3]))
            if now < (then + 3600):
                # We can use the email address, yay
                n = l.split('user=')[-1].split(',')[0]
                return n 
                        
        return system("nmblookup -A %s | grep '<00>' | grep -v '<GROUP>' | awk '{print $1}'" % ip).addBoth(parseNmb)

    def parseSamba(sessions):
        name = None
        for i in sessions.split('\n'):
            if ip in i:
                l = i.split('\\')
                name = l[1]
                updateNCache(ip, name)
                # immediate return 
                return name
        # Find mail
        return system("grep '@.*%s' /var/log/mail.log | grep 'LOGIN,' | tail -n 1" % ip).addBoth(checkMail)
        
    # Try samba
    return system('net status sessions parseable').addBoth(parseSamba)


def refreshBranches(sysconf):
    bserv = sysconf.Mail.get('branches', [])
    if not bserv:
        # Nothing configured
        return True

    def serverFail(failure, server):
        print server, "failed", failure
        return server, None

    def serverGotData(data, server):
        # Not authorised :(
        if "Access Denied" in data:
            print server, "Access denied"
            return server, False

        return server, data.split('\n')

    defers = []
    for r in bserv:
        if isinstance(r, list):
            # Handle our old datastructure a well for now - remove this in later versions
            server,relay = r
        else:
            server = r 

        defers.append(  
            client.getPage(
                'http://%s:9681/handlesMailFor' % server
            ).addCallback(
                serverGotData,
                server
            ).addErrback(
                serverFail,
                server
            )
        )

    def done(res):
        print "Exim restarted", res
        return True
    def finishedChecking(dlistResult):
        M = sysconf.Mail
        btopo = M.get('branchtopology', {})

        sysChange = False # Flags a change to the system - restart exim etc
        servers = []
        for status, r in dlistResult:
            server, result = r
            servers.append(server)
            if result == None:
                continue

            if result == False:
                # Server is not authorising us (different to connection failure!) 
                # remove it from our topology
                if server in btopo:
                    sysChange = True
                    del btopo[server]

                continue

            # If we assume consistency of the list order, we can derive equality 
            # between our storage and the other server

            if server in btopo:
                if btopo[server] != result:
                    sysChange = True
                    btopo[server] = result
            else:
                sysChange = True
                # Store this branch
                btopo[server] = result

        for svr in btopo.keys():
            if svr not in servers:
                sysChange = True
                del btopo[svr]

        if sysChange:
            print "New topology", btopo
            # Save config if it has changed.
            M['branchtopology'] = btopo
            sysconf.Mail = M

            # Reconfigure exim and restart it
            return system('/usr/local/tcs/tums/configurator --exim; /etc/init.d/exim4 restart').addBoth(done)

        return True

    # Return our list of results to a final callback for processing
    return defer.DeferredList(defers).addBoth(finishedChecking)

def getUsers():
    """Get the users in our default tree, returns a list of email addresses"""
    import Settings, LDAP

    l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
    dc = "%s,o=%s" % (LDAP.domainToDC(Settings.defaultDomain), Settings.LDAPBase)

    # Hammer it a bit
    d, v = 0, None
    while (not v and d < 3):
        v = LDAP.searchTree(l, dc, 'uid=*', [])
        d += 1


    addrs = []

    for i in v:
        path, detail = i[0]
        if "ou=People" not in path:
            continue

        if "uid=root" in path:
            # Ignore the root user
            continue
        if "uid=nobody" in path:
            # Ignore nobody
            continue

        addr = detail['mail'][0]
        if addr not in addrs:
            addrs.append(addr)

    return addrs

