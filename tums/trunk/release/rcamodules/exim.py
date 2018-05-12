# RCA for Exim

from Core import WebUtils
import os

log_problems = [
    ('failed to stat /var/spool/mail/forward/', 'Mail spool failure. Spool directory is damaged'),
    ('clamd: unable to connect to UNIX socket /var/run/clamav/clamd.sock (No such file or directory)', 
        'Mail anti-virus critical failure. No socket'),
    ('failed to bind the LDAP connection to server', 'Mail critical failure. LDAP server is faulty'),
    ('no IP address found for host', 'Possible DNS fault'),
]

class RCA(object):
    def __init__(self, logger):
        self.logger = logger
        self.runChecks()

    def checkLog(self):
        def processResult(result):
            print result
            for i,v in log_problems:
                if i in result:
                    self.logger.log(v)
            return None
        return WebUtils.system('tail -n 20 /var/log/exim4/mainlog').addCallback(processResult)

    def checkProcess(self):
        def processResult(result):
            if 'exim' not in result:
                self.logger.log('Mail critical failure. No mail daemon running')
            return None
        return WebUtils.system('ps aux | grep exim | grep -v grep').addCallback(processResult)

    def checkClam(self):
        try:
            os.stat('/var/run/clamav/clamd.sock')
        except:
            self.logger.log('No socket bound for anti-virus')
        return None

    def runChecks(self):
        checks = [self.checkProcess(), self.checkClam(), self.checkLog()]
        return checks
