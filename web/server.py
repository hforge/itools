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
from itools.http import set_response
from itools.i18n import init_language_selector
from itools.log import log_error, log_warning, register_logger
from context import Context, set_context, del_context, select_language
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


    #######################################################################
    # Stage 0: Initialize the context
    #######################################################################
    def init_context(self, context):
        # (1) Initialize the response status to None, it will be changed
        # through the request handling process.
        context.status = None

        # (2) The server, the data root and the authenticated user
        context.server = self
        context.root = self.root

        # (3) The authenticated user
        context.authenticate()

        # (4) The Site Root
        self.find_site_root(context)
        context.site_root.before_traverse(context)  # Hook

        # (5) Keep the context
        set_context(context)


    def find_site_root(self, context):
        """This method may be overriden to support virtual hosting.
        """
        context.site_root = self.root


    ########################################################################
    # Request handling: main functions
    ########################################################################
    def listen(self, address, port):
        # Language negotiation
        init_language_selector(select_language)

        # Add handlers
        HTTPServer.listen(self, address, port)
        self.add_handler('/', self.path_callback)
        self.add_handler('*', self.star_callback)


    def path_callback(self, soup_message, path):
        # (1) If path is null => 400 Bad Request
        if path is None:
            log_warning('Unexpected HTTP path (null)', domain='itools.web')
            return set_response(soup_message, 400)

        # (2) Initialize the context
        # XXX This try/except can be removed if its body contains no bug
        # anymore
        try:
            context = Context(soup_message, path)
            self.init_context(context)
        except Exception:
            log_error('Internal error', domain='itools.web')
            return set_response(soup_message, 500)

        # (3) Get the method that will handle the request
        method_name = soup_message.get_method()
        method = getattr(context, 'http_%s' % method_name.lower(), None)
        # 501 Not Implemented
        if method is None:
            log_warning('Unexpected "%s" HTTP method' % method_name,
                        domain='itools.web')
            return set_response(soup_message, 501)

        # (4) Pass control to the method
        try:
            method(self)
        except Exception:
            log_error('Failed to handle request', domain='itools.web')
            set_response(soup_message, 500)
        finally:
            del_context()


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
