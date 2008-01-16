# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from itools.handlers import Folder, Database
from itools.i18n import get_accept


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



class DomainAware(object):

    class_domain = None


    @classmethod
    def get_languages(cls):
        return NotImplementedError


    @classmethod
    def select_language(cls, languages=None):
        if languages is None:
            languages = cls.get_languages()

        accept = get_accept()
        return accept.select_language(languages)


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
