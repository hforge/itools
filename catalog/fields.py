# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


###########################################################################
# Base class
###########################################################################
class BaseField(object):
    """
    Abstract class, the base for every field class. To define a new field
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
        """
        To index a field it must be split in a sequence of words and
        positions:

          [(word, 0), (word, 1), (word, 2), ...]

        Where <word> will be a unicode value. Usually this function will
        be a generator.
        """
        raise NotImplementedError


    @staticmethod
    def decode(string):
        """
        When a field is stored, this function allows to deserialize the
        unicode string to the right type.
        """
        raise NotImplementedError


    @staticmethod
    def encode(value):
        """
        When a field is stored, this function allows to serialize the
        value to a unicode string.
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
        1 -> 1 [letter or number]
        1 -> 0 [stop word]
        """
        position = 0
        state = 0
        lexeme = u''
        for c in value:
            if state == 1:
                if c.isalnum():
                    lexeme += c
                else:
                    lexeme = lexeme.lower()
                    yield lexeme, position
                    position += 1
                    lexeme = u''
                    state = 0
            else: # state == 0
                if c.isalnum():
                    lexeme += c
                    state = 1
        # Last word
        if state == 1:
            lexeme = lexeme.lower()
            yield lexeme, position


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
