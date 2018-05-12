#!/usr/bin/python
import tcsStore

testUpdateResponse = [
    ("roundCube", "1.2"),
    ("tums1.4", "1.2"),
    ("tcs-LTSP", "1.2")
]

store = tcsStore.TCSStore()

def getNewUpdates():
    """ Retrieve availiable updates for this version """
    current = store.getInstalled()
    myVersion = store.getCurrentVersion()
    new = []
    updateResponse = testUpdateResponse # This should be an RPC call with the version number
    for u in updateResponse:
        if not u[0] in current:
            if u[1] == store.getCurrentVersion():
                new.append(u[0])
    store.updateUpdates(new)
    return new

getNewUpdates()
print store.getInstalled()
print store.getUpdates()
