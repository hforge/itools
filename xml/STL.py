# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


########################################################################
# Evaluate STL expressions
########################################################################

# STL exceptions
class STLSyntaxError(XML.XMLError):
    """ """


class STLNameError(NameError):
    """ """


# XXX Remove TCONTENT and TATTRIBUTES (it is a long time ago since we used
# it for the last time)

# Expressions tokens
TID, TSLASH, TOPEN, TCLOSE, TEOF, TCONTENT, TATTRIBUTES, TREPEAT = range(8)
token_name = ['id', 'slash', 'open parentheses', 'close parentheses',
              'end of expression', 'reserved word "content"',
              'reserver word "attributes"', 'reserved word "repeat"']


keywords = {'content': TCONTENT, 'attributes': TATTRIBUTES, 'repeat': TREPEAT}


class Expression(object):
    """
    Parses and evaluates stl expressions.
    
    Examples of allowed expressions:
    
      a
      a(content)
      a(attributes/alt)
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
    #   parser2 = TCONTENT parser3
    #             | TATTRIBUTES TSLASH TID parser3
    #             | TID parser3
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
        if token == TCONTENT:
            value = self.node.toxml()
            self.parameters = (value,)
            self.parser3()
            return
        elif token == TATTRIBUTES:
            token, lexeme = self.get_token()
            if token == TSLASH:
                token, lexeme = self.get_token()
                if token == TID:
                    attribute = self.node.attributes[lexeme]
                    self.parameters = (attribute.value,)
                    self.parser3()
                    return
        elif token == TID:
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
    # Semantic process.
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


###########################################################################
# Namespace
###########################################################################
def lookup(namespace, name):
    """
    Looks for a variable in a namespace (an instance, a mapping, etc..)
    """
    if hasattr(namespace, 'stl_lookup'):
        return namespace.stl_lookup(name)

    if isinstance(namespace, dict):
        if name in namespace:
            return namespace[name]

    try:
        value = getattr(namespace, name)
    except AttributeError:
        # XXX Maybe we shouldn't try this one
        try:
            value = namespace[name]
        except KeyError:
            raise STLNameError, 'name "%s" not found in the namespace' % name

    return value



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
class Attribute(XML.Attribute):
    namespace = 'http://xml.itools.org/namespaces/stl'


class RepeatAttr(Attribute):
    def __init__(self, prefix, name, value):
        Attribute.__init__(self, prefix, name, value)
        # Parse the expression
        name, expression = value.split(' ', 1)
        self.stl_name = name
        self.stl_expression = Expression(expression)


class IfAttr(Attribute):
    def __init__(self, prefix, name, value):
        Attribute.__init__(self, prefix, name, value)
        # Parse the expression
        self.stl_expression = Expression(value)


class IfnotAttr(Attribute):
    def __init__(self, prefix, name, value):
        Attribute.__init__(self, prefix, name, value)
        # Parse the expression
        self.stl_expression = Expression(value)


class AttributesAttr(Attribute):
    def __init__(self, prefix, name, value):
        Attribute.__init__(self, prefix, name, value)
        # Parse the expression
        attributes = []
        for x in value.split(';'):
            x = x.strip().split(' ')
            if len(x) != 2:
                raise STLSyntaxError, \
                      'attributes expression expects two fields'
            name, expr = x
            attributes.append((name, Expression(expr)))

        self.stl_attributes = tuple(attributes)


class ContentAttr(Attribute):
    def __init__(self, prefix, name, value):
        Attribute.__init__(self, prefix, name, value)
        # Parse the expression
        self.stl_expression = Expression(value)



########################################################################
# The namespace handler
class STL(object):
    """The stl namespace handler. It is an aspect."""

    def __call__(self, namespace={}):
        # XXX Rewrite with walk.

        # Initialize the namespace stack
        stack = NamespaceStack()
        stack.append(namespace)
        # Initialize the repeat stack (keeps repeat/index, repeat/odd, etc...)
        repeat = NamespaceStack()
        # Get the document
        document = self.handler
        # Process the children
        s = u''
        for child in document.children:
            if isinstance(child, XML.Element):
                s += self.process(child, stack, repeat)
            else:
                s += unicode(child)
        return s


    def process(self, node, stack, repeat_stack):
        # Raw nodes
        if isinstance(node, (XML.Raw, XML.Comment)):
            return unicode(node)

        # Element nodes
        attrs = node.attributes
        stl_uri = 'http://xml.itools.org/namespaces/stl'
        stl_attrs = attrs.namespaces.get(stl_uri, {})

        s = u''
        # Process stl:repeat
        if 'repeat' in stl_attrs:
            repeat = stl_attrs['repeat']
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
                s += self.process1(node, newstack, newrepeat)

                # Increment counter
                i = i + 1

            return s

        return s + self.process1(node, stack, repeat_stack)


    def process1(self, node, stack, repeat):
        """
        Process stl:if, stl:ifnot, stl:attributes and stl:content.
        """
        attrs = node.attributes
        stl_uri = 'http://xml.itools.org/namespaces/stl'
        stl_attrs = attrs.namespaces.get(stl_uri, {})

        # Remove the element if the given expression evaluates to false
        if 'if' in stl_attrs:
            expression = stl_attrs['if'].stl_expression
            if not expression.evaluate(stack, repeat):
                return u''

        # Remove the element if the given expression evaluates to true
        if 'ifnot' in stl_attrs:
            expression = stl_attrs['ifnot'].stl_expression
            if expression.evaluate(stack, repeat):
                return u''

        # Print tag name
        head = u'<' + node.qname

        # Process attributes
        changed_attributes = {} # qname: value
        # Evaluate stl:attributes
        if 'attributes' in stl_attrs:
            for name, expression in stl_attrs['attributes'].stl_attributes:
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
        for attribute in node.attributes:
            # Ommit stl attributes
            if attribute.prefix == 'stl':
                continue
            # Get the attribute value
            qname = attribute.qname
            if qname in changed_attributes:
                value = changed_attributes.pop(qname)
            else:
                value = attribute.value
            # Output only values different than None
            if value is not None:
                head += ' %s="%s"' % (qname, value)

        # Output remaining attributes
        for qname, value in changed_attributes.items():
            if value is not None:
                head += ' %s="%s"' % (qname, value)

        # Close the open tag
        head += '>'

        # Process the content
        if 'content' in stl_attrs:
            expression = stl_attrs['content'].stl_expression
            content = expression.evaluate(stack, repeat)
            # Coerce
            if isinstance(content, int):
                content = str(content)
        else:
            content = ''
            for child in node.children:
                content += self.process(child, stack, repeat)

        # Remove the element but preserves its children if it is a stl:block
        # or a stl:inline
        if isinstance(node, Element):
            return content

        foot = '</%s>' % node.qname
        return head + content + foot



########################################################################
# Interface for the XML parser, factories
class NSHandler(object):
    def namespace_handler(self, document):
        if not hasattr(document, 'stl'):
            aspect = STL()
            aspect.handler = document
            document.stl = aspect


    def get_element(self, prefix, name):
        """Element factory, returns the right element instance."""
        if name in ('block', 'inline'):
            return Element(prefix, name)

        raise STLSyntaxError, 'unexpected element name: %s' % name


    def get_attribute(self, prefix, name, value):
        """Attribute factory, returns the right attribute instance."""
        # XXX Kept for backwards compatibility, to be removed
        if name == 'i18n':
            return XML.Attribute(prefix, name, value)

        attributes = {'repeat': RepeatAttr, 'if': IfAttr, 'ifnot': IfnotAttr,
                      'attributes': AttributesAttr, 'content': ContentAttr}
        attribute = attributes.get(name)
        if attribute is None:
            raise STLSyntaxError, 'unexpected attribute name: %s' % name
        return attribute(prefix, name, value)


########################################################################
# Register
XML.registry.set_namespace('http://xml.itools.org/namespaces/stl', NSHandler())
