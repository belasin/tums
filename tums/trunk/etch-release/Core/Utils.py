""" A utilities library """
import os, socket, fcntl, struct, array, smtplib, time, sys, traceback, math
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
from Core import confparse
import telnetlib
import itertools
import time
import base64

def runIter(run, iterable, padding=None):
    it = iter(iterable)
    while True:
        currentRun = list(itertools.islice(it, run))
        lcr = len(currentRun)
        if lcr == 0:
            break
        yield currentRun + [padding] * (run - lcr)


class Log:
    filename = '/var/log/tums-audit.log'
    def __init__(self):
        try:
            self.fp = open(self.filename, 'at')
        except:
            self.fp = None

    def msg(self, *a):
        msg = "%s %s\n" % (time.strftime('%Y %b %d %H:%M:%S'), ' '.join(a))
        if self.fp:
            self.fp.write(msg)
            self.fp.flush()
        else:
            print msg

log = Log()


class SetDefaults:
    BaseDir = '/usr/local/tcs/tums'

try:
    import Settings
except:
    Settings = SetDefaults()

months = {
    1: 'January',
    2: 'February', 
    3: 'March',
    4: 'April',
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September',
    10: 'October',
    11: 'November',
    12: 'December',
}

portCache = {}

   

def humanReadableTimeDelta(delta):
    """
    Convert a C{datetime.timedelta} instance into a human readable string.
    Copyright (C) Jonathan Jacobs 
    """
    days = delta.days
 
    seconds = delta.seconds
 
    hours = seconds // 3600
    seconds -= hours * 3600
 
    minutes = seconds // 60
    seconds -= minutes * 60
 
    def makeText(s, value):
        if value == 1:
            s = s[:-1]
        return s % (value,)
 
    def getParts():
        if days:
            yield makeText(u'%d days', days)
        if hours:
            yield makeText(u'%d hours', hours)
        if minutes:
            yield makeText(u'%d minutes', minutes)
        if seconds:
            yield makeText(u'%d seconds', seconds)
 
    parts = list(getParts())
    if not parts:
        parts = [u'never']
 
    return u' '.join(parts)

def insertBeforeLine(s, before, what, repeat = False):
    lp = s.split('\n')
    newl = []
    done = False
    for i in lp:
        if before in i and not done:
            newl.append(what)
            done = not repeat
        newl.append(i)

    return '\n'.join(newl)

def insertAfterLine(s, after, what, repeat = False):
    lp = s.split('\n')
    newl = []
    done = False
    for i in lp:
        if after in i and not done:
            newl.append(i)
            newl.append(what)
            done = not repeat
        else:
            newl.append(i)

    return '\n'.join(newl)

def insertBeforeBlock(s, pattern, what, repeat = False):
    if repeat:
        lp = s.split(pattern)
    else:
        lp = s.split(pattern, 1)

    newblock = what+pattern
    return newblock.join(lp)

def insertAfterBlock(s, pattern, what, repeat = False):
    if repeat:
        lp = s.split(pattern)
    else:
        lp = s.split(pattern, 1)

    newblock = pattern+what
    return newblock.join(lp)

def currentProfile():
    try:
        l = open('/usr/local/tcs/tums/currentProfile')
    except:
        return ("Default", "default.py")
    i = l.read().replace('\n', '').strip() 
    name = i[:-3].replace('_', ' ').capitalize()
    return (name, i)

def runningProfile():
    try:
        l = open('/usr/local/tcs/tums/runningProfile')
    except:
        return ("Default", "default.py")
    i = l.read().replace('\n', '').strip() 
    name = i[:-3].replace('_', ' ').capitalize()
    return (name, i)

def lookupIp(ip):
    # Try look in the leases config first
    conf =  __import__('config')
    leases = conf.DHCP.get('leases', {})
    for lip, hostmac in conf.DHCP.get('leases', {}).items():
        host, mac = hostmac
        if lip == ip:
            return host

    from twisted.names import client
    def res(lookup):
        name = str(lookup[0][0].payload.name)
        # Take away our common domain and strip any residual dots
        return name.replace(Settings.defaultDomain, '').strip('.')

    def failure(eek):
        return ip

    def ipToPtr(ip):
        return "%s.in-addr.arpa" % '.'.join([i for i in reversed(ip.split('.'))])

    return client.lookupAddress(ipToPtr(ip)).addCallbacks(res, failure)

def renameIf(iface):
    return iface

def getIFStat():
    ps = open("/proc/net/dev")

    results = {}

    for ln in ps:
        line = ln.strip()
        if "ppp" in line or "eth" in line or "tap" in line:
            bits = line.split(':')[-1].split()
            ipin = float(bits[0])
            ipout = float(bits[8])
            iface = line.split(':')[0]
            if "eth" in iface:
                num = iface.strip('eth')
            if "ppp" in iface:
                num = iface.strip('ppp')
            if iface!="lo":
                results[iface] = (ipin, ipout)

    ps.close()

    return results

def getMAC(ip):
    lf = open('/proc/net/arp')
    for i in lf:
        if ip in i:
            return i.split()[3].lower()

    # Try look in the leases config
    conf =  __import__('config')
    leases = conf.DHCP.get('leases', {})
    mac = conf.DHCP.get('leases', {}).get(ip, None)
    if mac:
        return mac[1]

    return None # Didn't find one

def getIpFromMac(mac):
    lf = open('/proc/net/arp')
    for i in lf:
        if mac.lower() in i.lower():
            return i.split()[0]

    conf =  __import__('config')
    leases = conf.DHCP.get('leases', {})
    for ip, hostmac in conf.DHCP.get('leases', {}).items():
        host, lmac = hostmac
        if lmac == mac:
            return ip

    return None # Didn't find one

def resolvePort(port):
    """Get the canonical ARIN name for a port"""
    if not portCache: 
        ports = open('/etc/services', 'r')
        for ln in ports:
            l = ln.strip()
            if l and l[0] != "#":
                defn = l.split()
                portCache[int(defn[1].split('/')[0])] = defn[0]
        portCache[9680] = 'Thusa Thebe'
        portCache[9682] = 'Thusa TUMS'
        portCache[9682] = 'Thusa NetFlow Concentrator'
        portCache[65535] = 'Unknown Services*'
    
    return portCache.get(port, str(port))

def getDf():

    mtab = open('/etc/mtab')

    fs = []

    for mount in mtab:
        if mount[0] != '/':
            # Not interesting
            continue

        node, point = mount.split()[:2]

        stat = os.statvfs(point)

        disk_total = (stat.f_blocks * stat.f_frsize)/1024.0
        disk_free = (stat.f_bfree * stat.f_frsize)/1024.0
        disk_consumed = disk_total-disk_free
        percentage_consumed = math.ceil((disk_consumed/disk_total)*100)

        fs.append((
            point, 
            node, 
            int(disk_total),
            int(disk_free),
            int(disk_consumed),
            int(percentage_consumed)
        ))
     
    return fs

def exceptionOccured(e):
    text = traceback.format_exc()
    print text
    sendMail("%s <tums@thusa.net>" % Settings.LDAPOrganisation, ["colin@thusa.co.za"], "TUMS Error", text)
    #raise e

def intToH(bytes):
    prefix = ['PB', 'TB', 'GB', 'MB', 'KB', 'B']
    val = bytes
    while val > 1000 and len(prefix)>1:
        val = val/1000.0
        prefix.pop()
    
    return "%0.2f%s" % (val, prefix[-1])

def intToHBnormal(bytes, nofloat=False):
    prefix = ['PB', 'TB', 'GB', 'MB', 'KB', 'B']
    val = bytes
    while val > 1024 and len(prefix)>1:
        val = val/1024.0
        prefix.pop()
        
    if nofloat:
        return "%s%s" % (int(math.ceil(val)), prefix[-1])
    return "%0.2f%s" % (val, prefix[-1])

def reconfigure(plug):
    """Call a reconfigure action for a plugin """
    os.system(Settings.BaseDir+'/configurator --%s' % plug)

def writeConf(conf, data, comsymbol):
    """ Writes a config file - not very usefull but modularises stuff"""
    l = open(conf, 'wt')
    if comsymbol:
        l.write(comsymbol + '# Generated by Vulani Configurator http://vulani.net on %s \n' % time.ctime())
    l.write(data)
    l.close()

def sendMail(send_from, send_to, subject, text, files=[], server="127.0.0.1", html=False, importance = None):
    """Sends an email"""
    assert type(send_to)==list
    assert type(files)==list

    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    if importance:
        msg['Importance'] = importance

    if html:
        msg.attach(MIMEText(text, 'html'))
    else:
        msg.attach(MIMEText(text))

    for f in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload( open(f,"rb").read() )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
        msg.attach(part)

    from twisted.mail import smtp

    def finished(_):
        print "Mail sent", _
        return True
    # Clean realFrom
    if "<" in send_from:
        realFrom = send_from.split('<')[-1].split('>')[0]
    else:
        realFrom = send_from
    return smtp.sendmail(server, realFrom, [send_to], msg.as_string())
    #.addCallbacks(finished, finished)


def getInterfaces():
    """ Returns machine interfaces """

    nlist = []
    l = open('/proc/net/dev')
    for i in l:
        if ':' in i:
            devname = i.split(':')[0].strip()
            if len(devname) == 4:
                if devname in ['sit0']:
                    continue
                nlist.append(devname)
    l.close()
    return nlist

def yesno(bool):
    """Returns C(str) 'yes' for bool value of True and 'no' for False"""
    return (bool and "yes") or "no"

def parseNet():
    """ Returns our configurator network information """
    conf = confparse.Config()
    return conf.EthernetDevices

def buildNet(net):
    """ Builds a network configuration """
    out = ""
    for key in net.keys():
        if type(net[key]) is list:
            out += "%s=(\n" % (key,)

            for l in net[key]:
                out += '    "%s"\n' % (l,)

            out += ")\n\n"
        else:
            out += '%s="%s"\n\n' % (key, net[key])

    return out

def getNetwork(ip):
    """ Returns the network address and CIDR for a given CIDR IP"""
    bits = ip.split('/')[-1]
    ips = ip.split('/')[0]

    bitmask = 0xffffffff - ((1 << (32-int(bits))) -1 )

    ipandmask = struct.unpack('>L',socket.inet_aton(ips))[0] & bitmask

    return "%s/%s" % (socket.inet_ntoa(struct.pack('>L', ipandmask)), bits)

def getBroadcast(ip):
    """ Return broadcast address for a given network address """
    bits = ip.split('/')[-1]
    ips = ip.split('/')[0]

    bitmask = 0xffffffff - ((1 << (32-int(bits))) -1 )

    ipormask = struct.unpack('>L',socket.inet_aton(ips))[0] | (bitmask ^ 0xffffffff)

    return socket.inet_ntoa(struct.pack('>L', ipormask))

def matchIP(netmask, ip):
    """Checks if ip is inside netmask range"""
    netmaskseg = netmask.split('/')[0]

    bits = int(netmask.split('/')[-1])

    mask = struct.unpack('>L', socket.inet_aton(netmaskseg))[0]

    bitmask =  0xffffffff - ((1 << (32-int(bits))) -1 )

    ipandmask = struct.unpack('>L',socket.inet_aton(ip))[0] & bitmask

    return (mask == ipandmask)

def getV6Network(ip):
    # XXX This method really sucks, only works in 16 bit increments
    prefix = ip.split('/')[-1]
    mip = ip.split('/')[0]
    ipseg1 = mip.split('::')[0]
    ipseg2 = mip.split('::')[1]
    ip = [0,0,0,0,0,0,0,0]
    for i,j in enumerate(ipseg1.split(':')):
        ip[i] = int(j, 16)
    if ipseg2:
        for i,j in enumerate(reversed(ipseg2.split(':'))):
            ip[7-i] = int(j, 16)
    segs = int(prefix)/16
    fix =  ':'.join([str(hex(i)) for i in ip[:segs]]) + '::/' + prefix
    return fix.replace('0x', '')

def cidr2netmask(cidr):
    return socket.inet_ntoa(struct.pack('<L', socket.htonl(0xffffffff - ((1 << (32-int(cidr))) -1 ))))

def netmask2cidr(netmask):
    netmaskbytes = socket.inet_aton(netmask)
    mylong = struct.unpack(">L", netmaskbytes)[0]
    tail = mylong ^ 0xffffffff
    c = 32
    while tail > 0:
        tail = tail >> 1
        c -= 1
    return c

def startTwisted(application, startDir = './', nodaemon = 0, logfile=None, rundir='.', appname='tums', pidfile='/var/run/tums.pid'):
    """ A freezable twistd bootstrap layer """
    from twisted.application import service, internet, strports, app
    from twisted.python import log, syslog
    try:
        from twisted.scripts import _twistd_unix as twistd
    except:
        from twisted.scripts import twistd

    config = {
        'profile': None,          'reactor': None,
        'encrypted': 0,           'syslog': 0,
        'prefix': appname,        'report-profile': None,
        'euid': 0,                'file': 'twistd.tap',
        'originalname': appname,  'rundir': rundir,
        'logfile': logfile,       'nodaemon': nodaemon,
        'uid': None,              'xml': None,
        'chroot': None,           'no_save': True,
        'quiet': 0,               'source': None,
        'nothotshot': 0,          'gid': None,
        'savestats': 0,           'debug': False,
        'pidfile': pidfile,       'umask': None
    }

    twistd.checkPID(config['pidfile'])

    config['nodaemon'] = config['nodaemon'] or config['debug']

    oldstdout = sys.stdout
    oldstderr = sys.stderr

    try:
        twistd.startLogging(config['logfile'], config['syslog'], 
            config['prefix'], config['nodaemon'])
        app.initialLog()
    except:
        pass


    try:
        twistd.startApplication(config, application)
        AR = None
    except:
        AR = twistd.UnixApplicationRunner(config)
        AR.application = application
        AR.preApplication()

        AR.logger.start(application)

        AR.postApplication()
        AR.logger.stop()

        return 
        #AR.startApplication(application)

    app.runReactorWithLogging(config, oldstdout, oldstderr)

    twistd.removePID(config['pidfile'])

    app.reportProfile(
        config['report-profile'],
        service.IProcess(application).processName
    )
    log.msg("Server Shut Down.")


def quaggaStats():
    HOST = "localhost"

    password = "2sa"
    l = open('/etc/quagga/bgpd.conf')
    for i in l:
        if i.strip() and 'password' in i.split()[0]:
            password = i.strip('\n').split()[1]
    l.close()

    tn = telnetlib.Telnet(HOST, 2605)
    tn.read_until("Password: ")
    tn.write(password + "\n")
    tn.write("show ip bgp\n")
    tn.write("show ip bgp summary\n")
    tn.write("exit\n")
    blob = tn.read_all()

    tn = telnetlib.Telnet(HOST, 2601)
    tn.read_until("Password: ")
    tn.write(password + "\n")
    tn.write("show ip ro\n")
    tn.write("exit\n")
    blob += tn.read_all()


    networks = []
    neighbors = []
    routes = []
    working = 0
    for l in blob.split('\n'):
        xl = l.strip().replace('\r', '')
        if "Neighbor" in xl:
            working = 1
        elif "Network" in xl:
            working = 2
        elif "lilith> show ip ro" in xl:
            working = 3
        elif not xl:
            if working != 3:
                working = 0

        if working == 1:
            if not "Neighbor" in xl:
                neighbors.append(xl.split())

        elif working == 2:
            if not "Network" in xl:
                networks.append(xl.split())

        elif working == 3:
            if "/" in xl:
                state = xl[:3]
                prefix = xl[4:].split()[0]
                iface = xl.split(',')[-1].strip()
                if 'via' in xl:
                    nexthop = xl[4:].split()[2]
                else:
                    nexthop = "CON"
                routes.append([state, prefix, nexthop, iface])


    return {
        'bgpnetworks': networks,
        'bgpneighbors': neighbors,
        'routes': routes
    }

def locateIp(config, ip):
    """Find the network interface responsible for an IP"""
    iface = None
    resort = False
    for k,v in config.EthernetDevices.items():
        network = v.get('network')
        ifip = v.get('ip')

        if not ifip:
            # This interface is broken
            continue 

        if (not network) and ifip:
            network = getNetwork(ifip)

        if matchIP(network, ip):
            # Best match type - local segment
            return k, network, False
        else:
            isDefault = False
            for dst,gate in v.get('routes', []):
                if dst == 'default':
                    isDefault = True
                else:
                    if matchIP(dst, ip):
                        iface = k
                        network = dst

            if iface:
                resort = iface, network, True
            if isDefault:
                resort = k, '0.0.0.0/0', True
    return resort

def getZone(config, iface):
    """Get the zone that an interface lies in"""
    zs = config.Shorewall.get('zones', {})
    for k,v in zs.items():
        ifs = v.get('interfaces', [])
        for i in ifs:
            if iface in i:
                return k

def traceTopology(config, ip):
    """Return a topology trace for an IP address"""
    loc = locateIp(config, ip)
    if not loc:
        return False

    iface, network, routed = loc
    zone = getZone(config, iface)
    return iface, zone, network, routed

def getLans(config):
    lans = config.LANPrimary
    if isinstance(lans, list):
        lans.sort()
        return lans
    else:
        return [lans]

def getWans(config):
    lans = getLans(config)

    wans = []
    for n in config.EthernetDevices.keys():
        if n not in lans:
            wans.append(n)

    for p in config.WANDevices.keys():
        wans.append(p)

    wans.sort()
    return wans

def getLanZones(config):
    lans = getLans(config)
    zones = []
    for k in lans:
        z = getZone(config, k)
        if not (z in zones):
            zones.append(z)
    return zones

def getLanIPs(config):
    lans = getLans(config)
    ips = []
    for k in lans:
        v = config.EthernetDevices[k]
        ip = v.get('ip')
        if ip:
            ips.append(ip.split('/')[0])

    return ips

def getLanIP6s(config):
    lans = getLans(config)
    ips = []
    for k in lans:
        v = config.EthernetDevices[k]
        ip = v.get('ipv6')
        if ip:
            ips.append(ip)

    return ips

def getLanNetworks(config):
    lans = getLans(config)

    networks = {}
    for k in lans:
        v = config.EthernetDevices[k]
        network = v.get('network')
        ip = v.get('ip')
        if (not network) and ip:
            network = getNetwork(ip)
        if network:
            networks[k] = network

    return networks

def getNetworks(config):
    networks = {}
    for k,v in config.EthernetDevices.items():
        network = v.get('network')
        ip = v.get('ip')
        if (not network) and ip:
            network = getNetwork(ip)
        if network:
            networks[k] = network

        else:
            networks[k] = "DHCP"

    return networks
 
def getLanAttr(config, attr):
    lans = getLans(config)
    
    stuff = {}
    for k in lans:
        v = config.EthernetDevices[k]
        n = v.get(attr)
        if n:
            stuff[k] = n

    return stuff

def isPackageInstalled(name):
    import apt
    pkgCache = apt.cache.Cache()
    pkgCache.open(None)
    return pkgCache[name].isInstalled

def getNetflowIndex(config, interface):
    lans = getLans(config)
    wans = getWans(config)

    if interface in lans:
        return 100
    else:
        return wans.index(interface)+201

def getInterfaceFromIndex(config, index):
    for i,k in enumerate(getWans(config)):
        if (index-201)==i:
            return k

    return None

def getNetflowIndexes(config):
    wans = getWans(config)

    indexes = [ 201+c for c, iface in enumerate(wans)]
    indexes.append(100)

    return indexes

# Hashing helpers
def set_odd_parity (byte):
    """
    Turns one-byte into odd parity. Odd parity means that a number in
    binary has odd number of 1's.
    """
    assert len(byte) == 1
    parity = 0
    ordbyte = ord(byte)
    for dummy in range(8):
        if (ordbyte & 0x01) != 0:
            parity += 1
        ordbyte >>= 1
    ordbyte = ord(byte)
    if parity % 2 == 0:
        if (ordbyte & 0x01) != 0:
            ordbyte &= 0xFE
        else:
            ordbyte |= 0x01
    return chr(ordbyte)

def convert_key (key):
    """Convert 7 byte key to 8 byte key"""
    bytes = [key[0],
             chr(((ord(key[0]) << 7) & 0xFF) | (ord(key[1]) >> 1)),
             chr(((ord(key[1]) << 6) & 0xFF) | (ord(key[2]) >> 2)),
             chr(((ord(key[2]) << 5) & 0xFF) | (ord(key[3]) >> 3)),
             chr(((ord(key[3]) << 4) & 0xFF) | (ord(key[4]) >> 4)),
             chr(((ord(key[4]) << 3) & 0xFF) | (ord(key[5]) >> 5)),
             chr(((ord(key[5]) << 2) & 0xFF) | (ord(key[6]) >> 6)),
             chr( (ord(key[6]) << 1) & 0xFF),
            ]
    return "".join([ set_odd_parity(b) for b in bytes ])

def create_lm_password (passwd):
    """Create Lan Manager hashed password."""
    passwd = passwd.upper()
    if len(passwd) < 14:
        lm_pw = passwd + ('\x00'*(14-len(passwd)))
    else:
        lm_pw = passwd[0:14]
    return lm_pw

def createLMHash(passwd):
    """
    Create LanManager hashed password.
    """
    from Crypto.Cipher import DES
    lm_pw = create_lm_password(passwd)
    # do hash
    magic_lst = [0x4B, 0x47, 0x53, 0x21, 0x40, 0x23, 0x24, 0x25]
    magic_str = "".join([chr(i & 0xFF) for i in magic_lst])
    lm_hpw = DES.new(convert_key(lm_pw[0:7])).encrypt(magic_str)
    lm_hpw += DES.new(convert_key(lm_pw[7:14])).encrypt(magic_str)
    return base64.b16encode(lm_hpw)

def createNTHash(passwd):
    """Create NT hashed password."""
    from Crypto.Hash import MD4
    # we have to have UNICODE password
    pw = "".join([ c+'\x00' for c in passwd])
    # do MD4 hash
    md4_context = MD4.new()
    md4_context.update(pw)
    nt_hpw = md4_context.digest()
    return base64.b16encode(nt_hpw)

