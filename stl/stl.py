# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007-2008 Henry Obein <henry@itaapy.com>
# Copyright (C) 2007-2008 Sylvain Taverne <sylvain@itaapy.com>
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
from types import GeneratorType, MethodType

# Import from itools
from itools.core import freeze, thingy
from itools.datatypes import Boolean
from itools.gettext import MSG
from itools.log import log_error
from itools.uri import Path, Reference, get_reference
from itools.xml import XMLParser, find_end, get_attr_datatype , stream_to_str
from itools.xml import DOCUMENT_TYPE, START_ELEMENT, END_ELEMENT, TEXT
from itools.xml import xmlns_uri
from itools.html import xhtml_uri
from itools.html import stream_to_str_as_html, stream_to_str_as_xhtml
from schema import stl_uri



########################################################################
# Exceptions
########################################################################
class STLError(StandardError):
    pass


ERR_EXPR_VALUE = "unexpected value for the '${%s}' expression"



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
    err = "evaluation of '%s' failed, '%s' could not be resolved"
    try:
        value = stack.lookup(path[0])
    except STLError:
        raise STLError, err % (expression, path[0])

    for name in path[1:]:
        try:
            value = lookup(value, name)
        except STLError:
            raise STLError, err % (expression, name)

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
    # Case 1: dict
    if type(namespace) is dict:
        if name not in namespace:
            raise STLError
        return namespace[name]

    # Case 2: instance
    try:
        value = getattr(namespace, name)
    except AttributeError:
        log_error('lookup failed', domain='itools.stl')
        raise STLError
    if type(value) is MethodType:
        value = value()
    return value


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
            except STLError:
                pass

        raise STLError, 'name "%s" not found in the namespace' % name


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
        if isinstance(value, MSG):
            return value.gettext().encode(encoding), 1
        elif type(value) is unicode:
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
        if isinstance(value, MSG):
            return value.gettext().encode(encoding)
        elif type(value) is unicode:
            return value.encode(encoding)
        return str(value)
    return subs_expr.subn(repl, data)



def substitute(data, stack, repeat_stack, encoding='utf-8'):
    """Interprets the given data as a substitution string with the "${expr}"
    format, where the expression within the brackets is an STL expression.

    Returns a tuple with the interpreted string and the number of
    substitutions done.
    """
    if type(data) is not str:
        raise ValueError, 'byte string expected, not %s' % type(data)

    segments = subs_expr.split(data)
    for i, segment in enumerate(segments):
        if i % 2:
            # Evaluate expression
            value = evaluate(segment, stack, repeat_stack)
            # An STL template (duck typing)
            render = getattr(value, 'render', None)
            if render:
                value = render()
            # Ignore if None
            if value is None:
                continue
            # Yield
            if isinstance(value, MSG):
                value = value.gettext()
                yield TEXT, value.encode(encoding), 0
            elif isinstance(value, (list, GeneratorType, XMLParser)):
                for x in value:
                    if type(x) is not tuple:
                        raise STLError, ERR_EXPR_VALUE % segment
                    yield x
            elif type(value) is unicode:
                yield TEXT, value.encode(encoding), 0
            else:
                yield TEXT, str(value), 0
        elif segment:
            yield TEXT, segment, 0



def stl(document=None, namespace=freeze({}), prefix=None, events=None,
        mode='events', skip=(DOCUMENT_TYPE,)):
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
    stream = process(events, 0, len(events), stack, repeat, encoding, skip)

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
stl_omit_tag = stl_uri, 'omit-tag'


def process_start_tag(tag_uri, tag_name, attributes, stack, repeat, encoding):
    # Skip "<stl:block>" and "<stl:inline>"
    if tag_uri == stl_uri:
        return None

    # stl:omit-tag
    if stl_omit_tag in attributes:
        expression = attributes[stl_omit_tag]
        if evaluate_if(expression, stack, repeat):
            return None

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
        datatype = get_attr_datatype(tag_uri, tag_name, attr_uri, attr_name,
                                     attributes)
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


def process(events, start, end, stack, repeat_stack, encoding, skip_events):
    skip = set()
    i = start
    while i < end:
        event, value, line = events[i]
        if event == TEXT:
            stream = substitute(value, stack, repeat_stack, encoding)
            for event, value, kk in stream:
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
                                     loop_repeat, encoding, skip_events):
                        yield y
                    if x is not None:
                        yield events[loop_end]
                i = loop_end
            # stl:if
            elif stl_if in attributes:
                attributes = attributes.copy()
                expression = attributes.pop(stl_if)
                if evaluate_if(expression, stack, repeat_stack):
                    x = process_start_tag(tag_uri, tag_name, attributes,
                                          stack, repeat_stack, encoding)
                    if x is None:
                        skip.add(find_end(events, i))
                    else:
                        yield x
                else:
                    i = find_end(events, i)
            # nothing
            else:
                if tag_uri != stl_uri:
                    x = process_start_tag(tag_uri, tag_name, attributes,
                                          stack, repeat_stack, encoding)
                    if x is None:
                        skip.add(find_end(events, i))
                    else:
                        yield x
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_uri != stl_uri and i not in skip:
                yield event, value, line
        elif event not in skip_events:
            yield event, value, line
        # Next
        i += 1



########################################################################
# Set prefix
########################################################################
css_uri_expr = compile (r"url\(([a-zA-Z0-9\./%\-\_]*/%3[bB]{1}download)\);")

def set_prefix(stream, prefix, ns_uri=xhtml_uri):
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
                if tag_uri == ns_uri and attr_uri in (None, ns_uri):
                    # <... src="X" />
                    if attr_name == 'src':
                        value = resolve_pointer(value, prefix)
                    # <a href="X"> or <link href="X">
                    elif tag_name in ('a', 'link'):
                        if attr_name == 'href':
                            value = resolve_pointer(value, prefix)
                    elif attr_name == 'style':
                        # Rewrite url inside style attribute
                        # Get the chunks
                        chunks = []
                        segments = css_uri_expr.split(value)
                        for index, segment in enumerate(segments):
                            if index % 2 == 1:
                                new_segment = resolve_pointer(segment, prefix)
                                chunks.append('url(%s);' % new_segment)
                            else:
                                chunks.append(segment)
                        value = ''.join(chunks)
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
    # FIXME Exception for STL
    if value[:2] == '${':
        return value

    # Absolute URI or path
    uri = get_reference(value)
    if uri.scheme or uri.authority or uri.path.is_absolute():
        return value

    # Resolve Path
    path = offset.resolve(uri.path)
    value = Reference('', '', path, uri.query.copy(), uri.fragment)
    return str(value)


###########################################################################
# Templates
###########################################################################

class STLTemplate(thingy):

    def show(self):
        return True


    def get_template(self):
        raise NotImplementedError


    def render(self):
        if self.show() is False:
            return None

        # Case 1: a ready made list of events
        template = self.get_template()
        if type(template) is list:
            return stl(events=template, namespace=self)

        # Case 2: we assume it is a handler
        return stl(template, self)

