from Core import confparse, Utils, WebUtils
from time import time
import os

config = confparse.Config()

def getCodecs():
    """ Fetch all available codecs in the system """
    codecs = []
    exclude = ['zap', 'a_mu', 'lpc10']

    for fi in os.listdir('/usr/lib/asterisk/modules'):
        if fi[:6] == "codec_" and fi[6:-3] not in exclude:
            codecs.append(fi[6:-3])
    
    return codecs

def getAvaExtenNumSelect(limit=True, includeInLimit=[]):
    """Get a list of availible extensions ready for use within an option selection for formal
    @Param limit specifies if we should include only extension numbers that have not been assigned
    @Param includeInLimit if limit is true then the list of extensions here will be included even if they are bound"""
    extList = getAllExtensions()
    output = [('s', 'DEFAULT')]
    usedExtList = []
    for user, extDet in config.PBXExtensions.items():
        usedExtList.extend(extDet.get('extensions',[]))
    for queue, qDet in config.PBX.get('queues', {}).items():
        usedExtList.extend(qDet['extensions'])
    for ext in extList:
        ext = str(ext)
        if ext in usedExtList and ext not in includeInLimit:
            if limit:
                continue
        output.append((ext,ext))
    return output

def getExtensionSelect():
    userExtensions = [
        ('special/CONF','Conference'),
        ('special/PICKUP','Call Pickup'),
    ]

    for queueName, queue in config.PBX.get('queues', {}).items():
        userExtensions.append(('queue/%s' % queueName,'%s Queue' % queueName.capitalize()))

    for ivrName, ivr in config.PBX.get('ivr', {}).items():
        userExtensions.append(('ivr/%s' % ivrName, '%s IVR' % ivrName.capitalize()))

    for user in WebUtils.getUsers():
        username = user.split('@')[0]
        if username in config.PBXExtensions:
            userExtensions.append(('ext/'+username,username))
    return userExtensions

def getAllExtensions():
    extList = []
    extensions = config.PBX.get('extension', {})
    for ext in extensions:
        endExt = ext + extensions[ext]
        extList.extend(range(ext, endExt))
    return extList

def getAllAvaExtDeviceEndPoints():
    devList = getAllExtDeviceEndPoints()
    PBXExtensions = config.PBXExtensions
    for username in PBXExtensions:
        for devName in PBXExtensions[username].get('device', []):
            if devName in devList:
                del devList[devName]
    return devList
       

def getAllExtDeviceEndPoints():
    devList = []
    #Start with Hardware
    hw = PBXHardware()
    hw.detect()
    for dev in hw:
        for port in dev:
            if dev.pluginEntity.getPortGroup(port[0]):
                continue
            devList.append(port[0])

    PBXPhones = config.PBX.get('phones', {})
    for phone in PBXPhones:
        devList.append('Phone/' + phone)

    return devList

def resolveProviderDevice(provider):
    output = {}
    if provider['type'] == 'hardware':
        hw = PBXHardware()
        hw.detect()
        #Search for specific port
        for dev in hw:
            portList = dev.getChannelPorts()
            if not portList:
                continue
            for port in portList:
                for device in provider['device']:
                    if port[1][0] == device:
                        #print port
                        output[device] = port[0] 
        #Search for specific Group
        for pluginName, plugin in hw.plugins.items():
            if not plugin.groupSupport:
                continue
            for device in provider['device']:
                if plugin.groupName == device[0:len(plugin.groupName)]:
                   output[device] = plugin.getGroupRouting(device) 
    return output

def resolveDevice(device):
    if 'Phone/' == device[0:6]:
        #Handset device
        return 'SIP/%s' % device[6:]
    else:
        dummyProvider = {
            'device': [device],
            'type': 'hardware'
        }
        devList = resolveProviderDevice(dummyProvider)
        return devList.items()[0][1]

def resolveKeyNumber(key):
    if not key:
        return None
    config.expireCache()
    if 'ext/' == key[0:4]:
        if key[4:] in config.PBXExtensions:
            ext = config.PBXExtensions[key[4:]]
            return ext['extensions'][0], resolveDevice(ext['devices'][0])
    if 'special/' == key[0:8]:
        specKey = key[8:]
        if specKey == 'PICKUP':
            return '*8', 'PickUp(1)' 
        #if specKey == "CONF":
        return None
    if 'queue/' == key[0:6]:
        if key[6:] in config.PBX.get('queues', {}):
            queue = config.PBX.get('queues', {})[key[6:]]
            return queue['extensions'][0], None
    if 'ivr/' == key[0:4]:
        if key[4:] in config.PBX.get('ivr', {}):
            ivr = config.PBX.get('ivr', {})[key[4:]]
            return ivr['extensions'][0], None

def getDeviceExtension(device):
    config.expireCache()
    for extension in config.PBXExtensions.items():
        if device in extension[1]['devices']:
            return extension
    return None

def getExtensionContext(extension):
    return 'userProv-' + str.join('-',extension['outbound'])

def getVoicePrompts():
    allowedExt = ['wav', 'gsm']
    def genFriendlyName(fName):
        return fName.split('.')[0].replace('-',' ')
    output = []
    for fi in sorted(os.listdir('/usr/local/share/asterisk/sounds')):
        if fi.split('.')[-1] not in allowedExt:
            continue
        output.append(('custom/'+fi, genFriendlyName(fi)))
    for fi in sorted(os.listdir('/usr/share/asterisk/sounds')):
        if fi.split('.')[-1] not in allowedExt:
            continue
        output.append((fi, genFriendlyName(fi)))
    return output

class PBXHardware(object):
    """Provides an interface for figuring out hardware details and generating configurations when needed
    Each hardware plugin will generate a set of device entities that can then be used to manage each device seperately.
    The user will then be presented with the devices which then can be configured individually. 
    
    On completion the changes will
    then be applied by the PBXHardware through configurator which will call the .save and then proceed reload asterisk to make the
    changes effective
    """
    name = 'hardware'

    plugins = {} 
    
    def __init__(self):
        """Load all plugins into plugins list"""
        dirList = os.listdir("Core/PBXUtils/HardwarePlugins")
        for pluginFileName in dirList:
            if ".py" == pluginFileName[-3:] and not "__init__" in pluginFileName:
                #try:
                hardwarePlugin = __import__("HardwarePlugins."+pluginFileName.replace(".py",""),globals(), locals(), ['plugins']).Plugin(config)
                if hardwarePlugin.name:
                    self.plugins[hardwarePlugin.name] = hardwarePlugin
                    #print "[PBXHardware] %s(%s) hardware plugin loaded" % (hardwarePlugin.name, hardwarePlugin.description)
                else:
                    print "[PBXHardware] Invalid Plugin(%s): name attribute was not defined" % (pluginFileName)
                #except Exception, e:
                #    print "[PBXHardware] Error Loading Plugin(%s): %s" % (pluginFileName, e)
                #    continue

    def detect(self):
        """Runs a detect method on each plugin and returns a list of cards 
           and generates new entries that should be in the config that are not there presently"""
        result = {}
        for pluginName in self.plugins:
            if self.plugins[pluginName].candetect:
                #try: XXX Needs to be in production
                result[pluginName] = self.plugins[pluginName].detect()
                #except Exception, e:
                    #print "[PBXHardware] Unable to detect hardware using plugin", pluginName, str(e)

        return result

    def save(self):
        """Tells all the plugins to generate their config files"""
        result = True
        for pluginName in self.plugins:
            #try:
            self.plugins[pluginName].save()
            #except Exception, e:
            #    print "[PBXHardware] Unable to save hardware using plugin", pluginName
            #    result = False

        return result

    def __iter__(self):
        """Returns a device iterator so that the user can go through all configured devices"""
        return self.deviceIterator(self.plugins)

    def __getitem__(self, attr):
        for plugin in self.plugins.values():
            if attr in plugin.devices:
                return plugin.devices[attr]
        raise IndexError("Device %s does not exist" % attr)

    def defineRouting(self, routingData):
        """Hook that is used by providers to define device grouping and inbound contexts"""
        chanList = []
        for pluginName in self.plugins:
            res = self.plugins[pluginName].defineRouting(routingData)
            if res:
                chanList.append(res)

    class deviceIterator(object):
        """Iterator to allow the user to iterate through all availible devices (Configured and not configured)"""
        plugins = {}
        devices = []
        def __init__(self, pluginList = {}):
            self.plugins = pluginList
            for pluginName in self.plugins:
                for deviceName in self.plugins[pluginName].devices:
                    self.devices.append(self.plugins[pluginName].devices[deviceName])

        def __iter__(self):
            return self

        def next(self):
            if len(self.devices) > 0:
                return self.devices.pop()
            else:
                raise StopIteration

    def findDevPort(self, portName):
        for dev in self:
            for port in dev:
                if port[0] == portName:
                    return (dev, port)
        return None
                

class PBXCardPortConfig(object):
    """
    Storage Class that is used to define parameters needed from the user when configuring a PBX Port/Card
    This could be a dict however I believe this makes it a little easier to work with
    """
    name = ""
    human_name = ""
    options = {}
    defaultOption = ""
    description = ""
    validationExpression = None
    isAdvanced = False

    def __init__(self, name, human_name, description, options=[], default="", validationExpression=None ):
        self.name = name
        self.human_name = human_name
        self.description = description
        self.options = options
        self.validationExpression = validationExpression
        self.defaultOption = default

    def __str__(self):
        return "{ human_name: '%s', options: '%s', description: '%s', DEFAULT: '%s'}" % (
           self.human_name,
           str(self.options),
           self.description,
           self.defaultOption)

    def advanced(self, state=True):
        self.isAdvanced = state
        return self

class DeviceEntity(object):
    """
    Primitive for parsing and gaining information from the card

    It also wraps the Vulani config parser into the module to simplify the adjustment of individual ports config and
    reduce possible problems in the future.
    """
    name = ""
    description = ""

    chan = ""

    cardParam = {}

    portParam = {}

    groups = {}

    contexts = {}

    groupPrefix = "g"

    supportGroups = True

    pluginEntity = None

    devConfig = None

    pbxConfig = None

    timeVal = 0

    def _renewConf(self):
        if time() - self.timeVal > 1:
            self.devConfig = self.cfg.PBXHardware[self.name]
            self.pbxConfig = self.cfg.PBX
            self.timeVal = time()

    def getDevConf(self):
        self._renewConf()
        return self.devConfig

    def getPBXConf(self):
        self._renewConf()
        return self.pbxConfig

    def checkStatus(self):
        """
        Retrieves the current status of the card
        @returns: tuple of (state, "Textual representation of the status"), where state is -1 for error, 0 for Not Active and 1 for active
        """
        pass

    def write(self):
        """
        If you change an entry within __getitem__ directly it will not save automatically so you should call write to force a write to the
        vulani config
        """
        pass

    def getDeviceContext(self):
        return self.getDevConf().get("context", self.getPBXConf().get('defaultContext', "incomming"))
        #return config.PBXHardware[self.name].get("context", config.PBX.get('defaultContext', "incomming"))

    def getPortContext(self, portNumber):
        return self[portNumber]['context']

    def setPortContext(self, portNumber, context):
        tmp = self[portNumber]
        tmp['context'] = context
        self[portNumber] = tmp

    def __getitem__(self, key):
        """Acquires the configuration for entity"""
        #self._checkConfig()
        if type(key) == int: #Is a port number
            res = self.getDevConf()['ports'][key]
            #res = config.PBXHardware[self.name]['ports'][key] #I want a copy of the data
            #Load the default settings
            for portParam in self.portParam:
                if not portParam.name in res:
                    #res[portParam.name] = portParam.defaultOption
                    res.setdefault(portParam.name, portParam.defaultOption)
            #if "context" not in res:
            #res['context'] = self.getDeviceContext()
            res['context'] = 'incomming' #Change to use incomming
            res['callerid'] = "asreceived"
            res['callgroup'] = ""
            res['pickupgroup'] = ""
            devName = self.getPortList()[key][0]
            ext = getDeviceExtension(devName)
            if ext:
                context = getExtensionContext(ext[1])
                if context:
                    res['context'] = context

                if 'fullcallerID' in ext[1]:
                    res['callerid'] = ext[1]['fullcallerID']

                res['callgroup'] = '0'
                res['pickupgroup'] = '0'

            return res

        if type(key) == str: #Is a config option for the card
            for cardParam in self.cardParam:
                if key == cardParam.name: #If the key is in the parameter list
                    #if key in config.PBXHardware[self.name]['config']: #Check to see if it exist in the config
                    #    return config.PBXHardware[self.name]['config'][key] #Return config entry
                    if key in self.getDevConf()['config']: #Check to see if it exist in the config
                        return self.getDevConf()['config'][key] #Return config entry
                    else:
                        return cardParam.defaultOption #Return default option
            if key == "context":
                return self.getDeviceContext()
                
                    
        raise KeyError("Config key %s for device %s is invalid" % (key, self.name,))

    def __setitem__(self, key, item):
        """Set a config for this entity"""
        self._checkConfig()
        deviceContext = self.getDeviceContext()
        if type(key) == int:#Integers indicate port number
            #Validate the port parameter
            for paramName in item.keys():
                foundState = False
                if paramName == 'context':
                    continue
                for portParam in self.portParam:#could probably simplify this XXX Rewrite at some point
                    #Scan through the portparmamters and make sure that the user has not provided anything outside of the bounds of
                    #the specified parameters, i.e. induce sanity
                    if portParam.name == paramName:
                        foundState = True #Raise state that we found the parameter name
                        break
                if not foundState: #If no foundState then raise an error
                    raise ValueError("Invalid port parameter %s in values %s" % (paramName, item))
            PBXHardware = config.PBXHardware
            PBXHardware[self.name]['ports'][key] = item #update config
            config.PBXHardware = PBXHardware
            return
        elif type(key) == str:#Strings indicate card config
            for cardParam in self.cardParam:
                if key == cardParam.name:
                    PBXHardware = config.PBXHardware
                    PBXHardware[self.name]['config'][key] = item #update config
                    config.PBXHardware = PBXHardware
                    return
            if key == "context": #Set the default context for the card
                PBXHardware = config.PBXHardware
                PBXHardware[self.name]['context'] = item #update config
                config.PBXHardware = PBXHardware
                return
        self.timeVal = 0
        raise KeyError("Key %s is invalid" % key) #If key is not an int and not a string then throw some toys

    def _checkConfig(self):
        """Checks if config for this entry exists if not then it generates it"""
        if not self.name in config.PBXHardware:
            self.prepareConfig()
        if not 'enabled' in config.PBXHardware[self.name]:
            self.prepareConfig() #Just in case
        #Final Check, Count number of ports and make sure they are consistent
        if len(self) != len(config.PBXHardware[self.name]['ports']):
            self.prepareConfig() #We should ever get here but if we do rather than generate an error we should generate a new config
 
    def isConfigured(self):
        return self.isEnabled()

    def prepareConfig(self):
        """Prepares the initial config and generates a default config set for the device based on the params"""
        #Generate the config
        tmp = config.PBXHardware
        tmp[self.name] = { 
            'enabled': False,
            'config': {},
            'context': "",
            'ports': [{} for k, portDet in enumerate(self.getPortList())],
        }
        config.PBXHardware = tmp #Speed the spoil and hasten the booty

    def _setEnableState(self, newState=False):
        """Sets the enable state on the card"""
        self._checkConfig()
        tmp = config.PBXHardware
        tmp[self.name]['enabled'] = newState
        self.timeVal = 0
        config.PBXHardware = tmp

    def enable(self):
        """Enables the device - The device will be included in the configurations and all resulting routing through the device will be enabled"""
        self._setEnableState(True)

    def disable(self):
        """Disables the device - The device will not be included in the generation of the configuration and all related routing will be disabled"""
        self._setEnableState(False)

    def isEnabled(self):
        """Tests to see if the device is enabled or not"""
        self._checkConfig()
        return self.getDevConf()['enabled']

    def getPortList(self):
        """
        Returns a list object of tuples containing details of the port ('name', state, 'status text', providerEntityInstance), the index reflects the port number,
        the state is the current status -1 for error, 0 for normal/idle/inactive, 1 raised state indicates that the port is in use or active and finally the provider instance
        """
        pass
    
    def setPortGroup(self, portNumber, groupNumber):
        """
        Sets the ports groupNumber
        """
        return self.pluginEntity.addPortToGroup(groupNumber, self.getPortList()[portNumber][0])

    def delPortGroup(self, portNumber, groupNumber):
        """
        Removes the port from the groupNumber
        """
        return self.pluginEntity.delPortFromGroup(groupNumber, self.getPortList()[portNumber][0])

    def getPortGroups(self, portNumber):
        """
        Gets a list of groups the plugin belongs to
        """
        return self.pluginEntity.getPortGroup(self.getPortList()[portNumber][0])

    def getChannel(self, portNumber, groupID=None):
        if groupID:
            self.setPortGroup(portNumber, groupID)
            return self.pluginEntity.chan + "/" + self.groupPrefix + groupID
        else:
            return self.pluginEntity.chan + "/" + self[portNumber]

    def getChannelPorts(self):
        """Get A list of valid routable channels and a descriptive name"""
        output = [
            (self.pluginEntity.chan + "/" + str(port[-1]), port) 
            for k, port in enumerate(self.getPortList())
        ]
        return output

    def __len__(self):
        """
        Indicates the number of ports availible in this device
        """
        return len(self.getPortList())

    def __str__(self):
        return "Card Name: %s, Ports: %s" % (self.name, len(self))

    def __iter__(self):
        """Returns an instance of portIterator"""
        self._checkConfig()
        return self.portIterator(self.getPortList())

    class portIterator(object):
        """Iterator to allow the user to iterate through all ports"""
        portList = []
        def __init__(self, portList = []):
            self.portList = portList

        def __iter__(self):
            return self

        def next(self):
            if len(self.portList) > 0:
                return self.portList.pop(0)
            else:
                raise StopIteration
 
class PBXHardwarePlugin(object):
    """Primitive Interface that is used to implement Hardware Plugins"""
    name = ""
    description = ""
    candetect = False

    chan = ""

    """Matches the prefix of the in PBXHardware"""
    groupName = "" 

    groupPrefix = "g"
    
    """If hardware type support port grouping such as zaptel then set this to True"""
    groupSupport = False

    devices = {}

    timeVal = 0

    curConfig = None

    def _renewConf(self):
        if time() - self.timeVal > 1:
            self.curConfig = self.cfg.PBXHardware
            self.timeVal = time()

    def getConf(self):
        """Gets the PBXHardware Config"""
        self._renewConf()
        return self.curConfig

    def __init__(self):
        pass

    def detect(self):
        pass

    def save(self):
        pass

    def defineRouting(self, routingData):
        pass

    def _genGroupNumName(self, groupNumber):
        return self.groupName + '/' + str(groupNumber)

    def setGroup(self, groupNumber, portList):
        """set the groups port list"""
        if type(portList) == list:
            """Must be a list"""
            PBXHardware = config.PBXHardware
            PBXHardware[self._genGroupNumName(groupNumber)] = portList
            config.PBXHardware = PBXHardware
            self.timeVal = 0

    def addPortToGroup(self, groupNumber, port):
        """Adds the port to the group"""
        portList = self.getGroup(groupNumber)
        if port not in portList:
            portList.append(port)
            self.setGroup(groupNumber, portList)

    def delPortFromGroup(self, groupNumber, port):
        """Deletes a port from a group"""
        portList = self.getGroup(groupNumber)
        if port in portList:
            portList.remove(port)
            self.setGroup(groupNumber, portList)

    def getGroup(self, groupNumber):
        """get the groups port list"""
        return self.getConf().get(self._genGroupNumName(groupNumber), [])

    def getPortGroup(self, portName):
        """Fetch the groups for the portName"""
        groupList = []
        for group in self.getGroupList():
            if portName in self.getConf().get(self._genGroupNumName(group), []): 
                groupList.append(group)
        return groupList

    def getGroupChan(self, groupNumber):
        """gets the group chan used for dialing"""
        return self.getConf().get(self._genGroupNumName(groupNumber), [])
    
    def groupExists(self, groupNumber):
        return self.getConf().get(self._genGroupNumName(groupNumber), False) and True or False

    def getGroupList(self):
        """get a list of groups"""
        groupList = []
        for key in self.getConf().keys():
            if self.groupName + "/" in key[:len(self.groupName)+1]:
                groupNumber = key[len(self.groupName)+1:]
                groupList.append(groupNumber)
        return groupList

    def getGroupRouting(self, groupName):
        if self.groupName == groupName[:len(self.groupName)]:
            if groupName in self.getConf().keys():
                return "%s/%s%s" % (
                    self.chan,
                    self.groupPrefix,
                    groupName[len(self.groupName)+1:]
                )

def enabled():
    """Returns the currents PBX Enable state also creates the entry if it does not exist and set it to false by default"""
    if "enabled" in config.PBX:
        return config.PBX["enabled"]
    else:
        tmpPBX = config.PBX
        tmpPBX["enabled"] = False
        config.PBX = tmpPBX

