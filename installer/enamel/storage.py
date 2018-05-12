import sqlalchemy as sa
from sasync.database import AccessBroker, transact
from zope.interface import implements, Interface
from twisted.internet import defer, reactor



class IStorage(Interface):
    """ Parent for all storage instances """
    pass

class Vanilla(object):
    """ Vanila Storage class. Does nothing, can have simple deferreds implemented in it
        Must be subclassed.
    """
    implements(IStorage)


class SQL(AccessBroker):
    """ SQLAlchemy storage class. 
        Must be subclassed.
    """
    implements(IStorage)
    
    tables = {}

    def userStartup(self):
        tlist = []
        for table, cols in self.tables.items():
            tlist.append(self.table(table, 
                *tuple(cols)
            ))
        if tlist:
            return defer.DeferredList(tlist)

