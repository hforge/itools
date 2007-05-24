# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from itools.xml import Parser, START_ELEMENT, END_ELEMENT, TEXT, stream_to_str


stl_uri = 'http://xml.itools.org/namespaces/stl'

def _stl2stl(stream):
    skip = 0
    for event in stream:
        type, value, line = event
        # Skip (stl:content)
        if skip > 0:
            if type == START_ELEMENT:
                skip += 1
            elif type == END_ELEMENT:
                skip -= 1
        if skip > 0:
            continue

        if type == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            # stl:attributes
            key = (stl_uri, 'attributes')
            if key in attributes:
                stl_attributes = attributes.pop(key)
                for stl_attribute in stl_attributes.split(';'):
                    name, expr = stl_attribute.strip().split(' ', 1)
                    if expr.startswith('not') and expr[3].isspace():
                        raise NotImplementedError
                    else:
                        expr = "${%s}" % expr
                    attributes[(tag_uri, name)] = expr
            # stl:content (TODO)
            key = (stl_uri, 'content')
            if key in attributes:
                stl_content = "${%s}" % attributes.pop(key)
            else:
                stl_content = None
            # Yield 
            yield type, (tag_uri, tag_name, attributes), line
            if stl_content is not None:
                yield TEXT, stl_content, line
                skip = 1
        else:
            yield event


def stl2stl(filename):
    data = open(filename).read()
    parser = Parser(data)
    new_stl = _stl2stl(parser)
    return list(new_stl)
 

if __name__ == '__main__':
    filename = 'template.xhtml.en'
    new_stl = stl2stl(filename)
    import itools.stl
    print stream_to_str(new_stl)
