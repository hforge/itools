
# Import Python modules
from cStringIO import StringIO
import os
import pprint
import sys

# Import Python modules
from Products.PageTemplates import Expressions, PathIterator, TALES
from Products.PageTemplates.PageTemplate import PTRuntimeError, \
     PageTemplateTracebackSupplement
from Products.PageTemplates.PageTemplateFile import PageTemplateFile \
     as ZopePageTemplateFile
from Products.PageTemplates.PythonExpr import getSecurityManager, PythonExpr
from TAL.HTMLTALParser import HTMLTALParser
from TAL.TALGenerator import TALGenerator
from TAL.TALInterpreter import TALInterpreter

Z_DEBUG_MODE = os.environ.get('Z_DEBUG_MODE') == '1'



###########################################################################
# Redifine a non restricted version of PathExpr
###########################################################################
def unrestrictedTraverse(self, path, securityManager,
                         get=getattr, has=hasattr, N=None, M=[],
                         TupleType=type(()) ):

    REQUEST = {'path': path}
    REQUEST['TraversalRequestNameStack'] = path = path[:] # Copy!
    if not path[0]:
        # If the path starts with an empty string, go to the root first.
        self = self.getPhysicalRoot()
        path.pop(0)
        
    path.reverse()
    object = self
    while path:
        __traceback_info__ = REQUEST
        name = path.pop()

        if isinstance(name, TupleType):
            object = apply(object, name)
            continue

        if name[0] == '_':
            # Never allowed in a URL.
            raise AttributeError, name

        if name=='..':
            o = get(object, 'aq_parent', M)
            if o is not M:
                object=o
                continue

        t=get(object, '__bobo_traverse__', N)
        if t is not N:
            o=t(REQUEST, name)
                    
            container = None
            if has(o, 'im_self'):
                container = o.im_self
            elif (has(get(object, 'aq_base', object), name)
                and get(object, name) == o):
                container = object
        else:
            o=get(object, name, M)
            if o is not M:
                pass
            else:
                try:
                    o=object[name]
                except (AttributeError, TypeError):
                    raise AttributeError, name
        object = o

    return object


class SubPathExpr(Expressions.SubPathExpr):
    def _eval(self, econtext,
              list=list, isinstance=isinstance, StringType=type('')):
        vars = econtext.vars
        path = self._path
        if self._dp:
            path = list(path) # Copy!
            for i, varname in self._dp:
                val = vars[varname]
                if isinstance(val, StringType):
                    path[i] = val
                else:
                    # If the value isn't a string, assume it's a sequence
                    # of path names.
                    path[i:i+1] = list(val)
        __traceback_info__ = base = self._base
        if base == 'CONTEXTS':
            ob = econtext.contexts
        else:
            ob = vars[base]
        if isinstance(ob, Expressions.DeferWrapper):
            ob = ob()
        if path:
            ob = unrestrictedTraverse(ob, path, getSecurityManager())
        return ob


class PathExpr(Expressions.PathExpr):
    def __init__(self, name, expr, engine):
        self._s = expr
        self._name = name
        self._hybrid = 0
        paths = expr.split('|')
        self._subexprs = []
        add = self._subexprs.append
        for i in range(len(paths)):
            path = paths[i].lstrip()
            if TALES._parse_expr(path):
                # This part is the start of another expression type,
                # so glue it back together and compile it.
                add(engine.compile('|'.join(paths[i:]).lstrip()))
                break
            add(SubPathExpr(path)._eval)




###########################################################################
# Define non restricted classes and methods (as found in
# PageTemplates.Expressions).
###########################################################################
_engine = None
def getEngine():
    global _engine
    if _engine is None:
        _engine = TALES.Engine(PathIterator.Iterator)
        installHandlers(_engine)
        _engine._nocatch = (TALES.TALESError, 'Redirect')
    return _engine


def installHandlers(engine):
    reg = engine.registerType
    pe = PathExpr
    for pt in ('standard', 'path', 'exists', 'nocall'):
        reg(pt, pe)
    reg('string', Expressions.StringExpr)
    reg('python', PythonExpr)
    reg('not', Expressions.NotExpr)
    reg('defer', Expressions.DeferExpr)



try:
    from zExceptions import Unauthorized
except ImportError:
    Unauthorized = "Unauthorized"

def call_with_ns(f, ns, arg=1):
    if arg==2:
        return f(None, ns)
    else:
        return f(ns)

class _SecureModuleImporter:
    """Simple version of the importer for use with trusted code."""
    __allow_access_to_unprotected_subobjects__ = 1
    def __getitem__(self, module):
        __import__(module)
        return sys.modules[module]


SecureModuleImporter = _SecureModuleImporter()



###########################################################################
# Redifine the PageTemplateFile methods that use getEngine and
# SecureModuleImporter
###########################################################################
class PageTemplateFile(ZopePageTemplateFile):
    def pt_getContext(self):
        root = self.getPhysicalRoot()
        c = {'template': self,
             'here': self._getContext(),
             'container': self._getContainer(),
             'nothing': None,
             'options': {},
             'root': root,
             'request': getattr(root, 'REQUEST', None),
             'modules': SecureModuleImporter,
             }
        return c


    def pt_render(self, source=0, extra_context={}):
        """Render this Page Template"""
        if not self._v_cooked:
            self._cook()

        __traceback_supplement__ = (PageTemplateTracebackSupplement, self)

        if self._v_errors:
            raise PTRuntimeError, 'Page Template %s has errors.' % self.id
        output = self.StringIO()
        c = self.pt_getContext()
        c.update(extra_context)

        TALInterpreter(self._v_program, self._v_macros,
                       getEngine().getContext(c),
                       output,
                       tal=not source, strictinsert=0)()
        return output.getvalue()


    def _cook(self):
        """Compile the TAL and METAL statments.

        A Page Template must always be cooked, and cooking must not
        fail due to user input.
        """
        if self.html():
            gen = TALGenerator(getEngine(), xml=0)
            parser = HTMLTALParser(gen)
        else:
            gen = TALGenerator(getEngine())
            parser = TALParser(gen)

        self._v_errors = ()
        try:
            parser.parseString(self._text)
            self._v_program, self._v_macros = parser.getCode()
        except:
            self._v_errors = ["Compilation failed",
                              "%s: %s" % sys.exc_info()[:2]]
        self._v_warnings = parser.getWarnings()
