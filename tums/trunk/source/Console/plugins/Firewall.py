import Console, Settings
import os, sys, copy, re, time
import Settings, LDAP, Tree, lang
from Core import Shorewall
from subprocess import call

class Plugin(Console.AttrHooker):
    name = "firewall"
    
    rules = Shorewall.Rules()    
    
    #Protocols are used for matching user input
    # matchText.upper() : 'setting value'
    protocols = {
                 'ANY':   '-',
                 'TCP': 'tcp',
                 'UDP': 'udp',
                 'PPTP': '47',
                 'ICMP': 'icmp'
                }
        
    regNumber = re.compile('^[0-9]{0,}$', re.IGNORECASE)
    regRuleAction = re.compile('^(ACCEPT|REJECT)$', re.IGNORECASE)
    regZonePolicy = re.compile('^(ACCEPT|DROP)$', re.IGNORECASE)
    #I Love Regular expressions
    regRuleIPDetails = re.compile(r"""^(?P<IP>((((|!)[0-9]{1,3}(\.[12]?[0-9]?[0-9]){3})(|/([0-9]{1,2})))|[aA][nN][yY]))(|:(?P<PORT>([0-9\-\,]{0,})|[aA][nN][yY]))(|@(?P<ZONE>[a-zA-Z0-9]{2,}))$""", re.IGNORECASE|re.VERBOSE)

    
    help = {"__default__":"Firewall Management"}
    
    def checkFirewall(self):
        if os.path.exists('/usr/local/tcs/tums/shorewallBroken'):
            print "!!!ALERT!!! Firewall is currently not working please check your settings for errors"
        
    def config_add(self, *a):
        """config firewall add: [rulenum] <action> <srcip>[:sport[-sport]][,sport][@szone] <dstip>[:dport[-dport][,dport]][@dzone] [protocol]
    Adds a rule to the firewall"""
        #There should always be nothing less than 3 arguments otherwise we are missing something
        if len(a) < 3:            
            print "ERROR: Missing required parameter(s)"            
            self.genAllDoc('config')
            return
        #Determine if option 0 is an action or a rule number
        aipRules = self.rules.read()['AIP']        
        #Determine the last rulenumber and make sure that the provided rule number does not exceed it     
        ruleNumber = None   
        if type(a[0]) == int:
            if a[0] + 1  > len(aipRules):
                ruleNumber = None
            else:
                ruleNumber = a[0]
        if ruleNumber >= 0:
            #If we are inserting a rule get the index of the rule to insert at
            realRuleNumber = aipRules[ruleNumber][8]
        else:
            #Enumerate and figure out the last rule number
            realRuleNumber = 0
            for v,i in enumerate(self.config.Shorewall['rules']):
                if "ACCEPT" in i[1] or "REJECT" in i[1]:
                    realRuleNumber = v
            realRuleNumber += 1
        baseIndex = type(a[0]) == int and 1 or 0
        protocol = '-' #Default protocol is always ANY / -
        matchRuleAction = self.regRuleAction.match(str(a[baseIndex]))
        if not matchRuleAction:
            print "ERROR: Invalid action specified should be ACCEPT or REJECT"            
            self.genAllDoc('config')
            return
            
        #If ruleNumber is set then we need to verify that the number of subsequent parameters will be satisfactory        
        if type(a[0]) == int:
            if len(a) < 4:
                print "ERROR: Missing required parameter(s)"
                self.genAllDoc('config')
                return
            elif len(a) > 4:
                #If the argument length is more than 4 we know that the user has provided a protocol
                #we should then overide the default with the user specified one
                #we should also validate the user input
                if str(a[4]).upper() in self.protocols:
                    protocol = self.protocols[str(a[4]).upper()]
                else:
                    print "ERROR: Invalid Protocol provided"
                    self.genAllDoc('config')
                    return
                
        zones = self.config.Shorewall.get('zones' , {})
        
        def genIPDetails(name,ipMatch):
            if not ipMatch:
                #The regex failed to match the string therefore the user provided an invalid input
                print "ERROR: Invalid %s IP string" % name
                return False
            output = {}
            output['ip'] = str(ipMatch.group('IP')).upper().replace('ANY','')            
            if 'ANY' in str(ipMatch.group('PORT')).upper():
                output['port'] = '-'
            elif ipMatch.group('PORT'):
                #If port has been specified we need to check a few things
                #Port must not be above 65535
                #Port range alpha must be less than beta
                #start by splitting by ,                
                output['port'] = '' #Reset output for port
                ports = []
                for portEntry in str(ipMatch.group('PORT')).split(','):
                    #Validation
                    lastPort = None
                    for port in portEntry.split('-'):
                        if int(port) < 1 or int(port) > 65535:
                            #Port is invalid
                            print "Invalid %s Port" % name
                            return False
                        elif lastPort and int(lastPort) >= int(port):
                            print "ERROR: %s port range, %s should be smaller than %s" % (name, lastPort, port)
                            return False
                        lastPort = port
                    if len(portEntry.split('-')) > 2:
                        print "ERROR: %s port range %s should not have more than 1 '-'" % (name, portEntry)
                    #Build Port String
                    portEntry = portEntry.replace('-',':')
                    ports.append(portEntry)
                output['port'] = str.join(',', ports)
            else:                
                #Default value for port is ANY
                output['port'] = '-'
            #Check Zones
            if ipMatch.group('ZONE') and not ipMatch.group('ZONE').upper() in ('ANY','ALL'):
                if ipMatch.group('ZONE') in zones.keys():
                    output['zone'] = ipMatch.group('ZONE')
                else:
                    #Zone does not exist
                    print "ERROR: %s zone %s does not exist" % (name, ipMatch.group('ZONE'))
                    return False
            else:
                if len(output['ip']) > 0:
                    print "ERROR: %s zone is required for the provided ip" % name
                    return False
                output['zone'] = 'all'                
            #Return output
            return output
        
        #Match IP Addresses        
        #Validate the Src and Dst IP check that zones are correct
        srcIPMatch = self.regRuleIPDetails.search(str(a[baseIndex+1]))
        srcIPDetails = genIPDetails('Source',srcIPMatch)
        
        dstIPMatch = self.regRuleIPDetails.search(str(a[baseIndex+2]))        
        dstIPDetails = genIPDetails('Destination',dstIPMatch)
            
        if srcIPDetails and dstIPDetails:
            #Build new firewall rule
            rule = "%s   %s%s    %s%s        %s    %s    %s" % (
                str(a[baseIndex]).upper(), #Action
                srcIPDetails['zone'], #SRCZone
                srcIPDetails['ip'] and ':' + srcIPDetails['ip'] or '', #SRCIP Address
                dstIPDetails['zone'], #DSTZone                
                dstIPDetails['ip'] and ':' + dstIPDetails['ip'] or '', #DSTIP Address
                protocol,
                dstIPDetails['port'], #Destination Port
                srcIPDetails['port'], #Source Port
            )
            #Add new rule to firewall
            currentRuleset = self.config.Shorewall
            currentRuleset['rules'].insert(realRuleNumber, [1, rule])
            self.config.Shorewall = currentRuleset            
            print "Added Rule (run: 'config firewall apply' to apply to firewall)"
        
    def config_add_proxy(self, *a):
#        """config firewall add proxy: [srcip:]<sport>[@szone] [dstip:]<dport> <protocol>
#    Adds a rule to the firewall"""
        pass
        
    def config_add_snat(self, *a):
#        """config firewall add snat: <srcip> <extip> [extint]
#    Adds a rule to the firewall"""
        pass
        
    def config_add_nat(self, *a):
#        """config firewall add nat: [srcip
#    Adds a rule to the firewall"""
        pass
        
    def config_add_zone(self, zoneName=None, policy=None, logDetails=None, *a):
        """config firewall add <zone name> <policy(ACCEPT|DROP)> <log|NONE> [interfaces] 
    Adds a zone to the firewall, if you would like to specify no log specify None
    To specify multiple interfaces seperate with a :"""
        if not zoneName or not policy:
            print "Error: zone name and a policy are required"
            self.genAllDoc('config')
            return           
        
        matchZonePolicy = self.regZonePolicy.match(str(policy))
        if not matchZonePolicy:
            print "ERROR: Invalid policy specified should be ACCEPT or DROP"            
            self.genAllDoc('config')
            return
            
        k = self.config.Shorewall
        # Make a zone def if there isn't one
        if not k.get('zones', None):
            k['zones'] = {}
        
        if str(logDetails).upper() == 'NONE':
            logDetails = None
        
        if zoneName in k.get('zones', {}):
            del k['zones'][zoneName]

        if a:
            ifs = Console.fixIfaces(str.join(' ',a)).split(':')
        else:
            ifs = []
            
        zone = {
            'policy': policy.upper(),
            'log' : logDetails or '',
            'interfaces': ifs
        }
        
        k['zones'][zoneName] = zone

        self.config.Shorewall = k 
        print "Zone has been added successfully"

        
    def config_add_forward(self, *a):
#        """config firewall add forward <rule>
#    Adds a rule to the firewall"""
        pass
        
    def config_del(self, ruleNo=None, *a):
        """config firewall del: <rule number>
    Remove a firewall rule at rulenumber"""
        if ruleNo == None:
            print "Rule number is empty please specify a valid rule number"
            self.genAllDoc('config')
            return
            
        #Sanitise input
        try:
            ruledetail = self.rules.read()['AIP'][ruleNo]
        except:
            print "Rule number %s does not exist" % ruleNo
            return
        
        #Physically remove rule
        if self.delFirewallRule(ruledetail[8]):
            print "Rule %s was removed" % ruleNo
        else:
            print "Failed to remove rule at %s" % ruleNo
    
        
    def config_del_proxy(self, ruleNo=None, *a):
#        """config firewall del rule: <rule number>
#    Remove a firewall transparent proxy rule at rulenumber"""
        if ruleNo == None:
            print "Rule number is empty please specify a valid rule number"
            self.genAllDoc('config')
            return
            
        #Sanitise input
        try:
            ruledetail = self.rules.read()['PROXY'][ruleNo]
        except:
            print "Rule number %s does not exist" % ruleNo
            return
        
        #Physically remove rule
        if self.delFirewallRule(ruledetail[6]):
            print "Rule %s was removed" % ruleNo
        else:
            print "Failed to remove rule at %s" % ruleNo
    
        
    def config_del_forward(self, ruleNo=None, *a):
#        """config firewall del rule: <rule number>
#    Remove a firewall port forward rule at rulenumber"""
        if ruleNo == None:
            print "Rule number is empty please specify a valid rule number"
            self.genAllDoc('config')
            return
            
        #Sanitise input
        try:
            ruledetail = self.rules.read()['FORWARD'][ruleNo]
        except:
            print "Rule number %s does not exist" % ruleNo
            return
        
        #Physically remove rule
        if self.delFirewallRule(ruledetail[7]):
            print "Rule %s was removed" % ruleNo
        else:
            print "Failed to remove rule at %s" % ruleNo
    
    def delFirewallRule(self, ruleNumber):
        """Removes a firewall rule at ruleNumber from the config"""        
        try:      
            k = self.config.Shorewall
            del k['rules'][int(ruleNumber)]
            self.config.Shorewall = k   
            #Return True if we found it and deleted it
            return True        
        except:
            #Return false if we could not find it
            return False
    
    def config_del_zone(self, zoneName=None, *a):
        """config firewall del zone: <zoneName>
    Remove a firewall zone"""
        if not zoneName:
            print "Zone name is empty please specify a valid zone Name"            
            self.genAllDoc('config')
            return
        #Grab zones of the firewall
        zones = self.config.Shorewall.get('zones' , {})
        #Check is provided zone name is in the firewall
        if zoneName in zones:
            k = self.config.Shorewall
            del k['zones'][zoneName]
            self.config.Shorewall = k
            print "Zone %s has been removed" % zoneName            
            
    def config_del_nat(self, ruleNo=None, *a):
#        """config firewall del nat: <rule number>"""
        pass
        
    def config_del_snat(self, ruleNo=None, *a):
#        """config firewall del snat: <rule number>"""
        pass
    
    def config_apply(self, *a):
        """config firewall apply
    Applies the new configuration onto the server
    after which the firewall is reloaded"""
        try:
            retcode = call(Settings.BaseDir+'/configurator --shorewall', shell=True)
            print "Config Applied"
            self.service_restart()
        except OSError, e:
            print "Execution failed:", e      
    
    
    #XXX XXX XXX
    #Need to work on creating a method that takes a mapping and generates the output of the below show outputs
    
    def show_zones(self, *a):
        """show firewall zones
    Produces a list of firewall zones"""            
        self.checkFirewall()
        zones = self.config.Shorewall.get('zones', {})
        if len(zones) < 1:
            print "No zones found"
            return
        else:
            print "| Zone Name | Policy |     Log Target |                          Interfaces |"
            print "|-----------+--------+----------------+-------------------------------------|"
        for zone, zd in zones.items():
            print "| % 9s | % 6s | % 14s | % 35s |" % (
                str(zone), str(zd['policy']),
                str(zd['log']),
                str.join(' ',[Console.renameIfaces(str(i)) for i in zd['interfaces']]).rstrip()
            )
        
        print "+-----------+--------+----------------+-------------------------------------+"

    def show_all_rules(self, *a):
        """show firewall all rules
    Displays standard, proxy and forward rules"""
        print "Standard Rules:"
        self.show_rules()
        print "Proxy Rules:"
        self.show_proxy()
        print "Forward Rules:"
        self.show_forward()
                
    
    def show_rules(self, *a):
        """show firewall rules
    Displays a list of firewall rules"""    
        self.checkFirewall()
        #Read current ruleset
        rules = self.rules.read()['AIP']
                
        if len(rules) < 1:
            print "No general firewall rules found"
            return
        else:
            print "  RN|     Action |              |     Zone |                            Port |                  IP Address | Protocol |"
            print "    |------------+--------------+----------+---------------------------------+-----------------------------+----------|"
        for ruleIndex,ruleData in enumerate(rules):
            print "% 4s| % 10s | % 12s | % 8s | % 31s | % 27s | % 8s |" % (
                ruleIndex,
                #str(ruleData[8]),
                str(ruleData[0]),
                "Source",
                str(ruleData[1]),
                str(ruleData[3].replace('-', 'Any')),
                str(ruleData[2]),
                str(ruleData[6].replace('-', 'Any')),
            )
            print "% 4s| % 10s | % 12s | % 8s | % 31s | % 27s | % 8s |" % (            
                "","",
                "Destination",
                str(ruleData[4]),
                str(ruleData[7].replace('-', 'Any')),
                str(ruleData[5]),
                ""
            )
        print "    +------------+--------------+----------+---------------------------------+-----------------------------+----------+"
        
    
    def show_snat(self, *a):  
        """ show firewall snat
    Displays a list of SNAT rules"""
        self.checkFirewall()
        #SNAT rules
        snat = self.config.Shorewall.get('snat',[])
        if len(snat) < 1:
            print "No snat rules found"
            return
        else:
            print "  RN|       Source IP |  Ext Int |     Internal IP | Any Interface |  Use Internal |"
            print "    |-----------------+----------+-----------------+---------------+---------------|"
        ruleIndex = 0              
        for ru in snat:
            rule = ru.split()
            #Fix interfaces
            rule[1] = Console.renameIfaces(rule[1])
            print "% 4d| % 15s | % 8s | % 15s | % 13s | % 13s |" % (
                ruleIndex,
                rule[0],rule[1],rule[2],rule[3], rule[4]
            )
            ruleIndex += 1
    
        print "    +-----------------+----------+-----------------+---------------+---------------+"
    
    def show_nat(self, *a):
        """show firewall nat
    Displays a lis of NAT rules"""
        self.checkFirewall()
        masq = self.config.Shorewall.get('masq',  [])
        natRules = []
        for k,mas in masq.items():
            for v in mas:
                if type(v) == list:
                    l = [str(Console.renameIfaces(k))]
                    l.extend([str(Console.renameIfaces(i.replace('-', 'Any'))) for i in v])
                    natRules.append(l)
                else:
                    natRules.append([
                        Console.renameIfaces(k), 
                        'Any', Console.renameIfaces(v), 'Any', 'Any', 'Any', 'Any'
                    ])
        if len(natRules) < 1:
            print "No nat rules found"
            return
        else:
            print "  RN| Dest Int |        Dest Network |  Src Int |         Src Network |          Nat IP | Protocol |  Port |"
            print "    |----------+---------------------+----------+---------------------+-----------------+----------+-------|"
        ruleIndex = 0
        for natRule in natRules:
            print "% 4d| % 8s | % 19s | % 8s | % 19s | % 15s | % 8s | % 5s |" % (
                 ruleIndex, natRule[0], natRule[1], natRule[2], 
                natRule[3], natRule[4], natRule[5], natRule[6],
            ) #Not ideal
            ruleIndex += 1
        
        print "    +----------+---------------------+----------+---------------------+-----------------+----------+-------+"
        
    def show_proxy(self, *a):
        """show firewall proxy
    Shows a list of transparent proxy rules"""
        self.checkFirewall()
        proxy = self.rules.read()['PROXY']
        if len(proxy) < 1:
            print "No transparent proxy rules found"
            return
        else:
            print "  RN| Source Zone |         Src Network | Src Port | Dst Port | Protocol |         Dst Network |"
            print "    |-------------+---------------------+----------+----------+----------+---------------------|"
        for ruleIndex,ruleData in enumerate(proxy):
            print "% 4d| % 11s | % 19s | % 8s | % 8s | % 8s | % 19s |" % (
                ruleIndex,
                #ruleData[6],
                ruleData[0],                
                ruleData[1],
                ruleData[2],
                ruleData[3],
                ruleData[4],
                ruleData[5],
            )
        print "    +-------------+---------------------+----------+----------+----------+---------------------+"
        
        
    def show_forward(self, *a):
        """show firewall forward
    Displays a list of forward ports"""
        self.checkFirewall()
        forward = self.rules.read()['FORWARD']
        
        if len(forward) < 1:
            print "No forward ports found"
            return
        else:
            print "  RN| Source Zone |          Src IP |            Forward To | Dst Zone | Protocol | Dst Port |          Src IP |"
            print "    |-------------+-----------------+-----------------------+----------+----------+----------+-----------------|"
        for ruleIndex,ruleData in enumerate(forward):
            print "% 4d| % 11s | % 15s | % 21s | % 8s | % 8s | % 8s | % 15s |" % (
                ruleIndex,
                #ruleData[7],
                ruleData[0],                
                ruleData[1],
                ruleData[2],
                ruleData[3],
                ruleData[4],
                ruleData[5],
                ruleData[6],
            )
        print "    +-------------+-----------------+-----------------------+----------+----------+----------+-----------------+"
        
    
    def service_restart(self, *a):
        """service firewall restart
    Restarts the firewall"""
        try:
            retcode = call('shorewall restart', shell=True)
            if retcode > 0:
                l = open('/usr/local/tcs/tums/shorewallBroken', 'wt')
                l.write(str(retcode))
                print "Firewall failed to start"
            else:                
                retcode = call('rm /usr/local/tcs/tums/shorewallBroken > /dev/null 2>&1', shell=True)
                print "Firewall Restarted"
        except OSError, e:
            print "Execution failed:", e        
    
    def service_stop(self, *a):
        """service firewall stop
    Stops the firewall"""
        try:
            retcode = call('shorewall stop', shell=True)
            print "Firewall Stopped"
        except OSError, e:
            print "Execution failed:", e        
    
    def service_start(self, *a):
        """service firewall start
    Starts the firewall"""
        try:
            retcode = call('shorewall start', shell=True)
            if retcode > 0:
                l = open('/usr/local/tcs/tums/shorewallBroken', 'wt')
                l.write(str(retcode))
                print "Firewall failed to start"
            else:                
                retcode = call('rm /usr/local/tcs/tums/shorewallBroken > /dev/null 2>&1', shell=True)
                print "Firewall Started"
        except OSError, e:
            print "Execution failed:", e        
    
