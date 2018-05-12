# Sweeper 
# Provides functions to clean trash between versions, to make sure dpkg
# has done its job

import os

forCleaning = [
    '/usr/local/tcs/tums/epsilon',
    '/usr/local/tcs/tums/sqlalchemy',
    '/usr/local/tcs/tums/formal',
    '/usr/local/tcs/tums/pycha',
    '/usr/local/tcs/tums/nevow',
    '/usr/local/tcs/tums/axiom',
    '/usr/local/tcs/tums/formless',
    '/usr/local/tcs/tums/sasync',
    '/usr/local/tcs/tums/reportlab'
]

def cleanAll():
    rmcmd = '/bin/rm -rf %s > /dev/null 2>&1'
    
    for path in forCleaning:
        if os.path.exists(path):
            os.system(rmcmd % path)
