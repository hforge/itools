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
from itools.xml import XMLNamespace, register_namespace, XMLError


# TODO
# Theses class are only used by ODT (for the moment)
# For the future, we can move this class to the xml package for example


class XlinkNamespace(XMLNamespace):

    uri = "http://www.w3.org/1999/xlink"
    prefix = 'xlink'


class MathMlNamespace(XMLNamespace):

    uri = "http://www.w3.org/1998/Math/MathML"
    prefix = 'math'

    elements_schema = {
        'math': {'is_inline': False, 'is_empty': False}
    }


class EventsNamespace(XMLNamespace):

    uri = "http://www.w3.org/2001/xml-events"
    prefix = 'dom'


class XformsNamespace(XMLNamespace):

    uri = "http://www.w3.org/2002/xforms"
    prefix = 'xforms'

    elements_schema = {
        'model': {'is_inline': False, 'is_empty': False}
    }


class XsdNamespace(XMLNamespace):

    uri = "http://www.w3.org/2001/XMLSchema"
    prefix = 'xsd'


class XsiNamespace(XMLNamespace):

    uri = "http://www.w3.org/2001/XMLSchema-instance"
    prefix = 'xsi'


###########################################################################
# Register
###########################################################################
for namespace in [XlinkNamespace, MathMlNamespace, EventsNamespace,
                  XformsNamespace, XsdNamespace, XsiNamespace]:
    register_namespace(namespace)
