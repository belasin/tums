import ldap
from ldap import modlist


class ldapQueryMaker:

    def __init__(self, host, baseDN, user, password):
        self.host = host
        self.baseDN = baseDN
        self.user = user
        self.password = password
    
    def createLDAPConnection(self):
        self.ldapConnector = ldap.open(self.host)
        self.ldapConnector.protocol_version = ldap.VERSION3
        self.ldapConnector.simple_bind("%s,%s" %(self.user, self.baseDN), self.password)

    def closeConnection(self):
        self.ldapConnector.unbind_s()

    def executeSearch(self, dn, retrieveAttributes, searchFilter):
        self.createLDAPConnection()
        ldap_result_id = self.ldapConnector.search(dn+","+self.baseDN, ldap.SCOPE_SUBTREE, searchFilter, retrieveAttributes)
        result_set = []
        while 1:
            result_type, result_data = self.ldapConnector.result(ldap_result_id, 0)
            if (result_data == []):
                break
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    result_set.append(result_data[0])

        self.closeConnection()
        if not result_set:
            return []

        return result_set

    def cleanSearch(self, dn, retrieveAttribute, searchFilter):
        """ Expects the same arguments as executeSearch but returns a more filtered subset for a single attribute"""
        self.createLDAPConnection()
        ldap_result_id = self.ldapConnector.search(dn+","+self.baseDN, ldap.SCOPE_SUBTREE, searchFilter, [retrieveAttribute])
        result_set = []
        while 1:
            result_type, result_data = self.ldapConnector.result(ldap_result_id, 0)
            if (result_data == []):
                break
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    result_set.append(result_data[0])

        self.closeConnection()
        if not result_set:
            return []

        ans = []
        for i in result_set:
            for k in i[1][retrieveAttribute]:
                ans.append(k)

        return ans

    def replaceAttributes(self, dn, attr):
        self.createLDAPConnection()
        self.ldapConnector.modify_s(dn, [(ldap.MOD_REPLACE, k, v) for k,v in attr.items()])
        self.closeConnection()

    def addAttribute(self, dn, k,v):
        self.createLDAPConnection()
        self.ldapConnector.modify_s(dn, [(ldap.MOD_ADD, k,v)])
        self.closeConnection()

    def modifyElement(self, dn, oldData, newData):
        self.createLDAPConnection()
        self.ldapConnector.modify_s(dn, modlist.modifyModlist(oldData, newData))
        self.closeConnection()

    def addElement(self, dn, data):
        self.createLDAPConnection()
        self.ldapConnector.add_s(dn+","+self.baseDN, modlist.addModlist(data))
        self.closeConnection()

    def deleteElement(self, dn):
        self.createLDAPConnection()
        self.ldapConnector.delete_s(dn+","+self.baseDN)
        self.closeConnection()

