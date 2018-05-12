import sqlalchemy as sa
from sasync.database import AccessBroker, transact
import sha, time, datetime, os
from twisted.internet import defer, reactor
import Settings

from axiom.store import Store
from axiom.item import Item
from axiom.attributes import bytes, boolean, reference, integer, AND
from axiom.errors import ItemNotFound
from axiom.upgrade import registerAttributeCopyingUpgrader

class Volume(Item):
    """ Item class represents a volume record for netflow data """
    typeName = 'db_volume'
    schemaVersion = 1

    vIn = integer()
    vOut = integer()

    timestamp = integer()
    month = integer()
    year = integer()
    day = integer()

    port = integer()

    localIp = bytes()

class AggregatorDatabase:
    """ Database object for NetFlow aggregator"""
    def __init__(self):
        self.store = Store('/usr/local/tcs/tums/db.axiom')

    def addVolume(self, ip, vIn, vOut, port):
        # Volume records may generaly have *either* vIn or vOut.
        # This is because a flow record adds only per flow which is in 
        # a single direction. 
        # We aggregate more to the port, we don't care about connector source 
        # ports because these are *always* random high ports.
        timenow = int(time.time())
        date = datetime.datetime.now()
        month = date.month
        year = date.year
        day = date.day

        volume = self.store.findOrCreate(Volume,
            localIp = ip,
            port = port, 
            vIn = vIn,
            vOut = vOut,
            timestamp = timenow,
            month = month,
            year = year,
            day = day
        )

    def getVolumeTotalByIp(self, month, year, day=0):
        if day > 0:
            volumeRecs = self.store.query(Volume,
                AND(Volume.month==month, Volume.year==year, Volume.day==day)
            )
        else:
            volumeRecs = self.store.query(Volume,
                AND(Volume.month==month, Volume.year==year)
            )
        volumeTotalsByIp = {}
        for volume in volumeRecs:
            if volume.localIp in volumeTotalsByIp:
                volumeTotalsByIp[volume.localIp][0] += volume.vIn
                volumeTotalsByIp[volume.localIp][1] += volume.vOut
            else:
                volumeTotalsByIp[volume.localIp] = [volume.vIn, volume.vOut]

        return volumeTotalsByIp

    def getVolumeRecByIp(self, month, year, ip):
        return [(i.timestamp, i.vIn, i.vOut) for i in self.store.query(Volume,
            AND(Volume.month==month, Volume.year==year, Volume.localIp==ip)
        )]

    def getPortBreakdownForIp(self, month, year, ip, day=0):
        if day <1:
            volumeRecs = self.store.query(Volume,
                AND(Volume.month==month, Volume.year==year, Volume.localIp==ip)
            )
        else:
            volumeRecs = self.store.query(Volume,
                AND(Volume.month==month, Volume.year==year, Volume.localIp==ip, Volume.day ==day)
            )
 
        
        volumeByPort = {}
        for volume in volumeRecs:
            if volume.port in volumeByPort:
                volumeByPort[volume.port][0] += volume.vIn
                volumeByPort[volume.port][1] += volume.vOut
            else:
                volumeByPort[volume.port] = [volume.vIn, volume.vOut]
        return volumeByPort

    def getPortTotals(self, month, year, day=0):
        if day > 0:
            volumeRecs = self.store.query(Volume,
                AND(Volume.month==month, Volume.year==year, Volume.day==day)
            )
        else:
            volumeRecs = self.store.query(Volume,
                AND(Volume.month==month, Volume.year==year)
            )

        volumeByPort = {}
        for volume in volumeRecs:
            if volume.port in volumeByPort:
                volumeByPort[volume.port][0] += volume.vIn
                volumeByPort[volume.port][1] += volume.vOut
            else:
                volumeByPort[volume.port] = [volume.vIn, volume.vOut]
        return volumeByPort

def hashPass(strng):
    """ SHA1 hash a string
    @param strng: any C{str}
    """
    return sha.sha(strng).hexdigest()
    
class DatabaseBroker(AccessBroker):
    """Provides a sAsync AccessBroker
       myBroker = DatabaseBroker('sqlite://foo.db')
    """
    def userStartup(self):
        messages = self.table('messages',
            sa.Column('server',         sa.String(32)),
            sa.Column('message_id',     sa.String(16)),
            sa.Column('timestamp',      sa.Integer),
            sa.Column('msgid',          sa.String(255)), # 3
            sa.Column('completed',      sa.Integer),
            sa.Column('mailfrom',       sa.String(255)), # 5
            sa.Column('host_addr',      sa.String(15)),
            sa.Column('host_rdns',      sa.String(255)),
            sa.Column('host_ident',     sa.String(255)),
            sa.Column('host_helo',      sa.String(255)),
            sa.Column('proto',          sa.String(32)),
            sa.Column('size',           sa.Integer),
            sa.Column('tls_cipher',     sa.String(128)),
            sa.Column('user',           sa.String(128)),
            sa.Column('bounce_parent',  sa.String(16))
        )
    
        deliveries = self.table('deliveries',
            sa.Column('server',             sa.String(32)), # 15 down
            sa.Column('message_id',         sa.String(16)),
            sa.Column('timestamp',          sa.Integer),
            sa.Column('rcpt',               sa.String(200)), # 18
            sa.Column('rcpt_intermediate',  sa.String(200)),
            sa.Column('rcpt_final',         sa.String(200)),
            sa.Column('host_addr',          sa.String(15)),
            sa.Column('host_dns',           sa.String(255)),
            sa.Column('tls_cipher',         sa.String(128)),
            sa.Column('router',             sa.String(128)),
            sa.Column('transport',          sa.String(128)),
            sa.Column('shadow_transport',   sa.String(128))
        )
    
        queue = self.table('queue', 
            sa.Column('server',               sa.String(32)),
            sa.Column('message_id',           sa.String(16)),  #1
            sa.Column('mailfrom',             sa.String(255)), #2
            sa.Column('timestamp',            sa.Integer),     #3
            sa.Column('num_dsn',              sa.Integer),
            sa.Column('frozen',               sa.Integer),
            sa.Column('recipients_delivered', sa.BLOB),        #5
            sa.Column('recipients_pending',   sa.BLOB),        #7
            sa.Column('spool_path',           sa.String(64)),  
            sa.Column('subject',              sa.String(255)), #9
            sa.Column('msgid',                sa.String(255)), 
            sa.Column('headers',              sa.BLOB),
            sa.Column('action',               sa.String(64))   #12
        )
        
        return defer.DeferredList([deliveries, messages, queue])
    
    @transact
    def getLastMessages(self, offset=0):
        return sa.join(
                          self.messages, self.deliveries, self.messages.c.message_id == self.deliveries.c.message_id
                      ).select(limit=20, offset=offset, order_by=[sa.desc(self.messages.c.timestamp)]).execute().fetchall()
    
    @transact 
    def searchMessages(self, eto, efrom, fromdate, todate):
        q = []
        if efrom and efrom != "None":
            q.append(self.messages.c.mailfrom.like('%'+efrom+'%'))

        if eto and eto != "None":
            q.append(self.deliveries.c.rcpt.like('%'+eto+'%'))

        if int(fromdate):
            if int(todate):
                if int(todate) > int(fromdate):
                    q.append(self.messages.c.timestamp > int(fromdate))
                    q.append(self.messages.c.timestamp < int(todate))
                else:
                    q.append(self.messages.c.timestamp < int(fromdate))
                    q.append(self.messages.c.timestamp > int(todate))
            else:
                q.append(self.messages.c.timestamp > int(fromdate))

        elif int(todate):
            q.append(self.messages.c.timestamp < int(todate))
    
        return sa.join(
                          self.messages, self.deliveries, self.messages.c.message_id == self.deliveries.c.message_id
                      ).select(sa.and_(*q)).execute().fetchall()
    
    @transact
    def getMailQueue(self):
        return self.queue.select(order_by=[sa.desc(self.queue.c.timestamp)]).execute().fetchall()
    
    @transact
    def arbQuery(self):
        return self.messages.select().execute().fetchone()



class MySAR(AccessBroker):
    """Provides a sAsync AccessBroker for MySAR
    """
    def userStartup(self):
        """ Define the tables """
        config = self.table('config',
            sa.Column('name',           sa.String(255)),
            sa.Column('value',          sa.String(255))
        )

        hostnames = self.table('hostnames', 
            sa.Column('id',             sa.Integer, primary_key=True),
            sa.Column('ip',             sa.Integer),
            sa.Column('description',    sa.String(50)),
            sa.Column('isResolved',     sa.Integer),
            sa.Column('hostname',       sa.String(255))
        )

        sites = self.table('sites', 
            sa.Column('id',             sa.Integer, primary_key=True),
            sa.Column('date',           sa.Date),
            sa.Column('site',           sa.String(255))
        )

        traffic = self.table('traffic', 
            sa.Column('id',             sa.Integer, primary_key=True),
            sa.Column('date',           sa.Date),
            sa.Column('time',           sa.Time), 
            sa.Column('ip',             sa.Integer),
            sa.Column('resultCode',     sa.String(50)),
            sa.Column('bytes',          sa.Integer),
            sa.Column('url',            sa.BLOB),
            sa.Column('authuser',       sa.String(30)),
            sa.Column('sitesID',        sa.Integer),
            sa.Column('usersID',        sa.Integer)
        )

        trafficSummaries = self.table('trafficSummaries', 
            sa.Column('id',             sa.Integer, primary_key=True),
            sa.Column('date',           sa.Date),
            sa.Column('ip',             sa.Integer),
            sa.Column('usersID',        sa.Integer),
            sa.Column('inCache',        sa.Integer),
            sa.Column('outCache',       sa.Integer),
            sa.Column('sitesID',        sa.Integer),
            sa.Column('summaryTime',    sa.Integer)
        )

        users = self.table('users',
            sa.Column('id',             sa.Integer, primary_key=True),
            sa.Column('authuser',       sa.String(50)),
            sa.Column('date',           sa.Date)
        )

        return defer.DeferredList([config, hostnames, sites, traffic, trafficSummaries, users])

    @transact
    def getConfig(self):
        return self.config.select().execute().fetchall()

    @transact
    def getUsers(self):
        return self.users.select().execute().fetchall()

    @transact
    def getHostnames(self):
        return self.hostnames.select().execute().fetchall()

    @transact
    def getTraffic(self):
        return self.traffic.select().execute().fetchall()

    @transact
    def getSites(self):
        return self.sites.select().execute().fetchall()

    @transact
    def getTrafficSummaries(self):
        return self.trafficSummaries.select().execute().fetchall()


    @transact
    def getSummary(self, year, month, day=0):
        """ Provides a day (or month) summary of usages per host """
        if day:
            dateConstraint = [self.trafficSummaries.c.date == datetime.date(year, month, day)]
        else:
            if month < 12:
                yearn, monthn = (year, month+1)
            else:
                yearn, monthn = (year+1, 1)

            dateConstraint = [
                self.trafficSummaries.c.date >= datetime.date(year, month,1),
                self.trafficSummaries.c.date < datetime.date(yearn, monthn,1)
            ]

        dateConstraint.extend([
            self.hostnames.c.ip == self.trafficSummaries.c.ip,
            self.trafficSummaries.c.date == self.users.c.date,
            self.trafficSummaries.c.usersID == self.users.c.id
        ])
 
        return sa.select(
                [
                    sa.func.sum(self.trafficSummaries.c.inCache + self.trafficSummaries.c.outCache),
                    sa.func.count(sa.func.distinctrow(self.trafficSummaries.c.sitesID)),
                    self.hostnames.c.hostname,
                    self.trafficSummaries.c.ip,
                    self.users.c.id,
                    self.users.c.authuser,
                    self.trafficSummaries.c.date,
                ],
                sa.and_(
                    *dateConstraint
                ),
                group_by=[self.trafficSummaries.c.ip, self.trafficSummaries.c.usersID],
                order_by=[self.trafficSummaries.c.date]
            ).execute().fetchall()

    @transact
    def getDaySummary(self, year, month):
        """ Show a summary of traffic used by day for a month """
        if month < 12:
            yearn, monthn = (year, month+1)
        else:
            yearn, monthn = (year+1, 1)

        return sa.select(
            [
                self.trafficSummaries.c.date,
                sa.func.sum(self.trafficSummaries.c.inCache+self.trafficSummaries.c.outCache),
                sa.func.count(sa.func.distinctrow(self.trafficSummaries.c.sitesID)),
            ],
            sa.and_(
                self.trafficSummaries.c.date >= datetime.date(year, month,1),
                self.trafficSummaries.c.date < datetime.date(yearn, monthn,1)
            ),
            group_by=[self.trafficSummaries.c.date],
            order_by=[self.trafficSummaries.c.date]
        ).execute().fetchall()

    @transact
    def getMonths(self):
        """ Return a list of months containing data """
        return sa.select(
            [
                self.trafficSummaries.c.date,
                sa.func.sum(self.trafficSummaries.c.inCache+self.trafficSummaries.c.outCache),
                sa.func.count(sa.func.distinctrow(self.trafficSummaries.c.sitesID))
            ],
            group_by=[self.trafficSummaries.c.date],
            order_by=[self.trafficSummaries.c.date]
        ).execute().fetchall()

    @transact
    def getSiteSummary(self, ip, year, month, day=0):
        """ Return site ussage summary for an IP by a specific day or month """
        if day:
            constraints = [self.trafficSummaries.c.date == datetime.date(year, month, day)]
        else:
            if month < 12:
                yearn, monthn = (year, month+1)
            else:
                yearn, monthn = (year+1, 1)

            constraints = [
                self.trafficSummaries.c.date >= datetime.date(year, month,1),
                self.trafficSummaries.c.date < datetime.date(yearn, monthn,1)
            ]

        constraints.extend([
            self.trafficSummaries.c.sitesID == self.sites.c.id,
            self.trafficSummaries.c.ip == ip,
            self.hostnames.c.ip == self.trafficSummaries.c.ip
        ])

        return sa.select(
            [
                sa.func.sum(self.trafficSummaries.c.inCache+self.trafficSummaries.c.outCache),
                self.sites.c.site,
                self.trafficSummaries.c.sitesID,
                self.hostnames.c.hostname,
            ],
            sa.and_(
                *constraints
            ),
            group_by=[self.trafficSummaries.c.sitesID],
            order_by=[sa.desc(self.trafficSummaries.c.inCache + self.trafficSummaries.c.outCache)]
        ).execute().fetchall()

