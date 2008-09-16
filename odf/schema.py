# -*- coding: UTF-8 -*-
# Copyright (C) 2008 David Versmisse <david.versmisse@itaapy.com>
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
from itools import get_abspath
from itools.relaxng import RelaxNGFile
from itools.xml import register_namespace


###########################################################################
# Metadata
###########################################################################
text_uri = 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'
inline_elements = [
    (text_uri, 'page-count'),
    (text_uri, 'page-number'),
    (text_uri, 'span'),
    (text_uri, 'line-break'),
    (text_uri, 's'),
    (text_uri, 'tab')]


###########################################################################
# Make the namespaces
###########################################################################

# Read the Relax NG schema
rng_file = RelaxNGFile(get_abspath('OpenDocument-strict-schema-v1.1.rng'))
namespaces = rng_file.get_namespaces()

# Apply the metadata
for uri, element_name in inline_elements:
    element = namespaces[uri].get_element_schema(element_name)
    element.is_inline = True

# Register the namespaces
for namespace in namespaces.itervalues():
    register_namespace(namespace)


