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

class Rules:
    rules = confparse.Config()
    parsedRules = {}
    
    def deleteRule(self, type, num):
        rules = "/etc/shorewall/rules"
        fi = open(rules)
        ri = fi.read().split('\n')
        rules = self.rules.Shorewall
        ri = copy.deepcopy(rules.get('rules', []))
        fi.close()
        self.read()
        ro = []
        thisRule = self.parsedRules[type][num]
        if type=="AIP":
            for l in ri:
                if "ACCEPT" in l[1] and thisRule[0] in l[1] and thisRule[1] in l[1]:
                    pass
                else:
                    ro.append([l[0], l[1]])
        elif type=="APORT":
            for l in ri:
                rS = l[1].split()
                if len(rS)>4 and rS[0]=="ACCEPT" and rS[1]==thisRule[0] and rS[3]==thisRule[1] and rS[4]==thisRule[2] and thisRule[3] in l[1]:
                    pass
                else:
                    ro.append([l[0], l[1]])
        elif type=="FORWARD":
            for l in ri:
                if "DNAT" in l[1] and thisRule[0] in l[1] and thisRule[1] in l[1] and thisRule[2] in l[1] and thisRule[3] in l[1]: 
                    pass
                else:
                    ro.append([l[0], l[1]])
        elif type=="PROXY":
            for l in ri:
                if "REDIRECT" in l[1] and thisRule[0] in l[1] and thisRule[1] in l[1] and thisRule[2] in l[1] and thisRule[3] in l[1] and thisRule[4] in l[1]:
                    pass
                else:
                    ro.append([l[0], l[1]])
        else:
            return 
        if ro: # some protection from blanking the rules
            rules['rules'] = ro
            self.rules.Shorewall = rules


    def buildRule(self, type, *cont):
        if type == "AIP":
            rule = "ACCEPT   %s:%s   all" % (cont[0], cont[1])            

        elif type == "APORT":
            rule = "ACCEPT   %s     all     %s    %s" % (cont[0], cont[1], cont[2])
            if cont[3]:
                rule += "   -    %s" % cont[3]

        elif type == "PROXY":
            rule = "REDIRECT  loc%s   %s    %s    %s    -   %s" % (
                cont[0] or "", #  Optional ip exclusion (source)
                cont[1], #  destination port
                cont[2], # protocol 
                cont[3], # catch port
                cont[4], # exclusion destination range
            )
                
        elif type == "FORWARD":
            if cont[3].strip():
                dstport = ":%s" % cont[3].strip()
            else:
                dstport = ""
            rule = "DNAT    net    loc:%s    %s      %s    -           %s" % (
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
        if not rules.get('rules', []):
            rules['rules'] = []
        rules['rules'].append([1, scont.encode()])
        self.rules.Shorewall = copy.deepcopy(rules)
        
    
    def read(self):
        parsedRules = {
            'AIP':[],
            'APORT':[],
            'FORWARD':[],
            'PROXY':[]
        }

        for l in self.rules.Shorewall.get('rules', []):
            line = l[1]
            if line and l[0]:
                thisRule = line.split()
                type = thisRule[0]
                if type == "ACCEPT":
                    if ":" in thisRule[1]:
                        ip = thisRule[1].split(':')[-1]
                        net = thisRule[1].split(':')[0]
                        parsedRules['AIP'].append([net,ip])

                    else:
                        if len(thisRule)>4: # Enough parameters
                            net = thisRule[1]
                            dest = thisRule[2]
                            proto = thisRule[3]
                            port = thisRule[4]
                            if len(thisRule)>6:
                                dest = thisRule[6]
                            else:
                                dest = ""
                            parsedRules['APORT'].append([net, proto, port, dest])

                if type == "DNAT":
                    if len(thisRule)>5:
                        destip = thisRule[2].split(':',1)[-1]
                        proto = thisRule[3]
                        port = thisRule[4].strip('-') or "ANY"
                        if len(thisRule)>6:
                            sourceip = thisRule[6]
                        else:
                            sourceip = ""
                        parsedRules['FORWARD'].append([destip, proto, port, sourceip])

                if type == "REDIRECT":
                    if ":" in thisRule[1]:
                        source = thisRule[1].split(':')[-1]
                    else:
                        source = ""

                    srcport = thisRule[4]
                    dstport = thisRule[2]
                    proto = thisRule[3]
                    dest = thisRule[6]
                    parsedRules['PROXY'].append([source, srcport, dstport, proto, dest])
        self.parsedRules = parsedRules
        return parsedRules
