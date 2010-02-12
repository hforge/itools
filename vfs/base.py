# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2009 David Versmisse <david.versmisse@itaapy.com>
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>

# Import from itools
from itools.core import guess_type
from filename import FileName


######################################################################
# Constants
######################################################################
READ = 'r'
WRITE = 'w'
READ_WRITE = 'rw'
APPEND = 'a'


######################################################################
# Public API
######################################################################
def get_mimetype(name):
    """Try to guess the mimetype given the name. To guess from the name we
    need to extract the type extension, we use an heuristic for this task,
    but it needs to be improved because there are many patterns:

    <name>                                 README
    <name>.<type>                          index.html
    <name>.<type>.<language>               index.html.en
    <name>.<type>.<language>.<encoding>    index.html.en.UTF-8
    <name>.<type>.<compression>            itools.tar.gz
    etc...

    And even more complex, the name could contain dots, or the filename
    could start by a dot (a hidden file in Unix systems).
    """
    name, extension, language = FileName.decode(name)
    # Figure out the mimetype from the filename extension
    if extension is not None:
        mimetype, encoding = guess_type('%s.%s' % (name, extension))
        # FIXME Compression schemes are not mimetypes, see /etc/mime.types
        if encoding == 'gzip':
            if mimetype == 'application/x-tar':
                return 'application/x-tgz'
            return 'application/x-gzip'
        elif encoding == 'bzip2':
            if mimetype == 'application/x-tar':
                return 'application/x-tbz2'
            return 'application/x-bzip2'
        elif mimetype is not None:
            return mimetype

    return 'application/octet-stream'
