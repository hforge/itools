# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
STL stands for Simple Template Language, as it is the simplest template
language I could imagine.
"""

# Import from the Standard Library
from re import compile
from types import GeneratorType

# Import from itools
from itools.datatypes import Boolean, String, URI
from itools.uri import Path
from itools.xml import (XMLError, XMLNSNamespace, set_namespace,
    get_namespace, AbstractNamespace, XMLParser, START_ELEMENT, END_ELEMENT,
    TEXT, COMMENT, find_end, stream_to_str)
from itools.html import (xhtml_uri, stream_to_str_as_html,
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
def evaluate(expression, stack, repeat_stack):
    """Parses and evaluates stl expressions.

    Examples of allowed expressions:

      none
      a
      a/b/c
      repeat/a/index
      ...
    """

    # none
    if expression == 'none':
        return None

    # Repeat
    path = expression.split('/')
    if path[0] == 'repeat':
        stack = repeat_stack
        path = path[1:]

    # Traverse
    value = stack.lookup(path[0])
    for name in path[1:]:
        value = lookup(value, name)

    # Call
    if callable(value):
        try:
            value = value()
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

    return value



def evaluate_if(expression, stack, repeat_stack):
    if expression[:3] == 'not' and expression[3].isspace():
        expression = expression[3:].lstrip()
        return not evaluate(expression, stack, repeat_stack)
    return evaluate(expression, stack, repeat_stack)



def evaluate_repeat(expression, stack, repeat_stack):
    name, expression = expression.split(' ', 1)
    values = evaluate(expression, stack, repeat_stack)
    return name, values


###########################################################################
# Namespace
###########################################################################
def lookup(namespace, name):
    """Looks for a variable in a namespace (an instance, a mapping, etc..)
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
    """This class represents a namespace stack as used by STL. A variable
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



########################################################################
# The run-time engine
########################################################################
subs_expr_solo = compile("^\$\{([\w\/:]+?)\}$")
subs_expr = compile("\$\{(.+?)\}")


def substitute_boolean(data, stack, repeat_stack, encoding='utf-8'):
    if isinstance(data, bool):
        return data

    match = subs_expr_solo.match(data)
    if match is None:
        return True
    expression = match.group(1)
    value = evaluate(expression, stack, repeat_stack)
    return bool(value)


def substitute_attribute(data, stack, repeat_stack, encoding='utf-8'):
    """Interprets the given data as a substitution string with the "${expr}"
    format, where the expression within the brackets is an STL expression.

    Returns a tuple with the interpreted string and the number of
    substitutions done.
    """
    if not isinstance(data, str):
        raise ValueError, 'byte string expected, not %s' % type(data)
    # Solo, preserve the value None
    match = subs_expr_solo.match(data)
    if match is not None:
        expression = match.group(1)
        value = evaluate(expression, stack, repeat_stack)
        # Preserve the value None
        if value is None:
            return None, 1
        # Send the string
        if isinstance(value, unicode):
            return value.encode(encoding), 1
        return str(value), 1
    # A little more complex
    def repl(match):
        expression = match.group(1)
        value = evaluate(expression, stack, repeat_stack)
        # Remove if None
        if value is None:
            return ''
        # Send the string
        if isinstance(value, unicode):
            return value.encode(encoding)
        return str(value)
    return subs_expr.subn(repl, data)



def substitute(data, stack, repeat_stack, encoding='utf-8'):
    """Interprets the given data as a substitution string with the "${expr}"
    format, where the expression within the brackets is an STL expression.

    Returns a tuple with the interpreted string and the number of
    substitutions done.
    """
    if not isinstance(data, str):
        raise ValueError, 'byte string expected, not %s' % type(data)

    start = 0
    state = 0
    for i, c in enumerate(data):
        if state == 0:
            if c == '$':
                state = 1
        elif state == 1:
            if c == '{':
                end = (i - 1)
                state = 2
            else:
                state = 0
        elif state == 2:
            if c == '}':
                # Evaluate expression
                expression = data[end+2:i]
                value = evaluate(expression, stack, repeat_stack)
                # Next
                if end > start:
                    yield TEXT, data[start:end], 0
                start = (i + 1)
                state = 0
                # Send back
                if value is None:
                    continue
                if isinstance(value, (list, GeneratorType, XMLParser)):
                    for x in value:
                        yield x
                elif isinstance(value, unicode):
                    yield TEXT, value.encode(encoding), 0
                else:
                    yield TEXT, str(value), 0

    if start <= i:
        yield TEXT, data[start:], 0



def stl(document=None, namespace={}, prefix=None, events=None, mode='events'):
    # Input
    encoding = 'utf-8'
    if events is None:
        events = document.events

    # Prefix
    if prefix is not None:
        stream = set_prefix(events, prefix)
        events = list(stream)
    elif isinstance(events, (GeneratorType, XMLParser)):
        events = list(events)

    # Initialize the namespace stacks
    stack = NamespaceStack()
    stack.append(namespace)
    repeat = NamespaceStack()

    # Process
    stream = process(events, 0, len(events), stack, repeat, encoding)

    # Return
    if mode == 'events':
        return stream
    elif mode == 'xml':
        return stream_to_str(stream, encoding)
    elif mode == 'xhtml':
        return stream_to_str_as_xhtml(stream, encoding)
    elif mode == 'html':
        return stream_to_str_as_html(stream, encoding)

    raise ValueError, 'unexpected mode "%s"' % mode



stl_repeat = stl_uri, 'repeat'
stl_if = stl_uri, 'if'


def process_start_tag(tag_uri, tag_name, attributes, stack, repeat, encoding):
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
        datatype = get_namespace(attr_uri).get_datatype(attr_name)
        # Boolean attributes
        if issubclass(datatype, Boolean):
            value = substitute_boolean(value, stack, repeat, encoding)
            if value is True:
                aux[(attr_uri, attr_name)] = attr_name
            continue
        # Non Boolean attributes
        value, n = substitute_attribute(value, stack, repeat, encoding)
        # Output only values different than None
        if value is None:
            continue
        aux[(attr_uri, attr_name)] = value

    return START_ELEMENT, (tag_uri, tag_name, aux), None


def process(events, start, end, stack, repeat_stack, encoding):
    i = start
    while i < end:
        event, value, line = events[i]
        if event == TEXT:
            stream = substitute(value, stack, repeat_stack, encoding)
            for event, value, kk in stream:
                yield event, value, line
        elif event == COMMENT:
            yield event, value, line
        elif event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            # stl:repeat
            if stl_repeat in attributes:
                attributes = attributes.copy()
                expr = attributes.pop(stl_repeat)
                name, values = evaluate_repeat(expr, stack, repeat_stack)
                # Build new namespace stacks
                loops = []
                n_values = len(values)
                for j, value in enumerate(values):
                    loop_stack = stack[:]
                    loop_stack.append({name: value})
                    loop_repeat = repeat_stack[:]
                    loop_repeat.append(
                        {name: {'index': j,
                                'start': j == 0,
                                'end': j == n_values - 1,
                                'even': j % 2 and 'odd' or 'even'}})
                    loops.append((loop_stack, loop_repeat))
                # Filter the branches when "stl:if" is present
                if stl_if in attributes:
                    expr = attributes.pop(stl_if)
                    loops = [ (x, y) for x, y in loops
                              if evaluate_if(expr, x, y) ]
                # Process the loops
                loop_end = find_end(events, i)
                i += 1
                for loop_stack, loop_repeat in loops:
                    x = process_start_tag(tag_uri, tag_name, attributes,
                                          loop_stack, loop_repeat, encoding)
                    if x is not None:
                        yield x
                    for y in process(events, i, loop_end, loop_stack,
                                     loop_repeat, encoding):
                        yield y
                    if x is not None:
                        yield events[loop_end]
                i = loop_end
            # stl:if
            elif stl_if in attributes:
                attributes = attributes.copy()
                expression = attributes.pop(stl_if)
                if evaluate_if(expression, stack, repeat_stack):
                    x = process_start_tag(tag_uri, tag_name, attributes, stack,
                                          repeat_stack, encoding)
                    if x is not None:
                        yield x
                else:
                    i = find_end(events, i)
            # nothing
            else:
                if tag_uri != stl_uri:
                    x = process_start_tag(tag_uri, tag_name, attributes, stack,
                                          repeat_stack, encoding)
                    if x is not None:
                        yield x
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_uri != stl_uri:
                yield event, value, line
        else:
            yield events[i]
        # Next
        i += 1



########################################################################
# Set prefix
########################################################################
def set_prefix(stream, prefix):
    if isinstance(prefix, str):
        prefix = Path(prefix)

    for event in stream:
        type, value, line = event
        # Rewrite URLs (XXX specific to HTML)
        if type == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            aux = {}
            for attr_uri, attr_name in attributes:
                value = attributes[(attr_uri, attr_name)]
                if tag_uri == xhtml_uri and attr_uri == xhtml_uri:
                    # <... src="X" />
                    if attr_name == 'src':
                        value = resolve_pointer(value, prefix)
                    # <a href="X"> or <link href="X">
                    elif tag_name in ('a', 'link'):
                        if attr_name == 'href':
                            value = resolve_pointer(value, prefix)
                    # <param name="movie" value="X" />
                    elif tag_name == 'param':
                        if attr_name == 'value':
                            param_name = attributes.get((attr_uri, 'name'))
                            if param_name == 'movie':
                                value = resolve_pointer(value, prefix)
                aux[(attr_uri, attr_name)] = value
            yield START_ELEMENT, (tag_uri, tag_name, aux), line
        else:
            yield event



def resolve_pointer(value, offset):
    # XXX Exception for STL
    if value.startswith('${'):
        return value

    uri = URI.decode(value)
    if not uri.scheme and not uri.authority:
        if uri.path.is_relative():
            if uri.path or str(uri) == '.':
                # XXX Here we loss the query and fragment.
                value = offset.resolve(uri.path)
                return str(value)

    return value


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

    datatypes = {'repeat': String, 'if': String}

    @staticmethod
    def get_element_schema(name):
        try:
            return elements_schema[name]
        except KeyError:
            raise STLSyntaxError, 'unexpected element name: %s' % name

set_namespace(Namespace)

