# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from itools
from itools import uri


common_words = set(['about', 'an', 'and', 'are', 'at', 'as', 'be', 'from',
                    'for', 'how', 'in', 'is', 'it', 'of', 'on', 'or', 'that',
                    'the', 'this', 'to', 'was', 'what', 'when', 'where',
                    'which', 'who', 'why', 'will'])


def Text(data):
    """
    Returns the next word and its position in the data. The analysis
    is done with the automaton:

    0 -> 1 [letter or number]
    0 -> 0 [stop word]
    1 -> 1 [letter or number]
    1 -> 0 [stop word]

    0 -> 1 [letter or number]
    0 -> 0 [stop word]
    1 -> 2 [letter or number]
    1 -> 0 [stop word]
    2 -> 2 [letter or number]
    2 -> word [stop word]
    """
    position = 0
    state = 0
    lexeme = u''
    for c in data:
        if state == 0:
            if c.isalpha():
                lexeme += c
                state = 1
        elif state == 1:
            if c.isalpha():
                lexeme += c
            else:
                lexeme = lexeme.lower()
                yield lexeme, position
                position += 1
                lexeme = u''
                state = 0
    # Last word
    if state == 1:
        lexeme = lexeme.lower()
        yield lexeme, position



def Bool(value):
    yield unicode(int(value)), 0



def Keyword(value):
    if value:
        if isinstance(value, (list, set, frozenset)):
            for x in value:
                yield unicode(x), 0
        else:
            yield unicode(value), 0



def Path(value):
    if not isinstance(value, uri.Path):
        value = uri.Path(value)

    i = 0
    for segment in value:
        yield unicode(segment), i
        i += 1



analysers = {'text': Text,
             'bool': Bool,
             'keyword': Keyword,
             'path': Path}

def get_analyser(name):
    return analysers.get(name)
