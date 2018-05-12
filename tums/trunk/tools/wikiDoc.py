#!/usr/bin/python

import pydoc, inspect, __builtin__, sys
from string import rstrip, join
from collections import deque

class wikiDoc(pydoc.TextDoc):
    def bold(self, text):
        return "'''%s'''" % text

    def iindent(self, text, prefix=""):
        return prefix+"+"+text

    def section(self, title, contents):
        return "= %s =\n%s\n\n" % (title, contents)

    def formattree(self, *a):
        # Pointless waste of space...
        return ""
    def docmodule(self, object, name=None, mod=None):
        """Produce text documentation for a given module object."""
        name = object.__name__ # ignore the passed-in name
        synop, desc = pydoc.splitdoc(pydoc.getdoc(object))
        result = self.section('NAME', name + (synop and ' - ' + synop))

        try:
            all = object.__all__
        except AttributeError:
            all = None

        try:
            file = "source:tums/trunk/source/%s" % inspect.getabsfile(object).split('/source/')[-1]
        except TypeError:
            file = '(built-in)'
        result = result + self.section('FILE', file)

        docloc = self.getdocloc(object)
        if docloc is not None:
            result = result + self.section('MODULE DOCS', docloc)

        if desc:
            result = result + self.section('DESCRIPTION', desc)

        classes = []
        for key, value in inspect.getmembers(object, inspect.isclass):
            # if __all__ exists, believe it.  Otherwise use old heuristic.
            if (all is not None
                or (inspect.getmodule(value) or object) is object):
                if pydoc.visiblename(key, all):
                    classes.append((key, value))
        funcs = []
        for key, value in inspect.getmembers(object, inspect.isroutine):
            # if __all__ exists, believe it.  Otherwise use old heuristic.
            if (all is not None or
                inspect.isbuiltin(value) or inspect.getmodule(value) is object):
                if pydoc.visiblename(key, all):
                    funcs.append((key, value))
        data = []
        for key, value in inspect.getmembers(object, pydoc.isdata):
            if pydoc.visiblename(key, all):
                data.append((key, value))

        if hasattr(object, '__path__'):
            modpkgs = []
            for importer, modname, ispkg in pkgutil.iter_modules(object.__path__):
                if ispkg:
                    modpkgs.append(modname + ' (package)')
                else:
                    modpkgs.append(modname)

            modpkgs.sort()
            result = result + self.section(
                'PACKAGE CONTENTS', join(modpkgs, '\n'))

        if classes:
            classlist = map(lambda (key, value): value, classes)
            contents = []
            contentsFirst = []
            for key, value in classes:
                thisDoc = self.document(value, key, name)
                if not "==" in thisDoc:
                    contentsFirst.append(thisDoc)
                else:
                    contents.append(thisDoc)
            result = result + self.section('CLASSES', join(contentsFirst, '\n\n') + "\n\n" + join(contents, '\n'))

        if funcs:
            contents = []
            for key, value in funcs:
                contents.append(self.document(value, key, name))
            result = result + self.section('FUNCTIONS', join(contents, '\n'))

        if data:
            contents = []
            for key, value in data:
                contents.append(self.docother(value, key, name, maxlen=70))
            result = result + self.section('DATA', join(contents, '\n\n'))

        if hasattr(object, '__version__'):
            version = str(object.__version__)
            if version[:11] == '$' + 'Revision: ' and version[-1:] == '$':
                version = strip(version[11:-1])
            result = result + self.section('VERSION', version)
        if hasattr(object, '__date__'):
            result = result + self.section('DATE', str(object.__date__))
        if hasattr(object, '__author__'):
            result = result + self.section('AUTHOR', str(object.__author__))
        if hasattr(object, '__credits__'):
            result = result + self.section('CREDITS', str(object.__credits__))
        return result


    def docclass(self, object, name=None, mod=None):
        """Produce text documentation for a given class object."""
        realname = object.__name__
        name = name or realname
        bases = object.__bases__

        def makename(c, m=object.__module__):
            return pydoc.classname(c, m)

        if name == realname:
            title = '== class ' + self.bold(realname)
        else:
            title = '== ' + self.bold(name) + ' = class ' + realname
        if bases:
            parents = map(makename, bases)
            title += '(%s)' % join(parents, ', ')

        title += " =="

        classDoc = pydoc.getdoc(object)

        contents = []

        if classDoc:
            itrs = []
            for k in classDoc.split('\n'):
                if "@ivar " in k:
                    n = k.strip('@ivar ').split(':')
                    itrs.append(" * '''%s''': %s" % tuple(n))
                else:
                    itrs.append(k)
            
            contents.append('\n'.join(itrs) + '\n')
        push = contents.append

        # List the mro, if non-trivial.
        mro = deque(inspect.getmro(object))
        if len(mro) > 2:
            push("Method resolution order:")
            for base in mro:
                push('    ' + makename(base))
            push('')

        def spill(msg, attrs, predicate):
            ok, attrs = pydoc._split_list(attrs, predicate)
            if ok:
                push(msg)
                for name, kind, homecls, value in ok:
                    push(self.document(getattr(object, name),
                                       name, mod, object))
            return attrs

        def spilldescriptors(msg, attrs, predicate):
            ok, attrs = pydoc._split_list(attrs, predicate)
            if ok:
                push(msg)
                for name, kind, homecls, value in ok:
                    push(self._docdescriptor(name, value, mod))
            return attrs

        def spilldata(msg, attrs, predicate):
            ok, attrs = pydoc._split_list(attrs, predicate)
            if ok:
                push(msg)
                for name, kind, homecls, value in ok:
                    if callable(value) or inspect.isdatadescriptor(value):
                        doc = pydoc.getdoc(value)
                    else:
                        doc = None
                    push(self.docother(getattr(object, name),
                                       name, mod, maxlen=70, doc=doc) + '\n')
            return attrs

        attrs = filter(lambda (name, kind, cls, value): pydoc.visiblename(name),
                       inspect.classify_class_attrs(object))
        while attrs:
            if mro:
                thisclass = mro.popleft()
            else:
                thisclass = attrs[0][2]
            attrs, inherited = pydoc._split_list(attrs, lambda t: t[2] is thisclass)

            if thisclass is __builtin__.object:
                attrs = inherited
                continue
            elif thisclass is object:
                tag = "defined here"
            else:
                tag = "inherited from %s" % pydoc.classname(thisclass,
                                                      object.__module__)
            filter(lambda t: not t[0].startswith('_'), attrs)

            # Sort attrs by name.
            attrs.sort()

            # Pump out the attrs, segregated by kind.
            attrs = spill("=== Methods %s: ===\n" % tag, attrs,
                          lambda t: t[1] == 'method')
            attrs = spill("=== Class methods %s: ===\n" % tag, attrs,
                          lambda t: t[1] == 'class method')
            attrs = spill("=== Static methods %s: ===\n" % tag, attrs,
                          lambda t: t[1] == 'static method')
            attrs = spilldescriptors("=== Data descriptors %s: ===\n" % tag, attrs,
                                     lambda t: t[1] == 'data descriptor')
            attrs = spilldata("=== Data and other attributes %s: ===\n" % tag, attrs,
                              lambda t: t[1] == 'data')
            assert attrs == []
            attrs = inherited
        
        contents = '\n'.join(contents)
        if not contents:
            return title + '\n'
        return title + '\n' + self.indent(rstrip(contents), '') + '\n'


    def docroutine(self, object, name=None, mod=None, cl=None):
        """Produce text documentation for a function or method object."""
        realname = object.__name__
        name = name or realname
        note = ''
        skipdocs = 0
        if inspect.ismethod(object):
            imclass = object.im_class
            if cl:
                if imclass is not cl:
                    note = ' from ' + pydoc.classname(imclass, mod)
            else:
                if object.im_self is not None:
                    note = ' method of %s instance' % pydoc.classname(
                        object.im_self.__class__, mod)
                else:
                    note = ' unbound %s method' % pydoc.classname(imclass,mod)
            object = object.im_func

        if name == realname:
            title = self.bold(realname)
        else:
            if (cl and realname in cl.__dict__ and
                cl.__dict__[realname] is object):
                skipdocs = 1
            title = self.bold(name) + ' = ' + realname
        if inspect.isfunction(object):
            args, varargs, varkw, defaults = inspect.getargspec(object)
            argspec = inspect.formatargspec(
                args, varargs, varkw, defaults, formatvalue=self.formatvalue)
            if realname == '<lambda>':
                title = self.bold(name) + ' lambda '
                argspec = argspec[1:-1] # remove parentheses
        else:
            argspec = '(...)'
        decl = title + argspec + note

        # Argh this pydoc thing is designed like shit...
        # no where to catch class methods vs base methods?!?! FAIL!!! FAIL MR GUIDO!!! FAIL!!

        if "(self" in decl:
            st = "==== %s ====\n" % decl
        else:
            st = "== %s ==\n" % decl

        if skipdocs:
            return st
        else:
            doc = pydoc.getdoc(object) or ''
            content = []
            if doc:
                itrs = []
                for k in doc.split('\n'):
                    if "@param " in k:
                        n = k.strip('@param ').split(':')
                        itrs.append(" * '''%s''': %s" % tuple(n))
                    else:
                        itrs.append(k)
            
                content.append('\n'.join(itrs) + '\n')

            return "%s%s\n" % (st, '\n'.join(content))

sys.path.append('/root/dev/Vulani/tums/trunk/source')

# Import our module

n = sys.argv[1].strip('/').replace('/', '.')[:-3]

module = __import__(n, globals(), locals(), n.split('.')[:-1])

doc = wikiDoc()
n = doc.document(module)

print "[[PageOutline]]\n"+n
