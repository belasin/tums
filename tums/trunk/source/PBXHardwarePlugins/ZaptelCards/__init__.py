from Core import PBXUtils

"""Zaptel Card Primitives"""

class CardEntity(PBXUtils.DeviceEntity):
    """Primitive for parsing and gaining information from the card"""
    name = ""
    description = ""
    fileName = ""

    carDet = {}

    portLines = []

    cardParam = {}

    portParam = {}

    ports = []

    span = 0

    lbo = 3

    framing = 'ccs'

    coding = 'ami'

    """Should we generate a span header for zaptel"""
    useSpanHeader = True

    """Can be used to supply timing"""
    supportsTiming = True

    def __init__(self, pluginEntity, cardDet, portLines, fileName):
        """
        Populate and parsePorts data
        """
        self.name = cardDet["cardid"]
        self.description = cardDet["carddesc"]
        self.cardDet = cardDet
        self.span = cardDet['span']
        self.portLines = portLines
        self.fileName = fileName
        self.pluginEntity = pluginEntity #Stores the instance of the factory that created this object 
        self.cfg = self.pluginEntity.cfg
 
    def getZaptelConf(self):
        """Returns a textual representation of the zaptel.conf line"""
        pass

    def getZapataConf(self):
        """Returns a textual representation of the zapata.conf for Asterisk"""
        pass

    def checkStatus(self):
        """
        Retrieves the current status of the card
        @returns: tuple of (state, "Textual representation of the status"), where state is -1 for error, 0 for Not Active and 1 for active
        """
        pass

    def mergeConfigList(self, configProfile, variableList):
        """
        Merges the config list and generates an asterisk friendly list of values that
        can be joined together by "\n"
        @returns: list of strings that describe a config
        """
        output = []
        for varname in variableList:
            if varname in configProfile:
                output.append("%s = %s"% (varname, configProfile[varname]))
        return output

    def getSpanDetails(self):
        """
        Returns a dictionary detailing span details for this entry
        """
        pass
