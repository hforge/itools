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
from itools.uri import Path
from itools.handlers import get_handler, File
from context import HTTPContext



class HTTPMount(object):

    context_class = HTTPContext


    def get_context(self, soup_message, path):
        context = self.context_class(soup_message, path)
        context.mount = self
        return context


    def handle_request(self, context):
        raise NotImplementedError



class StaticMount(HTTPMount):

    def __init__(self, prefix, path):
        self.prefix = Path(prefix)
        self.path = path


    def handle_request(self, context):
        # Load the handler
        n = len(self.prefix)
        path = '%s/%s' % (self.path, context.path[n:])
        try:
            handler = get_handler(path)
        except LookupError:
            return context.set_response(404)

        # Check it is a file
        if not isinstance(handler, File):
            return context.set_response(404)

        # Modification time
        mtime = handler.get_mtime()
        since = context.get_header('If-Modified-Since')
        if since and since >= mtime:
            return context.set_status(304)

        # Ok
        context.set_header('Last-Modified', mtime)
        mimetype = handler.get_mimetype()
        context.set_status(200)
        context.set_body(mimetype, handler.to_str())

