#!/usr/bin/python
import sys, os, time, termios, fcntl, struct
import xmlrpclib, sha
sys.path.append('.')
sys.path.append('/usr/lib/python2.5/site-packages')
sys.path.append('/usr/lib/python2.5')
sys.path.append('/usr/local/tcs/tums')
sys.path.append('/usr/local/tcs/tums/lib/')

# stub encodings hack for freeze
import encodings
from encodings import ascii, utf_8, latin_1
a = u"a"
b = a.encode()
# end stub encodings hack

def currentProfile():
    try:
        l = open('/usr/local/tcs/tums/currentProfile')
    except:
        return ("Default", "default.py")
    i = l.read().replace('\n', '').strip() 
    name = i[:-3].replace('_', ' ').capitalize()
    return (name, i)

def runningProfile():
    try:
        l = open('/usr/local/tcs/tums/runningProfile')
    except:
        return ("Default", "default.py")
    i = l.read().replace('\n', '').strip() 
    name = i[:-3].replace('_', ' ').capitalize()
    return (name, i)

# Before importing the config, copy the profile into place. 

if not os.path.exists('/usr/local/tcs/tums/profiles'):
    print "No profiles have been found. I will upgrade the default profile from the current config.py and"
    print "create a default config in /usr/local/tcs/tums/profiles"
    os.system('mkdir /usr/local/tcs/tums/profiles')
    from plugins import upgradeConfig
    upgrader = upgradeConfig.Plugin() 
    upgrader.writeConfig()
    os.system('cp /usr/local/tcs/tums/config.py /usr/local/tcs/tums/profiles/default.py')
    os.system('echo default.py > /usr/local/tcs/tums/runningProfile')
    os.system('echo default.py > /usr/local/tcs/tums/currentProfile')
    print "The default configuration has been created, please re-run configurator with the operation you were attempting."
    sys.exit(1)

cP = currentProfile()[1]
if currentProfile() == runningProfile():
    if os.path.exists("/usr/local/tcs/tums/profiles/%s" % cP):
        os.system('echo "# Running config - Please do not edit this file anymore."> /usr/local/tcs/tums/config.py')
        os.system('echo "# Edit the running profile in /usr/local/tcs/tums/profiles">> /usr/local/tcs/tums/config.py')
        os.system('cat /usr/local/tcs/tums/profiles/%s >> /usr/local/tcs/tums/config.py' % cP)
    else:
        print "No valid profile could be found. Please ensure you use profiles under /usr/local/tcs/tums/profiles"
        sys.exit(1)

# Flush any byte-compiled config info
os.system('rm /usr/local/tcs/tums/config.pyc > /dev/null 2>&1') 
import config

import debianDefaults
defaults = debianDefaults

sets = []
configRepo = "http://tcs-config.thusa.co.za/"
configPath = "/usr/local/tcs/tums/"
sys.path.append(configPath)
#configPath = "/root/dev/TUMS/trunk/source/"
methodDests = {}

def writeConf(conf, data, comsymbol): 
    """ Wrapper method for writing a config file"""
    if data:
        l = open(conf, 'wt') 
        if comsymbol:
            l.write(comsymbol + '# Generated by Vulani Configurator - http://vulani.net on %s \n' % time.ctime()) 
        l.write(data)
        l.close()

def DEBUG(message):
    """ Debugging wrapper that trigers with the V sets-flag """
    if "V" in sets:
        print message

def fixNetwork(*a):
    os.system("for i in `ls /sys/class/net/ | grep eth`; do echo SUBSYSTEM==\"net\", `udevinfo -a -p /sys/class/net/$i | grep address | sed 's/\ //g'`, NAME=\"$i\"; done > /etc/udev/rules.d/20-network.rules")

def writeTemplate(workfile, destination):
    """ Writes a template and applies the replacement operations 
    @param workfile: C{str} File to use as a template
    @param destination: C{str} Destination config file to write
    """

    if 'V' in sets:
        print "Rewriting %s to %s..." % (workfile, destination)
    tfile = open(workfile).read()
    for find, replace in defaults.StandardFiles['replacers']:
        temp = tfile.replace(find, replace)
        tfile = temp
    try:
        dfile = open(destination, 'wt')
        dfile.write(tfile)
        dfile.close()
    except:
        pass

def runTemplates(*a):
    """ Run all the template operations """
    DEBUG("Configuring all templates")
    for workfile, destination in defaults.StandardFiles['files']:
        writeTemplate('%sconfigs/%s' % (configPath, workfile), destination)

def applyDestination(*paths):
    """ Apply a template (OR plugin) based on the desired config file
    NOTE: For plugins responsibile stuff, other config files may be written
    over as well"""
    DEBUG("Configuring destination set %s" % repr(paths))
    written = []
    
    for workfile, destination in defaults.StandardFiles['files']:
        if destination in paths:
            writeTemplate('%sconfigs/%s' % (configPath, workfile), destination)
            written.append(destination)
    for path in paths:
        if path in methodDests.keys():
            print "Branch method ", methodDests[path]
            if type(methodDests[path]) is list:
                for l in methodDests[path]:
                    l()
            else:
                methodDests[path]()
            written.append(path)
        if path not in written:
            print "I don't know how to write %s, you probably want -t." % path
        
def pullConfig(*a):
    """ Downloads a config from a server specified by C{str}configRepo 
    """
    def getID():
        conf = raw_input("Configuration Id [? to list, ! to bail]: ")
        if "!" in conf:
            return None
        if "?" in conf:
            os.system('rm fl > /dev/null 2>&1; wget -q %sfl'% configRepo)
            fl = open('fl')
            confs = []
            for i in fl:
                fi = i.strip('\n')
                if fi != "fl":
                    confs.append(fi.strip('.py'))
            spaces = " "
            l = len(confs)
            rows = (l/5)+1
            for i in range(rows):
                line = ""
                for k in range(i*5, 5+(i*5)):
                    if k < l:
                        cell = confs[k]
                        spaces = " "*(20-len(cell))
                        line+= cell + spaces
                print line
            conf = getID()
        return conf
    confid = getID()
    os.system('rm %s.py  > /dev/null 2>&1; wget -q %s%s.py' % (confid, configRepo, confid))
    if not confid:
        return None
    try:
        config = __import__(confid)
        try:
            if config.CompanyName:
                print "Configuration successfully retrieved"
                os.system('cp %s.py %sconfig.py' % (confid, configPath))
        except:
            print "Configuration failed. Please ensure the configuration is valid"
    except:
        print "Configuration failed. Please ensure you have entered a valid configuration id"
        
BOLD = '\033[1m'
RED = BOLD+'\033[31m'
GREEN = BOLD+'\033[32m'
BLUE = BOLD+'\033[34m'
YELLOW = BOLD+'\033[33m'
RESET = '\033[0;0m'

def getSize():
    try:
        s = struct.pack("HHHH", 0, 0, 0, 0)
        fd_stdout = sys.stdout.fileno()
        x = fcntl.ioctl(fd_stdout, termios.TIOCGWINSZ, s)
        return struct.unpack("HHHH", x)[:2]
    except:
        # Unsupported terminal
        return (25,80)

def printBanner(text):
    rows, cols = getSize()
    blocks = (cols/4) - (len(text)/2) +4
    space = "="*blocks
    print YELLOW+space+" "+text+" "+space+RESET

def printMod(name, status):
    ok = "[ %sOK%s ]" %( GREEN, RESET )
    fail = "[%sFAIL%s]" % ( RED, RESET )

    if status:
        stat = ok
    else:
        stat = fail

    rows, cols = getSize()
    dots = (cols/2) - len(name)

    print " "+name+"."*dots, stat

def reconfigure(*a):
    runTemplates()
    for plug in plugins:
        if plug.autoRun:
            try:
                plug.writeConfig()
                printMod(plug.parameterDescription, True)
            except Exception, e:
                printMod(plug.parameterDescription, False)
                print e

    print "Reloading services"
    for plug in plugins:
        if plug.autoRun:
            try:
                plug.reloadServices()
                printMod(plug.parameterDescription, True)
            except Exception, e:
                printMod(plug.parameterDescription, False)
                print e

def prePrep():
    # Debian needs some preprep stuff
    print "Performing Debian prepreparations"
    os.system('mkdir -p /var/lib/samba/data > /dev/null 2>&1')
    os.system('mkdir /var/lib/samba/netlogon > /dev/null 2>&1')
    os.system('mkdir /var/lib/samba/profiles > /dev/null 2>&1')
    os.system('cp -a /usr/share/doc/shorewall/default-config/* /etc/shorewall/ > /dev/null 2>&1')

def prep(*a):
    prePrep()
    runTemplates()
    TUMS = __import__("plugins.TUMS", globals(), locals(), ['plugins']).Plugin()
    TUMS.writeConfig()

    for plug in plugins:
        if plug.autoRun:
            try:
                plug.writeConfig()
                printMod(plug.parameterDescription, True)
            except Exception, e:
                printMod(plug.parameterDescription, False)
                print e

def debianAll(*a):
    if not os.path.exists('/usr/local/tcs/tums/packages/set') or not os.path.exists('/usr/local/tcs/tums/keyfil'):
        print """You are missing an important file created during the setup process. 
/usr/local/tcs/tums/tums-setup.py creates this file, which is the 
preferred method of installation.
"""
    # These may not fail
    DebianTCS = __import__("plugins.DebianTCS", globals(), locals(), ['plugins']).Plugin()
    PostPrep = __import__("plugins.PostPrep", globals(), locals(), ['plugins']).Plugin()

    # Do some self preparation 
    if not os.path.exists('/root/cdinst'):
        os.system('aptitude -q update > /dev/null 2>&1')
        os.system('DEBIAN_FRONTEND="noninteractive" apt-get -y -q --force-yes install python-zopeinterface build-essential python-dev > /dev/null 2>&1')
    os.system('cd /usr/local/tcs/tums/packages; tar -jxf Twisted-8.2.0.tar.bz2')
    os.system('cd /usr/local/tcs/tums/packages/Twisted-8.2.0; python setup.py install > /dev/null 2>&1')
    print "Preparing Debian system..."
    DebianTCS.writeConfig()

    print "Preparing configurations..."
    prep()
    print "Preparing base system..."
    PostPrep.writeConfig()

methodDests = {}

moduleHelp = ""

plugins = []

def help(*a):
    helpText = """Vulani Configurator by Colin Alston. Copyright (C) THUSA 2007 - http://vulani.net

Usage: configurator [option] [operation]
   or: configurator [[option] [parameter 1] [parameter 2] [...] [parameter n]]

Operations: 
   --help                 Displays this help screen 
   -f PATH1 [PATH2] ...   Apply a specific configuration file. Specify the
                          *destination* configuration file(s) to be written.
   -t TEMPLATE DEST       Write a configuration file from a specified template TEMPLATE 
                          and write it to destination config file DEST.

Non-template operations 
   -R                     Pull the configuration from the remote repository
   -r                     Re-applies all configuration settings and restarts 
                          the associated daemons
   -B                     Applies all configuration settings without reloading anything

Modules
%s

Operations are run in the order they are specified. 
EG. If you want to install a machine for the first time, the correct syntax is
   configurator -B --postprep
""" % moduleHelp
    print helpText

def processArgs():
    """ An arguments processing hack """
    global sets, moduleHelp
    argc = len(sys.argv)-1
    argv = sys.argv[1:]

    settors = {
        '-v':'V'
    }
    
    params = {
        '--help': help, 
        '-t':writeTemplate,
        '-f':applyDestination,
        '-R': pullConfig,
        '-r': reconfigure,
        '-B': prep,
        '-D': debianAll
    }

    # Apply plugins
    # 
    # This scans through the plugins directory for all .py files except __init__.py
    # These files are all loaded and reference pointers appended to C{list} plugins 
    # Plugins can add their own parameter methods, help texts etc (see the plugins own code)
    #
    plugs = os.listdir(configPath + 'plugins/')
    plugs.sort()

    finalHooks = []

    for plug in plugs:
        if ".py" == plug[-3:] and not "__init__" in plug:
            try:
                module = __import__("plugins."+plug.replace('.py',''), globals(), locals(), ['plugins']).Plugin()
            except Exception, _e:
                print "Error loading plugin %s, %s" % (str(plug), str(_e))    
                continue

            # Check if module should run last 
            try:
                if module.runLast:
                    finalHooks.append((module.parameterHook, None, module.writeConfig))
                    runsLast = True
                else:
                    runsLast = False
            except:
                # Not set...
                runsLast = False
            
            if not runsLast:
                if module.parameterHook in params:
                    params[module.parameterHook].append(module.writeConfig)
                else: # First module of this name encountered (or first one without runsLast)
                    params[module.parameterHook] = [ module.writeConfig ]

            for file in module.configFiles:
                if not runsLast:
                    if file in methodDests:
                        methodDests[file].append(module.writeConfig)
                    else:
                        methodDests[file] = [module.writeConfig]
                else:
                    finalHooks.append((None, file, module.writeConfig))

            spaces = " " * (21-len(module.parameterHook+module.parameterArgs))

            # If this is the first one, not an override
            if module.parameterHook not in moduleHelp and not runsLast:
                moduleHelp += "   %s %s %s\n" % (module.parameterHook+module.parameterArgs, spaces, module.parameterDescription)

            if not runsLast:
                plugins.append(module)
            else:
                finalHooks.append((None, None, module))
    
    for hook, file, plugin in finalHooks:
        if hook:
            params[hook].append(plugin)        
        elif file:
            if file in methodDests:
                methodDests[file].append(plugin)
            else:
                methodDests[file] = [plugin]
        else:
            plugins.append(plugin)

    if argc<1:
        help()

    paramin = {}
    paramin_ordered = []
    lastparam = ""
    for argument in argv:
        if '-' in argument[0]:
            lastparam = argument
            paramin[argument]=[]
            paramin_ordered.append(argument)
        else:
            paramin[lastparam].append(argument)

    for param in settors.keys():
        if param in paramin.keys():
            sets.append(settors[param])
    
    for param in paramin_ordered:
        if param in params.keys():
            if type(params[param]) is list:
                # We have multiple parameters 
                for meth in params[param]:
                    meth(*paramin[param])
            else:
                params[param](*paramin[param])
        elif not param in settors.keys():
            print "Unknown operation %s. See --help for correct usage" % param

if __name__ == '__main__':
    # Check profile settings
    processArgs()



