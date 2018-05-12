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
        rulecnt = 0 
        for l in self.rules.Shorewall.get('rules', []):
            line = l[1]
            if line and l[0]:
                thisRule = line.split()
                type = thisRule[0]
                if type == "ACCEPT" or type == "REJECT":
                    # pad and split each of these, making sure we have sufficient params or nones
                    src = thisRule[1]+':Any:Any:'
                    src = src.split(':') 
                    srczone = src[0].replace('all', 'Any')
                    srcip = src[1]
                    srcport = src[2]

                    dst = thisRule[2]+':Any:Any:'
                    dst = dst.split(':')
                    dstzone = dst[0].replace('all', 'Any')
                    dstip = dst[1]
                    #dstport = dst[2]

                    myrule = ['Any' for i in range(4)]
                    for i,v in enumerate(thisRule[3:]):
                        myrule[i] = v 

                    if myrule[2] != "Any":
                        srcport = myrule[2]

                    if myrule[3] != "Any":
                        dstip = myrule[3]
                    thisRule = [
                        type,
                        srczone, srcip, srcport,
                        dstzone, dstip, 
                        myrule[0], myrule[1], rulecnt
                    ]
                    parsedRules['AIP'].append(thisRule)

                if type == "DNAT":
                    destz = thisRule[1].split(':',1)[0]
                    if ':' in thisRule[1]:
                        source = thisRule[1].split(':',1)[-1]
                    else:
                        source = "Any"
                    tzone = thisRule[2].split(':',1)[0]
                    destip = thisRule[2].split(':',1)[-1]
                    proto = thisRule[3]
                    port = thisRule[4].strip('-') or "ANY"
                    if len(thisRule)>6:
                        sourceip = thisRule[6]
                    else:
                        sourceip = ""
                    parsedRules['FORWARD'].append([destz, source, destip, tzone, proto, port, sourceip, rulecnt])

                if type == "REDIRECT":
                    if ":" in thisRule[1]:
                        source = thisRule[1].split(':')[-1]
                        zone = thisRule[1].split(':')[0]
                    else:
                        source = ""
                        zone = thisRule[1]

                    srcport = thisRule[4]
                    dstport = thisRule[2]
                    proto = thisRule[3]
                    if len(thisRule) > 6:
                        dest = thisRule[6]
                    else:
                        dest = "-"
                    parsedRules['PROXY'].append([zone, source, srcport, dstport, proto, dest, rulecnt])
                
            # increase rule count
            rulecnt += 1
        self.parsedRules = parsedRules
        return parsedRules
