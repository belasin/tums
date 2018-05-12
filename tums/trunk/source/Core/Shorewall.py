# Some shorewall helper stuff
import copy
from Core import confparse

class TCClasses:
    tcfile = '/etc/shorewall/tcclasses'

    def read(self):
        l = open(self.tcfile)
        classes = []
        for i in l:
            this = i.strip('\n').strip()
            if this and this[0]!="#" :
                blankru = [None for i in xrange(7)]
                comment = ""
                for i,k in enumerate(this.split()):
                    if "#" in k:
                        comment = ' '.join(this.split()[i:])
                    else:
                        blankru[i] = k
                blankru[6] = comment.strip('#')
                classes.append(copy.copy(blankru))
        
        return classes

class TCRules:
    tcfile = '/etc/shorewall/tcrules'

    def read(self):
        l = open(self.tcfile)
        rules = {}

        for i in l:
            this = i.strip('\n').strip()
            if this and this[0]!='#' :
                ru = this.split()
                mark = ru.pop(0)
                blankru = [None for i in xrange(7)]
                comment = ""
                for i,r in enumerate(ru):
                    if "#" in r:
                        comment = r.strip('#')
                    else:
                        blankru[i] = r
                blankru[6] = comment
                if not rules.get(mark, False):
                    rules[mark] = []
                rules[mark].append(copy.copy(blankru))

        return rules

def upgradeRules():
    """Upgrades the configuration rules, runs on instantiation of the firewall interface"""
    rulesParser = Rules()
    config = confparse.Config()
    #List of rules to automatically remove
    removeList = [
       'Ping/ACCEPT       all      all',
       'AllowICMPs        all      all',
       'ACCEPT            all      all    udp        33434:33463',
    ]

    """
    Parse Rules.read() split 
     AIP to rules 
     PROXY to redirect 
     FORWARD to dnat
    """
    curRules = config.Shorewall.get('rules', [])

    shw = config.Shorewall #Temp firewall rules

    parsedRules = rulesParser.read()

    def copyRules(parsedRulesIn, outPut, ruleNameFilter=None):
        if ruleNameFilter:
            newOut = []
            for k,curRule in enumerate(outPut):
                if curRule[1].split()[0] == ruleNameFilter:
                    newOut.append(curRule)
            outPut = newOut

        for rule in parsedRulesIn:
            try:
                if rule[-1] in parsedRules['UPGRADERULETAG'] or not ruleNameFilter:
                    ruleData = curRules[rule[-1]] #This should only run for PROXY FORWARD and DNAT if the rule was marked as an upgrade
                else:
                    continue
            except:
                print "Bad Rule: %s" % str(rule)
                continue

            if ruleData[1] not in removeList:
                outPut.append(ruleData)
        return outPut

    shw["rules"] = copyRules(parsedRules['AIP'], [])
    shw["redirect"] = copyRules(parsedRules['PROXY'],
        config.Shorewall.get('redirect', []), "REDIRECT")
    shw["dnat"] = copyRules(parsedRules['FORWARD'],
        config.Shorewall.get('dnat', []), "DNAT")

    config.Shorewall = shw #Overwrite the config



class Rules:
    rules = confparse.Config()
    parsedRules = {}
    
    def deleteRule(self, type, num): #XXX XXX XXX Remove
        # Pick the dataset to add this rule to
        if type == "FORWARD": 
            rarea = 'dnat'
        elif type == "PROXY": 
            rarea = 'redirect'
        else:
            rarea = 'rules'

        rules = self.rules.Shorewall
        ri = copy.deepcopy(rules.get(rarea, []))

        del ri[num]

        rules[rarea] = ri
        self.rules.Shorewall = rules


    def buildRule(self, type, *cont):
        if type == "AIP":
            rule = "ACCEPT   %s:%s   all" % (cont[0], cont[1])            

        elif type == "APORT":
            rule = "ACCEPT   %s     all     %s    %s" % (cont[0], cont[1], cont[2])
            if cont[3]:
                rule += "   -    %s" % cont[3]

        elif type == "PROXY":
            rule = "REDIRECT  %s%s   %s    %s    %s    -   %s" % (
                cont[0],
                cont[1] or "", #  Optional ip exclusion (source)
                cont[2], #  destination port
                cont[3], # protocol 
                cont[4], # catch port
                cont[5], # exclusion destination range
            )
                
        elif type == "FORWARD":
            if cont[3].strip():
                dstport = ":%s" % cont[3].strip()
            else:
                dstport = ""

            if cont[7].strip():
                source = ":%s" % cont[7].strip()
            else:
                source = ""

            rule = "DNAT    %s%s    %s:%s    %s      %s    -           %s" % (
                cont[5], 
                source,
                cont[6],
                cont[0] + dstport,
                cont[1], 
                cont[2] or "-",
                cont[4] or " ",
            )
        else:
            return None
        return rule

    def addRule(self, type, scont):
        rules = self.rules.Shorewall # ['rules']
        if not scont:
            return 

        # Pick the dataset to add this rule to
        if type == "FORWARD": 
            rarea = 'dnat'
        elif type == "PROXY": 
            rarea = 'redirect'
        else:
            rarea = 'rules'

        if not rules.get(rarea, []):
            rules[rarea] = []
        rules[rarea].append([1, scont.encode('ascii', 'replace')])
        self.rules.Shorewall = copy.deepcopy(rules)
        
    
    def read(self):
        def parseRule(rule):
            # pad and split each of these, making sure we have sufficient params or nones
            src = rule[1]+':Any:Any:'
            src = src.split(':') 
            srczone = src[0].replace('all', 'Any')
            srcip = src[1]
            srcport = src[2]

            dst = rule[2]+':Any:Any:'
            dst = dst.split(':')
            dstzone = dst[0].replace('all', 'Any')
            dstip = dst[1]
            #dstport = dst[2]

            myrule = ['Any' for i in range(4)]
            for i,v in enumerate(rule[3:]):
                myrule[i] = v 

            if myrule[2] != "Any":
                srcport = myrule[2]

            if myrule[3] != "Any":
                dstip = myrule[3]

            return [
                type,
                srczone, srcip, srcport,
                dstzone, dstip, 
                myrule[0], myrule[1], rulecnt
            ]

        def parseForward(rule):
            destz = rule[1].split(':',1)[0]
            if ':' in rule[1]:
                source = rule[1].split(':',1)[-1]
            else:
                source = "Any"
            tzone = rule[2].split(':',1)[0]
            destip = rule[2].split(':',1)[-1]
            proto = rule[3]
            port = rule[4].strip('-') or "ANY"
            if len(rule)>6:
                sourceip = rule[6]
            else:
                sourceip = ""

            return [destz, source, destip, tzone, proto, port, sourceip, rulecnt]

        def parseRedirect(rule):
            if ":" in rule[1]:
                source = rule[1].split(':')[-1]
                zone = rule[1].split(':')[0]
            else:
                source = ""
                zone = rule[1]

            srcport = rule[4]
            dstport = rule[2]
            proto = rule[3]
            if len(rule) > 6:
                dest = rule[6]
            else:
                dest = "-"
            return [zone, source, srcport, dstport, proto, dest, rulecnt]

        parsedRules = {
            'AIP':[],
            'APORT':[],
            'FORWARD':[],
            'PROXY':[],
            'UPGRADERULETAG':[], #Stop Repeating rule problem
        }
        rulecnt = 0 
        for l in self.rules.Shorewall.get('rules', []):
            line = l[1]
            if line and l[0]:
                thisRule = line.split()
                type = thisRule[0]
                if type == "ACCEPT" or type == "REJECT":
                    parsedRules['AIP'].append(parseRule(thisRule))
                #Here for legacy reasons (You never know)
                if type == "DNAT":
                    parsedRules['FORWARD'].append(parseForward(thisRule))
                    parsedRules['UPGRADERULETAG'].append(rulecnt)
                if type == "REDIRECT":
                    parsedRules['PROXY'].append(parseRedirect(thisRule))
                    parsedRules['UPGRADERULETAG'].append(rulecnt)
            # increase rule count
            rulecnt += 1

        rulecnt = 0 
        for l in self.rules.Shorewall.get('dnat', []):
            line = l[1]
            if line and l[0]:
                thisRule = line.split()
                type = thisRule[0]
 
                if type == "DNAT":
                    parsedRules['FORWARD'].append(parseForward(thisRule))

            # increase rule count
            rulecnt += 1

        rulecnt = 0 
        for l in self.rules.Shorewall.get('redirect', []):
            line = l[1]
            if line and l[0]:
                thisRule = line.split()
                type = thisRule[0]
 
                if type == "REDIRECT":

                    parsedRules['PROXY'].append(parseRedirect(thisRule))
                
            # increase rule count
            rulecnt += 1

        self.parsedRules = parsedRules
        return parsedRules
