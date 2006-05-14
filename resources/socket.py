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
        self.in_buffer = ''
        self.out_buffer = ''


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

        buffer = self.in_buffer
        buffer_size = len(buffer)
        # The buffer already has all the data we need
        if buffer_size >= size:
            self.in_buffer = buffer[size:]
            return buffer[:size]

        # Read (at least 512 bytes)
        data = buffer + self.socket.recv(max(512, size - n))

        #
        data_size = len(data)
        if data_size > size:
            self.in_buffer = data[size:]
            return data[:size]

        self.in_buffer = ''
        return data


    def write(self, data):
        data = self.out_buffer + data
        if len(data) >= 512:
            n_bytes_sent = self.socket.send(data)
            self.out_buffer = data[n_bytes_sent:]
        else:
            self.out_buffer = data


    def flush(self):
        if self.out_buffer:
            self.socket.sendall(self.out_buffer)
            self.out_buffer = ''


    def _close(self):
        self.flush()
        self.socket.close()
