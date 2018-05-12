from Core import PBXUtils
from PBXHardwarePlugins import ZaptelCards
"""
Provides analog card implementation of card entity for the zaptel hardware plugin
"""

class MultiPort(ZaptelCards.CardEntity):
    """Sangoma and Digium multiport analog card support"""
    name = "Analog Multiport"
    description = "Digium and Sangoma Multiport analog cards"

    cardParam = []

    portParam = [ PBXUtils.PBXCardPortConfig(
                    'type',
                    "Port Type",
                    "Each analogue port can be either Active(FXS) or Passive(FXO). FXS ports produce a dialtone and therefore a telephone can be plugged into it, where as the FXO does not. It is important to realise that you should never plug two FXS ports into each other as this will likely result in damage",
                    {'na': 'Empty', 'fxs': 'Active(FXS)', 'fxo': 'Passive(FXO)'}, "na"),
                  PBXUtils.PBXCardPortConfig(
                    'signalling', 
                    "Port Signalling", 
                    "", 
                    {'ks': 'Kewl Start', 'ls': 'Loop Start', 'gs': 'Ground Start'}, 
                    'ks').advanced()
                ]

    useSpanHeader = False

    pluginObject = None

    def getZaptelConf(self):
        """Returns a textual representation of the zaptel.conf lines"""
        output = []
        for portInd, portLine in enumerate(self.portLines):
            if self[portInd]['type'] != 'na':
                values = self[portInd]
                values['type'] = values['type'] == 'fxs' and "fxo" or 'fxs' #Hmm crazy zaptel idea that your fxo is your fxs in zapata but the correct way around in zaptel
                output.append("%(type)s%(signalling)s=" % self[portInd] + str(portLine[0]))
        return output

    def getZapataConf(self):
        """Returns a textual representation of the zapata.conf for Asterisk"""
        #cProf = briProfiles[self['briconfig']] #Grab the config profile
        #output = self.mergeConfigList(cProf, briConfigList)
        output = []
        for portInd, portLine in enumerate(self.portLines[:-1]):
            if self[portInd]['type'] == 'na':
                continue
            signalling = str.join('_', (self[portInd]['type'], self[portInd]['signalling']))
            output.append("group = "+ str.join(', ', self.pluginEntity.getPortGroup(portLine[1])))
            #Get CallerID
            output.append("callerid = " + self[portInd]['callerid'])
            #Get PickupGroup
            output.append("callgroup = " + self[portInd]['callgroup'])
            output.append("pickupgroup = " + self[portInd]['pickupgroup'])
            #Context Bindings
            output.append("context = "+ self[portInd]['context'])
            output.append("signalling = "+ signalling) 
            output.append("channel = "+ str(portLine[0]))
        return output

    def checkStatus(self):
        """Card type does not have a status without opening /dev/zap/ctl"""
        return None

    def getPortList(self):
        """
        Returns a list object of tuples containing details of the port ('name', state, 'status text'), the index reflects the port number,
        the state is the current status -1 for error, 0 for normal/idle/inactive, 1 raised state indicates that the port is in use or active
        """
        return [(portDetail[1], "In Use" in str(portDetail[2]) and int(1) or int(0), portDetail[2], portDetail[0]) for portDetail in self.portLines]
        
