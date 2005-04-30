# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2002-2003 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from itools import get_abspath
import accept
import segment



#############################################################################
# Initialization
#############################################################################

# Initializes a dictionary containing the iso 639 language codes/names
languages = {}
filename = get_abspath(globals(), 'languages.txt')
for line in open(filename).readlines():
    line = line.strip()
    if line and line[0] != '#':
        code, name = line.split(' ', 1)
        languages[code] = name

# Builds a sorted list with the languages code and name
language_codes = languages.keys()
language_codes.sort()
langs = [ {'code': x, 'name': languages[x]} for x in language_codes ]



#############################################################################
# Public interface
#############################################################################

__all__ = ['get_languages', 'get_language_name', 'Multilingual']


def get_languages():
    """
    Returns a list of tuples with the code and the name of each language.
    """
    return [ x.copy() for x in langs ]


def get_language_name(code):
    """
    Returns the name of a language.
    """
    return languages.get(code, '???')



class Multilingual:
    """
    Mixin class that defines multilingual objects.
    """

    # XXX The variable _languages should be a set, it is not because we want
    # to keep compatibilty with Python 2.1; it could be a list too, but it
    # is a tuple to avoid mistakes in multilingual persistent classes.

    _languages = ()
    _default_language = None


    ########################################################################
    # API
    ########################################################################
    def get_languages(self):
        """
        Returns all the object languages.
        """
        return self._languages


    def set_languages(self, languages):
        """
        Sets the object languages.
        """
        self._languages = tuple(languages)


    def add_language(self, language):
        """
        Adds a new language.
        """
        if language not in self._languages:
            self._languages = tuple(self._languages) + (language,)


    def del_language(self, language):
        """
        Removes a language.
        """
        if language in self._languages:
            self._languages = tuple([ x for x in self._languages
                                      if x != language ])


    def get_languages_mapping(self):
        """
        Returns a list of dictionary, one for each objects language. The
        dictionary contains the language code, its name and a boolean
        value that tells wether the language is the default one or not.
        """
        return [ {'code': x,
                  'name': get_language_name(x),
                  'default': x == self._default_language}
                 for x in self._languages ]


    def get_available_languages(self, **kw):
        """
        Returns the langauges available. For example, a language could be
        considered as available only if there is some data associated to
        it.

        This method is used by the language negotiation code (see
        'get_selected_language'), sometimes you will want to redefine
        it in your classes.
        """
        return self._languages


    def get_default_language(self):
        """
        Returns the default language.

        This method is used by the language negotiation code (see
        'get_selected_language'), sometimes you will want to redefine
        it in your classes.

        For example, maybe you will want to define it to return always
        a default language, even when internally it is None.
        """
        return self._default_language
