# -*- coding: UTF-8 -*-
# Copyright (C) 2011 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from itools.handlers import RODatabase, File
from itools.http import set_response
from itools.uri import Path
from context import Context


database = RODatabase()


class StaticContext(Context):

    def http_get(self):
        n = len(Path(self.mount_path))
        path = Path(self.path)[n:]
        path = '%s%s' % (self.local_path, path)
        # Load the handler
        try:
            handler = database.get_handler(path)
        except LookupError:
            return set_response(self.soup_message, 404)

        # Check it is a file
        if not isinstance(handler, File):
            return set_response(self.soup_message, 404)

        # Modification time
        mtime = handler.get_mtime()
        since = self.get_header('If-Modified-Since')
        if since and since >= mtime:
            return set_response(self.soup_message, 304)

        # FIXME Check we set the encoding for text files
        mimetype = handler.get_mimetype()
        self.soup_message.set_status(200)
        self.soup_message.set_response(mimetype, handler.to_str())
        self.set_header('Last-Modified', mtime)
