# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006-2007 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007-2008 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008 David Versmisse <david.versmisse@itaapy.com>
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

# Import from the Standard Library
from datetime import timedelta

# Import from itools
from itools.http import HTTPServer
from itools.i18n import init_language_selector
from itools.log import register_logger
from context import select_language
from context import WebLogger


class WebServer(HTTPServer):

    access_log = None
    event_log = None

    database = None
    auth_cookie_expires = timedelta(0)


    def __init__(self, root, access_log=None, event_log=None):
        super(WebServer, self).__init__(access_log)
        # The application's root
        self.root = root
        # Logging
        register_logger(WebLogger(log_file=event_log), 'itools.web')


    def listen(self, address, port):
        # Language negotiation
        init_language_selector(select_language)

        # Add handlers
        HTTPServer.listen(self, address, port)
        self.add_handler('*', self.star_callback)


    def set_context(self, path, context):
        context = context(server=self, root=self.root)
        self.add_handler(path, context.handle_request)
        return context


    def star_callback(self, soup_message, path):
        """This method is called for the special "*" request URI, which means
        the request concerns the server itself, and not any particular
        resource.

        Currently this feature is only supported for the OPTIONS request
        method:

          OPTIONS * HTTP/1.1
        """
        method = soup_message.get_method()
        if method != 'OPTIONS':
            soup_message.set_status(405)
            soup_message.set_header('Allow', 'OPTIONS')
            return

        # XXX Hardcoded
        known_methods = ['GET', 'HEAD', 'POST', 'OPTIONS', 'PUT', 'DELETE']
        soup_message.set_status(200)
        soup_message.set_header('Allow', ','.join(known_methods))
