# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008 Matthieu France <matthieu@itaapy.com>
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
from sys import _getframe

# Import from itools
from itools.handlers import RODatabase


# XXX This code does not take into account changes in the filesystem once a
# domain has been registered/loaded.


domains = {}

def register_domain(name, locale_path):
    if name not in domains:
        domains[name] = Domain(locale_path)


def get_domain(name):
    return domains[name]



database = RODatabase()

class Domain(dict):

    def __init__(self, uri):
        folder = database.get_handler(uri)
        for key in folder.get_handler_names():
            if key[-3:] == '.mo':
                language = key[:-3]
                self[language] = folder.get_handler(key)


    def gettext(self, message, language):
        if language not in self:
            return message
        handler = self[language]
        return handler.gettext(message)


    def get_languages(self):
        return self.keys()



class MSG(object):

    __slots__ = ['message', 'domain', 'kw']

    def __init__(self, message, domain=None, **kw):
        if domain is None:
            domain = _getframe(1).f_globals.get('__name__')
            domain = domain.split('.', 1)[0]

        self.message = message
        self.domain = domain
        # FIXME Used by the subclass 'INFO' (from itools.web)
        self.kw = kw


    def gettext(self, language=None, **kw):
        message = self.message
        domain = domains.get(self.domain)

        if domain is not None:
            # Find out the language
            if language is None:
                languages = domain.get_languages()
                # The 'select_language' function must be built-in
                language = select_language(languages)

            # Look-up
            if language is not None:
                message = domain.gettext(message, language)

        # Interpolation
        if kw:
            return message.format(**kw)

        return message
