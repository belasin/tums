from nevow import stan, tags
import Settings
import ldap

def retrieveTree(host, user, password, baseDN):
    dcn = 0
    noError = False
    noResult = True
    searchScope = ldap.SCOPE_SUBTREE
    retrieveAttributes = ['']
    searchFilter = ""
    # Try 3 times to connect to LDAP server
    while (dcn < 3) and (not noError):
        ldapConnector = ldap.open(host)
        ldapConnector.protocol_version = ldap.VERSION3
        ldapConnector.simple_bind("%s, %s" %(user, baseDN), password)
        try:
            ldap_result_id = ldapConnector.search(baseDN, searchScope) #, searchFilter, retrieveAttributes)
            result_set = []
            while noResult:
                result_type, result_data = ldapConnector.result(ldap_result_id, 0)
                if (result_data == []):
                    noResult = False
                else:
                    if result_type == ldap.RES_SEARCH_ENTRY:
                        result_set.append(result_data)
            noError = True

        except ldap.LDAPError, e:
            dcn += 1
            print "error", e

    ldapConnector.unbind_s()
    if result_set:
        unprocessed = [','.join(list(reversed(node[0][0].split(',')))) for node in result_set]
        return unprocessed
    else:
        return None

def flattenTree(nodes, bNode='o=THUSA', eNode='ou=People'):
    newNodes = []
    for node in nodes:
        if eNode in node.split(','):
            # Strip from o to past ou
            _break = node.split(',%s'%eNode)
            domContext = _break[0].replace(bNode + ',dc=', '')  # Now have "za,dc=co,dc=thusa"
            domain = '.'.join(reversed( domContext.split(',dc=') )) # now have 'thusa.co.za'
            # Now make up a node type called 'dm' and create 'o=THUSA,dm=thusa.co.za,uid=...'
            if len(_break)<2:
                newNodes.append("%s,dm=%s" % (bNode, domain)) # Was just the ou defenition
            else:
                newNodes.append("%s,dm=%s%s" % (bNode, domain, _break[-1]))
    return newNodes

class Tree:
    """ Basic Tree class """
    def __init__(self, type, name, domain = None):
        self.children=[]
        self.type=type
        self.name=name
        self.domain = domain

    def getNode(self):
        return "%s=%s" % (self.type, self.name)

    def addNode(self, Node):
        self.children.append(Node)

    def __repr__(self, *a):
        #return self.getNode()
        return self.name

class TreeNode(Tree):
    """ A tree node """
    def __init__(self, name, contents, domain = None):
        self.children=[]
        self.contents = contents
        self.name = name
        self.domain = domain

    def getNode(self):
        return self.name, self.contents

    def matchNode(self, name, contents):
        return self.name==name and self.contents==contents

    def __repr__(self, *a):
        #return "%s=%s" % ( self.name, self.contents )
        return self.contents

def traverseTree(Tree, Parent=None, itr=0):
    if itr==0:
        print repr(Tree)
    else:
        if itr%2!=0:
            tag = "+"
        else:
            tag = "+"
        print "   "*itr + tag +"%s=%s" %(Tree.getNode())

    for Branch in Tree.children:
        traverseTree(Branch, Parent=Tree, itr=itr+1)

def StanTree(Tree, sel):
    def buildStanTree(Tree, mstan, itr=0, bigcnt=0, lastDom=None):
        which = 1
        if Tree.children or Tree.domain:
            # This is a branch
            bigcnt+=1
            if Tree.name == 'dm':
                if Settings.defaultDomain == repr(Tree):
                    groupUrl = tags.li(_class="groupsm.png")[
                        tags.a(href="/auth/Users/GroupMod/%s/" % (repr(Tree)), 
                        id="node_%s" % (bigcnt+1,),
                        title="Modify groups"
                        )["Edit Groups"]
                    ]
                else:
                    groupUrl = [
                       tags.li(_class="domdel.gif")[
                           tags.a(href="/auth/Users/DomainDel/%s/"%(repr(Tree)),
                           id="node_%s"%(bigcnt+2),
                           title="Delete this domain",
                           onclick="return confirm('Are you sure you want to delete this domain?');")["Delete Domain"]
                       ],
                    ]
                extra = [
                    tags.li(_class="dhtmlgoodies_add.gif")[
                        tags.a(href="/auth/Users/Add/%s/"%(repr(Tree)), title="Add new user", id="node_%s"%bigcnt)["Add User"]
                    ],
                    groupUrl
                ]
            else:
                extra = tags.li(_class="domadd.gif")[
                    tags.a(href="/auth/Users/DomainAdd/", id="node_%s"%bigcnt, title="Add new domain")["Add Domain"]
                ]
            mstan.children.append(tags.li[tags.a(href='/auth/Users/'+repr(Tree), id="node_%s"%bigcnt)[repr(Tree)], tags.ul[extra]])
            lastDom = repr(Tree)
            for Branch in Tree.children:
                buildStanTree(Branch, mstan.children[-1].children[-1], itr=itr+1, bigcnt=itr+which+bigcnt, lastDom=lastDom)
                which +=1
            
        else:
            # This is the end of a limb
            if sel == repr(Tree):
                icon = "dhtmlgoodies_selected.gif"
            else:
                icon = "dhtmlgoodies_sheet.gif"

            if lastDom == 'Domains':
                mstan.children.append(tags.li[
                    tags.a(href="/auth/Users/Add/%s"%(repr(Tree)), id = "node_%s"%bigcnt)[repr(Tree)]
                ])
            else:
                mstan.children.append(tags.li(_class=icon)[
                    tags.a(href="/auth/Users/Edit/%s/%s"%(lastDom, repr(Tree)), id="node_%s"%bigcnt)[repr(Tree)]
                ])
            
    rstan = tags.ul(id="tree", _class="ctree")['']
    buildStanTree(Tree, rstan)
    return rstan

def addPath(path, Tree, leg=None, node=None,itr=0):
    """ Add something like "dc=bar,dc=foo,ou=baz" to the tree
        Each itteration of this function represents a level of the tree
        on this basis we can match the path to tree branches.

        Nodes must be added phasicly, the tree is built in order.
    """
    if leg==None: # If we have a leg, assume there is a node too... or someone smoked some crack
        leg = path.split(',')[:-1][1:] # Tree Leg to match, and throw the root away
        node = path.split(',')[-1] # Node to add

    if leg==[]: # fully parsed
        dm = not( 'uid=' in path )
        Tree.addNode(
            TreeNode(domain=dm, *node.split('='))
        )
    else:
        for Branch in Tree.children:
            if Branch.matchNode(*leg[0].split('=')): #
                addPath(path, Branch, leg=leg[1:], node=node, itr=itr+1)
            else:
                pass # No match on this leg


