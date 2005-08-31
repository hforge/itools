# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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



class Mailto(object):

    scheme = 'mailto'

    def __init__(self, username, host):
        self.username = username
        self.host = host


    def __str__(self):
        return 'mailto:%s@%s' % (self.username, self.host)



def decode(data):
    if '@' not in data:
        # It is normal to use mailto references like 'toto AT example DOT com'
        # to trick robots. In this case we just return the given string.
        return data

    username, host = data.split('@', 1)
    return Mailto(username, host)
