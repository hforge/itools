# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008 Henry Obein <henry@itaapy.com>
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
from itools.uri import Path
from itools.i18n import is_asian_character, is_punctuation


###########################################################################
# Base class
###########################################################################
class BaseField(object):
    """Abstract class, the base for every field class. To define a new field
    class these methods must be implemented:

    * split(value) -- returns a sequence of two-elements tuple, where the
      first element is a word to be indexed and the second element is the
      position of the word. For example: [(word, 0), (word, 1), ...]. It
      maybe a generator.

    * decode(string) -- gets a unicode string and must return a value with
      the right type (for example IntegerField returns an integer value)

    * encode(value) -- gets a value with some type and must return a unicode
      string that represents it.
    """

    type = None
    is_indexed = True
    is_stored = False


    def __init__(self, name, is_indexed=None, is_stored=None):
        self.name = name
        if is_indexed is not None:
            self.is_indexed = is_indexed
        if is_stored is not None:
            self.is_stored = is_stored


    @staticmethod
    def split(value):
        """To index a field it must be split in a sequence of words and
        positions:

          [(word, 0), (word, 1), (word, 2), ...]

        Where <word> will be a unicode value. Usually this function will be a
        generator.
        """
        raise NotImplementedError


    @staticmethod
    def decode(string):
        """When a field is stored, this function allows to deserialize the
        unicode string to the right type.
        """
        raise NotImplementedError


    @staticmethod
    def encode(value):
        """When a field is stored, this function allows to serialize the value
        to a unicode string.
        """
        raise NotImplementedError


###########################################################################
# Built-in field types
###########################################################################

#common_words = set(['about', 'an', 'and', 'are', 'at', 'as', 'be', 'from',
#                    'for', 'how', 'in', 'is', 'it', 'of', 'on', 'or', 'that',
#                    'the', 'this', 'to', 'was', 'what', 'when', 'where',
#                    'which', 'who', 'why', 'will'])


class TextField(BaseField):

    type = 'text'

    @staticmethod
    def split(value):
        """
        Returns the next word and its position in the data. The analysis
        is done with the automaton:

        0 -> 1 [letter or number]
        0 -> 0 [stop word]
        1 -> 1 [letter or number or cjk]
        1 -> 0 [stop word]
        0 -> 2 [cjk]
        2 -> 0 [stop word]
        2 -> 3 [letter or number or cjk]
        3 -> 3 [letter or number or cjk]
        3 -> 0 [stop word]
        """
        if value is None:
            return

        # FIXME value should be an unicode object
        if isinstance(value, (unicode, str)) is False:
            raise TypeError, 'unexpected %s' % type(value)

        position = state = 0
        lexeme = previous_cjk = u''
        mode_cjk = None

        for c in value:
            if mode_cjk is None:
                mode_cjk = is_asian_character(c)

            if is_punctuation(c):
                # Stop word
                if mode_cjk: # CJK
                    if previous_cjk and state == 2: # CJK not yielded yet
                        yield previous_cjk, position
                        position += 1
                else: # ASCII
                    if state == 1:
                        lexeme = lexeme.lower()
                        yield lexeme, position
                        position += 1

                # reset state
                lexeme = u''
                previous_cjk = u''
                state = 0
                mode_cjk = None
            else:
                if mode_cjk is False: # ASCII
                    if state == 1:
                        lexeme += c
                    else: # state == 0
                        lexeme += c
                        state = 1

                else: # CJK
                    # c.lower() -> ASCII in CJK mode
                    if previous_cjk:
                        yield u'%s%s' % (previous_cjk, c.lower()), position
                        position += 1
                        state = 3
                    else:
                        state = 2
                    previous_cjk = c.lower()

        # Last word
        if state == 1:
            lexeme = lexeme.lower()
            yield lexeme, position
        elif previous_cjk and state == 2:
            yield previous_cjk, position


    @staticmethod
    def decode(string):
        return string


    @staticmethod
    def encode(value):
        return value



class BoolField(BaseField):

    type = 'bool'

    @staticmethod
    def split(value):
        yield unicode(int(value)), 0


    @staticmethod
    def decode(string):
        return bool(int(string))


    @staticmethod
    def encode(value):
        return unicode(int(value))



class KeywordField(BaseField):

    type = 'keyword'

    @staticmethod
    def split(value):
        if value is None:
            return

        if isinstance(value, (tuple, list, set, frozenset)):
            for x in value:
                yield unicode(x), 0
        else:
            value = unicode(value)
            if value:
                yield value, 0


    @staticmethod
    def decode(string):
        return string


    @staticmethod
    def encode(value):
        if isinstance(value, list):
            return u' '.join(value)
        return value




class IntegerField(BaseField):
    # FIXME This implementation is a quick and dirty hack

    type = 'integer'

    @staticmethod
    def split(value):
        value = '%10d' % value
        return KeywordField.split(value)


    @staticmethod
    def decode(string):
        return int(string)


    @staticmethod
    def encode(value):
        return unicode(value)



#class PathField(BaseField):
#
#    type = 'path'
#
#    @staticmethod
#    def split(value):
#        if not isinstance(value, Path):
#            value = Path(value)
#
#        i = 0
#        for segment in value:
#            yield unicode(segment), i
#            i += 1



###########################################################################
# The registry
###########################################################################
fields = {}

def register_field(cls):
    fields[cls.type] = cls


def get_field(type):
    return fields[type]



for cls in TextField, KeywordField, IntegerField, BoolField:
    register_field(cls)
