# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

"""
STL stands for Simple Template Language, as it is the simplest template
language I could imagine.
"""

# Import from the Standard Library
from decimal import Decimal
import re

# Import from itools
from itools.datatypes import (Boolean, DataType, URI, XMLAttribute,
    XML as XMLContent)
from itools.schemas import (Schema as BaseSchema, get_datatype_by_uri,
    register_schema)
from itools.xml import (XMLError, XMLNSNamespace, get_namespace, set_namespace,
    AbstractNamespace, get_start_tag, get_end_tag, START_ELEMENT, END_ELEMENT,
    TEXT, COMMENT, find_end)
from itools.xhtml import (xhtml_uri, stream_to_str_as_html,
                          stream_to_str_as_xhtml)



stl_uri = 'http://xml.itools.org/namespaces/stl'

xmlns_uri = XMLNSNamespace.class_uri



########################################################################
# Exceptions
########################################################################
class STLSyntaxError(XMLError):
    pass


class STLNameError(NameError):
    pass


class STLTypeError(TypeError):
    pass


########################################################################
# Expressions
########################################################################

class Expression(object):
    """
    Parses and evaluates stl expressions.
    
    Examples of allowed expressions:
    
      none
      a
      a/b/c
      repeat/a/index
      ...
    """

    def __init__(self, expression):
        self.repeat = False
        # none
        if expression == 'none':
            self.path = ()
        else:
            path = expression.split('/')
            for x in path:
                if x == '':
                    raise STLSyntaxError, 'malformed STL expression'
            # repeat
            if path[0] == 'repeat':
                self.repeat = True
                path = path[1:]
                if len(path) != 2:
                    raise STLSyntaxError, 'malformed STL expression'
            self.path = tuple(path)


    ###################################################################
    # API
    ###################################################################
    def evaluate(self, stack, repeat):
        if not self.path:
            return None

        if self.repeat:
            stack = repeat

        # Traverse
        x = stack.lookup(self.path[0])
        for name in self.path[1:]:
            x = lookup(x, name)

        # Call
        if callable(x):
            try:
                x = x()
            except AttributeError, error_value:
                # XXX "callable" could return true even if the object is not
                # callable (see Python's documentation).
                #
                # This happens, for example, in the context of Zope, maybe
                # because of extension classes and acquisition. So we catch
                # the AttributeError exception, we should test also for the
                # exception value to be "__call__". This is dangereous
                # because we could hide real errors. Further exploration
                # needed..
                pass

        return x


    def __str__(self):
        if not self.path:
            return 'none'
        s = '/'.join(self.path)
        if self.repeat is True:
            return 'repeat/%s' % s
        return s


############################################################################
# Boolean expressions
class NotExpression(Expression):

    def __init__(self, expression):
        expression = expression[3:].strip()
        Expression.__init__(self, expression)


    def evaluate(self, stack, repeat):
        value = Expression.evaluate(self, stack, repeat)
        return not value


    def __str__(self):
        return 'not %s' % Expression.__str__(self)


###########################################################################
# Namespace
###########################################################################
def lookup(namespace, name):
    """
    Looks for a variable in a namespace (an instance, a mapping, etc..)
    """
    if hasattr(namespace, 'stl_lookup'):
        return namespace.stl_lookup(name)
    elif isinstance(namespace, dict):
        if name in namespace:
            return namespace[name]
    elif hasattr(namespace, name):
        return getattr(namespace, name)

    raise STLNameError, 'name "%s" not found in the namespace' % name



class NamespaceStack(list):
    """
    This class represents a namespace stack as used by STL. A variable
    is looked up in the stack from the top to the bottom until found.
    """

    def lookup(self, name):
        stack = self[:]
        stack.reverse()
        for namespace in stack:
            try:
                return lookup(namespace, name)
            except STLNameError:
                pass

        raise STLNameError, 'name "%s" not found in the namespace' % name


    def __getslice__(self, a, b):
        return self.__class__(list.__getslice__(self, a, b))



###########################################################################
# The tree
###########################################################################

class IfAttr(DataType):

    @staticmethod
    def decode(data):
        if data.startswith('not') and data[3].isspace():
            return NotExpression(data)
        return Expression(data)


    @staticmethod
    def encode(value):
        return str(value)



class RepeatAttr(DataType):

    @staticmethod
    def decode(data):
        name, expression = data.split(' ', 1)
        return name, Expression(expression)


    @staticmethod
    def encode(value):
        return '%s %s' % value



########################################################################
# The run-time engine
########################################################################
subs_expr_solo = re.compile("^\$\{([\w\/:]+?)\}$")
subs_expr = re.compile("\$\{(.+?)\}")


def substitute_boolean(data, stack, repeat_stack, encoding='utf-8'):
    if isinstance(data, bool):
        return data

    match = subs_expr_solo.match(data)
    if match is None:
        return True
    expr = Expression(match.group(1))
    value = expr.evaluate(stack, repeat_stack)
    return bool(value)


def substitute(data, stack, repeat_stack, encoding='utf-8'):
    """
    Interprets the given data as a substitution string with the "${expr}"
    format, where the expression within the brackets is an STL expression.

    Returns a tuple with the interpreted string and the number of
    substitutions done.
    """
    if isinstance(data, str):
        pass
    elif isinstance(data, unicode):
        data = data.encode('utf-8')
    else:
        data = str(data)
    # Solo, preserve the value None
    match = subs_expr_solo.match(data)
    if match is not None:
        expr = Expression(match.group(1))
        value = expr.evaluate(stack, repeat_stack)
        # Preserve the value None
        if value is None:
            return None, 1
        # Send the string
        if isinstance(value, unicode):
            return value.encode(encoding), 1
        return str(value), 1
    # A little more complex
    def repl(match):
        expr = Expression(match.group(1))
        value = expr.evaluate(stack, repeat_stack)
        # Remove if None
        if value is None:
            return ''
        # Send the string
        if isinstance(value, unicode):
            return value.encode(encoding)
        return str(value)
    return subs_expr.subn(repl, data)


def stl(document, namespace={}, prefix=None, html=True):
    # Initialize the namespace stack
    stack = NamespaceStack()
    stack.append(namespace)
    # Initialize the repeat stack (keeps repeat/index, repeat/odd, etc...)
    repeat = NamespaceStack()
    # Get the document
    events = document.events
    encoding = 'utf-8'
    stream = process(document, 0, len(events), stack, repeat, encoding, prefix)
    if html is True:
        return stream_to_str_as_html(stream, encoding)
    else:
        return stream_to_str_as_xhtml(stream, encoding)



stl_repeat = stl_uri, 'repeat'
stl_if = stl_uri, 'if'


def process_start_tag(tag_uri, tag_name, attributes, stack, repeat, encoding,
                      prefix):
    # Skip "stl:block" and "stl:inline"
    if tag_uri == stl_uri:
        return
    # Process attributes
    aux = {}
    for attr_uri, attr_name in attributes:
        # Omit stl attributes
        if attr_uri == stl_uri:
            continue
        # Omit stl namespace
        if attr_uri == xmlns_uri and attr_name == 'stl':
            continue

        value = attributes[(attr_uri, attr_name)]
        # Process "${...}" expressions
        datatype = get_datatype_by_uri(attr_uri, attr_name)
        # Boolean attributes
        if issubclass(datatype, Boolean):
            value = substitute_boolean(value, stack, repeat, encoding)
            if value is True:
                aux[(attr_uri, attr_name)] = attr_name
            continue
        # Non Boolean attributes
        value, n = substitute(value, stack, repeat, encoding)
        # Output only values different than None
        if value is None:
            continue
        # Rewrite URLs (XXX specific to HTML)
        if prefix is None or n > 0:
            aux[(attr_uri, attr_name)] = value
            continue
        if tag_uri == xhtml_uri and attr_uri == xhtml_uri:
            # <... src="X" />
            if attr_name == 'src':
                value = resolve_pointer(value, prefix)
            # <link href="X" />
            elif tag_name == 'link':
                if attr_name == 'href':
                    value = resolve_pointer(value, prefix)
            # <param name="movie" value="X" />
            elif tag_name == 'param':
                if attr_name == 'value':
                    param_name = attributes.get((attr_uri, 'name'))
                    if param_name == 'movie':
                        value = resolve_pointer(value, prefix)
        aux[(attr_uri, attr_name)] = value

    return START_ELEMENT, (tag_uri, tag_name, aux), None


def process(document, start, end, stack, repeat_stack, encoding, prefix=None):
    events = document.events

    i = start
    while i < end:
        event, value, line = events[i]
        if event == TEXT:
            value = value.encode(encoding)
            value = XMLContent.encode(value)
            value, kk = substitute(value, stack, repeat_stack, encoding)
            value = XMLContent.decode(value)
            value = unicode(value, encoding)
            yield event, value, line
        elif event == COMMENT:
            yield event, value, line
        elif event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            # stl:repeat
            if stl_repeat in attributes:
                attributes = attributes.copy()
                name, expression = attributes.pop(stl_repeat)
                # Build new namespace stacks
                loops = []
                values = expression.evaluate(stack, repeat_stack)
                n_values = len(values)
                for value in values:
                    loop_stack = stack[:]
                    loop_stack.append({name: value})
                    loop_repeat = repeat_stack[:]
                    loop_repeat.append(
                        {name: {'index': i,
                                'start': i == 0,
                                'end': i == n_values - 1,
                                'even': 'odd' if i % 2 else 'even'}})
                    loops.append((loop_stack, loop_repeat))
                # Filter the branches when "stl:if" is present
                if stl_if in attributes:
                    evaluate = attributes.pop(stl_if).evaluate
                    loops = [ x for x, y in loops if evaluate(x, y) ]
                # Process the loops
                loop_end = find_end(document.events, i)
                i += 1
                for loop_stack, loop_repeat in loops:
                    x = process_start_tag(tag_uri, tag_name, attributes,
                                          loop_stack, loop_repeat, encoding,
                                          prefix)
                    if x is not None:
                        yield x
                    for x in process(document, i, loop_end, loop_stack,
                                     loop_repeat, encoding, prefix):
                        yield x
                i = loop_end
            # stl:if
            elif stl_if in attributes:
                attributes = attributes.copy()
                expression = attributes.pop(stl_if)
                if expression.evaluate(stack, repeat_stack):
                    x = process_start_tag(tag_uri, tag_name, attributes, stack,
                                          repeat_stack, encoding, prefix)
                    if x is not None:
                        yield x
                else:
                    i = find_end(document.events, i)
            # nothing
            else:
                if tag_uri != stl_uri:
                    x = process_start_tag(tag_uri, tag_name, attributes, stack,
                                          repeat_stack, encoding, prefix)
                    if x is not None:
                        yield x
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_uri != stl_uri:
                yield event, value, line
        else:
            raise NotImplementedError
        # Next
        i += 1



def resolve_pointer(uri, offset):
    uri = URI.decode(uri)
    if not uri.scheme and not uri.authority:
        if uri.path.is_relative():
            if uri.path or str(uri) == '.':
                # XXX Here we loss the query and fragment.
                value = offset.resolve(uri.path)
                return str(value)

    return URI.encode(uri)


########################################################################
# The XML namespace handler
########################################################################

elements_schema = {
    'block': {'is_inline': False},
    'inline': {'is_inline': True}
    }


class Namespace(AbstractNamespace):

    class_uri = 'http://xml.itools.org/namespaces/stl'
    class_prefix = 'stl'


    @staticmethod
    def get_element_schema(name):
        try:
            return elements_schema[name]
        except KeyError:
            raise STLSyntaxError, 'unexpected element name: %s' % name

set_namespace(Namespace)


class Schema(BaseSchema):

    class_uri = 'http://xml.itools.org/namespaces/stl'
    class_prefix = 'stl'


    datatypes = {'repeat': RepeatAttr,
                 'if': IfAttr}

register_schema(Schema)
