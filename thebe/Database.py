from enamel import sql, storage
import sha

import datetime

class ThebeStorage(storage.SQL):
    tables = {
        'users':[
            sql.Column('id',            sql.Integer, primary_key = True),
            sql.Column('username',      sql.String(255)), # 1
            sql.Column('password',      sql.String(255)),
            sql.Column('fullname',      sql.String(255)), #3 
            sql.Column('email',         sql.String(255)), #4
            sql.Column('company',       sql.String(255)),
            sql.Column('address',       sql.String(255)),
            sql.Column('address1',      sql.String(255)),
            sql.Column('address2',      sql.String(255)),
            sql.Column('address3',      sql.String(255)),
            sql.Column('phone',         sql.String(255)),
            sql.Column('zaId',          sql.String(14)),
            sql.Column('country',       sql.String(255)),
            sql.Column('acthash',       sql.String(255)),
            sql.Column('emailConfirmed',sql.Integer),
            sql.Column('accountActive', sql.Integer),
            #sql.Column('billingAccName', sql.String(255)),
            #sql.Column('billingAccActive',sql.Integer),
        ],
        'groups':[
            sql.Column('id', sql.Integer, primary_key = True),
            sql.Column('name', sql.String(255)),
        ],
        'domains':[
            sql.Column('id', sql.Integer, primary_key = True),
            sql.Column('domain', sql.String(255)),
            sql.Column('registrant', sql.String(255)),
            sql.Column('addresspost', sql.String(255)),
            sql.Column('addressstreet', sql.String(255)),
            sql.Column('phonenum', sql.String(255)),
            sql.Column('email', sql.String(255))
        ],
        'domaingroup':[ # The a domains membership to a group
            sql.Column('id', sql.Integer, primary_key = True),
            sql.Column('did', sql.Integer),
            sql.Column('gid', sql.Integer),
        ],
        'isdsl':[
            sql.Column('id', sql.Integer, primary_key = True),
            sql.Column('gid', sql.Integer),
            sql.Column('linetag', sql.String(128)),
            sql.Column('gateway', sql.String(20)),
            sql.Column('name', sql.String(128)),
            sql.Column('hash', sql.String(255)),
            sql.Column('svsdescrip', sql.String(255))
        ],
        'usergroup':[ # User - Group mapping
            sql.Column('id',  sql.Integer, primary_key = True),
            sql.Column('uid', sql.Integer),
            sql.Column('gid', sql.Integer),
        ],
        'servergroup':[ # Server - Group mapping
            sql.Column('id',  sql.Integer, primary_key = True),
            sql.Column('gid', sql.Integer),
            sql.Column('sid', sql.Integer)
        ],
        'server':[
            sql.Column('id',        sql.Integer, primary_key = True),
            sql.Column('name',      sql.String(255)),
            sql.Column('hostname',  sql.String(255)),  #2
            sql.Column('skey',       sql.String(255)),
            sql.Column('lasthost',  sql.String(255)), # 4
            sql.Column('support',  sql.String(255)),
            sql.Column('lastversion', sql.String(255)),
        ],
        'orders':[
            sql.Column('id',        sql.Integer, primary_key = True),
            sql.Column('uid',       sql.Integer),
            sql.Column('sid',       sql.Integer),
            sql.Column('name',      sql.String(255)), # 3
            sql.Column('hostname',  sql.String(255)),  
            sql.Column('type',      sql.String(255)),   #5
            sql.Column('support',   sql.String(255)),
            sql.Column('status',    sql.String(255)),
            sql.Column('created',   sql.DateTime),
            sql.Column('modified',  sql.DateTime),
        ],
        'transactionlog':[
            sql.Column('id',        sql.Integer, primary_key = True), 
            sql.Column('orderid',   sql.Integer), 
            sql.Column('rcode',     sql.String(255)),
            sql.Column('tdata',     sql.TEXT)
        ], 
        'updates':[
            sql.Column('id',        sql.Integer, primary_key = True),
            sql.Column('sid',       sql.Integer),
            sql.Column('package',   sql.String(255)), 
            sql.Column('date',      sql.DateTime),
            sql.Column('applied',   sql.Integer),
        ],
        'pending':[
            sql.Column('id',        sql.Integer, primary_key = True),
            sql.Column('uid',       sql.Integer),   # UID of person who made the change
            sql.Column('sid',       sql.Integer),   # Server this message is destined for
            sql.Column('type',      sql.String),    # What this is all about
            sql.Column('detail',    sql.String),    # Arbitrary detail which depends on the type 
        ],
        'log':[
            sql.Column('id', sql.Integer, primary_key = True),

            sql.Column('sid',       sql.Integer), # Zero for a general message
            sql.Column('type',      sql.String(255)),
            sql.Column('message',   sql.String(255)),
            sql.Column('date',      sql.DateTime),
        ],
        'backuplog':[
            sql.Column('id', sql.Integer, primary_key = True),

            sql.Column('sid',       sql.Integer),
            sql.Column('type',      sql.String(255)),
            sql.Column('success',   sql.Integer),
            sql.Column('date',      sql.DateTime)
        ],
        'serverdomains':[
            sql.Column('id',        sql.Integer, primary_key = True),
            sql.Column('sid',       sql.Integer),
            sql.Column('domain',    sql.String(255)),
        ], 
        'serverconfigs':[
            sql.Column('id',            sql.Integer, primary_key = True),
            sql.Column('gid',           sql.Integer), # GID to which this profile belongs
            sql.Column('description',   sql.String(255)),
            sql.Column('filename',      sql.String(255))
        ],
        'serverusers':[
            sql.Column('id', sql.Integer, primary_key = True),

            sql.Column('sid',           sql.Integer),    # 1
            sql.Column('domain',        sql.String(255)), # 2
            sql.Column('name',          sql.String(255)), # 3
            sql.Column('giveName',      sql.String(255)), # 4 
            sql.Column('sn',            sql.String(255)), #5 
            sql.Column('cn',            sql.String(255)),
            sql.Column('uid',           sql.String(255)),
            sql.Column('gid',           sql.String(255)),
            sql.Column('emp',           sql.String(255)), # 9 
            sql.Column('active',        sql.String(255)), # 10 
            sql.Column('mail',          sql.String(255)),
            sql.Column('mailForward',   sql.String(255)),
            sql.Column('mailAlias',     sql.String(255)), # 13
            sql.Column('ntPass',        sql.String(255)),
            sql.Column('password',      sql.String(255)), # 15
            sql.Column('lmPass',        sql.String(255)),
            sql.Column('samSid',        sql.String(255)), # 17
            sql.Column('pgSid',         sql.String(255)),
            sql.Column('vacation',      sql.TEXT),        #19
            sql.Column('vacEnable',     sql.Integer),     #20 
            sql.Column('flags',         sql.String(255))
        ]
    }

    @sql.transact
    def authenticateUser(self, username, password):
        # handle preauthentication
        if password:
            check = sql.and_(self.users.c.username == username,
                self.users.c.password == sha.sha(password).hexdigest())
        elif password == None:
            check = (self.users.c.username == username)

        return self.users.select(
            check
        ).execute().fetchone()

    @sql.transact
    def addUser(self, username, password, email):
        return self.users.insert().execute(
            username = username, password = password, email = email
        )

    @sql.transact
    def addUserFull(self, fullname, company, email, phone, address0, address1, address2, address3, country, password, acthash):
        keys = {
            'username': email,
            'fullname': fullname,
            'email':    email,
            'company':  company,
            'phone':    phone,
            'address':  address0,
            'address1': address1,
            'address2': address2,
            'address3': address3,
            'country':  country,
            'password': sha.sha(password).hexdigest(),
            'acthash': acthash
        }
        return self.users.insert().execute(**keys)

    @sql.transact
    def getUserByHash(self, acthash):
        return self.users.select(self.users.c.acthash == acthash).execute().fetchone()

    @sql.transact
    def confirmUser(self, uid):
        return self.users.update(self.users.c.id==uid).execute(
            emailConfirmed = 1,
            accountActive = 1
        )

    @sql.transact
    def getUser(self, uid):
        return self.users.select(self.users.c.id == uid).execute().fetchone()

    @sql.transact
    def editUser(self, uid, fullname, company, email, phone, address0, address1, address2, address3, password):
        keys = {
            'fullname': fullname,
            'email':    email,
            'company':  company,
            'address':  address0,
            'address1': address1,
            'address2': address2,
            'address3': address3,
            'phone':    phone
        }
            
        if password:
            keys['password'] = sha.sha(password).hexdigest()
        
        return self.users.update(self.users.c.id==uid).execute(**keys)

    @sql.transact
    def addDomain(self, domain):
        return self.domains.insert().execute(
            domain = domain,
        )

    @sql.transact
    def getDomains(self):
        return self.domains.select().execute().fetchall()

    @sql.transact
    def deleteDomain(self, did):
        return self.domains.delete(
            self.domains.c.id == did
        ).execute()

    @sql.transact
    def getDomainByName(self, domain):
        return self.domains.select(self.domains.c.domain == domain).execute().fetchone()

    @sql.transact
    def getUsers(self):
        return self.users.select().execute().fetchall()

    @sql.transact
    def deleteUser(self, uid):
        return self.users.delete(
            self.users.c.id == uid
        ).execute()

    @sql.transact
    def addGroup(self, group):
        return self.groups.insert().execute(
            name = group
        )

    @sql.transact
    def getGroups(self):
        """ Return all groups - should only be used for very high administration"""
        return self.groups.select().execute().fetchall()

    @sql.transact
    def delGroup(self, gid):
        return self.groups.delete(
            self.groups.c.id == gid
        ).execute()

    @sql.transact
    def addMembership(self, uid, gid):
        return self.usergroup.insert().execute(
            uid = uid,
            gid = gid
        )

    @sql.transact
    def addServerMembership(self, gid, sid):
        return self.servergroup.insert().execute(
            sid = sid,
            gid = gid
        )

    @sql.transact
    def deleteServerMembership(self, gid, sid):
        return self.servergroup.delete(
            sql.and_(
                self.servergroup.c.sid == sid,
                self.servergroup.c.gid == gid
            )
        ).execute()

    @sql.transact
    def addDomainMembership(self, gid, did):
        return self.domaingroup.insert().execute(
            gid = gid, did = did
        )

    @sql.transact
    def deleteDomainMembership(self, did):
        return self.domaingroup.delete(self.domaingroup.c.did == did).execute()

    @sql.transact
    def getGids(self, uid):
        """Get group memberships for a user. A user can belong to multiple groups"""
        return self.usergroup.select(self.usergroup.c.uid == uid).execute().fetchall()

    @sql.transact
    def getMembership(self, uid):
        return sql.select([
                self.usergroup.c.uid,
                self.usergroup.c.gid,
                self.groups.c.name,
            ],
            sql.and_(
                self.usergroup.c.uid==uid,
                self.groups.c.id == self.usergroup.c.gid
            )).execute().fetchall()

    @sql.transact
    def getServerMembership(self, sid):
        return sql.select([
                self.servergroup.c.sid,
                self.servergroup.c.gid,
                self.groups.c.name,
            ],
            sql.and_(
                self.servergroup.c.sid==sid,
                self.groups.c.id == self.servergroup.c.gid
            )).execute().fetchall()

    @sql.transact
    def getMemberships(self):
        return sql.select([
                self.usergroup.c.uid,
                self.usergroup.c.gid,
                self.groups.c.name,
                self.users.c.username,
            ],
            sql.and_(
                self.groups.c.id == self.usergroup.c.gid,
                self.users.c.id == self.usergroup.c.uid
            )).execute().fetchall()

    @sql.transact
    def getGroupUsers(self, gid):
        return sql.select([
                self.users.c.id, 
                self.users.c.username
            ], 
            sql.and_(
                self.usergroup.c.gid == gid,
                self.users.c.id == self.usergroup.c.uid,
            )).execute().fetchall()
            

    @sql.transact
    def getServerMemberships(self):
        return sql.select([
                self.servergroup.c.sid,
                self.servergroup.c.gid,
                self.groups.c.name,
                self.server.c.name,
            ],
            sql.and_(
                self.groups.c.id == self.servergroup.c.gid,
                self.server.c.id == self.servergroup.c.sid
            )).execute().fetchall()

    @sql.transact
    def getDomainMemberships(self):
        return sql.select([
                self.domaingroup.c.did,
                self.domaingroup.c.gid,
                self.groups.c.name,
                self.domains.c.domain,
            ],
            sql.and_(
                self.domaingroup.c.gid == self.groups.c.id,
                self.domaingroup.c.did == self.domains.c.id
            )).execute().fetchall()

    @sql.transact
    def addServer(self, name, hostname, key):
        return self.server.insert().execute(
            name = name,
            hostname = hostname,
            skey = key
        )

    @sql.transact
    def updateServerDetail(self, sid, name, hostname, key):
        return self.server.update(self.server.c.id == sid).execute(
            name = name,
            hostname = hostname,
            skey = key
        )

    @sql.transact
    def updateServerVersion(self, sid, version):
        return self.server.update(self.server.c.id ==sid).execute(
            lastversion = version
        )

    @sql.transact
    def deleteServer(self, sid):
        ds = self.server.delete(self.server.c.id == sid).execute()
        # Delete all references :(
        dl = self.log.delete(self.log.c.sid == sid).execute()
        dbl = self.backuplog.delete(self.backuplog.c.sid == sid).execute()
        dsd = self.serverdomains.delete(self.serverdomains.c.sid == sid).execute()
        dsu = self.serverusers.delete(self.serverusers.c.sid == sid).execute()
        du = self.updates.delete(self.updates.c.sid == sid).execute()
        dsg = self.servergroup.delete(self.servergroup.c.sid == sid).execute()
        dp = self.pending.delete(self.pending.c.sid == sid).execute()

        return [ds, dl, dbl, dsd, dsu, du, dsg, dp]

    @sql.transact
    def flushUpdates(self, sid):
        return self.updates.delete(self.updates.c.sid == sid).execute()

    @sql.transact
    def addUpdate(self, sid, package):
        return self.updates.insert().execute(
            sid = sid,
            package = package,
            applied = 0,
            date = datetime.datetime.now()
        )

    @sql.transact
    def getUpdates(self, sid):
        return self.updates.select(
            self.updates.c.sid == sid
        ).execute().fetchall()

    @sql.transact
    def updateApplied(self, sid, package):
        return self.updates.update(
            sql.and_(
                self.updates.c.sid == sid,
                self.updates.c.package == package
            )
        ).execute(
            date = datetime.datetime.now(),
            applied = 1
        )

    @sql.transact
    def addBogie(self, name, hostname, key):
        return self.server.insert().execute(
            name = name,
            hostname = hostname,
            skey = key
        )

    @sql.transact
    def logValidation(self, sid, hostname, key):
        return self.log.insert().execute(
            sid = sid,
            type = "KEYAUTH",
            message = "%s+%s" % (key, hostname),
            date = datetime.datetime.now()
        )

    @sql.transact
    def logMessage(self, type, message, sid=0):
        return self.log.insert().execute(
            sid = sid,
            type = type,
            message = message,
            date = datetime.datetime.now()
        )

    @sql.transact
    def getServerEvents(self, sid):
        return sql.select(
            [
                self.log.c.date,
                self.log.c.type,
                self.log.c.message,
            ], 
            self.log.c.sid == sid,
            order_by = [sql.desc(self.log.c.date)],
            limit = 20,
        ).execute().fetchall()

    @sql.transact
    def validateKey(self, key):
        return self.server.select(
            self.server.c.skey == key
        ).execute().fetchone()

    @sql.transact
    def getServersInGroup(self, gids):
        """ Get all the servers in a C(list) of groups """
        result = []

        for gid in gids:
            query = sql.select([
                    self.server.c.id,
                    self.server.c.name,
                    self.server.c.hostname,
                    self.server.c.skey,
                    self.server.c.lasthost,
                    self.server.c.lastversion
                ], 
                sql.and_(
                    self.servergroup.c.gid == gid,
                    self.server.c.id == self.servergroup.c.sid
                )).execute().fetchall()
            for r in query:
                result.append(r)

        return result

    @sql.transact
    def getDomainsInGroup(self, gids):
        """ Get all the domains viewable in C(list) of groups """
        result = []
        for gid in gids:
            query = sql.select([
                self.domains.c.id,
                self.domains.c.domain,
            ],
            sql.and_(
                self.domaingroup.c.gid == gid,
                self.domains.c.id == self.domaingroup.c.did
            )).execute().fetchall()
            for r in query:
                result.append(r)
        return result

    @sql.transact
    def getServer(self, sid):
        return self.server.select(self.server.c.id == sid).execute().fetchone()

    @sql.transact
    def getServerByName(self, name):
        return self.server.select(self.server.c.name == name).execute().fetchone()

    @sql.transact
    def getServers(self):
        return self.server.select().execute().fetchall()

    @sql.transact
    def updateServerLasthost(self, sid, hostname):
        return self.server.update(self.server.c.id == sid).execute(
            lasthost = hostname
        )
   
    @sql.transact
    def addServerUser(self, sid, detail):
        newDetail={'sid':sid}

        valid = [
            'pgSid', 'domain', 'cn', 'mailForward', 'emp', 'name',
            'lmPass', 'mailAlias', 'active', 'gid', 'sn', 'giveName',
            'uid', 'mail', 'ntPass', 'password', 'samSid', 'vacation', 'vacEnable', 'flags'
        ]
 
        for key in valid:
            if key == 'vacEnable':
                print detail.get('vacation', '')
                if 'True' in detail.get(key, ''):
                    newDetail[key] = 1
                else:
                    newDetail[key] = 0
            else:
                newDetail[key] = detail.get(key, '')

        return self.serverusers.insert().execute(**newDetail)

    @sql.transact
    def updateServerUser(self, sid, id, detail):
        newDetail={'sid':sid}

        valid = [
            'pgSid', 'domain', 'cn', 'mailForward', 'emp', 'name',
            'lmPass', 'mailAlias', 'active', 'gid', 'sn', 'giveName',
            'uid', 'mail', 'ntPass', 'password', 'samSid', 'vacation', 'vacEnable', 'flags'
        ]
 
        for key in valid:
            if key == 'vacEnable':
                if 'True' in detail.get(key, ''):
                    newDetail[key] = 1
                else:
                    newDetail[key] = 0
            else:
                newDetail[key] = detail.get(key, '')

        return self.serverusers.update(
            sql.and_(
                self.serverusers.c.id == id,
                self.serverusers.c.sid == sid
            )
        ).execute(**newDetail)

    @sql.transact
    def delServerUser(self, sid, id=None, name=None, domain=None):
        if id:
            return self.serverusers.delete(self.serverusers.c.id == id).execute()
        else:
            return self.serverusers.delete(
                sql.and_(
                    self.serverusers.c.name == name, 
                    self.serverusers.c.domain == domain,
                )
            ).execute()

    @sql.transact
    def getGroupServerDomains(self, gid):
        return sql.select(
            [
                self.serverusers.c.domain
            ],
            sql.and_(
                self.servergroup.c.gid == gid,
                self.serverusers.c.sid == self.servergroup.c.sid,
            ),
            group_by=[self.serverusers.c.domain]
        ).execute().fetchall()

    @sql.transact
    def getServerDomains(self, sid):
        return self.serverdomains.select(
            self.serverdomains.c.sid == sid
        ).execute().fetchall()

    @sql.transact
    def getServerUsers(self, sid):
        return self.serverusers.select(
            sql.and_(
                self.serverusers.c.sid == sid,
            )
        ).execute().fetchall()

    @sql.transact
    def getServerUsersByDomain(self, domain, gid):
        return sql.select(
            [
                self.serverusers.c.id,
                self.serverusers.c.name,
                self.server.c.name
            ], 
            sql.and_(
                self.serverusers.c.domain == domain, 
                self.server.c.id == self.serverusers.c.sid,
                self.servergroup.c.sid == self.serverusers.c.sid,
                self.servergroup.c.gid == gid
            ), 
            group_by = [self.serverusers.c.name]
        ).execute().fetchall()
 
    @sql.transact
    def getServerUserById(self, uid, gid):
        return sql.select([
            self.serverusers.c.id,
            self.serverusers.c.sid,
            self.serverusers.c.domain,
            self.serverusers.c.name,
            self.serverusers.c.giveName,
            self.serverusers.c.sn,
            self.serverusers.c.cn,
            self.serverusers.c.uid,
            self.serverusers.c.gid,
            self.serverusers.c.emp,
            self.serverusers.c.active,
            self.serverusers.c.mail,
            self.serverusers.c.mailForward,
            self.serverusers.c.mailAlias,
            self.serverusers.c.ntPass,
            self.serverusers.c.password,
            self.serverusers.c.lmPass,
            self.serverusers.c.samSid,
            self.serverusers.c.pgSid,
            self.serverusers.c.vacation,
            self.serverusers.c.vacEnable,
            self.serverusers.c.flags
        ],
        sql.and_(
            self.serverusers.c.id == uid, 
            self.servergroup.c.sid == self.serverusers.c.sid,
            self.servergroup.c.gid in gid
        )
        ).execute().fetchone()

    @sql.transact
    def getServerForUser(self, uid):
        return sql.select(
            [   
                self.server.c.id, 
                self.server.c.name
            ],
            sql.and_(
                self.serverusers.c.id == uid, 
                self.server.c.id == self.serverusers.c.sid
            )
        ).execute().fetchone()

    @sql.transact
    def findServerUser(self, sid, name, domain):
        return self.serverusers.select(
            sql.and_(
                self.serverusers.c.sid == sid,
                self.serverusers.c.domain == domain,
                self.serverusers.c.name == name,
            )
        ).execute().fetchone()

    @sql.transact
    def getAllUsers(self):
        return self.serverusers.select().execute().fetchall()

    @sql.transact
    def getUsersFromSGroup(self, gid):
        return sql.select(
            [
                self.serverusers.c.id,
                self.serverusers.c.sid,
                self.serverusers.c.domain,
                self.serverusers.c.name,
                self.serverusers.c.giveName
            ],
            sql.and_(
                self.serverusers.c.sid == self.servergroup.c.sid,
                self.servergroup.c.gid == gid
            ),
            order_by = [self.serverusers.c.name]
        ).execute().fetchall()

    @sql.transact
    def listPendingOrders(self):
        return sql.select(
            [
                self.orders.c.id,
                self.orders.c.uid,
                self.orders.c.sid,
                self.orders.c.name,
                self.orders.c.hostname,
                self.orders.c.type,
                self.orders.c.support,
                self.orders.c.status,
                self.orders.c.created,
                self.orders.c.modified,
                self.users.c.fullname
            ],
            sql.and_(
                self.users.c.id == self.orders.c.uid, 
                sql.or_(
                    self.orders.c.status != "Completed", 
                    self.orders.c.status == None
                )
            ), 
            order_by = [self.orders.c.modified]
        ).execute().fetchall()

    @sql.transact
    def createOrder(self, gid, name, hostname, support, type):
        return self.orders.insert().execute(
            uid = gid,
            name = name,
            hostname = hostname,
            support = support, 
            type = type,
            status = "",
            created = datetime.datetime.now(),
            modified = datetime.datetime.now()
        )
    
    @sql.transact
    def findOrder(self, gid, name, hostname, support, type):
        return self.orders.select(sql.and_(
            self.orders.c.uid == gid,
            self.orders.c.name == name, 
            self.orders.c.hostname == hostname,
            self.orders.c.support == support,
            self.orders.c.type == type
        )).execute().fetchone()

    @sql.transact
    def updateStatus(self, id, status):
         return self.orders.update(self.orders.c.id==id).execute(
                status = status,
                modified = datetime.datetime.now()
            )

    @sql.transact
    def updateOrder(self, id, sid, status):
        return self.orders.update(self.orders.c.id==id).execute(
                sid = sid, 
                status = status,
                modified = datetime.datetime.now()
            )

    @sql.transact
    def purgeOrder(self, id):
        return self.orders.delete(
            self.orders.c.id == id
        ).execute()

    @sql.transact
    def getOrders(self, gid):
        return self.orders.select(self.orders.c.uid == gid).execute().fetchall()

    @sql.transact
    def getOrder(self, id):
        return self.orders.select(self.orders.c.id == id).execute().fetchone()

    @sql.transact
    def logTransaction(self, orderId, rcode, tdata):
        return self.transactionlog.insert().execute(
            orderid = orderId, 
            rcode = rcode, 
            tdata = tdata
        )
