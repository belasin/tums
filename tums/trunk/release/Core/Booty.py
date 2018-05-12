# Loads plugins and hooks them into TUMS
import os, Settings, traceback
from nevow import rend, static, compression

class HookyStatic(rend.Page):
    def __init__(self):
        rend.Page.__init__(self)

        self.modules = {}

    def childFactory(self, ctx, seg):
        if seg in self.modules:
            return compression.CompressingResourceWrapper(static.File(Settings.BaseDir+'/Waps/%s/static/' % seg))

class Hooky(object):
    def __init__(self):
        self.urlRootHooks = {}
        self.plugins = {}

        self.extends = {}

        self.modulesStatic = HookyStatic()

        # Must always happen last
        self.pluginBootstrap()

    def getRootHooks(self):
        pass

    def hookExists(self, seg):
        if seg in self.urlRootHooks:
            return True
        return False

    def integrateTools(self, toolsDict):
        toolsExtends = {
            'Applications': {}
        }
    
        for plugin, pages in self.extends.items():
            try:
                for segment, page in pages.items():
                    pageClass, linkPath = page

                    if segment in self.urlRootHooks and self.urlRootHooks[segment][0] != self.plugins[plugin][0].appName:
                        print "Error! The module named %s already implements the segment %s" % (
                            self.urlRootHooks[segment][0], 
                            segment
                        )
                        continue
                    
                    if linkPath:
                        context, parent, node = linkPath
                        if context == "ToolsMenu":
                            context = toolsExtends
                            np, n2 = node
                            if parent:
                                if (parent in context) and (np not in context[parent]):
                                    context[parent][np] = (segment, n2)
                                else:
                                    context[parent] = {
                                        np: (segment, n2)
                                    }
                            else:
                                if np not in context:
                                    context[np] = (segment, n2)
                        elif not context:
                            np, n2 = node
                            if np not in toolsExtends['Applications']:
                                toolsExtends['Applications'][np] = (segment, n2)
            except Exception, e:
                print "Error loading module", plugin,":" ,e
                print "-- Traceback --"
                print traceback.format_exc()
                print "-- End error --"


        for k,v in toolsExtends.items():
            # Add new entries in, but don't allow replacing them
            if isinstance(v, tuple) and k not in toolsDict:
                toolsDict[k] = v
            
            # Same nest for subs
            if isinstance(v, dict):
                if k not in toolsDict:
                    toolsDict[k] = {}
                
                for k1,v1 in v.items():
                    if k1 not in toolsDict[k]:
                        toolsDict[k][k1] = v1

    def getHook(self, seg):
        appName, pageClass = self.urlRootHooks[seg]
        return pageClass

    def unloadPlugin(self, name):
        # Remove root hooks
        for segment, v in self.extends[name].items():
            try:
                pageClass, linkPath = v
                del self.urlRootHooks[segment]
            except Exception, e:
                print "Failed to remove faulty menu hook", e, name

        try:
            # Remove module references
            del self.extends[name]
            del self.plugins[name]
        except Exception, e:
            print "Failed to remove faulty plugin.", e, name

    def pluginBootstrap(self):
        # Searches plugins and populates the root hook map
        plugDir = Settings.BaseDir + '/Waps'
        
        try:
            plugs = os.listdir(plugDir)
        except:
            return 
        
        plugs.sort()
        for plug in plugs:
            print plug 
            
            if '.py' in plug or '.' == plug[0]:
                continue 
            try:
                module = __import__("Waps.%s.main"  % (plug), globals(), locals(), ['Waps.%s' % plug])
            except Exception, _e:
                print "Error loading plugin %s, %s" % (str(plug), str(_e))
                continue
            
            try:
                appInstance = module.appClass()
                self.plugins[plug] = (appInstance, appInstance.appName, appInstance.appVersion)
                
                self.modulesStatic.modules[plug] = appInstance.appName
                
                self.extends[plug] = appInstance.getPages()
                
                for segment, v in self.extends[plug].items():
                    print segment, v
                    pageClass, linkPath = v
                    self.urlRootHooks[segment] = (appInstance.appName, pageClass)

            except Exception, e:
                print "Error loading plugin %s, %s" % (str(plug), str(e))
                continue
