# RCA for Exim

from Core import WebUtils
import os

log_problems = [
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

    def runChecks(self):
        checks = [self.checkLog()]
        return checks
