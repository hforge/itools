# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008 Gautier Hayoun <gautier.hayoun@itaapy.com>
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
from itools.html import HTMLParser
import itools.http
from itools.uri import get_reference, Path
from itools import vfs
from itools.vfs import exists, is_file, is_folder, make_file, WRITE
from itools.vfs import get_mimetype
from itools.xml import START_ELEMENT


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


def get_repository(location):
    """Return a repository object depending on the location
    """
    ref = get_reference(location)
    mimetype = get_mimetype(ref)
    if mimetype == 'text/html':
        return HTMLRepository(ref)

    raise ValueError, '"%s" is not a valid repository' % location


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


def parse_repository(package_url):
    """On a web page finds link with href to something looking like a
    package name -TODO:, or follow the externals links-.
    """

    index_data = vfs.open(package_url).read()

    for type, value, line in HTMLParser(index_data):
        if type == START_ELEMENT and value[1] == 'a':
            href = value[2][(None, 'href')]
            href = get_reference(href)

            if href.scheme == 'mailto':
                continue

            name = href.path.get_name()
            if not any([name.endswith(ext) for ext in EXTENSIONS]):
                continue

            # be sure the link is always absolute
            if href.scheme == 'http':
                yield href
            else:
                yield get_reference(package_url).resolve2(href)


class HTMLRepository(object):

    def __init__(self, location):
        self.dists = {}
        self.location = location


    def list_distributions(self, package_name):
        """return a list of available distributions
        """
        if package_name in self.dists:
            return self.dists[package_name]

        package_url = str(self.location.resolve2(package_name))
        self.dists[package_name] = []
        for package in parse_repository(package_url):
            package_infos = parse_package_name(package.path.get_name())
            package_infos['url'] = package
            self.dists[package_name].append(package_infos)

        return self.dists[package_name]


    def download(self, package_name, version, to):
        dists = self.list_distributions(package_name)
        for dist in dists:
            if dist['version'] == version:
                return download(dist['url'], to)

