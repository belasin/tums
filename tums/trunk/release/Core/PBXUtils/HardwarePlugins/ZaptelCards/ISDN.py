from Core.PBXUtils.HardwarePlugins import ZaptelCards
from Core import PBXUtils
"""
Provides ISDN card implementation of card entity for the zaptel hardware plugin
"""

priConfig = PBXUtils.PBXCardPortConfig(
    'priconfig', #Config Entity
    "PRI Config", #Title
    "Please select a configuration profile", #Description
    { #Options
        'za': "South Africa(Telkom, Neotel)(E1)",
        'de': "Germany (E1)",
        'uk': "United Kingdom (E1)",
        'usa': "United States (T1)",
        #'t1cbank': "T1 Channelbank",
        #'e1cbank': "E1 ChannelBank",
    },
    "za" #Future default will be set to the country
)

briConfig =  PBXUtils.PBXCardPortConfig(
    'briconfig', #Config Entity
    "BRI Config", #Title
    "Please select a configuration profile", #Description
    { #Options
        'za': "South Africa(Telkom, Neotel)(E1)",
        'de': "Germany (E1)",
        'uk': "United Kingdom (E1)",
    },
    "za" #Future default will be set to the country
)

#Germany + ZA + UK share same profile for BRI and PRI
priEuro = {
    "switchtype": "euroisdn",
    "signalling": "pri_cpe",
    "pridialplan": 'local',
    "prilocaldialplan": 'local',
    "callprogress": 'yes',
    "framing": 'ccs',
    "coding": 'hdb3',
    "dchan": 16,
}

briEuro = priEuro
briEuro['coding'] = 'ami'
briEuro['signalling'] = 'bri_cpe_ptmp'

briConfigList = briEuro.keys()
briConfigList.remove('dchan')
briConfigList.remove("coding")
briConfigList.remove("framing")

priUSA = priEuro
priUSA['dchan'] = 24
priUSA['switchtype'] = "national"

briProfiles = {
    'za': briEuro,
    'de': briEuro,
    'uk': briEuro,
}

priProfiles = {
    'za': priEuro,
    'de': priEuro,
    'uk': priEuro,
    'usa': priUSA
}

class BriStuff(ZaptelCards.CardEntity):
    description = "BRI Card"
    lbo = 0
    framing = 'ccs'
    coding = 'ami'

    cardParam = [briConfig]

    def __init__(self, pluginObject, cardDet, portLines, fileName):
        ZaptelCards.CardEntity.__init__(self, pluginObject, cardDet, portLines, fileName)

    def getZaptelConf(self):
        """Returns a textual representation of the zaptel.conf lines"""
        output = []
        for portInd, portLine in enumerate(self.portLines[:-1]):
            output.append("bchan="+str(portLine[0]))
        output.append("dchan="+ str(self.portLines[-1][0]))
        return output

    def getZapataConf(self):
        """Returns a textual representation of the zapata.conf for Asterisk"""
        cProf = briProfiles[self['briconfig']] #Grab the config profile
        output = self.mergeConfigList(cProf, briConfigList)
        for portInd, portLine in enumerate(self.portLines[:-1]):
            output.append("group = "+ str.join(', ', self.pluginEntity.getPortGroup(portLine[1])))
            #Get CallerID
            output.append("callerid = " + self[portInd]['callerid'])
            #Get PickupGroup
            output.append("callgroup = " + self[portInd]['callgroup'])
            output.append("pickupgroup = " + self[portInd]['pickupgroup'])
            #Context Bindings
            output.append("context = "+ self[portInd]['context'])
            output.append("channel = "+ str(portLine[0]))
            
        return output

    def getSpanDetails(self):
        cProf = briProfiles[self['briconfig']] #Grab the config profile
        return {
           "coding": cProf["coding"],
           "lbo": 0,
           "framing": cProf["framing"]
        }
        
    def getPortList(self):
        """
        Returns a list object of tuples containing details of the port ('name', state, 'status text'), the index reflects the port number,
        the state is the current status -1 for error, 0 for normal/idle/inactive, 1 raised state indicates that the port is in use or active
        
        Note that in the case of a BRI Card the 3rd port is always the d channel and should not be counted
        """
        return [(portDetail[1], "In Use" in str(portDetail[2]) and int(1) or int(0), portDetail[2], str(portDetail[0])) for portDetail in self.portLines[:-1]]
 

class GSMBriStuff(ZaptelCards.CardEntity):
    description = "Junghannes's GSM Cards"
    lbo = 0
    framing = 'ccs'

    cardParam = [briConfig]

    def __init__(self, pluginObject, cardDet, portLines, fileName):
        ZaptelCards.CardEntity.__init__(self, pluginObject, cardDet, portLines, fileName)
    
    def getSpanDetails(self):
        cProf = briProfiles[self['briconfig']] #Grab the config profile
        return {
           "coding": ["coding"],
           "lbo": 0,
           "framing": cProf["framing"]
        }
        
    def getZapataConf(self):
        """Returns a textual representation of the zapata.conf for Asterisk"""
        cProf = briProfiles[self['briconfig']] #Grab the config profile
        output = self.mergeConfigList(cProf, briConfigList)
        return output

 
    def getPortList(self):
        """
        Returns a list object of tuples containing details of the port ('name', state, 'status text'), the index reflects the port number,
        the state is the current status -1 for error, 0 for normal/idle/inactive, 1 raised state indicates that the port is in use or active
        """
        return [(portDetail[1], "In Use" in str(portDetail[2]) and int(1) or int(0), portDetail[2], str(portDetail[0])) for portDetail in self.portLines]


class PriCards(ZaptelCards.CardEntity): #XXX XXX XXX XXX Note that the contry specific setting would go into this section
    #E1 cards has 30 channels with 2 dchans (EuroISDN) also ulaw
    #T1 Card has 24 channels with 2 dchans (American) also alaw
    """Provides PRI card settings"""
    description = "Pri Type cards"
    
    cardParam = [priConfig]
 
    def __init__(self, pluginObject, cardDet, portLines, fileName):
        ZaptelCards.CardEntity.__init__(self, pluginObject, cardDet, portLines, fileName)
    
    def getSpanDetails(self):
        cProf = priProfiles[self['priconfig']] #Grab the config profile
        return {
           "coding": cProf["coding"],
           "lbo": 0,
           "framing": cProf["framing"]
        }
        
    def getZapataConf(self):
        """Returns a textual representation of the zapata.conf for Asterisk"""
        cProf = briProfiles[self['briconfig']] #Grab the config profile
        output = self.mergeConfigList(cProf, briConfigList)
        return output

 
    def getPortList(self):
        """
        Returns a list object of tuples containing details of the port ('name', state, 'status text'), the index reflects the port number,
        the state is the current status -1 for error, 0 for normal/idle/inactive, 1 raised state indicates that the port is in use or active
        """
        return [(portDetail[1], "In Use" in str(portDetail[2]) and int(1) or int(0), portDetail[2], str(portDetail[0])) for portDetail in self.portLines]

