# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from itools import uri


common_words = ['about', 'an', 'and', 'are', 'at', 'as', 'be', 'from', 'for',
                'how', 'in', 'is', 'it', 'of', 'on', 'or',
                'that', 'the', 'this', 'to',
                'was', 'what', 'when', 'where', 'which', 'who', 'why', 'will']


def Text(data):
    """
    Returns the next word and its position in the data. The analysis
    is done with the automaton:

    0 -> 1 [letter or number]
    0 -> 0 [stop word]
    1 -> 2 [letter or number]
    1 -> 0 [stop word]
    2 -> 2 [letter or number]
    2 -> word [stop word]
    """
    data = data
    index = 0
    position = 0

    state = 0
    lexeme = u''
    while index < len(data):
        c = data[index]
        if state == 0:
            if c.isalpha():
                lexeme += c
                state = 1
        elif state == 1:
            if c.isalpha():
                lexeme += c
                state = 2
            else:
                lexeme = u''
                state = 0
        elif state == 2:
            if c.isalpha():
                lexeme += c
            else:
                lexeme = lexeme.lower()
                if lexeme in common_words:
                    lexeme = u''
                    state = 0
                else:
                    yield lexeme, position
                    position += 1
                    lexeme = u''
                    state = 0
        index += 1
    # Last word
    if state == 2:
        lexeme = lexeme.lower()
        yield lexeme, position



def Bool(value):
    print value
    yield str(int(value)), 0



def Keyword(value):
    if value:
        yield value, 0



def Path(value):
    if not isinstance(value, uri.Path):
        value = uri.Path(value)

    i = 0
    for segment in value:
        yield str(segment), i
        i += 1
