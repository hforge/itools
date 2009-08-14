# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from server import HTTPServer


class Ping(object):

    def handle_request(self, context):
        if context.method not in ['GET', 'HEAD']:
            return context.set_response(405)

        context.set_status(200)
        context.set_body('text/plain', str(context.path))



if __name__ == '__main__':
    server = HTTPServer()
    server.mount('/', Ping())
    server.start()

