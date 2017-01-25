# -*- coding: UTF-8 -*-
# Copyright (C) 2011-2012 J. David Ibáñez <jdavid.ibp@gmail.com>
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
from datetime import datetime
from os.path import basename, getmtime, isfile

# Import from itools
from itools.core import fixed_offset
from itools.fs.common import get_mimetype
from itools.uri import Path
from router import BaseRouter, RequestMethod


class GET_STATIC(RequestMethod):

    @classmethod
    def handle_request(cls, context):
        n = len(Path(context.mount_path))
        path = Path(context.path)[n:]
        path = '%s%s' % (context.router.local_path, path)

        # 404 Not Found
        if not isfile(path):
            return context.set_default_response(404)

        # 304 Not Modified
        mtime = getmtime(path)
        mtime = datetime.utcfromtimestamp(mtime)
        mtime = mtime.replace(microsecond=0)
        mtime = fixed_offset(0).localize(mtime)
        since = context.get_header('If-Modified-Since')
        if since and since >= mtime:
            return context.set_default_response(304)

        # 200 Ok
        # FIXME Check we set the encoding for text files
        mimetype = get_mimetype(basename(path))
        # XXX Close file
        data = open(path).read()
        # Response
        context.set_content_type(mimetype)
        context.set_header('Last-Modified', mtime)
        context.status = 200
        context.entity = data
        context.set_response_from_context()



class StaticRouter(BaseRouter):

    methods = {'GET': GET_STATIC}
