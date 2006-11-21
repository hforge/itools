# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from the Standard Library
from htmlentitydefs import name2codepoint

# Import from itools
from itools.handlers.Text import Text


guess_encoding = Text.guess_encoding


def xml_to_text(data):
    output = u''
    # 0 = Default
    # 1 = Start tag
    # 2 = Start text
    # 3 = Char or entity reference
    state = 0
    buffer = ''

    for c in data:
        if state == 0:
            if c == '<':
                state = 1
                continue
        elif state == 1:
            if c == '>':
                # Force word separator
                output += u' '
                state = 2
                continue
        elif state == 2:
            if c == '<' or c == '&':
                encoding = guess_encoding(buffer)
                #try:
                output += unicode(buffer, encoding, 'replace')
                #except UnicodeEncodeError:
                #    pass
                buffer = ''
                if c == '<':
                    state = 1
                    continue
                elif c == '&':
                    state = 3
                    continue
            else:
                buffer += c
        elif state == 3:
            if c == ';':
                if buffer[0] == '#':
                    output += unichr(int(buffer[1:]))
                elif buffer[0] == 'x':
                    output += unichr(int(buffer[1:], 16))
                else:
                    # XXX Assume entity
                    output += unichr(name2codepoint.get(buffer, 63)) # '?'
                buffer = ''
                state = 2
                continue
            else:
                buffer += c

    return output
