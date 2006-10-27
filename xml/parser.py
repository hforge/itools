# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from itools
from itools.xml._parser import Parser

XML_DECL, DOCUMENT_TYPE, START_ELEMENT, END_ELEMENT, TEXT, COMMENT, PI, CHAR_REF, ENTITY_REF, CDATA, NAMESPACE = range(11)


def parse(data):
    parser = Parser(data)
    while True:
        x = parser.get_token()
        if x is None:
            break

        token, value, line_no = x

        if token == START_ELEMENT:
            uri, name, attributes, namespaces = value
            # Namespaces
            for ns_uri in namespaces.values():
                yield NAMESPACE, ns_uri, line_no
            # Yield
            yield token, (uri, name, attributes), line_no
        else:
            # Yield
            yield token, value, line_no

