import Console, Settings
import os, sys, copy, re, datetime
import Settings, LDAP, Tree
#Cleanup

from subprocess import call

class Plugin(Console.AttrHooker): 
        
    name = "net"
    
    help = { 
             "__default__":"Networking",
             "service": ""
           }
    
    def config_set_ip(self, *a):
        """config net set ip: <interface> <address>"""        
        if not len(a) > 1:
            print "No interface and/or address specified"
        if "port" not in a[0].lower():
            print "IP addresses only self.configurable on Port interfaces"
        elif not Console.validInetaddr(a[1]):
            print "Invalid IP address"
        else:
            iff = Console.fixIfaces(a[0])
            e = self.config.EthernetDevices
            if e.get(iff, False):
                oldip = e[iff].get('ip', '')
                e[iff]['ip'] = a[1]
                self.config.EthernetDevices = e
                os.system('ip addr del %s dev %s' % (oldip, iff))
                os.system('ip addr add %s dev %s' % (a[1], iff))
            else:
                # Check if this interface is plugged in at all...
                l = open('/proc/net/dev').read()
                if iff in l:
                    e[iff] = {'type':'static', 'ip':a[1]}
                    self.config.EthernetDevices = e
                    os.system('ifconfig %s up; ip addr add %s dev %s' % (iff, a[1], iff))
                    print "Interface %s setup with ip %s" % a
                else:
                    print "%s does not exist" % a[0]

    def config_del_ip(self, *a):    
        """config net del ip: <interface> <address>"""
        if not len(a) > 1:
            print "No interface and/or address specified"
        if "port" not in a[0].lower():
            print "IP addresses only self.configurable on Port interfaces"
        elif not Console.validInetaddr(a[1]):
            print "Invalid IP address"
        else:
            iff = Console.fixIfaces(a[0])
            e = self.config.EthernetDevices
            if e.get(iff, False):
                # Configured
                live = []
                for i in e[iff].get('aliases', []):
                    if i != a[1]:
                        live.append(i)
                os.system('ip addr del %s dev %s' % (a[1], iff))
                self.config.EthernetDevices = e
                print "Removed ip %s from %s" % (a[1], a[0])
            else:
                print "%s is not self.configured. Use 'config net set ip' instead" % a[1]


    def config_add_ip(self, *a):
        """config net add ip: <interface> <address>"""
        if not len(a) > 1:
            print "No interface and/or address specified"
        if "port" not in a[0].lower():
            print "IP addresses only self.configurable on Port interfaces"
        elif not Console.validInetaddr(a[1]):
            print "Invalid IP address"
        else:
            iff = Console.fixIfaces(a[0])
            e = self.config.EthernetDevices
            if e.get(iff, False):
                # Configured
                if e[iff].get('aliases', False):
                    e[iff]['aliases'].append(a[1])
                else:
                    e[iff]['aliases'] = [a[1]]
                os.system('ip addr add %s dev %s' % (a[1], iff))
                self.config.EthernetDevices = e
                print "Added ip %s to %s" % (a[1], a[0])
            else:
                print "%s is not self.configured. Use 'config net set ip' instead" % a[1]

    def show_route(self, *a):
        """show net route[: regex]
    Displays routing table. (optional regex for searching)"""
        if a:
            regex = ' '.join([str(argument) for argument in a])
            matcher = re.compile(str(regex), flags=re.I)
        else:
            regex = None
        r = os.popen('ip ro')

        for i in r:
            l = Console.renameIfaces(i).replace('default', '0.0.0.0/0').strip('\n').strip().split()
            if 'blackhole' in i:
                p= "SN> %s dev null0" % l[1]
            elif "link" in i and "kernel" in i:
                p= "CK> %s dev %s" % (l[0], l[2])
            elif "via" in i:
                p= "SK> %s via %s dev %s" % (l[0], l[2], l[4])
            elif "dev" in i:
                p= "CS> %s dev %s" % (l[0], l[2])
            if regex:
                if matcher.search(p):
                    print p
            else:
                print p

    def show_int(self, *a):
        return self.show_interface(*a)

    def show_interface(self, *a):
        """show net int[erface][: interfaces]
    Displays information regarding a particular ip network 
    interface (optional interface parameter list)."""
        # Display interfaces
        showifs = [str(i).lower() for i in a]
        r = os.popen('ip addr')
        current = ""
        ifs = {}
        for i in r:
            l = i.strip('\n').strip()
            if "<" in l:
                current = Console.renameIfaces(l.split()[1].strip(':'))
                ifs[current] = {
                    'ip': [],
                    'ip6': [],
                    'up':False
                }
            if "link/" in l:
                try:
                    ifs[current]['mac'] = l.split()[1]
                except:
                    # No mac?
                    ifs[current]['mac'] = None

            if "inet " in l:
                ifs[current]['ip'].append(l.split()[1])
            if "inet6" in l and not "scope link" in l:
                # Inet6 but not link-local
                ifs[current]['ip6'].append(l.split()[1])
            if "valid_lft" in l:
                ifs[current]['up'] = True
        for i,v in ifs.items():
            if showifs:
                if i.lower() not in showifs:
                    continue
            print "Interface: ", i
            print "   State: ", v['up'] and "Connected" or "No Link"
            print "   MAC  : ", v['mac']
            for j in v['ip']:
                print "   IPv4 : ", j

            for j in v['ip6']:
                print "   IPv6 : ", j
            print ""
    
    def show_conn(self, *a):
        return self.show_connections() 
    
    def show_connections(self, *a):
        """show net conn[ections]
    Displays a list of currently active(non loop) connections through all interfaces"""
        # Collect the netstat information
        try:
            netStatOutput = os.popen('netstat -n --ip | grep -E ".?[0-9]?[0-9]?[0-9]\." | awk \'{print $4 " " $5}\'| uniq | sort')
        except:
            print "Error executing netstat command"
            return
        
        #Build a matcher
        outputMatcher = re.compile("(.*):(.*) (.*):(.*)")
        
        #Show heading
        print "% 15s|% 6s|% 15s|% 6s" % ("Source IP", "SPort", "Dest IP", "DPort")
        
        matchCount = 0
        
        for netStatLine in netStatOutput:
            reMatch = outputMatcher.match(netStatLine)
            if reMatch:
                outputGroups = reMatch.groups()
                if outputGroups[0] == outputGroups[2]:
                    #Loop Connections Ignore
                    continue
                print "% 15s|% 6s|% 15s|% 6s" % outputGroups
                matchCount += 1
        
        if matchCount > 0:
            print "%d Active Connections" % matchCount
        else:
            print "No active connections non loop connections detected"
            
        
    
