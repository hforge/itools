# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Gautier Hayoun <gautier.hayoun@itaapy.com>
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

# Import from itools
from itools import vfs
from itools.uri import get_reference, Path
from itools.vfs import exists, is_file, is_folder, make_file, WRITE


# List of supported extensions
EXTENSIONS = (".tar.gz", ".tgz", ".zip", ".tar.bz2")


def parse_package_name(package_name, extension=''):
    """
    (black magic powa)

    KNOWN BUG #1: does not handle Beaker-0.9-py2.5.egg well, understand -py2.5
    as if it where in in the version name

    >>> parse_package_name('Django-Is-Cool-0.99a2.tar.gz')
    {'file': 'Django-Is-Cool-0.99a2.tar.gz', 'name': 'Django-Is-Cool',\
    'version': '0.99a2', 'extension': '.tar.gz'}

    """
    parts = package_name.split('-')
    index = 0

    # Guess extension
    if extension == '':
        for ext in EXTENSIONS:
            if package_name.endswith(ext):
                extension = ext

    for part in parts:
        if '.' in part:
            maybe_version = part.split('.')
            if maybe_version[0].isdigit():
                return {'file': package_name,
                    'name': '-'.join(parts[:index]),
                    #part[:-len(extension)],
                    # BUG #1 here:
                    'version': '-'.join(parts[index:])[:-len(extension)],
                    'extension': extension}
        index += 1
    return {'file': package_name, 'name': '', 'version': '', 'extension': ''}


def download(url, to):
    """download an url to to, if to is s a directory the file will be
    named by the path.get_name() of the url, or index.html if unknown.
    """
    if isinstance(url, str):
        url = get_reference(url)

    if isinstance(to, str):
        to = get_reference(to)

    url_handle = vfs.open(url)
    size = url_handle.headers['Content-Length']

    if exists(to) and is_folder(to):
        if url.path.get_name() != '':
            to = to.resolve2(url.path.get_name())
        else:
            to = to.resolve2('index.html')
        if exists(to):
            # If the file have been downloaded just return its name
            return to
    elif exists(to) and is_file(to):
        # If the file have been downloaded just return its name
        return to

    make_file(to)
    vfs.open(to, WRITE).write(url_handle.read())
    return to

