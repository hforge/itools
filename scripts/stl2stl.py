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

# Import from the Standard Library
from optparse import OptionParser
import sys

# Import from itools
import itools
from itools.datatypes import String
from itools.schemas import get_schema_by_uri
from itools.xml import Parser, START_ELEMENT, END_ELEMENT, TEXT, stream_to_str
import itools.stl


# Monkey patch STL
stl_uri = 'http://xml.itools.org/namespaces/stl'
schema = get_schema_by_uri(stl_uri)
schema.datatypes['content'] = String
schema.datatypes['attributes'] = String



def _stl2stl(stream):
    skip = 0
    omit = []
    changed = False
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
                changed = True
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
                changed = True
                stl_content = "${%s}" % attributes.pop(key)
            else:
                stl_content = None
            # stl:block, stl:inline
            if tag_uri == stl_uri:
                if bool(attributes):
                    omit.append(False)
                    yield type, (tag_uri, tag_name, attributes), line
                else:
                    omit.append(True)
            else:
                yield type, (tag_uri, tag_name, attributes), line
            if stl_content is not None:
                yield TEXT, stl_content, line
                skip = 1
        elif type == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_uri == stl_uri:
                if omit.pop() is False:
                    yield event
            else:
                yield event
        elif type == TEXT:
            # Escape entity references
            value = value.replace('\xa3', '&#163;')
            value = value.replace('\xc2\xa0', '&nbsp;')
            value = value.replace('\xc2\xa3', "&#163;")
            value = value.replace('\xc2\xa9', '&#169;')
            value = value.replace('\xc2\xbb', '&raquo;')
            value = value.replace('\xe2\x80\x93', '-') # XXX
            value = value.replace('\xe2\x80\x98', "'") # XXX
            value = value.replace('\xe2\x80\x99', "'") # XXX
            value = value.replace('\xe2\x80\x99', "'") # XXX
            value = value.replace('\xe2\x80\xa2', "&#8226;")
            value = value.replace('\xe2\x80\xba', '&rsaquo;')
            yield type, value, line
        else:
            yield event

    if changed is False:
        raise AssertionError, 'nothing to do'

 

if __name__ == '__main__':
    usage = '%prog FILENAME [FILENAME...]'
    version = 'itools %s' % itools.__version__
    parser = OptionParser(usage, version=version)

    options, args = parser.parse_args()
    if len(args) < 1:
        parser.error('incorrect number of arguments')

    for filename in args:
        print '>>>', filename
        data = open(filename).read()
        parser = Parser(data)
        new_stl = _stl2stl(parser)
        try:
            new_stl = list(new_stl)
        except AssertionError:
            pass
        else:
            new_stl = stream_to_str(new_stl)
            open(filename, 'w').write(new_stl)
