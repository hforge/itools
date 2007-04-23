# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from itools
from itools.uri import Path


###########################################################################
# Base class
###########################################################################
class BaseField(object):

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



class BoolField(BaseField):

    type = 'bool'

    @staticmethod
    def split(value):
        yield unicode(int(value)), 0



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



class IntegerField(BaseField):
    # FIXME This implementation is a quick and dirty hack

    type = 'integer'

    @staticmethod
    def split(value):
        value = '%10d' % value
        return KeywordField.split(value)



class PathField(BaseField):

    type = 'path'

    @staticmethod
    def split(value):
        if not isinstance(value, Path):
            value = Path(value)

        i = 0
        for segment in value:
            yield unicode(segment), i
            i += 1



###########################################################################
# The registry
###########################################################################
fields = {}

def register_field(cls):
    fields[cls.type] = cls


def get_field(type):
    return fields[type]



for cls in TextField, KeywordField, IntegerField, BoolField, PathField:
    register_field(cls)
