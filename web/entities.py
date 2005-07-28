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
from itools.handlers.File import File
from itools.web import headers


def read_line(data):
    size = len(data)
    index = 0
    while index < size:
        byte = data[index]
        index += 1
        if byte == '\n':
            line = data[:index]
            line = line.strip()
            return line, data[index:]

    return data, ''
        


def read_headers(data):
    size = len(data)
    index = 0

    entity_headers = {}
    body = None

    # The headers
    while data:
        line, data = read_line(data)
        if line:
            name, value = line.split(':', 1)
            name = name.strip()
            type = headers.get_type(name)
            entity_headers[name] = type.decode(value)
        else:
            break

    return entity_headers, data



class Entity(File):

    def _load_state(self, resource):
        state = self.state

        data = resource.read()
        entity_headers, data = read_headers(data)
        state.headers = entity_headers
        state.body = data


    def has_header(self, name):
        return name in self.state.headers


    def get_header(self, name):
        return self.state.headers[name]


    def get_body(self):
        return self.state.body
