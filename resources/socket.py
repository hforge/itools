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
import base



class File(base.File):

    def __init__(self, socket):
        self.socket = socket
        self.buffer = []


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
        buffer = self.buffer
        buffer_size = sum([ len(x) for x in buffer])
        remains = size - buffer_size
        while remains > 0:
            data = recv(remains)
            buffer.append(data)
            remains -= len(data)

        data = ''.join(buffer)
        self.buffer = [data[size:]]
        return data[:size]


    def readline(self):
        recv = self.socket.recv

        buffer = self.buffer
        line = []

        while True:
            if buffer:
                block = buffer.pop(0)
            else:
                block = recv(512)
                if block == '':
                    break

            i = block.find('\n')
            if i == -1:
                line.append(block)
            else:
                i = i + 1
                line.append(block[:i])
                remains = block[i:]
                if remains:
                    buffer.insert(0, remains)
                break

        return ''.join(line)
