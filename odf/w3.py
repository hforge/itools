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
from itools.xml import AbstractNamespace, set_namespace, XMLError


# TODO
# Theses class are only used by ODT (for the moment)
# For the future, we can move this class to the xml package for example


class XlinkNamespace(AbstractNamespace):

    class_uri = "http://www.w3.org/1999/xlink"
    class_prefix = 'xlink'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {}

        if name not in elements_schema:
            raise XMLError, 'unknown property "%s"' % name

        return elements_schema.get(name)



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



class EventsNamespace(AbstractNamespace):

    class_uri = "http://www.w3.org/2001/xml-events"
    class_prefix = 'dom'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {}

        if name not in elements_schema:
            raise XMLError, 'unknown property "%s"' % name

        return elements_schema.get(name)



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



class XsdNamespace(AbstractNamespace):

    class_uri = "http://www.w3.org/2001/XMLSchema"
    class_prefix = 'xsd'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {}
        if name not in elements_schema:
            raise XMLError, 'unknown property "%s"' % name



class XsiNamespace(AbstractNamespace):

    class_uri = "http://www.w3.org/2001/XMLSchema-instance"
    class_prefix = 'xsi'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {}
        if name not in elements_schema:
            raise XMLError, 'unknown property "%s"' % name



###########################################################################
# Register
###########################################################################
set_namespace(XlinkNamespace)
set_namespace(MathMlNamespace)
set_namespace(EventsNamespace)
set_namespace(XformsNamespace)
set_namespace(XsdNamespace)
set_namespace(XsiNamespace)
