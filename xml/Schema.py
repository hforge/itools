# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


# Import from the Standard Library
import warnings

# Import from Python
from itools.handlers import IO
from itools.xml import XML, namespaces


############################################################################
# Simple Types
############################################################################
##class XML(object):
##    def encode(cls, value):
##        return value
##    encode = classmethod(encode)


##    def decode(cls, value):
##        value = value.strip()
##        return value
##    decode = classmethod(decode)


class SimpleType(XML.Element):

    def __init__(self, prefix, name, schema={}):
        XML.Element.__init__(self, prefix, name)
        self.schema = schema


    def set_comment(self, comment):
        raise ValueError


    def set_element(self, element):
        raise ValueError


    def set_text(self, text, encoding='UTF-8'):
        text = text.strip()
        type, default = self.schema[self.name]
        if type is IO.Unicode:
            self.value = type.decode(text, encoding)
        else:
            self.value = type.decode(text)


############################################################################
# Complex Types
############################################################################
class ComplexType(XML.Element):

    def __init__(self, prefix, name, schema={}):
        XML.Element.__init__(self, prefix, name)
        self.schema = schema

        self._properties = {}


    #########################################################################
    # XXX Obsolete code, to be removed for 0.9
    #########################################################################
##    def __init__(self, **kw):
##        schema = self.schema
##        for key, value in kw.items():
##            if key in schema:
##                self.set_property(key, value)


    def encode(self, encoding='UTF-8'):
        schema = self.schema
        lines = []

        property_names = schema.keys()
        property_names.sort()
        for name in property_names:
            type, default = schema[name]
            if name in self._properties:
                value = self._properties[name]
                if isinstance(value, dict):
                    # Multilingual
                    for language, value in value.items():
                        if issubclass(type, IO.Unicode):
                            value = type.encode(value, encoding)
                        elif issubclass(type, ComplexType):
                            value = type.encode(value, encoding)
                        else:
                            value = type.encode(value)
                        lines.append('<%s lang="%s">%s</%s>\n'
                                     % (name, language, value, name))
                else:
                    if isinstance(value, list):
                        values = value
                    else:
                        values = [value]
                    for value in values:
                        if issubclass(type, IO.Unicode):
                            value = type.encode(value, encoding)
                        elif issubclass(type, ComplexType):
                            value = type.encode(value, encoding)
                        else:
                            value = type.encode(value)

                        if issubclass(type, ComplexType):
                            lines.append('<%s>\n' % name)
                            for line in value.splitlines():
                                lines.append('  %s\n' % line)
                            lines.append('</%s>\n' % name)
                        else:
                            lines.append('<%s>%s</%s>\n' % (name, value, name))
        return ''.join(lines)


    def decode(cls, node):
        schema = cls.schema
        property = cls(None, None, schema)
        for node in node.get_elements():
            name = node.name
            # Decode the value
            if name in schema:
                type, default = schema[name]
                if issubclass(type, ComplexType):
                    value = type.decode(node)
                else:
                    value = XML.Children.encode(node.children)
                    value = value.encode('utf8')
                    try:
                        value = type.decode(value)
                    except ValueError:
                        # XXX Better to log it?
                        warnings.warn('Unable to decode "%s"' % name)
                # The language
                if node.has_attribute(None, 'lang'):
                    # XXX the lang attribute should be "xml:lang", the xml
                    # namespace should load it as an string. Then we would
                    # not need to coerce the value to str.
                    language = node.get_attribute(None, 'lang')
                    language = str(language)
                else:
                    language = None
                # Set property value
                property.set_property(name, value, language=language)
            else:
                # XXX Maybe better to log it
                warnings.warn('The schema does not define "%s"' % name)
        return property

    decode = classmethod(decode)


    #########################################################################
    # API
    #########################################################################
    def get_property(self, name):
        schema = self.schema
        if name not in schema:
            raise LookupError, 'schema does not define property "%s"' % name
        type, default = schema[name]
        return self._properties.get(name, default)


    def has_property(self, name):
        schema = self.schema
        if name not in schema:
            raise LookupError, 'schema does not define property "%s"' % name
        return name in self._properties


    def set_property(self, name, value, language=None):
        if language is None:
            type, default = self.schema[name]
            if isinstance(default, list):
                if isinstance(value, list):
                    self._properties[name] = value
                else:
                    values = self._properties.setdefault(name, [])
                    values.append(value)
            else:
                self._properties[name] = value
        else:
            values = self._properties.setdefault(name, {})
            values[language] = value


    #########################################################################
    # Parsing
    #########################################################################
    def set_text(self, text, encoding='UTF-8'):
        pass


    def set_comment(self, comment):
        pass


    def set_element(self, element):
        type, default = self.schema[element.name]
        if issubclass(type, ComplexType):
            # XXX
            pass
        else:
            try:
                value = getattr(element, 'value')
            except AttributeError:
                value = type.decode('')

        if element.has_attribute(namespaces.xml, 'lang'):
            language = element.get_attribute(namespaces.xml, 'lang')
            self.set_property(element.name, value, language=str(language))
        else:
            self.set_property(element.name, value)
