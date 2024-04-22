# Copyright (C) 2003-2011 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2006, 2010 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2007-2008, 2010 Sylvain Taverne <taverne.sylvain@gmail.com>
# Copyright (C) 2007-2011 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2008 David Versmisse <versmisse@lil.univ-littoral.fr>
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
from functools import partial
from re import compile
from types import GeneratorType, MethodType
from logging import getLogger

# Import from itools
from itools.core import freeze, prototype
from itools.datatypes import Boolean
from itools.gettext import MSG
from itools.uri import Path, Reference, get_reference
from itools.xml import XMLParser, find_end, get_attr_datatype, stream_to_str
from itools.xml import DOCUMENT_TYPE, START_ELEMENT, END_ELEMENT, TEXT
from itools.xml import xmlns_uri
from itools.xml import is_xml_stream
from itools.xmlfile import XMLFile, get_units
from itools.html import xhtml_uri
from itools.html import stream_to_str_as_html, stream_to_str_as_xhtml
from .schema import stl_uri

log = getLogger("itools.stl")


########################################################################
# Exceptions
########################################################################
class STLError(Exception):
    pass


ERR_EXPR_XML = 'expected XML stream not "%s" in "${%s}" expression'



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
        raise STLError(err % (expression, path[0]))

    for name in path[1:]:
        try:
            value = lookup(value, name)
        except STLError:
            raise STLError(err % (expression, name))

    return value


def evaluate_if(expression, stack, repeat_stack):
    # stl:if="expression1 and expression2"
    # stl:if="expression1 or expression2"
    # stl:if="not expression1 and not expression2"
    for text_operator in [' and ', ' or ']:
        if text_operator in expression:
            ex1, ex2 = expression.split(text_operator)
            if ex1[:4] == 'not ':
                ex1 = ex1[4:]
                condition1 = not evaluate(ex1, stack, repeat_stack)
            else:
                condition1 = evaluate(ex1, stack, repeat_stack)
            if ex2[:4] == 'not ':
                ex2 = ex2[4:]
                condition2 = not evaluate(ex2, stack, repeat_stack)
            else:
                condition2 = evaluate(ex2, stack, repeat_stack)
            if text_operator == ' or ':
                return condition1 or condition2
            return condition1 and condition2
    # stl:if="not expression"
    if expression[:4] == 'not ':
        return not evaluate(expression[4:], stack, repeat_stack)
    # stl:if="expression"
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
            err = "name '{}' not found in the namespace"
            raise STLError(err.format(name))
        return namespace[name]

    # Case 2: instance
    try:
        value = getattr(namespace, name)
    except AttributeError:
        err = f"Lookup failed : name '{name}' not found in the namespace"
        log.error(err, exc_info=True)
        raise STLError(err.format(name))
    if type(value) is MethodType:
        value = value()
    return value


class NamespaceStack(list):
    """This class represents a namespace stack as used by STL. A variable
    is looked up in the stack from the top to the bottom until found.
    """

    def lookup(self, name):
        for namespace in reversed(self):
            try:
                return lookup(namespace, name)
            except STLError:
                pass

        raise STLError(f'name "{name}" not found in the namespace')

    def __getslice__(self, a, b):
        return self.__class__(list.__getslice__(self, a, b))



########################################################################
# The run-time engine
########################################################################
subs_expr_solo = compile(r"^\$\{([\w\/:]+?)\}$")
subs_expr = compile(r"\$\{(.+?)\}")


def substitute_boolean(data, stack, repeat_stack, encoding='utf-8'):
    if type(data) is bool:
        return data

    match = subs_expr_solo.match(data)
    if match is None:
        return True
    expression = match.group(1)
    value = evaluate(expression, stack, repeat_stack)
    return bool(value)


def substitute_attribute(data, stack, repeat_stack):
    """Interprets the given data as a substitution string with the "${expr}"
    format, where the expression within the brackets is an STL expression.

    Returns a tuple with the interpreted string and the number of
    substitutions done.
    """
    if type(data) is not str:
        raise ValueError(f'byte string expected, not {type(data)}')
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
            return value.gettext(), 1
        elif type(value) is str:
            return value, 1
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
            return value.gettext()
        elif type(value) is str:
            return value
        return str(value)
    return subs_expr.subn(repl, data)


def substitute(data, stack, repeat_stack, encoding='utf-8'):
    """Interprets the given data as a substitution string with the "${expr}"
    format, where the expression within the brackets is an STL expression.

    Returns a tuple with the interpreted string and the number of
    substitutions done.
    """
    if type(data) is not str:
        raise ValueError(f'byte string expected, not {type(data)}')

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

            # Case MSG: it returns <unicode> or <XMLParser>
            if isinstance(value, MSG):
                value = value.gettext()

            # Yield
            if type(value) is str:
                yield TEXT, value, 0
            elif is_xml_stream(value):
                for x in value:
                    if type(x) is not tuple:
                        raise STLError(ERR_EXPR_XML % (type(x), segment))
                    yield x
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
    elif type(events) in (GeneratorType, XMLParser):
        events = list(events)

    # Initialize the namespace stacks
    stack = NamespaceStack()
    stack.append(namespace)
    repeat = NamespaceStack()

    # Process
    stream = process(events, 0, len(events), stack, repeat, encoding, skip)

    # Return
    try:
        if mode == 'events':
            return stream
        elif mode == 'xml':
            return stream_to_str(stream, encoding)
        elif mode == 'xhtml':
            return stream_to_str_as_xhtml(stream, encoding)
        elif mode == 'html':
            return stream_to_str_as_html(stream, encoding)
    except STLError as e:
        error = f'Error in generation of {mode}\n'
        if document:
            error += f'Template {document.key}\n'
        raise STLError(error + str(e))
    # Unknow mode
    raise ValueError(f'unexpected mode "{mode}"')


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
        value, n = substitute_attribute(value, stack, repeat)
        # Output only values different than None
        if value is None:
            continue
        aux[(attr_uri, attr_name)] = value

    return START_ELEMENT, (tag_uri, tag_name, aux), None


def process(events, start, end, stack, re_stack, encoding, skip_events):
    skip = set()
    i = start
    while i < end:
        event, value, line = events[i]
        if event == TEXT:
            stream = substitute(value, stack, re_stack, encoding)
            for event, value, kk in stream:
                yield event, value, line
        elif event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            # stl:repeat
            if stl_repeat in attributes:
                attributes = attributes.copy()
                re_expr = attributes.pop(stl_repeat)
                if_expr = attributes.pop(stl_if, None)
                loop_end = find_end(events, i)
                i += 1
                # repeat...
                name, values = evaluate_repeat(re_expr, stack, re_stack)
                n_values = len(values)
                for j, value in enumerate(values):
                    # 1. New stacks
                    stack.append({name: value})
                    re_stack.append(
                        {name: {'index': j,
                                'start': j == 0,
                                'end': j == n_values - 1,
                                'even': j % 2 and 'odd' or 'even'}})
                    # 2. stl:if
                    if if_expr and not evaluate_if(if_expr, stack, re_stack):
                        continue
                    # 3. Process
                    x = process_start_tag(tag_uri, tag_name, attributes,
                                          stack, re_stack, encoding)
                    if x is not None:
                        yield x
                    yield from process(events, i, loop_end, stack, re_stack,
                                     encoding, skip_events)
                    if x is not None:
                        yield events[loop_end]
                    # 4. Restore stacks
                    stack.pop()
                    re_stack.pop()
                i = loop_end
            # stl:if
            elif stl_if in attributes:
                attributes = attributes.copy()
                expression = attributes.pop(stl_if)
                if evaluate_if(expression, stack, re_stack):
                    x = process_start_tag(tag_uri, tag_name, attributes,
                                          stack, re_stack, encoding)
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
                                          stack, re_stack, encoding)
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
css_uri_expr = compile(r"url\(([a-zA-Z0-9\./%\-\_]*/%3[bB]{1}download)\);")


def set_prefix(stream, prefix, ns_uri=xhtml_uri, uri=None):
    if isinstance(prefix, str):
        prefix = Path(prefix)

    ref = None
    if uri:
        ref = Reference(scheme=uri.scheme, authority=uri.authority,
                        path='/', query={})
    rewrite = partial(resolve_pointer, prefix, ref)

    return rewrite_uris(stream, rewrite, ns_uri)


def resolve_pointer(offset, reference, value):
    # FIXME Exception for STL
    if value[:2] == '${':
        return value

    # Absolute URI or path
    uri = get_reference(value)
    if uri.scheme or uri.authority:
        return value

    # Resolve Path
    if uri.path.is_absolute():
        if reference is None:
            return value
        # Do not call resolve with absolute path
        path = uri.path
    else:
        path = offset.resolve(uri.path)

    scheme = authority = ''
    if reference:
        scheme = reference.scheme
        authority = reference.authority
    value = Reference(scheme, authority, path, uri.query.copy(), uri.fragment)
    return str(value)


def rewrite_uris(stream, rewrite, ns_uri=xhtml_uri):
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
                        value = rewrite(value)
                    # <a href="X"> or <link href="X">
                    elif tag_name in ('a', 'link'):
                        if attr_name == 'href':
                            value = rewrite(value)
                    elif attr_name == 'style':
                        # Rewrite url inside style attribute
                        # Get the chunks
                        chunks = []
                        segments = css_uri_expr.split(value)
                        for index, segment in enumerate(segments):
                            if index % 2 == 1:
                                new_segment = rewrite(segment)
                                chunks.append(f'url({new_segment});')
                            else:
                                chunks.append(segment)
                        value = ''.join(chunks)
                    # <object type="application/x-shockwave-flash" data="...">
                    elif tag_name == 'object':
                        if attr_name == 'data':
                            attr_type = attributes.get((attr_uri, 'type'))
                            if attr_type == 'application/x-shockwave-flash':
                                value = rewrite(value)
                    # <param name="movie" value="X" />
                    elif tag_name == 'param':
                        if attr_name == 'value':
                            param_name = attributes.get((attr_uri, 'name'))
                            if param_name == 'movie':
                                value = rewrite(value)
                aux[(attr_uri, attr_name)] = value
            yield START_ELEMENT, (tag_uri, tag_name, aux), line
        else:
            yield event


###########################################################################
# STLFile
###########################################################################
class STLFile(XMLFile):

    # FIXME To be changed once we have our own extension and mimetype (#864)
    class_mimetypes = ['text/xml', 'application/xml', 'application/xhtml+xml']

    def get_units(self, srx_handler=None):
        for source, context, line in get_units(self.events, srx_handler):
            if len(source) > 1 or subs_expr_solo.match(source[0][1]) is None:
                yield source, context, line


###########################################################################
# Templates
###########################################################################

class STLTemplate(prototype):

    template = None
    show = True

    def get_template(self):
        if type(self.template) is list:
            return self.template

        error = 'template variable of unexpected type "%s"'
        raise TypeError(error % type(self.template).__name__)

    def render(self, mode='events'):
        if not self.show:
            return None

        # Case 1: a ready made list of events
        template = self.get_template()
        if type(template) is list:
            return stl(events=template, namespace=self, mode=mode)

        # Case 2: we assume it is a handler
        return stl(template, self, mode=mode)

