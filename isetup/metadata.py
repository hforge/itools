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

# Import from the Standard Library
from os.path import join
from rfc822 import Message

# Import from itools
from itools.datatypes import String, LanguageTag, Tokens
from itools.handlers import ConfigFile, TextFile, register_handler_class
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


class RFC822File(TextFile):
    """ holds a rfc822 Message """

    attrs = {}
    message = None

    list_types = (type([]), type(()))
    str_types = (type(''),)


    def new(self, **kw):
        if 'attrs' in kw.keys():
            self.set_attrs(kw['attrs'])


    def _load_state_from_file(self, file):
        self.attrs = {}
        self.message = Message(file)
        for k in self.message.keys():
            if self.schema is None or self.schema.has_key(k):
                if len(self.message.getheaders(k)) == 1:
                    self.attrs[k] = self.message.getheader(k)
                else:
                    self.attrs[k] = self.message.getheaders(k)


    def to_str(self):
        data = ''
        list_types = (type([]), type(()))
        str_types = (type(''),)
        for key, val in self.attrs.items():
            if type(val) in str_types:
                data += '%s: %s\n' % (key, val)
            elif type(val) in list_types:
                # a new line for each item of the list
                for v in val:
                    data += '%s: %s\n' % (key, v)

        return data


    #######################################################################
    # API
    #######################################################################
    def set_attrs(self, attrs):
        # Check types of values
        type_error_msg = 'One of the given values is not compatible'
        for key, val in attrs.items():
            if self.schema is None or self.schema.has_key(key):
                if type(val) in self.str_types:
                    continue
                elif type(val) in self.list_types:
                    for v in val:
                        if type(v) not in self.str_types:
                            raise TypeError, type_error_msg
            else:
                del attrs[key]

        # Now attrs is sure
        self.attrs = attrs
        self.set_changed()



class PKGINFOFile(RFC822File):

    class_mimetypes = ['text/x-egg-info']

    schema = {
        'metadata-version': String(default=''),
        'name': String(default=''),
        'version': String(default=''),
        'summary': String(default=''),
        'author-email': String(default=''),
        'license': String(default=''),
        'download-url': String(default=''),

        # Optional
        'description': String(default=''),
        'keywords': String(default=''),
        'home-page': String(default=''),
        'author': String(default=''),
        'platform': String(default=''),
        'supported-platform': String(default=''),
        'classifier': String(default=''),
        'requires': String(default=''),
        'provides': String(default=''),
        'obsoletes': String(default=''),
    }


register_handler_class(PKGINFOFile)


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
    if exists(join(package_dir, "version.txt")):
        attributes['version'] = open(join(package_dir, "version.txt")).read()
    else:
        attributes['version'] = get_package_version(attributes['name'])
    return attributes


def get_package_version(package_name):
    try:
        mod = __import__(package_name)
        if hasattr(mod, 'Version'):
            if hasattr(mod.Version, "__call__"):
                return mod.Version()
            return mod.Version
        elif hasattr(mod, '__version__'):
            if hasattr(mod.__version__, "__call__"):
                return mod.__version__()
            return mod.__version__
        elif hasattr(mod, 'version'):
            if hasattr(mod.version, "__call__"):
                return mod.version()
            return mod.version
        else:
            return '?'
    except ImportError:
        return '?'


