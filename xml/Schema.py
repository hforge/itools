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
from itools.datatypes import Unicode
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
        if type is Unicode:
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


##    #########################################################################
##    # XXX Obsolete code, to be removed for 0.9
##    #########################################################################
##    def __init__(self, **kw):
##        schema = self.schema
##        for key, value in kw.items():
##            if key in schema:
##                self.set_property(key, value)



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
