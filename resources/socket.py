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
import base



class File(base.File):

    def __init__(self, socket):
        self.socket = socket


    def get_mtime(self):
        return None


    def open(self):
        pass


    def close(self):
        pass


    def read(self, size):
        """The 'size' parameter is mandatory in sockets."""
        # For some reason 'socket.recv' may not return all the data
        # in a single call, even in blocking mode.
        recv = self.socket.recv
        data = []
        while size:
            data.append(recv(size))
            size -= len(data[-1])
        return ''.join(data)


    def readline(self):
        recv = self.socket.recv

        data = []
        while True:
            byte = recv(1)
            if byte:
                data.append(byte)
                if byte == '\n':
                    break
            else:
                break

        return ''.join(data)
