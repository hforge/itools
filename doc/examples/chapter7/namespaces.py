# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from itools.xml import parser, namespaces
from itools import xhtml


data = '<html xmlns="http://www.w3.org/1999/xhtml">\n' \
       '  <head></head>\n' \
       '  <body>\n' \
       '    <a href="http://www.example.com" title="Example" />\n' \
       '  </body>\n' \
       '</html>'



for event, value, line_number in parser.parse(data):
    if event == parser.ATTRIBUTE:
        namespace_uri, prefix, local_name, value = value
        namespace = namespaces.get_namespace(namespace_uri)
        schema = namespace.get_attribute_schema(local_name)
        value = schema['type'].decode(value)
        print local_name, schema['type']
        print repr(value)
        print
