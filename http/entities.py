# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from itools
from itools.handlers.File import File
import headers


def parse_header(line):
    if line:
        name, value = line.split(':', 1)
        name = name.strip().lower()
        value = value.strip()
        type = headers.get_type(name)
        return name, type.decode(value)

    return None, None



def parse_header(line):
    if line:
        name, value = line.split(':', 1)
        name = name.strip().lower()
        value = value.strip()
        type = headers.get_type(name)
        return name, type.decode(value)

    return None, None



def read_headers(file):
    entity_headers = {}
    # Setup
    line = file.readline()
    line = line.strip()
    # Go
    while line:
        name, value = parse_header(line)
        entity_headers[name] = value
        # Next
        line = file.readline()
        line = line.strip()

    return entity_headers



class Entity(File):

    __slots__ = ['uri', 'timestamp', 'parent', 'name', 'real_handler',
                 'headers', 'body']


    def _load_state_from_file(self, file):
        self.headers = read_headers(file)
        body = file.read()
        if body.endswith('\r\n'):
            self.body = body[:-2]
        elif body.endswith('\n'):
            self.body = body[:-1]
        else:
            self.body = body


    def has_header(self, name):
        name = name.lower()
        return name in self.headers


    def get_header(self, name):
        name = name.lower()
        return self.headers[name]


    def get_body(self):
        return self.body
