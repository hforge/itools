# -*- coding: UTF-8 -*-
# Copyright (C) 2008-2009, 2011 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2009 David Versmisse <versmisse@lil.univ-littoral.fr>
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

# Import from the Standard Library
from types import GeneratorType

# Import from itools
from parser import XMLParser, TEXT, XML_DECL



def is_xml_stream(value):
    return type(value) in (list, GeneratorType, XMLParser)


def xml_to_text(stream):
    if type(stream) is str:
        stream = XMLParser(stream)

    encoding = 'utf-8'
    text = []
    for event, value, line in stream:
        # TODO Extract some attribute values
        if event == TEXT:
            text.append(value)
        elif event == XML_DECL:
            encoding = value[1]
    return unicode(' '.join(text), encoding)
