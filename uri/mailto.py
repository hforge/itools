# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from registry import register_scheme


class Mailto(object):

    scheme = 'mailto'

    def __init__(self, username, host):
        self.username = username
        self.host = host


    def __str__(self):
        return 'mailto:%s@%s' % (self.username, self.host)



class MailtoDataType(object):

    @staticmethod
    def decode(data):
        if '@' not in data:
            # It is normal to use mailto references like 'toto AT example
            # DOT com' to trick robots. In this case we just return the
            # given string.
            return data

        username, host = data.split('@', 1)
        return Mailto(username, host)


register_scheme('mailto', MailtoDataType)
