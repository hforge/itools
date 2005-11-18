# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
import os

# Import from itools
from itools.resources import get_resource
from itools.handlers.Folder import Folder
from itools.i18n.accept import AcceptLanguage

domains = {}

def register_domain(name, locale_path):
    if name not in domains:
        resource = get_resource(locale_path)
        domains[name] = Domain(resource)



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



class DomainAware(object):

    class_domain = None


    @classmethod
    def get_languages(cls):
        return NotImplementedError


    @classmethod
    def select_language(cls, languages=None):
        if languages is None:
            languages = cls.get_languages()

        language = os.environ.get('LANGUAGE')
        if language is None:
            return None
        language = language.split('.')[0]
        language = language.replace('_', '-')
        accept_language = AcceptLanguage(language)
        return accept_language.select_language(languages)


    @classmethod
    def gettext(cls, message, language=None, domain=None):
        if domain is None:
            domain = cls.class_domain

        if domain not in domains:
            return message

        domain = domains[domain]
        if language is None:
            languages = domain.get_languages()
            language = cls.select_language(languages)

        if language is None:
            return message

        return domain.gettext(message, language)
