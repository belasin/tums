#
#  Vulani TUMS 
#  Copyright (C) Thusa Business Support (Pty) Ltd.
#  All rights reserved
#  
#  Database.py - SQLAlchemy Database classes and functions
#

import sqlalchemy as sa
from sasync.database import AccessBroker, transact
from datetime import datetime as dt
import sha, time, datetime, os
from twisted.internet import defer, reactor
from Core import confparse
import Settings
from axiom.store import Store
from axiom.item import Item
from axiom.attributes import bytes, boolean, reference, integer, timestamp, AND
from axiom.errors import ItemNotFound
from axiom.upgrade import registerAttributeCopyingUpgrader, registerUpgrader

conf = confparse.Config()

class CalendarEntry(Item):
    typeName = 'db_caldate'
    schemaVersion = 1

    # The FQ name of the entry owner (ie, joe@blogs.com)
    owner = bytes()

    # All the bits of the date (easier to process chunks like this than a timestamp object)
    day = integer()
    month = integer()
    year = integer()

    # Start time
    hourS = integer()
    minuteS = integer()

    # End time
    hourE = integer()
    minuteE = integer()

    # The description
    descrip = bytes()

    # Should the user get emailed an allert for this 
    emailAlert = boolean()

    # Repeats: 0 - does not repeat, 1- repeats every day, 2- repeats weekly, 3- repeats monthly, 4- repeays yearly
    repeats = integer()

    # Should I set a vacation message during this date :-)
    vacation = boolean()

    # Even if the users calander is shared, hide this particular one
    private = boolean()

    # Ehash 
    ehash = bytes()

class CalendarShareMapper(Item):
    typeNAme = 'db_calsharer'
    schemaVersion = 1

    # The FQ name of the user who is sharing their calander (ie, joe@blogs.com)
    owner = bytes()
    
    # FQ name of user recieving the view permission
    viewer = bytes()

class CalendarDatabase:
    """ Database object for calendar"""
    def __init__(self):
        self.store = Store('/usr/local/tcs/tums/calendar.axiom')

    def createEntry(self, owner, date, stTime, enTime, descrip, email=False, repeat=0, vacation=False, private=False):
        day, month, year = date
        hourS, minuteS = stTime
        hourE, minuteE = enTime

        ehash = sha.sha('%s:%s:%s:%s%s' % (time.time(), day, month, year, owner)).hexdigest() 

        calEnt = self.store.findOrCreate(CalendarEntry,
            owner = owner,
            day = day, 
            month = month, 
            year = year, 
            hourS = hourS, 
            minuteS = minuteS, 
            hourE = hourE, 
            minuteE = minuteE, 
            descrip = descrip, 
            emailAlert = email, 
            repeats = repeat, 
            vacation = vacation, 
            private = private, 
            ehash = ehash
        )

        return calEnt

    def getEntriesMonth(self, owner, month, year):
        viewers = [i.owner for i in 
            self.store.query(CalendarShareMapper, CalendarShareMapper.viewer==owner)]
        
        owned = [owner]
        owned.extend(viewers)

        return self.store.query(CalendarEntry,
                AND(
                    CalendarEntry.owner in owned, 
                    CalendarEntry.month==month, 
                    CalendarEntry.year==year
                )
            )

    def getEntriesDay(self, owner, day, month, year):
        return self.store.query(CalendarEntry,
                AND(
                    CalendarEntry.owner==owner, 
                    CalendarEntry.day == day, 
                    CalendarEntry.month==month, 
                    CalendarEntry.year==year
                )
            )

class Volume(Item):
    """ Item class represents a volume record for netflow data """
    typeName = 'db_volume'
    schemaVersion = 2

    vIn = integer()
    vOut = integer()

    timestamp = integer()
    month = integer()
    year = integer()
    day = integer()

    port = integer()

    ifaceIndex = integer()

    localIp = bytes()

def upgradeVolume1to2(oldVolume):
    return oldVolume.upgradeVersion('db_volume', 1, 2,
        ifaceIndex= 1,

        vIn       = oldVolume.vIn,
        vOut      = oldVolume.vOut,

        timestamp = oldVolume.timestamp,
        month     = oldVolume.month,
        year      = oldVolume.year,
        day       = oldVolume.day,
        port      = oldVolume.port,
        localIp   = oldVolume.localIp
    )

# add interface Index attribute ifaceIndex
registerUpgrader(upgradeVolume1to2, 'db_volume', 1, 2)

class CDR(AccessBroker):
    """Describes the asterisk CDR DB"""
    """
    
    """
    def userStartup(self):
        cdr = self.table('cdr',
            sa.Column('calldate',       sa.DateTime),
            sa.Column('clid',           sa.String('80')),
            sa.Column('src',            sa.String('80')),
            sa.Column('dst',            sa.String('80')),
            sa.Column('dcontext',       sa.String('80')),
            sa.Column('channel',        sa.String('80')),
            sa.Column('dstchannel',     sa.String('80')),
            sa.Column('lastapp',        sa.String('80')),
            sa.Column('lastdata',       sa.String('80')),
            sa.Column('duration',       sa.Integer),
            sa.Column('billsec',        sa.Integer),
            sa.Column('disposition',    sa.String('45')),
            sa.Column('amaflags',       sa.Integer),
            sa.Column('accountcode',    sa.String('20')),
            sa.Column('userfield',      sa.String('255')),
            sa.Column('uniqueid',       sa.String('32')),
        )
        return defer.DeferredList([cdr])

    @transact
    def getAllEntries(self):
        return self.cdr.select().execute().fetchall()

    def genDateFilter(self, year,month,day):
        """Returns a Start and an End datetime entry to compare with"""
        if day == 0:
            start = datetime.datetime(year, month, 1, 0, 0, 0)
            if month == 12:
                end = datetime.datetime(year+1, 1, 1, 0, 0, 0)
            else:
                end = datetime.datetime(year, month+1, 1, 0, 0, 0)
        else:
            start = datetime.datetime(year, month, day, 0, 0, 0)
            end = start + datetime.timedelta(1)
        return start, end

    @transact
    def getUserOutTotals(self, year, month, day):
        start, end = self.genDateFilter(year,month,day)
        return sa.select(
            [ 
                self.cdr.c.accountcode,
                self.cdr.c.clid,
                sa.func.sum(self.cdr.c.duration),
                sa.func.sum(self.cdr.c.billsec),
                sa.func.count(self.cdr.c.calldate),
            ],
            sa.and_(
                self.cdr.c.userfield.like('%dstProv=%'),
                self.cdr.c.lastapp == "Dial",
                self.cdr.c.calldate >= start,
                self.cdr.c.calldate < end, 
            ),
            group_by=[self.cdr.c.accountcode],
        ).execute().fetchall()

    @transact
    def setUserQueue(self, username, devlist):
        devFilt = sa.or_()
        for dev in devlist:
            devFilt.append(self.cdr.c.dstchannel.like(str(dev) + '-%'))
        if not devFilt:
            raise Exception('Device list is empty')
        where = sa.and_(
                    self.cdr.c.lastapp == 'Queue',
                    sa.not_(self.cdr.c.userfield.like('%dst=%')),
                    sa.or_(devFilt))
        return sa.update(self.cdr, where).execute(userfield='dst='+str(username))
        #return self.cdr.update(
        #    sa.and_(
        #        self.cdr.c.lastapp == 'Queue',
        #        sa.not_(self.cdr.c.userfield.like('%dst=%')),
        #        sa.or_(devFilt),
        #    ),
        #    #{'userfield': 'dst=' + str(username)}
        #).execute()
    
    @transact
    def getUserOut(self, year, month, day, user=None):
        start, end = self.genDateFilter(year,month,day)
        if not user:
            userLim = self.cdr.c.accountcode != ''
        else:
            userLim = self.cdr.c.accountcode == user
        return self.cdr.select(
            sa.and_(
                userLim,
                self.cdr.c.userfield.like('%dstProv=%'),
                self.cdr.c.lastapp == "Dial",
                self.cdr.c.calldate >= start,
                self.cdr.c.calldate < end, 
            ),
            order_by=[sa.desc(self.cdr.c.calldate)],
        ).execute().fetchall()

    @transact
    def getUserIn(self, year, month, day, user=None):
        start, end = self.genDateFilter(year,month,day)
        if user:
            userLim = self.cdr.c.userfield.like('%dst='+user+'%')
        else:
            userLim = self.cdr.c.userfield.like('%dst=%')
        return self.cdr.select(
            sa.and_(
                userLim,
                self.cdr.c.lastapp == "Dial",
                self.cdr.c.calldate >= start,
                self.cdr.c.calldate < end, 
            ),
        ).execute().fetchall()

    @transact
    def getUserInAll(self, year, month, day, user=None):
        start, end = self.genDateFilter(year,month,day)
        if user:
            userLim = self.cdr.c.userfield.like('%dst='+user+'%')
        else:
            userLim = self.cdr.c.userfield.like('%dst=%')
        return self.cdr.select(
            sa.and_(
                userLim,
                self.cdr.c.calldate >= start,
                self.cdr.c.calldate < end, 
            ),
            order_by=[sa.desc(self.cdr.c.calldate)]
        ).execute().fetchall()

    @transact
    def getUserQueueIn(self,year,month,day, user=None):
        start, end = self.genDateFilter(year,month,day)
        if user:
            userLim = self.cdr.c.userfield.like('%dst='+user+'%')
        else:
            userLim = self.cdr.c.userfield.like('%dst=%')
        return self.cdr.select(
            sa.and_(
                self.cdr.c.userfield.like('%dst=%'),
                self.cdr.c.lastapp == "Queue",
                self.cdr.c.calldate >= start,
                self.cdr.c.calldate < end, 
            ),
        ).execute().fetchall()
   
    @transact
    def getReportData(self, year, month, day):
        start, end = self.genDateFilter(year,month,day)
        return self.cdr.select(
            sa.and_(
                self.cdr.c.calldate >= start,
                self.cdr.c.calldate < end, 
            )
        ).execute().fetchall()

    @transact
    def pingDB(self):
        #Keeps the session alive
        try:
            res = sa.select(
                [
                    self.cdr.c.calldate,
                ],
                limit=1
            ).execute().fetchall()
            return res
        except Exception, _exp:
            print "Issue pinging CDR, trying to reconnect"
            print _exp
            self.q.connection = self.q.engine.connect()
            self.startup()
            self.userStartup()

class AggregatorDatabase:
    """ Database object for NetFlow aggregator"""
    def __init__(self):
        self.store = Store('/usr/local/tcs/tums/db.axiom')

    def addVolume(self, ip, vIn, vOut, port, index):
        # Volume records may generaly have *either* vIn or vOut.
        # This is because a flow record adds only per flow which is in 
        # a single direction. 
        # We aggregate more to the port, we don't care about connector source 
        # ports because these are *always* random high ports.
        # We only add this per day.
        date = datetime.datetime.now()
        month = date.month
        year = date.year
        day = date.day

        volume = self.store.findOrCreate(Volume,
            localIp = ip,
            port = port,
            ifaceIndex = index,
            month = month,
            year = year,
            day = day
        )

        if volume.vIn:
            volume.vIn += vIn
        else:
            volume.vIn = vIn or 0

        if volume.vOut:
            volume.vOut += vOut 
        else:
            volume.vOut = vOut or 0


    def getTotalIndex(self, month, year, day=0):
        """ Get totals by interface index """
        if day > 0:
            volumeRecs = self.store.query(Volume,
                AND(Volume.month==month, Volume.year==year, Volume.day==day)
            )
        else:
            volumeRecs = self.store.query(Volume,
                AND(Volume.month==month, Volume.year==year)
            )
        
        volumeTotalsByIndex = {}

        for volume in volumeRecs:
            index = volume.ifaceIndex
            if index in volumeTotalsByIndex:
                if volume.vIn:
                    volumeTotalsByIndex[index][0] += volume.vIn
                if volume.vOut:
                    volumeTotalsByIndex[index][1] += volume.vOut
            else:
                volumeTotalsByIndex[index] = [volume.vIn or 0, volume.vOut or 0]

        return volumeTotalsByIndex

    def getVolumeTotalByIp(self, month, year, day=0, index=0):
        """ Gets total volumes for each IP address on the set date and index """
        a = []

        if day > 0:
            a.append(Volume.day==day)

        if index:
            a.append(Volume.ifaceIndex == index)

        volumeRecs = self.store.query(Volume,
            AND(Volume.month==month, Volume.year==year, *a)
        )

        volumeTotalsByIp = {}
        for volume in volumeRecs:
            if volume.localIp in volumeTotalsByIp:
                if volume.vIn:
                    volumeTotalsByIp[volume.localIp][0] += volume.vIn
                if volume.vOut:
                    volumeTotalsByIp[volume.localIp][1] += volume.vOut
            else:
                volumeTotalsByIp[volume.localIp] = [volume.vIn or 0, volume.vOut or 0]

        return volumeTotalsByIp

    def getVolumeRecByIp(self, month, year, ip):
        """ Get volume records for each IP on month """
        return [(i.timestamp, i.vIn, i.vOut) for i in self.store.query(Volume,
            AND(Volume.month==month, Volume.year==year, Volume.localIp==ip)
        )]

    def getPortBreakdownForIp(self, month, year, ip, day=0, index=0):
        """ Get port breakdown for each IP on date """
        a = []

        if day > 0:
            a.append(Volume.day==day)

        if index:
            a.append(Volume.ifaceIndex == index)

        volumeRecs = self.store.query(Volume,
            AND(Volume.month==month, Volume.year==year, Volume.localIp==ip, *a)
        )
        
        volumeByPort = {}
        for volume in volumeRecs:
            if volume.port in volumeByPort:
                if volume.vIn:
                    volumeByPort[volume.port][0] += volume.vIn
                if volume.vOut:
                    volumeByPort[volume.port][1] += volume.vOut
            else:
                volumeByPort[volume.port] = [volume.vIn or 0, volume.vOut or 0]
        return volumeByPort

    def getPortTotals(self, month, year, day=0, index=0):
        """ Get totals per port """
        a = []

        if day > 0:
            a.append(Volume.day==day)

        if index:
            a.append(Volume.ifaceIndex == index)

        volumeRecs = self.store.query(Volume,
            AND(Volume.month==month, Volume.year==year, *a)
        )

        volumeByPort = {}
        for volume in volumeRecs:
            if volume.port in volumeByPort:
                if volume.vIn:
                    volumeByPort[volume.port][0] += volume.vIn
                if volume.vOut:
                    volumeByPort[volume.port][1] += volume.vOut
            else:
                volumeByPort[volume.port] = [volume.vIn or 0, volume.vOut or 0]
        return volumeByPort

def hashPass(strng):
    """ SHA1 hash a string
    @param strng: any C{str}
    """
    return sha.sha(strng).hexdigest()
    
class UpdateCache(AccessBroker):
    def userStartup(self):
        files = self.table('files',
            sa.Column('type',           sa.String(255)),
            sa.Column('name',           sa.String(255)),
            sa.Column('downloads',      sa.Integer),
            sa.Column('size',           sa.Integer),
        )
        return defer.DeferredList([files])

    @transact
    def deleteFile(self, name):
        return self.files.delete(
            self.files.c.name == name
        ).execute()

    @transact
    def addFile(self, type, name, downloads, size):
        return self.files.insert().execute(
            type = type, 
            name = name, 
            downloads = downloads, 
            size = size
        )

    @transact
    def getAllFiles(self):
        return self.files.select().execute().fetchall()

    @transact
    def getFilesByType(self, type):
        return sa.select(
            [
                self.files.c.type, 
                self.files.c.name,
                self.files.c.downloads,
                self.files.c.size
            ],
            sa.and_(
                self.files.c.type == type,
                self.files.c.size > 10, 
            ), 
            order_by=[self.files.c.size, self.files.c.downloads]
        ).execute().fetchall()

    @transact
    def findFiles(self, name):
        return sa.select(
            [
                self.files.c.type, 
                self.files.c.name, 
                self.files.c.downloads,
                self.files.c.size
            ],
            self.files.c.name.like(name), 
            order_by=[self.files.c.size, self.files.c.downloads], 
        ).execute().fetchall()

    @transact
    def getTotals(self):
        return sa.select(
                [
                    self.files.c.type,
                    sa.func.sum(self.files.c.downloads),
                    sa.func.sum(self.files.c.size)
                ],
                group_by=[self.files.c.type],
            ).execute().fetchall()

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
        return sa.select(
            [
                self.messages, 
                self.deliveries
            ],
            self.messages.c.message_id == self.deliveries.c.message_id,
            limit=20, offset=offset, order_by=[sa.desc(self.messages.c.timestamp)]
        ).execute().fetchall()
    
    @transact
    def pingDB(self):
        #Keeps the session alive
        try:
            return sa.select(
                [
                    self.messages, 
                ],
                limit=1
            ).execute().fetchall()
        except Exception, _exp:
            print "Issue pinging EximDB, trying to reconnect"
            print _exp
            self.q.connection = self.q.engine.connect()
            self.startup()
            self.userStartup()

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
    
        return sa.select(
            [
                self.messages, 
                self.deliveries,
            ],
            
            sa.and_(
                self.messages.c.message_id == self.deliveries.c.message_id,
                *q
            ),

            order_by=[sa.desc(self.messages.c.timestamp)]
        ).execute().fetchall()
    
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
            sa.Column('usersID',        sa.Integer),
            sa.Column('sessionsID',      sa.Integer)
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
            sa.Column('date',           sa.Date),
            sa.Column('macAddress',     sa.String(60)),
            sa.Column('ip',             sa.Integer)
        )

        sessions = self.table('sessions',
            sa.Column('id',             sa.Integer, primary_key=True),
            sa.Column('startdatetime',  sa.DateTime, index=True),
            sa.Column('enddatetime',    sa.DateTime, index=True),
            sa.Column('datain',         sa.Integer),
            sa.Column('dataout',        sa.Integer),
            sa.Column('cachein',        sa.Integer),
            sa.Column('cacheout',       sa.Integer),
            sa.Column('user',           sa.String(100), index=True),
            sa.Column('macAddress',     sa.String(60), index=True),
            sa.Column('siteName',       sa.String(45), index=True),
            sa.Column('sessionTime',    sa.Float, index=True),
            sa.Column('hostnamesID',    sa.Integer, index=True),
            sa.Column('sitesID',        sa.Integer, index=True),
            sa.Column('usersID',        sa.Integer, index=True),
        )

        return defer.DeferredList([config, hostnames, sites, traffic, trafficSummaries, users, sessions])

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
    def pingDB(self):
        #Keeps the session alive
        try:
            return self.config.select().execute().fetchall()
        except Exception, _exp:
            print "Issue pinging SquidDB, trying to reconnect"
            print _exp
            self.q.connection = self.q.engine.connect()
            self.startup()
            self.userStartup()

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

        if day == 0:
            order = None
        else:
            order = [self.trafficSummaries.c.date]
            
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
                group_by=[self.trafficSummaries.c.ip, self.users.c.authuser],
                order_by=order
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

        if ip:
            constraints.extend([
                self.trafficSummaries.c.sitesID == self.sites.c.id,
                self.trafficSummaries.c.ip == ip,
                self.hostnames.c.ip == self.trafficSummaries.c.ip
            ])
            selection = [
                sa.func.sum(self.trafficSummaries.c.inCache+self.trafficSummaries.c.outCache),
                self.sites.c.site,
                self.trafficSummaries.c.sitesID,
                self.hostnames.c.hostname,
            ]

        else:
            constraints.extend([
                self.trafficSummaries.c.sitesID == self.sites.c.id,
            ])
            selection = [
                sa.func.sum(self.trafficSummaries.c.inCache+self.trafficSummaries.c.outCache),
                self.sites.c.site,
                self.trafficSummaries.c.sitesID,
            ]

        return sa.select(
            selection, 
            sa.and_(
                *constraints
            ),
            group_by=[self.sites.c.site],
            order_by=[sa.desc(self.trafficSummaries.c.inCache + self.trafficSummaries.c.outCache)]
        ).execute().fetchall()

    @transact
    def getSiteHosts(self, site, year, month, day=0):
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
            self.hostnames.c.ip == self.trafficSummaries.c.ip,
            self.trafficSummaries.c.date == self.users.c.date,
            self.trafficSummaries.c.usersID == self.users.c.id,
            self.trafficSummaries.c.sitesID == site,
            self.trafficSummaries.c.sitesID == self.sites.c.id,
        ])

        selection = [
            sa.func.sum(self.trafficSummaries.c.inCache + self.trafficSummaries.c.outCache),
            #sa.func.count(sa.func.distinctrow(self.trafficSummaries.c.sitesID)),
            self.hostnames.c.hostname,
            self.trafficSummaries.c.ip,
            self.users.c.id,
            self.users.c.authuser,
            self.trafficSummaries.c.date,
            self.sites.c.site
        ]

        return sa.select(
            selection, 
            sa.and_(
                *constraints
            ),
            group_by=[self.trafficSummaries.c.ip, self.users.c.authuser],
            order_by=[sa.desc(self.trafficSummaries.c.inCache + self.trafficSummaries.c.outCache)]
        ).execute().fetchall()
    
    #Writer Methods
    @transact
    def getLastEntryTime(self):
        result = sa.select([self.config.c.value],sa.and_(self.config.c.name=='lastTimestamp')).execute().fetchone()
        return result["value"]

    @transact
    def getUserDetails(self, date, ipAddr, user=None):
        ipA = dottedQuadToNum(ipAddr)
        macAddr = getCurrentIPMac(ipAddr)
        if user:
            where = sa.and_(
                self.users.c.date == date, 
                self.users.c.ip == ipA,
                self.users.c.authuser == user,
            )
        else:
            where = sa.and_(
                self.users.c.date == date, 
                self.users.c.ip == ipA,
            )

        sel =  [
                self.users.c.id,
                self.users.c.authuser,
                self.users.c.date,
                self.users.c.macAddress,
                self.users.c.ip
        ]

        result = sa.select(sel,where).execute().fetchone()
        if not result:
            where = sa.and_(
                self.users.c.date == date, 
                self.users.c.authuser == macAddr
            )
            result = sa.select(sel,where).execute().fetchone()

        if not result:
            #Attempt to resolve the IP to a mac address and then to a user XXX Split out to it's own function could be useful in other areas
            macAddr = getCurrentIPMac(ipAddr)
            userEnt = macAddr
            for k,userMaps in conf.Reporting.get('userMappings',{}).items():
                if ipAddr in userMaps:
                    userEnt = k
                    break
                if macAddr:
                    if macAddr in userMaps:
                        userEnt = k
            #Resolve Captive Portal Details
            if os.path.exists('/tmp/caportal/' + ipAddr):
                try:
                    f = open('/tmp/caportal/' + ipAddr)
                    line = f.readline()
                    f.close()
                    hostDet = line.split('|')
                    userEnt = hostDet[2]
                except Exception, _exp:
                    print "Error: %s" % _exp
            if user: #If the user has authenticated we should rely on that rather
                userEnt = user
            
            if not userEnt and not macAddr:
                userEnt = ipAddr

            result = self.users.insert().execute(
                authuser = userEnt,
                date = date,
                macAddress = macAddr,
                ip = ipA
            )
            return {
                'id': result.last_inserted_ids()[0],
                'authuser': userEnt,
                'ip': ipA,
                'date': date,
                'macAddress': macAddr
            }
        else:
            return result

    @transact
    def getHostEntry(self, ipAddr):
        ipA = dottedQuadToNum(ipAddr)
        result = sa.select(
            [
                self.hostnames.c.id,
                self.hostnames.c.ip,
                self.hostnames.c.isResolved,
                self.hostnames.c.hostname,
            ],
            sa.and_(self.hostnames.c.ip == ipA)
            ).execute().fetchone()
        if not result:
            result = self.hostnames.insert().execute(ip = ipA,isResolved = False)
            return  {
                'id': result.last_inserted_ids()[0],
                'ip': ipA,
                'isResolved': False,
                'hostname': None
            }
        else:
            return result

    @transact
    def getSite(self, date, siteName):
        result = sa.select(
            [
                self.sites.c.id,
                self.sites.c.date,
                self.sites.c.site,
            ],
            sa.and_(self.sites.c.date == date, self.sites.c.site == siteName)
            ).execute().fetchone()
        if not result:
            result = self.sites.insert().execute(date=date, site=siteName)
            return {
                'id': result.last_inserted_ids()[0],
                'date': date,
                'site': siteName
            }
        else:
            return result

    @transact
    def createSession(self, session):
        hID = int(session.hostnamesID)
        sID = int(session.sitesID)
        uID = int(session.usersID)
        result = self.sessions.insert().execute(
            startdatetime = dt.fromtimestamp(session.startTime),
            enddatetime = dt.fromtimestamp(session.endTime),
            datain = session.inBytes,
            dataout = session.outBytes,
            cachein = session.cacheIn,
            cacheout = session.cacheOut,
            sessionTime = session.currentTime,
            siteName = session.siteHost,
            hostnamesID = hID,
            sitesID = sID,
            usersID = uID,
        )
        return result.last_inserted_ids()[0]

    @transact
    def updateSession(self, session):
        where = sa.and_(self.sessions.c.id==session.sessionID)
        return sa.update(self.sessions, where).execute(
            enddatetime = dt.fromtimestamp(session.endTime),
            datain = session.inBytes,
            dataout = session.outBytes,
            cachein = session.cacheIn,
            cacheout = session.cacheOut,
            sessionTime = session.currentTime
        )
        
    @transact
    def closeSession(self, session):
        print "Session Close %s" % session
    
    @transact
    def addEntry(self, data, session):
        dtime = dt.fromtimestamp(data["time"])
        result = self.traffic.insert().execute(
            date = dtime.date(),
            time = dtime.time(),
            ip = data["userIP"]["ip"],
            resultCode = "/".join(data["status"]),
            bytes = data["inBytes"],
            bytesOut = data["reqBytes"],
            url = data["fullUrl"],
            authUser = data["username"],
            sitesID = int(session.sitesID),
            usersID = int(session.usersID),
            sessionsID = int(session.sessionID)
        )
        where = sa.and_(
            self.trafficSummaries.c.date == dtime.date(),
            self.trafficSummaries.c.ip == data["userIP"]["ip"],
            self.trafficSummaries.c.usersID == int(session.usersID),
            self.trafficSummaries.c.sitesID == int(session.sitesID)
        )
        inCacheVal = data["cacheMode"] and int(data["inBytes"]) or 0
        outCacheVal = data["cacheMode"] and int(data["inBytes"]) or 0
        result = sa.update(self.trafficSummaries, where).execute(
            inCache = self.trafficSummaries.c.inCache + inCacheVal,
            outCache = self.trafficSummaries.c.outCache + outCacheVal,
        )
        if result.rowcount > 0:
            print "Update"
        else:
            print "Insert"


    @transact
    def resolveHosts(self):
        pass


def dottedQuadToNum(ip):
    "convert decimal dotted quad string to long integer"
    hexn = ''.join(["%02X" % long(i) for i in ip.split('.')])
    return long(hexn, 16)

def getCurrentIPMac(ip):
    f = open('/proc/net/arp', "r")
    for line in f:
        entries = line.split()
        if ip in entries:
            f.close()
            return entries[3]
    f.close()
