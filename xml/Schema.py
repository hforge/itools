# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


# Import from itools
import XML


xsd_uri = 'http://www.w3.org/2001/XMLSchema'


class SchemaError(XML.XMLError):
    pass



###########################################################################
# Schema classes (one per element: xsd:schema, xsd:element,
# xsd:complexType, ...)
###########################################################################

class Schema(XML.Element):

    #######################################################################
    # Parser
    #######################################################################
    def __init__(self, prefix, name):
        XML.Element.__init__(self, prefix, name)

        self.target_namespace = None
        # Keep a mapping <element name>: <type>
        self.elements = {}
        self.types = {}

    def handle_attribute(self, ns_uri, prefix, name, value):
        if ns_uri == xsd_uri:
            if name == 'targetNamespace':
                self.target_namespace = value
            else:
                raise SchemaError, 'unexpected attribute "%s"' % name
        else:
            XML.Element.handle_attribute(self, ns_uri, prefix, name, value)


    def handle_start_element(self, ns_uri, prefix, name):
        if ns_uri == xsd_uri:
            if name == 'element':
                return Element(prefix, name)
            elif name == 'complexType':
                return ComplexType(prefix, name)
            elif name == 'simpleType':
                return SimpleType(prefix, name)
            elif name == 'annotation':
                return Annotation(prefix, name)
            else:
                raise SchemaError, 'unexpected Definitions "%s"' % name
                
        return XML.Element(prefix, name)


    def handle_end_element(self, element):
##        XML.logger.debug('xsd:schema.handle_end_element(%s)', element)
        if isinstance(element, Element):
            self.elements[element.xsd_name] = element.xsd_type
            if element.xsd_content != None:
                ctype = type(str(element.xsd_name),(InstanceElementType,), {})
                ctype.xsd_schema = self
                self.types[element.xsd_name] = ctype
        elif isinstance(element, ComplexType):
            ctype = type(str(element.xsd_name), (InstanceComplexType,), {})
            ctype.xsd_schema = self
            ctype.xsd_content = element.xsd_content
            ctype.xsd_attributes = element.xsd_attributes
            self.types[element.xsd_name] = ctype
        elif isinstance(element, SimpleType):
            content = element.xsd_content
            if isinstance(content, Restriction):
                ctype = type(str(element.xsd_name), (InstanceRestriction,), {})
                #ctype.pattern = content.XXX
##            elif isinstance(content, List):
            #ctype.xsd_attributes = element.xsd_attributes#
            self.types[element.xsd_name] = ctype
        elif isinstance(element, Annotation):
            ctype = type(str(element.xsd_name), (InstanceAnnotationType,), {})
            ctype.xsd_content = element.xsd_content
            self.types[element.xsd_name] = ctype
        else:
            XML.Element.handle_end_element(self, element)
 

    #######################################################################
    # API
    #######################################################################
    def get_element(self, prefix, name): 
##        XML.logger.debug('Schema.Schema.get_element(%s)', name)
        if name in self.elements:
            element_type = self.elements[name]
            if isinstance(element_type, unicode):
                element_type = self.types[element_type]
                return element_type(prefix, name)
            else:
                element = InstanceElement(prefix, name)
                element.xsd_type = element_type
                return element

        raise SchemaError, 'unexpected element "%s"' % name


    def get_attribute(self, prefix, name, value):
        raise SchemaError, 'unexpected attribute "%s"' % name


class Annotation(XML.Element):
    def __init__(self, prefix, name):
        XML.Element.__init__(self, prefix, name)
        self.xsd_name = None
        self.xsd_content = None
        self.elements = {}
        self.types = {}


    def handle_attribute(self, ns_uri, prefix, name, value):
        if ns_uri == xsd_uri:
            if name == 'id':
                self.xsd_type = String #Normal value!
            else:
                raise SchemaError, 'unexpected attribute "%s"' % name
        else:
            XML.Element.handle_attribute(self, ns_uri, prefix, name, value)

    def handle_start_element(self, ns_uri, prefix, name):
        if ns_uri == xsd_uri:
            if name == 'documentation':
                return Documentation(prefix, name)
            if name == 'appinfo':
                return Appinfo(prefix, name)
            else:
                raise SchemaError, 'unexpected element "%s"' % name
        else:
            XML.Element.handle_attribute(self, ns_uri, prefix, name, value)


    def handle_end_element(self, element):
        if isinstance(element, Documentation):
            self.xsd_content = element
        if isinstance(element, Appinfo):
            self.xsd_content = element
        else:
            XML.Element.handle_end_element(self, element)


class Documentation(XML.Element):

    def handle_attribute(self, ns_uri, prefix, name, value):
        if ns_uri == xsd_uri:
            if name == 'source':
                self.xsd_name = Source
            else:
                raise SchemaError, 'unexpected attribute "%s"' % name
        else:
            XML.Element.handle_attribute(self, ns_uri, prefix, name, value)
            

class Appinfo(XML.Element):
    def handle_start_element(self, ns_uri, prefix, name):
        if ns_uri == xsd_uri:
            if name == 'source':
                self.xsd_name = Source
            else:
                raise SchemaError, 'unexpected attribute "%s"' % name
        else:
            XML.Element.handle_attribute(self, ns_uri, prefix, name, value)


class Element(XML.Element):
    def __init__(self, prefix, name):
        XML.Element.__init__(self, prefix, name)
        self.xsd_name = None
        self.xsd_type = None
        self.elements = {}
        self.types = {}
        self.xsd_content = None


    def handle_attribute(self, ns_uri, prefix, name, value):
        list_name = ['value', 'ref', 'use', 'base']
        if ns_uri == xsd_uri:
            if name == 'name':
                self.xsd_name = value
            elif name == 'type':
                if value in builtin_types:
                    self.xsd_type = builtin_types[value]
                else:
                    self.xsd_type = value
            elif name == 'maxOccurs' or name in 'minOccurs':
                if value in builtin_types:
                    self.xsd_type = builtin_types[value]
                elif value == 'unbounded':              
                    self.xsd_type = value
                else:
                   raise SchemaError, 'unexpected value "%s"' % value
            elif name in list_name:
                warnings.warn('"%s" not yet supported' % name)
            else:
                raise SchemaError, 'unexpected attribute "%s"' % name
        else:
            XML.Element.handle_attribute(self, ns_uri, prefix, name, value)


    def handle_start_element(self, ns_uri, prefix, name):
        if ns_uri == xsd_uri:
            if name == 'complexType':
                return ComplexType(prefix, name)
            else:
                raise SchemaError, 'unexpected element "%s"' % name
        else:
            XML.Element.handle_attribute(self, ns_uri, prefix, name, value)


    def handle_end_element(self, element):
        if isinstance(element, ComplexType):
            self.xsd_content = element
        else:
            XML.Element.handle_end_element(self, element)



class ComplexType(XML.Element):
    def __init__(self, prefix, name):
        XML.Element.__init__(self, prefix, name)
        self.xsd_name = None
        self.xsd_content = None
        self.elements = {}
        self.types = {}
        self.xsd_attributes = {}


    def handle_attribute(self, ns_uri, prefix, name, value):
##        XML.logger.debug('xsd:complexType.handle_attr(%s, %s)', name, value)
        if ns_uri == xsd_uri:
            if name == 'name':
                self.xsd_name = value
            elif name == 'abstract':
                self.xsd_type = Boolean #Normal value!
            elif name == 'id':
                self.xsd_type = String #Normal value!
            else:
                raise SchemaError, 'unexpected attribute "%s"' % name
        else:
            XML.Element.handle_attribute(self, ns_uri, prefix, name, value)


    def handle_start_element(self, ns_uri, prefix, name):
        if ns_uri == xsd_uri:
            if name == 'sequence':
                return Sequence(prefix, name)
            if name == 'attribute':
                return Attribute(prefix, name)
            else:
                raise SchemaError, 'unexpected element "%s"' % name
        else:
            XML.Element.handle_attribute(self, ns_uri, prefix, name, value)


    def handle_end_element(self, element):
##        XML.logger.debug('xsd:complexType.handle_end_element(%s)', element)
        if isinstance(element, Sequence):
            self.xsd_content = element
        elif isinstance(element, Attribute):
            name = element.xsd_name
            type = element.xsd_type
            use = element.xsd_use
            self.xsd_attributes[name] = (type, use)
            self.elements[element.xsd_name] = element.xsd_type###
        else:
            XML.Element.handle_end_element(self, element)


class Sequence(XML.Element):
    def __init__(self, prefix, name):
        XML.Element.__init__(self, prefix, name)
        # Keep a mapping <element name>: <type>
        self.elements = {}
        self.types = {}


    def handle_start_element(self, ns_uri, prefix, name):
        if ns_uri == xsd_uri:
            if name == 'element':
                return Element(prefix, name)
            else:
                raise SchemaError, 'unexpected element "%s"' % name
        else:
            XML.Element.handle_attribute(self, ns_uri, prefix, name, value)
 

    def handle_end_element(self, element):
       if isinstance(element, Element):
           self.elements[element.xsd_name] = element.xsd_type



class Attribute(XML.Element):
    def __init__(self, prefix, name):
        XML.Element.__init__(self, prefix, name)
        self.xsd_name = None
        self.xsd_type = None
        self.xsd_id = None
        self.xsd_use = u'optional'

    def handle_attribute(self, ns_uri, prefix, name, value):
        if ns_uri == xsd_uri:
            if name == 'name':
                self.xsd_name = value
            elif name == 'type':
                if value in builtin_types:
                    self.xsd_type = builtin_types[value]
                else:
                    self.xsd_type = value
            elif name == 'id':
                self.xsd_id = value
            elif name == 'use':
                if value not in [u'optional', u'prohibited', u'required']:
                    raise SchemaError, 'unexpected value "%s" for "use"' % value
                self.xsd_use = value
            else:
                raise SchemaError, 'unexpected attribute "%s"' % name
        else:
            XML.Element.handle_attribute(self, ns_uri, prefix, name, value)


    def handle_start_element(self, ns_uri, prefix, name):
        if ns_uri == xsd_uri:
            if name == 'attribute':
                pass
            raise SchemaError, 'unexpected element "%s"' % name
        XML.Element.handle_attribute(self, ns_uri, prefix, name, value)


    def handle_end_element(self, element):
        pass


class SimpleType(XML.Element):
    def __init__(self, prefix, name):
        XML.Element.__init__(self, prefix, name)
        self.xsd_type = None
        self.xsd_name = None
        self.xsd_content = None
        self.elements = {}
        self.types = {}
        #self.xsd_attributes = {}


    def handle_attribute(self, ns_uri, prefix, name, value):
        if ns_uri == xsd_uri:
            if name == 'name':
                self.xsd_name = value
            elif name == 'abstract':
                self.xsd_type = Boolean #Normal value!
            elif name == 'id':
                self.xsd_type = String #Normal value!
            else:
                raise SchemaError, 'unexpected attribute "%s"' % name
        else:
            XML.Element.handle_attribute(self, ns_uri, prefix, name, value)


    def handle_start_element(self, ns_uri, prefix, name):
        if ns_uri == xsd_uri:
            if name == 'restriction':
                return Restriction(prefix, name)
            else:
                raise SchemaError, 'unexpected element "%s"' % name
        else:
            XML.Element.handle_attribute(self, ns_uri, prefix, name, value)


    def handle_end_element(self, element):
        if isinstance(element, Restriction):
            self.xsd_content = element
##        elif isinstance(element, List):
##            self.xsd_content = element
##        elif isinstance(element, Union):
##            self.xsd_content = element
        else:
            XML.Element.handle_end_element(self, element)


class Restriction(XML.Element):
    def __init__(self, prefix, name):
        XML.Element.__init__(self, prefix, name)
        # Keep a mapping <element name>: <type>
        self.elements = {}
        self.types = {}


    def handle_start_element(self, ns_uri, prefix, name):
        if ns_uri == xsd_uri:
            if name == 'element':
                return Element(prefix, name)
            elif name == 'pattern':
                return Pattern(prefix, name)
            else:
                raise SchemaError, 'unexpected element "%s"' % name
        else:
            XML.Element.handle_attribute(self, ns_uri, prefix, name, value)


    def handle_end_element(self, element):
       if isinstance(element, Element):
           self.elements[element.xsd_name] = element.xsd_type
       if isinstance(element, Pattern):
           pass
           #self.elements[element.xsd_name] = element.xsd_type



class Pattern(XML.Element):
    def __init__(self, prefix, name):
        XML.Element.__init__(self, prefix, name)
        self.xsd_name = None


    def handle_attribute(self, ns_uri, prefix, name, value):
        if ns_uri == xsd_uri:
            if name == 'value':
                self.xsd_value = RegularExpression 
            else:
                raise SchemaError, 'unexpected attribute "%s"' % name
        else:
            XML.Element.handle_attribute(self, ns_uri, prefix, name, value)

#    def handle_start_element(self, ns_uri, prefix, name):
#        if ns_uri == xsd_uri:
#            raise SchemaError, 'unexpected element "%s"' % name
#        XML.Element.handle_attribute(self, ns_uri, prefix, name, value)
#
#    def handle_end_element(self, element):
#        pass


###########################################################################
# Instance classes
###########################################################################
class InstanceComplexType(XML.Element):
    def __init__(self, prefix, name):
        XML.Element.__init__(self, prefix, name)
        self.target_namespace = None
        self.attributesInstance = {}
        self.typesInstance = {}
    xsd_uri = "http://www.lisa.org/tmx"
    #xsd_uri = "http://www.itools.org/namespaces/simple"

    def handle_attribute(self, ns_uri, prefix, name, value):
##        XML.logger.debug('%s:%s.handle_attribute(%s)',
##                         self.xsd_uri, self.__class__.__name__, name)
        if ns_uri == self.xsd_uri:
            if name not in self.xsd_attributes:
                raise SchemaError, 'unexpected attribute "%s"' % name
            type, use = self.xsd_attributes[name]
            if isinstance(type, unicode):
                if name in self.xsd_attributes:
                     attribute = self.xsd_attributes[name]
                     if attribute[1] == 'required':
                         pass ### to do
                     self.typesInstance[attribute[0]] =\
                     self.xsd_schema.types[attribute[0]]
                     #type = self.xsd_schema.types[attribute[0]]
            #value = type.decode(value)
            #attribute = XML.Attribute(prefix, name, value)
            #self.attributes.add(attribute)
        else:
            XML.Element.handle_attribute(self, ns_uri, prefix, name, value)


    def handle_start_element(self, ns_uri, prefix, name):
##        XML.logger.debug('%s:%s.handle_start_element(%s)',
##                         self.xsd_uri, self.__class__.__name__, name)
        if ns_uri == self.xsd_uri:
            elements = self.xsd_content.elements
            types = self.xsd_schema.types
            if name in elements:
                element_type = elements[name]
                if isinstance(element_type, unicode):
                    element_type = types[element_type]
                    return element_type(prefix, name)###do nothing
                else:
                    element = InstanceElement(prefix, name)
                    element.xsd_type = element_type
                    return element
            raise SchemaError, 'unexpected element "%s"' % name
        else:
            return XML.Element(prefix, name)

##    def handle_end_element(self, element):
##        pass


class InstanceElementType(XML.Element):
    def handle_start_element(self, ns_uri, prefix, name):
        return Element(prefix, name)

class InstanceSequenceType(XML.Element):
    def handle_start_element(self, ns_uri, prefix, name):
        return Sequence(prefix, namei)

class InstanceSimpleType(XML.Element):
    def __init__(self, prefix, name):
        XML.Element.__init__(self, prefix, name)
        self.target_namespace = None
    xsd_uri = "http://www.lisa.org/tmx"

    def handle_attribute(self, ns_uri, prefix, name, value):
##        XML.logger.debug('%s:%s.handle_attribute(%s)',
##                         self.xsd_uri, self.__class__.__name__, name)
        if ns_uri == self.xsd_uri:
            if name not in self.xsd_attributes:
                raise SchemaError, 'unexpected attribute "%s"' % name
            type, use = self.xsd_attributes[name]
            value = type.decode(value)
            attribute = XML.Attribute(prefix, name, value)
            self.attributes.add(attribute)
        else:
            XML.Element.handle_attribute(self, ns_uri, prefix, name, value)


    def handle_start_element(self, ns_uri, prefix, name):
        return Sequence(prefix, name)

class InstanceAttributeType(XML.Element):
    def handle_start_element(self, ns_uri, prefix, name):
        return SimpleType(prefix, name)


class InstancePatternType(XML.Element):
    def handle_start_element(self, ns_uri, prefix, name):
        return Pattern(prefix, name)

class InstanceAnnotationType(XML.Element):
    def handle_start_element(self, ns_uri, prefix, name):
        return Pattern(prefix, name)


##########################################################################
# Built in Simple types
##########################################################################

class Name(str):
    def __init__(self, x):
        if type(x) != str:
            raise ValueError, 'Unexpected string value "%d3'%x
        str.__init__(self, x) 


class String(object):
    def decode(data):
        return data

    decode = staticmethod(decode)


    def encode(value):
        return value

    encode = staticmethod(encode)


class RegularExpression (XML.Element):
    value = None
   
    def handle_rawdata(self, data):
        # XXX Conditions???
        self.value = data

class Source(XML.Element):
    value = None
     
    def handle_rawdata(self, data):
        # XXX data must be an URI
        self.value = data

###########################################################################
# Class for numbers

class Float(XML.Element):
    value = None
    x = 2**-128
    y = 2**149
    def handle_rawdata(self, data):
        if (int(data) > x) or (int(data) < y):
        # XXX float corresponds to the IEEE single-precision 32-bit 
            raise ValueError, 'Unexpected float value "%d3'%x
        self.value = float(data)


class Double(XML.Element):
    value = None
    x = 2**-1023
    y = 2**1022
    def handle_rawdata(self, data):
        if int(data) > x or int(data) < y:
        # XXX The double datatype corresponds to IEEE double-precision 64-bit
            raise ValueError, 'Unexpected double value "%d3'%x
        self.value = float(data)



class Decimal(XML.Element):
    value = None

    def handle_rawdata(self, data):
        #XXX decimal represents arbitrary precision decimal numbers.
        if type(int(data)) != long:
            raise ValueError, 'Unexpected decimal value "%d3'%x
        self.value = int(data)
 


class Integer(object):
    def decode(cls, data):
        value = int(data)
        if cls.is_ok(value):
            return value
        raise SchemaError, 'unexepected value "%s"' % value

    decode = classmethod(decode)


    def encode(cls, value):
        return str(value)

    encode = classmethod(encode)


    def is_ok(cls, value):
        return True

    is_ok = classmethod(is_ok)


class InstanceElement(XML.Element):
    xsd_type = None

    def handle_rawdata(self, data):
        self.value = self.xsd_type.decode(data)


        
class NonPositiveInteger(Integer):
    def is_ok(cls, value):
        return value <= 0

    is_ok = classmethod(is_ok)


   
class NonNegativeInteger(XML.Element):
    value = None

    def handle_rawdata(self, data):
       if int(data) < 0:
          raise ValueError, 'Unexpected nonNegativeInteger value "%d3'%x
       self.value = int(data)

class UnsignedLong(XML.Element):
    value = None

    def handle_rawdata(self, data):
        if int(data) > 18446744073709551615 or int(data) < 0:
            raise ValueError, 'Unexpected unsignedLong value "%d3'%x
        self.value = int(data)


class UnsignedInt(XML.Element):
    value = None

    def handle_rawdata(self, data):
        if int(data) > 4294967295 or int(data) < 0:
            raise ValueError, 'Unexpected unsignedInt value "%d3'%x
        self.value = int(data)


class UnsignedShort(XML.Element):
    value = None

    def handle_rawdata(self, data):
        if int (data) > 65535  or int(data) < 0:
            raise ValueError, 'Unexpected UnsignedShort value "%d3'%x
        self.value = int(data)


class UnsignedByte(UnsignedShort):
    value = None

    def handle_rawdata(self, data):

        if int(data) > 255 or int(data) < 0:
            raise ValueError, 'Unexpected UnsignedByte² value "%d3'%x
        self.value = int(data)


class PositiveInteger(Integer):
    value = None

    def handle_rawdata(self, data):
        if x <= 0:
            raise ValueError, 'Unexpected PositiveInteger value "%d3' % x
        self.value = int(data)


class NegativeInteger(NonPositiveInteger):
    value = None

    def handle_rawdata(self, data):
        if x <= 0:
            raise ValueError, 'Unexpected NegativeValue value "%d3'%x
        self.value = int(data)

    
class Long(Integer):
    value = None

    def handle_rawdata(self, data):
        self.value = int(data)


class Int(Long):
    value = None

    def handle_rawdata(self, data):
        if type(int(data)) != int:
            raise ValueError, 'Unexpected int value "%d3'%x
        self.value = int(data)


class Short(Int):
    value = None

    def handle_rawdata(self, data):
        if (int(data) > 32767) or (int(data) < -32768):
            raise ValueError, 'Unexpected short value "%d3'%x
        self.value = int(data)


class Byte(Short):
    value = None

    def handle_rawdata(self, data):
        if (int(data) > 127) or (int(data) < -128):
            raise ValueError, 'Unexpected byte value "%d3'%x
        self.value = int(data)

###########################################################################
# Class for non base 10 numbers

class Boolean:
    value = None

    def handle_rawdata(self, data):
        if data not in ['True', 'False']:
            raise ValueError, 'Unexpected boolean value "%d3'%x
        if data == 'False':
            data = ''
        self.value = boll(data)
        

builtin_types = {'xsd:float': Float,
                 'xsd:double': Double,
                 'xsd:decimal': Decimal,
                 'xsd:integer': Integer,
                 'xsd:nonPositiveInteger': NonPositiveInteger,
                 'xsd:nonNegativeInteger': NonNegativeInteger,
                 'xsd:unsignedLong': UnsignedLong,
                 'xsd:unsignetInt': UnsignedInt,
                 'xsd:unsignedShort': UnsignedShort,
                 'xsd:unsignedByte': UnsignedByte,
                 'xsd:positiveInteger': PositiveInteger,
                 'xsd:negativeInteger': NegativeInteger,
                 'xsd:long': Long,
                 'xsd:int': int,
                 'xsd:short': Short,
                 'xsd:byte': Byte,
                 'xsd:boolean': Boolean,
                 'xsd:string': String}

########################################################################
# User defined simple types
########################################################################
class InstanceRestriction(Integer):
    def is_ok(cls, value):
        return value <= 0

    is_ok = classmethod(is_ok)


########################################################################
# Register the Schema XML Namespace handler
########################################################################
class NSHandler(object):
    def get_element(self, prefix, name):
        if name == 'schema':
            return Schema(prefix, name)
        elif name == 'complexType':
            return ComplexType(prefix, name)
        elif name == 'simpleType':
            return SimpleType(prefix, name)
        elif name == 'annotation':
            return Annotation(prefix, name)
        elif name == 'element':
            return Element(prefix, name)

        return XML.Element(prefix, name)
             

    def get_attribute(self, prefix, name, value):
        return XML.Attribute(prefix, name, value)

XML.registry.register(xsd_uri, NSHandler())
