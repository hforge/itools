# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from mimetypes import MimeTypes


mimetypes = MimeTypes()


def guess_type(filename):
    return mimetypes.guess_type(filename)


def add_type(mimetype, extension):
    mimetypes.add_type(mimetype, extension)


def guess_extension(mimetype):
    return mimetypes.guess_extension(mimetype)


def guess_all_extensions(mimetype):
    return mimetypes.guess_all_extensions(mimetype)


def has_extension(extension):
    filename = 'toto.%s' % extension
    mimetype, encoding = mimetypes.guess_type(filename)
    return mimetype is not None


def has_encoding(extension):
    extension = '.%s' % extension
    encodings_map = mimetypes.encodings_map
    return extension in encodings_map or extension.lower() in encodings_map
