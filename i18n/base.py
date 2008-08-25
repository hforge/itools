# -*- coding: UTF-8 -*-
# Copyright (C) 2002-2003, 2007-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from itools.utils import get_abspath


# Initializes a dictionary containing the iso 639 language codes/names
languages = {}
filename = get_abspath('languages.txt')
for line in open(filename).readlines():
    line = line.strip()
    if line and line[0] != '#':
        code, name = line.split(' ', 1)
        languages[code] = name

# Builds a sorted list with the languages code and name
language_codes = languages.keys()
language_codes.sort()
langs = [ {'code': x, 'name': languages[x]} for x in language_codes ]



def has_language(code):
    return code in languages



def get_languages():
    """Returns a list of tuples with the code and the name of each language.
    """
    return [ x.copy() for x in langs ]



def get_language_name(code):
    """Returns the name of a language.
    """
    # FIXME The value returned should be a MSG object, but the MSG class comes
    # from the itools.gettext module, which is higher level than itools.i18n
    if code in languages:
        return languages[code]
    return u'???'



# FIXME This class is only used by Localizer, either refactor the code so
# it is used too by ikaaro, or move this code to Localizer.
class Multilingual(object):
    """Mixin class that defines multilingual objects.
    """

    # TODO For backwards compatibility with Python 2.1 the variable
    # _languages is a tuple.  Change it to a frozenset.
    _languages = ()
    _default_language = None


    ########################################################################
    # API
    ########################################################################
    def get_languages(self):
        """Returns all the object languages.
        """
        return self._languages


    def set_languages(self, languages):
        """Sets the object languages.
        """
        self._languages = tuple(languages)


    def add_language(self, language):
        """Adds a new language.
        """
        if language not in self._languages:
            self._languages = tuple(self._languages) + (language,)


    def del_language(self, language):
        """Removes a language.
        """
        if language in self._languages:
            self._languages = tuple([ x for x in self._languages
                                      if x != language ])


    def get_languages_mapping(self):
        """Returns a list of dictionary, one for each objects language. The
        dictionary contains the language code, its name and a boolean value
        that tells wether the language is the default one or not.
        """
        return [ {'code': x,
                  'name': get_language_name(x),
                  'default': x == self._default_language}
                 for x in self._languages ]


    def get_available_languages(self, **kw):
        """Returns the langauges available. For example, a language could be
        considered as available only if there is some data associated to it.

        This method is used by the language negotiation code (see
        'get_selected_language'), sometimes you will want to redefine it in
        your classes.
        """
        return self._languages


    def get_default_language(self):
        """Returns the default language.

        This method is used by the language negotiation code (see
        'get_selected_language'), sometimes you will want to redefine it in
        your classes.

        For example, maybe you will want to define it to return always a
        default language, even when internally it is None.
        """
        return self._default_language

