# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA


"""
STL stands for Simple Template Language, as it is the simplest template
language I could imagine.
"""


# Import from itools
from itools.xml import XML



stl_uri = 'http://xml.itools.org/namespaces/stl'



########################################################################
# Exceptions
########################################################################
class STLSyntaxError(XML.XMLError):
    pass


class STLNameError(NameError):
    pass


class STLTypeError(TypeError):
    pass


########################################################################
# Expressions
########################################################################

# Tokens
TID, TSLASH, TOPEN, TCLOSE, TEOF, TREPEAT = range(6)
token_name = ['id', 'slash', 'open parentheses', 'close parentheses',
              'end of expression', 'reserved word "repeat"']


keywords = {'repeat': TREPEAT}


class Expression(object):
    """
    Parses and evaluates stl expressions.
    
    Examples of allowed expressions:
    
      a
      a(literal)
      a/b/c
      a/b/c(content)
      ...
    """

    def __init__(self, expression):
        self.expression = expression

        # Initialize semantic structures
        self.path = ()
        self.parameters = ()
        self.repeat = False

        # Parsing
        self.index = 0
        self.parse()
        del self.index


    ###################################################################
    # Lexical analysis
    ###################################################################
    def get_token(self):
        token = TEOF
        lexeme = None
        state = 0

        while self.index < len(self.expression):
            c = self.expression[self.index]
            if state == 0:
                self.index += 1
                if c.isalnum() or c in ('_', '.'):
                    lexeme = c
                    state = 1
                elif c == '/':
                    return TSLASH, c
                elif c == '(':
                    return TOPEN, c
                elif c == ')':
                    return TCLOSE, c
                else:
                    raise STLSyntaxError, 'unexpected character (%s)' % c
            elif state == 1:
                if c.isalnum() or c in ('_', '.'):
                    lexeme += c
                    self.index += 1
                else:
                    break

        if lexeme is not None:
            token = keywords.get(lexeme, TID)

        return token, lexeme


    ###################################################################
    # Syntax and semantic analysis. Grammar:
    #
    #   parse = TID parser1
    #           | TREPEAT TSLASH TID TSLASH TID
    #   parser1 = TEOF
    #             | TSLASH parse
    #             | TOPEN parser2
    #   parser2 = TID parser3
    #   parser3 = TCLOSE TEOF
    ###################################################################
    def parse(self):
        token, lexeme = self.get_token()
        if token == TID:
            self.path = self.path + (lexeme,)
            self.parser1()
            return
        elif token == TREPEAT:
            self.repeat = True
            token, lexeme = self.get_token()
            if token == TSLASH:
                token, lexeme = self.get_token()
                if token == TID:
                    self.path = self.path + (lexeme,)
                    token, lexeme = self.get_token()
                    if token == TSLASH:
                        token, lexeme = self.get_token()
                        if token == TID:
                            self.path = self.path + (lexeme,)
                            return

        raise STLSyntaxError, 'unexpected %s' % token_name[token]


    def parser1(self):
        token, lexeme = self.get_token()
        if token == TEOF:
            return
        elif token == TSLASH:
            self.parse()
            return
        elif token == TOPEN:
            self.parser2()
            return

        raise STLSyntaxError, 'unexpected %s' % token_name[token]


    def parser2(self):
        token, lexeme = self.get_token()
        if token == TID:
            self.parameters = (lexeme,)
            self.parser3()
            return

        raise STLSyntaxError, 'unexpected %s' % token_name[token]


    def parser3(self):
        token, lexeme = self.get_token()
        if token == TCLOSE:
            token, lexeme = self.get_token()
            if token == TEOF:
                return

        raise STLSyntaxError, 'unexpected %s' % token_name[token]


    ###################################################################
    # API
    ###################################################################
    def evaluate(self, stack, repeat):
        if self.repeat:
            stack = repeat

        # Traverse
        x = stack.lookup(self.path[0])
        for name in self.path[1:]:
            x = lookup(x, name)

        # Call
        if self.parameters:
            x = apply(x, self.parameters)
        elif callable(x):
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
        s = '/'.join(self.path)
        if self.repeat is True:
            return 'repeat/%s' % s
        if self.parameters:
            return s + '(%s)' % self.parameters
        return s


########################################################################
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


# List of Boolean attributes in HTML that should be rendered in
# minimized form (e.g. <img ismap> rather than <img ismap="">)
# From http://www.w3.org/TR/xhtml1/#guidelines (C.10)
boolean_html_attributes = ['compact', 'nowrap', 'ismap', 'declare', 'noshade',
                           'checked', 'disabled', 'readonly', 'multiple',
                           'selected', 'noresize', 'defer']



########################################################################
# STL elements
class Element(XML.Element):
    namespace = 'http://xml.itools.org/namespaces/stl'

    def is_block(self):
        return self.name == 'block'


    def is_inline(self):
        return self.name == 'inline'



########################################################################
# STL attributes
class RepeatAttr(object):
    def __init__(self, value):
        name, expression = value.split(' ', 1)
        self.stl_name = name
        self.stl_expression = Expression(expression)

    def __str__(self):
        return '%s %s' % (self.stl_name, self.stl_expression)


# XXX This could be removed if "NSHandler.get_attributes" returns directly
# "self.stl_attributes"
class AttributesAttr(object):
    def __init__(self, value):
        attributes = []
        for x in value.split(';'):
            x = x.strip().split(' ', 1)
            if len(x) == 1:
                raise STLSyntaxError, \
                      'attributes expression expects two fields'

            name, expr = x
            if expr.startswith('not '):
                expr = NotExpression(expr)
            else:
                expr = Expression(expr)
            attributes.append((name, expr))

        self.stl_attributes = tuple(attributes)


    def __str__(self):
        return ';'.join([ '%s %s' % x for x in self.stl_attributes ])


########################################################################
# The namespace handler
class STL(object):
    """The stl namespace handler. It is an aspect."""

    def __call__(self, namespace={}):
        # XXX Rewrite with traverse2.

        # Initialize the namespace stack
        stack = NamespaceStack()
        stack.append(namespace)
        # Initialize the repeat stack (keeps repeat/index, repeat/odd, etc...)
        repeat = NamespaceStack()
        # Get the document
        document = self.handler
        # Process the children
        s = []
        for child in document.children:
            if isinstance(child, XML.Element):
                s.extend(self.process(child, stack, repeat))
            else:
                s.append(child.to_unicode())
        return u''.join(s)


    def process(self, node, stack, repeat_stack):
        # Raw nodes
        if isinstance(node, (XML.Raw, XML.Comment)):
            return [node.to_unicode()]

        s = []
        # Process stl:repeat
        if node.has_attribute('repeat', namespace=stl_uri):
            repeat = node.get_attribute('repeat', namespace=stl_uri)
            name, expression = repeat.stl_name, repeat.stl_expression

            i = 0
            values = expression.evaluate(stack, repeat_stack)
            nvalues = len(values)
            for value in values:
                # Create the new stack
                newstack = stack[:]
                newstack.append({name: value})

                newrepeat = repeat_stack[:]
                value = {'index': i,
                         'start': i == 0,
                         'end': i == nvalues - 1}
                newrepeat.append({name: value})

                # Process and append the clone
                s.extend(self.process1(node, newstack, newrepeat))

                # Increment counter
                i = i + 1

            return s

        s.extend(self.process1(node, stack, repeat_stack))
        return s


    def process1(self, node, stack, repeat):
        """
        Process stl:if, stl:attributes and stl:content.
        """
        # Remove the element if the given expression evaluates to false
        if node.has_attribute('if', namespace=stl_uri):
            stl_expression = node.get_attribute('if', namespace=stl_uri)
            if not stl_expression.evaluate(stack, repeat):
                return []

        # Print tag name
        s = ['<%s' % node.qname]

        # Process attributes
        changed_attributes = {} # qname: value
        # Evaluate stl:attributes
        if node.has_attribute('attributes', namespace=stl_uri):
            value = node.get_attribute('attributes', namespace=stl_uri)
            for name, expression in value.stl_attributes:
                value = expression.evaluate(stack, repeat)
                # XXX Do it only if it is an HTML document.
                if name in boolean_html_attributes:
                    if bool(value) is True:
                        value = name
                    else:
                        value = None
                # Coerce
                elif isinstance(value, int):
                    value = str(value)
                changed_attributes[name] = value

        # Output existing attributes
        for qname, value in node.attributes_by_qname.items():
            # Ommit stl attributes (XXX it should check the namespace, not the
            # prefix).
            if qname.startswith('stl:'):
                continue
            # Get the attribute value
            if qname in changed_attributes:
                value = changed_attributes.pop(qname)
            # Output only values different than None
            if value is not None:
                s.append(' %s="%s"' % (qname, value))

        # Output remaining attributes
        for qname, value in changed_attributes.items():
            if value is not None:
                s.append(' %s="%s"' % (qname, value))

        # Close the open tag
        s.append('>')

        # Process the content
        if node.has_attribute('content', namespace=stl_uri):
            stl_expression = node.get_attribute('content', namespace=stl_uri)
            content = stl_expression.evaluate(stack, repeat)
            # Coerce
            if isinstance(content, unicode):
                pass
            elif isinstance(content, str):
                content = [unicode(content)]
            elif isinstance(content, int):
                content = [unicode(content)]
            else:
                msg = 'expression "%(expr)s" evaluates to value of' \
                      ' unexpected type %(type)s'
                msg = msg % {'expr': str(stl_expression),
                             'type': content.__class__.__name__}
                raise STLTypeError, msg
        else:
            content = []
            for child in node.children:
                content.extend(self.process(child, stack, repeat))

        # Remove the element but preserves its children if it is a stl:block
        # or a stl:inline
        if isinstance(node, Element):
            return content

        s.extend(content)
        s.append('</%s>' % node.qname)
        return s



########################################################################
# Interface for the XML parser, factories
class Namespace(XML.Namespace):

    def namespace_handler(cls, document):
        if not hasattr(document, 'stl'):
            aspect = STL()
            aspect.handler = document
            document.stl = aspect

    namespace_handler = classmethod(namespace_handler)


    def get_element(cls, prefix, name):
        """Element factory, returns the right element instance."""
        if name in ('block', 'inline'):
            return Element(prefix, name)

        raise STLSyntaxError, 'unexpected element name: %s' % name

    get_element = classmethod(get_element)


    def get_attribute(cls, prefix, name, value):
        """Attribute factory, returns the right attribute instance."""
        attributes = {'repeat': RepeatAttr,
                      'attributes': AttributesAttr,
                      'content': Expression}
        if name == 'if':
            if value.startswith('not '):
                return NotExpression(value)
            else:
                return Expression(value)
        elif name in attributes:
            attribute = attributes[name]
            return attribute(value)
        else:
            raise STLSyntaxError, 'unexpected attribute name: %s' % name

    get_attribute = classmethod(get_attribute)


########################################################################
# Register
XML.set_namespace('http://xml.itools.org/namespaces/stl', Namespace)
