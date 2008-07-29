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
from itools.uri import get_reference, Path
from itools.vfs import open, exists, is_file, is_folder, make_file, WRITE
from itools.html import HTMLParser
from itools.xml import START_ELEMENT
import itools.http

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

    # Auto-guess extension
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

class RepositoryNotSupported(Exception):
    """like a git repository"""


def Repository(location):
    """Return a repository object depending on the location
    """
    ref = get_reference(location)
    if ref.scheme == 'http':
        return HTMLRepository(location)
    else:
        raise RepositoryNotSupported, ("%s is not a supported repository" %
                ref.sheme)


def download(url, to):
    """download an url to to, if to is s a directory the file will be
    named by the path.get_name() of the url, or index.html if unknown.
    """
    url_handle = open(url)
    size = url_handle.headers['Content-Length']

    to_ref = get_reference(to)
    url_ref = get_reference(url)
    if exists(to) and is_folder(to):
        if url_ref.path.get_name() != '':
            to = str(to_ref.resolve2(url_ref.path.get_name()))
        else:
            to = str(to_ref.resolve2('index.html'))
        if exists(to):
            # If the file have been downloaded just return its name
            return to
    elif exists(to) and is_file(to):
        # If the file have been downloaded just return its name
        return to

    make_file(to)
    out_handle = open(to, WRITE)
    out_handle.write(url_handle.read())
    out_handle.close()
    return to


def is_distable(url):
    url = Path(url)
    for ext in EXTENSIONS:
        if url.get_name().split('#')[0].endswith(ext):
            return True
    return False


class HTMLRepository(object):

    def __init__(self, location):
        self.dists = {}
        self.location = location
        self.ref = get_reference(location)


    def _init_distributions_list(self, package_name):
        if not self.dists.has_key(package_name):
            package_url = str(self.ref.resolve2(package_name))

            self.dists[package_name] = []
            for package in self._find_distibutions(package_url):
                package_infos = parse_package_name(Path(package).get_name())
                package_infos['url'] = package
                self.dists[package_name].append(package_infos)


    def list_distributions(self, package_name):
        """return a list of available distributions
        """
        self._init_distributions_list(package_name)

        return self.dists[package_name]


    def download(self, package_name, version, to):
        self._init_distributions_list(package_name)
        for dist in self.dists[package_name]:
            if dist['version'] == version:
                url = dist['url']
                return download(url, to)


    def _find_distibutions(self, package_url):
        """On a web page finds link with href to something looking like a
        package name -TODO:, or follow the externals links-.
        """

        index_handler = open(package_url)
        index_data = index_handler.read()
        index_handler.close()

        for type, value, line in HTMLParser(index_data):
            if type == START_ELEMENT and value[1] == 'a':
                href = value[2][(None, 'href')]
                if is_distable(href):
                    # be sure the link is always absolute
                    if href.startswith('http'):
                        yield href.split('#')[0]
                    else:
                        dl_url = get_reference(package_url).resolve2(href)
                        yield str(dl_url).split('#')[0]

