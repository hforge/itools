# -*- coding: UTF-8 -*-
# Copyright (C) 2002-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from os.path import join

# Import from itools
from itools.datatypes import String, LanguageTag, Tokens
from itools.handlers import ConfigFile
from itools.vfs import exists, is_folder


class SetupFile(ConfigFile):
    """abstract a setup.conf file
    """

    schema = {
        'name': String(default=''),
        'title': String(default=''),
        'url': String(default=''),
        'author_name': String(default=''),
        'author_email': String(default=''),
        'license': String(default=''),
        'description': String(default=''),
        'packages': Tokens(default=()),
        'requires': Tokens(default=()),
        'provides': Tokens(default=()),
        'scripts': Tokens(default=''),
        'source_language': LanguageTag(default=('en', 'EN')),
        'target_languages': Tokens(default=(('en', 'EN'),))
    }


# Note : some .egg-info are directories and not files
# XXX Implement it by subclassing itools.handlers.TextFile
def parse_pkginfo(data):
    """Return a dict containing information from PKG-INFO formated data
    like .egg-info files.

    >>> filename = '/usr/lib/python2.5/site-packages/pexpect-2.1.egg-info'
    >>> parse_pkginfo(open(filename).read())
    {'Author': 'Noah Spurrier', 'Author-email': 'noah@noah.org', ...}
    """
    attributes = {}
    last_line_key = None
    for line in data.splitlines():
        if ': ' in line:
            (key, val) = line.split(': ', 1)
            # Don't record useless attribute
            if val != 'UNKNOWN':
                # Comma separated string for lists
                if key in attributes.keys():
                    if hasattr(attributes[key], 'append'):
                        attributes[key].append(val)
                    else:
                        attributes[key] = [val]
                else:
                    attributes[key] = val
                last_line_key = key
        elif last_line_key is not None:
            attributes[last_line_key] += '\n'+line
    return attributes


def parse_setupconf(package_dir):
    """Return a dict containing information from setup.conf in a itools package
    plus the version of the package
    """
    attributes = {}
    if not is_folder(package_dir):
        return attributes
    if not exists(join(package_dir, "setup.conf")):
        return attributes
    config = SetupFile(join(package_dir, "setup.conf"))
    for attribute in config.schema:
        attributes[attribute] = config.get_value(attribute)
    attributes['version'] = get_package_version(attributes['name'])
    return attributes


def get_package_version(package_name):
    try:
        mod = __import__(package_name)
        if hasattr(mod, 'version'):
            if hasattr(mod.version, "__call__"):
                return mod.version()
            return mod.version
        elif hasattr(mod, '__version__'):
            if hasattr(mod.__version__, "__call__"):
                return mod.__version__()
            return mod.__version__
        else:
            return '?'
    except ImportError:
        return '?'


