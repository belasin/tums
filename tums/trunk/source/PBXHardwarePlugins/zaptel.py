from Core import PBXUtils
from PBXHardwarePlugins import ZaptelCards
from PBXHardwarePlugins.ZaptelCards import Analog, ISDN

import os, re, Settings

"""Zaptel support for Vulani"""

class Plugin(PBXUtils.PBXHardwarePlugin):
    name = "zaptel"
    description = "Zaptel type cards"
    candetect = True

    groupSupport = True

    groupName = "ZapGroup"

    chan = "ZAP"

    zaptelProcDir = "/proc/zaptel/" #Note that when we release this it should be /proc/zaptel

    zaptelConf = "/etc/zaptel.conf"

    zapataConf = "/etc/asterisk/peers/zap/vulani_zapata.conf"

    devices = {} 

    cardRe = re.compile('Span ([0-9]+): (.*) "(.*)"')

    cardMatching = [
        [re.compile('WCTDM/[0-9]+|WRTDM/[0-9]+|OPVXA1200/[0-9]+', re.I), ZaptelCards.Analog.MultiPort],
        [re.compile('ztgsm/[0-9]+', re.I), ZaptelCards.ISDN.GSMBriStuff],
        [re.compile('ZTHFC[0-9]+/[0-9]+|ztqoz/[0-9]+/[0-9]+|ztgsm/[0-9]+', re.I), ZaptelCards.ISDN.BriStuff],
        [re.compile('TE[24]+/[0-9]+|WCT1/[0-9]+|Tor2/[0-9]+|TorISA/[0-9]+', re.I), ZaptelCards.ISDN.PriCards],
        [re.compile('XPP_BRI_[0-9]+/[0-9]+|WP[TE]1/[0-9]+', re.I), ZaptelCards.ISDN.PriCards],
    ]

    def __init__(self, cfg):
        self.cfg = cfg
        try:
            self.zaptelProcDir = Settings.ProcOveride + "/zaptel/"
        except:
            pass
        if not os.path.exists(self.zaptelProcDir):
            #Drivers are not running so therefore this directory does not exist
            raise Exception("Zaptel drivers are not loaded")
        else:
            self._scan()

    def _scan(self):
        """Scans the directory (zaptelProcDir) and generates a list of cards and card ports"""
        for path,subdirs,files in os.walk(self.zaptelProcDir):
            files.sort()
            for fileName in files:
                res = self.parseFile(path+fileName)
                if(res):
                    self._autobindcard(res, path+fileName)

    def _autobindcard(self, res, fullfilename):
        """Parses a given file data and attempts to detect the card entry then creates a device list or update an existing list"""
        if res:
            for matchEntry in self.cardMatching:
                try:
                    if matchEntry[0].match(res[0]["cardid"]):
                        """Instantiate the card entity"""
                        self.devices[res[0]["cardid"]] = matchEntry[1](self, res[0], res[1], fullfilename)
                        
                except Exception, EXC:
                    print "Error in card definition: %s" % EXC

    def defineRouting(self, routingData):
        """Updates the routing definition for each of the ports of each of the devices."""
        routingContext = routingData[1]
        foundDevice = False
        for deviceName in routingData[2].keys():
            if deviceName in self.devices:
                foundDevice = True
                if type(routingData[2][deviceName]) is list:
                    self.devices[deviceName].setPortRouting(routingData[2][deviceName], routingContext)
                else:
                    ports = [portNumber for portNumber, portDetails in enumerate(self.devices[deviceName])] #Could be better done
                    self.devices[deviceName].setPortRouting(ports, routingContext)
        if foundDevice:
            """Build the group channel if we matched data to this and return that"""
            return self.chan + "/g" + str(routingData[0])
    
    def save(self):
        """Generates the zaptel.conf and zapata.conf configuration files and saves them"""
        outputFile = [
            "#Zaptel.conf generated by vulani configurator",
            "loadzone    =  za",
            "defaultzone =  za"
        ]

        timingCounter = 1
        for deviceName in self.devices:
            device = self.devices[deviceName]
            if device.isEnabled():
                #Some cards do not use the span headings and therefore we need to skip this part
                if device.useSpanHeader: #ISDN type devices always generate a span header
                    timing = 0
                    if device.supportsTiming: #Does the device have support for timing
                        #XXX Maybe enable advanced user to specify if this card should use CPE timing or CO, Internal or External source
                        timing = timingCounter
                        timingCounter += 1
                    #Genertate the span line to initiate the the card
                    spanConfig = device.getSpanDetails()
                    outputFile.append("span=" + str.join(',', (
                        str(device.span),
                        str(timing),
                        str(spanConfig["lbo"]),
                        str(spanConfig["framing"]),
                        str(spanConfig["coding"])
                    )))
                res = device.getZaptelConf()
                if type(res) == list:
                    outputFile += res
                else:
                    outputFile.append(device.getZaptelConf())

        #Write the zaptelConfiguration file
        zapTelConf = file(self.zaptelConf, 'w')
        zapTelConf.write(str.join('\n',outputFile))
        zapTelConf.close()

        #Now lets write the asterisk zapata.conf
        #For this we need to know the context and group of each port both of these are availible from PBXPeers object

        zapATAConf = file(self.zapataConf, 'w')

        outputFile = [
            ";Vulani Generated by %s plugin" % self.name,
            "usecallerid=yes",
            "callerid=asreceived",
            "threewaycalling=yes",
            "overlapdial=yes",
            "transfer=yes",
        ]

        for deviceName in self.devices:
            device = self.devices[deviceName]
            if device.isEnabled():
                devConf = device.getZapataConf()
                if type(devConf) != list:
                    continue
                outputFile.append("")
                outputFile.append(";Device configuration for %s" % device)
                outputFile.extend(devConf)

        zapATAConf.write(str.join('\n', outputFile))
        zapATAConf.close()

    def detect(self):
        """Returns a list of cards / devices that require configuration, isConfigured also makes sure that the device is created in the config"""
        output = []
        for cardName in self.devices.keys():
            output.append((self.devices[cardName].isConfigured(), self.devices[cardName]))
        return output

    def parseFile(self, fullfilename):
        fp = file(fullfilename, "r")
        fileData = fp.readlines()
        fp.close()
        cardMatch = self.cardRe.search(fileData[0])
        if cardMatch:
            cardDet = {
                'span': int(cardMatch.group(1)),
                'cardid': cardMatch.group(2),
                'carddesc': cardMatch.group(3)
            }
            portLines = []
            for line in fileData[1:]:
                if len(line) < 4:
                    continue
                else:
                    try:
                        ln = line.strip().split(" ")
                        portLines.append([
                                int(ln[0]),
                                ln[1],
                                len(ln)>2 and str.join(" ",ln[2:]) or None
                            ])
                    except:
                        print "Error processing line: " + line
                        continue
            return (cardDet, portLines)


