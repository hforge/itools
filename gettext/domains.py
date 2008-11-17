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
from string import Template
from sys import _getframe
from types import ModuleType

# Import from itools
from itools.handlers import Folder, Database


domains = {}

database = Database()
def register_domain(name, locale_path):
    if name not in domains:
        domain = Domain(locale_path)
        domain.database = database
        domains[name] = domain


def get_domain(name):
    return domains[name]



# FIXME The "Folder" handler class is not meant to be a base class, we should
# not inherit from it.  Figure out another way to do the job.
class Domain(Folder):

    def gettext(self, message, language):
        handler_name = '%s.mo' % language
        if self.has_handler(handler_name):
            handler = self.get_handler(handler_name)
            return handler.gettext(message)
        return message


    def get_languages(self):
        return [ x[:-3] for x in self.get_handler_names()
                 if x.endswith('.mo') ]



def gettext(domain_name, message, language=None, **kw):
    # Source look-up
    if type(message) is str:
        domain_name, message = find_module_name(domain_name, message)

    # Get the domain
    domain_name = domain_name.split('.', 1)[0]
    domain = domains[domain_name]

    # Find out the language (the 'select_language' function must be built-in)
    if language is None:
        languages = domain.get_languages()
        language = select_language(languages)

    # Look-up
    if language is not None:
        message = domain.gettext(message, language)

    # Interpolation
    if kw:
        return Template(message).substitute(kw)

    return message



class MSG(object):

    __slots__ = ['message', 'domain', 'kw']

    def __init__(self, message, domain=None, **kw):
        if domain is None:
            domain = _getframe(1).f_globals.get('__name__')
            domain = domain.split('.', 1)[0]

        self.message = message
        self.domain = domain
        # XXX Used by the subclass 'INFO' (from itools.web)
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
            return Template(message).substitute(kw)

        return message

