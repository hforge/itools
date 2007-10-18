# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2007 Sylvain Taverne <sylvain@itaapy.com>
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from itools
from itools.xml import AbstractNamespace, set_namespace
from itools.schemas import Schema as BaseSchema, register_schema
from itools.xml.parser import XMLError


# TODO
# Theses class are only used by ODT (for the moment)
# For the future, we can move this class to the xml package for example

#############################################
######## http://www.w3.org/1999/xlink  ######
#############################################

class XlinkNamespace(AbstractNamespace):

    class_uri = "http://www.w3.org/1999/xlink"
    class_prefix = 'xlink'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {}

        if name not in elements_schema:
            raise XMLError, 'unknown property "%s"' % name

        return elements_schema.get(name)

set_namespace(XlinkNamespace)



class XlinkSchema(BaseSchema):

    class_uri = 'http://www.w3.org/1999/xlink'
    class_prefix = 'xlink'

register_schema(XlinkSchema)



#################################################
######## http://www.w3.org/1998/Math/MathML  ####
#################################################


class MathMlNamespace(AbstractNamespace):

    class_uri = "http://www.w3.org/1998/Math/MathML"
    class_prefix = 'math'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {
            'math': {'is_inline': False, 'is_empty': False}
        }

        if name not in elements_schema:
            raise XMLError, 'unknown property "%s"' % name

        return elements_schema.get(name)


set_namespace(MathMlNamespace)



class MathMlSchema(BaseSchema):

    class_uri = "http://www.w3.org/1998/Math/MathML"
    class_prefix = 'math'

register_schema(MathMlSchema)



##################################################
######## http://www.w3.org/2001/xml-events  ######
##################################################

class EventsNamespace(AbstractNamespace):

    class_uri = "http://www.w3.org/2001/xml-events"
    class_prefix = 'dom'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {}

        if name not in elements_schema:
            raise XMLError, 'unknown property "%s"' % name

        return elements_schema.get(name)

set_namespace(EventsNamespace)



class EventsSchema(BaseSchema):

    class_uri =  "http://www.w3.org/2001/xml-events"
    class_prefix = 'dom'

register_schema(EventsSchema)



##################################################
######## http://www.w3.org/2002/xforms  ##########
##################################################

class XformsNamespace(AbstractNamespace):

    class_uri = "http://www.w3.org/2002/xforms"
    class_prefix = 'xforms'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {
            'model': {'is_inline': False, 'is_empty': False}
        }
        if name not in elements_schema:
            raise XMLError, 'unknown property "%s"' % name

        return elements_schema.get(name)


set_namespace(XformsNamespace)



class XformsSchema(BaseSchema):

    class_uri =  "http://www.w3.org/2002/xforms"
    class_prefix = 'xforms'

register_schema(XformsSchema)



####################################################
######## http://www.w3.org/2001/XMLSchema ##########
####################################################

class XsdNamespace(AbstractNamespace):

    class_uri = "http://www.w3.org/2001/XMLSchema"
    class_prefix = 'xsd'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {}
        if name not in elements_schema:
            raise XMLError, 'unknown property "%s"' % name


set_namespace(XsdNamespace)



class XsdSchema(BaseSchema):

    class_uri =  "http://www.w3.org/2001/XMLSchema"
    class_prefix = 'xsd'

register_schema(XsdSchema)



#############################################################
######## http://www.w3.org/2001/XMLSchema-instance ##########
#############################################################

class XsiNamespace(AbstractNamespace):

    class_uri = "http://www.w3.org/2001/XMLSchema-instance"
    class_prefix = 'xsi'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {}
        if name not in elements_schema:
            raise XMLError, 'unknown property "%s"' % name

set_namespace(XsiNamespace)



class XsiSchema(BaseSchema):

    class_uri =  "http://www.w3.org/2001/XMLSchema-instance"
    class_prefix = 'xsi'

register_schema(XsiSchema)
