# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006 Nicolas Deram <nicolas@itaapy.com>
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
from registry import register_scheme


class Mailto(object):
    __slots__ = ['address']
    scheme = 'mailto'

    def __init__(self, address):
        self.address = address


    def get_username(self):
        if '@' in self.address:
            return self.address.split('@', 1)[0]
        return None
    username = property(get_username, None, None, "")


    def get_host(self):
        if '@' in self.address:
            return self.address.split('@', 1)[1]
        return None
    host = property(get_host, None, None, "")


    def __str__(self):
        return 'mailto:%s' % self.address


    def __eq__(self, other):
        return str(self) == str(other)



class MailtoDataType(object):

    @staticmethod
    def decode(data):
        # It is normal to use mailto references like 'toto AT example
        # DOT com' to trick robots. In this case we just return the
        # given string.
        return Mailto(data[7:])


    @staticmethod
    def encode(value):
        return 'mailto:%s' % value.address


register_scheme('mailto', MailtoDataType)
