# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2007 Sylvain Taverne <sylvain@itaapy.com>
# Copyright (C) 2007-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008 Romain Gauthier <romain.gauthier@itaapy.com>
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
from itools.xml import XMLNamespace, register_namespace
from itools.xml import ElementSchema


# TODO
# Theses class are only used by ODT (for the moment)
# For the future, we can move this class to the xml package for example

###########################################################################
# Namespace URIs
###########################################################################
xlink_uri = 'http://www.w3.org/1999/xlink'
mathml_uri = 'http://www.w3.org/1998/Math/MathML'
dom_uri = 'http://www.w3.org/2001/xml-events'
xforms_uri = 'http://www.w3.org/2002/xforms'
xsd_uri = 'http://www.w3.org/2001/XMLSchema'
xsi_uri = 'http://www.w3.org/2001/XMLSchema-instance'



class Element(ElementSchema):

    # Default
    is_empty = False
    is_inline = True

    def __init__(self, name, attributes, **kw):
        ElementSchema.__init__(self, name, **kw)
        self.attributes = frozenset(attributes)



class BlockElement(Element):

    is_inline = False



mathml_elements = [
    BlockElement('math', [])]
xforms_elements = [
    BlockElement('model', [])]


xlink_namespace = XMLNamespace(xlink_uri, 'xlink', [])
mathml_namespace = XMLNamespace(mathml_uri, 'math', mathml_elements)
events_namespace = XMLNamespace(dom_uri, 'dom', [])
xforms_namespace = XMLNamespace(xforms_uri, 'xforms', xforms_elements)
xsd_namespace = XMLNamespace(xsd_uri, 'xsd', [])
xsi_namespace = XMLNamespace(xsi_uri, 'xsi', [])


###########################################################################
# Register
###########################################################################
for namespace in [xlink_namespace, mathml_namespace, events_namespace,
                  xforms_namespace, xsd_namespace, xsi_namespace]:
    register_namespace(namespace)
