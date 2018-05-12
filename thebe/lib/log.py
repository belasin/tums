
logTypes = {
    'KEYAUTH': (
        'Key Authorization',
        lambda x: "Request from %s" % x.split('+')[-1]
    ), 
    'CRITICAL': (
        'Critical Error', 
        lambda x: x
    )
}

def formatLogType(type):
    if type in logTypes:
        return logTypes[type][0]
    else:
        return type.lower().capitalize()

def formatLogMessage(type, message):
    if type in logTypes:
        if message != None:
            return logTypes[type][1](message)
        else:   
            return logTypes[type][1]('')
    else:
        return message
