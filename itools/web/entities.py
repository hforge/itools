# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2008, 2010-2011 J. David Ibáñez <jdavid.ibp@gmail.com>
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

from logging import getLogger

# Import from itools
from itools.handlers import File
from .headers import get_type

log = getLogger("itools.web")


def read_headers(file):
    entity_headers = {}
    # Setup
    line = file.readline().strip()
    while not line:
        line = file.readline().strip()
    # Go
    while line:
        name, value = line.split(':', 1)
        name = name.strip().lower()
        datatype = get_type(name)
        value = value.strip()
        try:
            value = datatype.decode(value)
        except Exception:
            log.warning("Failed to parse the '%s' header" % name, exc_info=True)
        else:
            entity_headers[name] = value
        # Next
        line = file.readline().strip()

    return entity_headers



class Entity(File):

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
