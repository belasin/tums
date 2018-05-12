#!/usr/bin/python

import sys, os

modList = [
    "ldappass",
    "epsilon",
    "axiom",
    "email",
    "defaults",
    "config",
    "Settings",
    "twisted",
    "xml",
    "nevow",
    "sasync",
    "sqlalchemy",
    "plugins",
    "dom",
    "lang",
    "zope",
    "OpenSSL",
    "Crypto",
    "binascii",
    "sha",
    "md5",
    "mysql",
    "termios",
    "fcntl",
    "struct",
    "pycha", 
    "cairo",
    "formal", 
    "reportlab", 
    "PIL", 
]

if len(sys.argv) > 1:
    relnum = sys.argv[1]
    if len(sys.argv) >2:
        configonly = True
    else:
        configonly = False
    
    os.system("rm -rf /root/build/Vulani/tums/branches/rel/%s" % relnum)
    print "Creating and tagging branch"
    os.system("cp -a /root/build/Vulani/tums/trunk/etch-release /root/build/Vulani/tums/branches/rel/%s" % relnum)

    loc = os.getcwd()

    newwd = "/root/build/Vulani/tums/branches/rel/%s" % relnum

    if not os.path.exists(newwd):
        print "Unable to change to new working directory, ", newwd
        sys.exit(1)

    os.chdir(newwd)
    print os.getcwd(), newwd
    if os.getcwd() == newwd:
        # Update version tag

        os.system ("sed  \"s/VERSION = .*/VERSION = '%s'/\" -i Core/PageHelpers.py" % relnum)
        os.system('echo > /root/build/freezeLog')

        fi = (
            ("Vulani/tums.", "tums.py"), 
            ("Vulani/tums Flow Collector.", "tums-fc.py"), 
            ("Configurator.", "configurator.py"),
            ("post-prep LDAP binders.", "ldapConfig.py")
        )

        if configonly:
            fi = [("Configurator.", "configurator.py")]

        for name, filen in fi:
            
            print "Building", name,
            if (filen == "tums.py") or (filen=="configurator.py"):
                myList = ' -x '.join(modList)
               # myList += ' -x encodings -x ascii -x utf-8 -x latin-1 '
            else:
                myList = ' -x '.join(modList)

            os.system("/root/build/Vulani/tums/trunk/build/Python-2.5.1/Tools/freeze/freeze.py -x %s %s >> /root/build/freezeLog 2>&1" % (myList, filen))
            print ".", 
            os.system("make >> /root/build/freezeLog 2>&1")
            print ".", 
            os.system("rm *.c *.o")
            os.system("rm Makefil*")
            print "."

        print "Cleaning."
        coms = [
            "rm -rf Pages",
            "rm Core/Auth.py Core/AuthApacheProxy.py Core/PageHelpers.py Core/Shorewall.py 2>&1",
            "rm conftest.py dbTest.py deploy-man.py tcsStore.py updateTest.py Settings.py testExcept.py > /dev/null 2>&1",
            "rm Tree.py Settings.py.backup bot.py configtest.py install.py lillith-thusa.py testLDAP.py xmlrpc.py ldapConfig.py > /dev/null 2>&1",
            "rm Realm.py backupConf.py configurator.py demo-config.py test_tums.py tums.py tums-fc.py dogbert.py > /dev/null 2>&1",
            "rm tcsstore.dat > /dev/null 2>&1",
            "rm statdb/* ",
            "rm testExcept.py",
            "rm Checks.py",
            "rm keyfil",
            "rm flr",
            "rm -rf _trial_temp",
            "mv config.py config.py.dist",
            "rm -rf db.axiom",
            "rm -rf profiles",
            "rm -rf tums.axiom",
            "rm -rf rrd/*",
            "rm -rf ThebeProtocol",
            "rm -rf images/graphs/*",
            "rm backup.dat",
            "rm tcsstore.dat",
            "rm test*",
            "rm config.*",
            "find . -iname \"*.pyc\" | xargs rm",
            "find . -iname \".svn\" | xargs rm -rf",
        ]

        for i in coms:
            print ".",
            os.system(i)

        print "Reconfiguring environment"
        os.chdir(loc)
        print "Done!"
    else:
        print "Can't move to location. Stopping before i break things."
