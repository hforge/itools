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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA

# Import from itools
from itools.handlers import get_handler

domains = {}

def register_domain(name, locale_path):
    if name not in domains:
        domains[name] = get_handler(locale_path)


class Domain:

    class_domain = None


    def gettext(self, message, language=None, domain=None):
        if domain is None:
            domain = self.class_domain

        if domain is None:
            return message

        if domain not in domains:
            return message

        domain = domains[domain]
        if language is None:
            # Build the list of available languages
            languages = [ x[:-3] for x in domain.get_handler_names()
                          if x.endswith('.mo') ]

            language = self.select_language(languages)

        if language is None:
            return message

        mo = domain.get_handler('%s.mo' % language)
        return mo.gettext(message)


    def select_language(self, languages):
        raise NotImplementedError
            


def N_(message, language=None):
    """
    Used to markup a string for translation but without translating it,
    this is known as deferred translations.
    """
    return message

