# -*- coding: UTF-8 -*-
# Copyright (C) 2010 J. David Ibáñez <jdavid.ibp@gmail.com>
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
from itools.http import HTTPServer
from itools.loop import Loop

class Ping(HTTPServer):
    def listen(self, address, port):
        super(Ping, self).listen(address, port)
        self.add_handler('/', self.path_callback)

    def path_callback(self, soup_message, path):
        method = soup_message.get_method()
        body = '%s %s' % (method, path)
        soup_message.set_status(200)
        soup_message.set_response('text/plain', body)

server = Ping()
server.listen('localhost', 8080)

loop = Loop()
loop.run()
