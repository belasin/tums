from twisted.python import log, syslog, failure
from nevow import rend, loaders, tags
from twisted.application import service, internet, strports, app
from twisted.internet import reactor
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
import sys
import storage

try:
    from twisted.scripts import _twistd_unix as twistd
except:
    from twisted.scripts import twistd

def initialiseDatabase(db):
    d = db.startup()
    def failure(_):
        print "[Enamel Error] Database startup failed"
    def started(_):
        print "Database started"
    return d.addCallbacks(started, failure)

def run(appname, services, pidLoc='/var/run'):
    """ Roll a list of services into an application and start it
    for example:
    deployment.run('testApp', (
        (TCPServer, 8080, (myWebApplication)), 
        (SSLServer, 443, (mySSLApplication, ServerContext))
    ) 
    This launches two applications, one is an SSL servlet which requires a context argument.
    """
    application = service.Application(appname)

    serviceList = []
    # Create a service list and add it to the application parent
    for app in services:
        app.parentName = appname
        # Create database bootstraps if required.
        if isinstance(app.storage, storage.SQL): # only valid for SQL
            reactor.callWhenRunning(initialiseDatabase, app.storage)
        serviceList.append(app.server(app.port, *app.site()))
        serviceList[-1].setServiceParent(application)

    nodaemon = 1 
    log = None
    if len(sys.argv) > 1:
        if sys.argv[1] == "-d":
            nodaemon = 0
            log = logfile= '/var/log/%s.log' % appname

    startTwisted(application, nodaemon = nodaemon, logfile= log, pidfile='%s/%s.pid' % (pidLoc, appname))

def startTwisted(application, startDir = './', nodaemon = 0, logfile=None, rundir='.', appname='enamel', pidfile='/var/run/enamel.pid'):
    """ A freezable twistd bootstrap layer """
    config = {
        'profile': None,          'reactor': None,
        'encrypted': 0,           'syslog': None,
        'prefix': appname,        'report-profile': None,
        'euid': 0,                'file': 'twistd.tap',
        'originalname': appname,  'rundir': rundir,
        'logfile': logfile,       'nodaemon': nodaemon,
        'uid': None,              'xml': None,
        'chroot': None,           'no_save': True,
        'quiet': 0,               'source': None,
        'nothotshot': 0,          'gid': None,
        'savestats': 0,           'debug': False,
        'pidfile': pidfile,       'umask': None,
    }

    #application = compat.convert(application)

    twistd.checkPID(config['pidfile'])
    #app.installReactor(config['reactor'])

    config['nodaemon'] = config['nodaemon'] or config['debug']

    oldstdout = sys.stdout
    oldstderr = sys.stderr
    try:
        twistd.startLogging(
            config['logfile'], 
            config['syslog'],
            config['prefix'], 
            config['nodaemon']
        )
        passDeprecate = False
    except AttributeError:
        passDeprecate = True
        if config['nodaemon']:
            config['logfile'] = "-"

    #if not passDeprecate:
    #app.initialLog()

    try:
        twistd.startApplication(config, application)
        print "twisted 2.5"
    except AttributeError:
        print "wt?"
        # Use hotshot in Twisted 8.x
        config['profiler'] ='hotshot'
        AR = twistd.UnixApplicationRunner(config)
        AR.startApplication(application)
        AR.logger.start(application)

    app.runReactorWithLogging(config, oldstdout, oldstderr)

    try:
        twistd.removePID(config['pidfile'])
    except AttributeError:
        AR.removePID(config['pidfile'])

    if not passDeprecate:
        app.reportProfile(
            config['report-profile'],
            service.IProcess(application).processName
        )
    log.msg("Server Shut Down.")

