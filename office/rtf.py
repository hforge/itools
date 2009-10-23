# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Hervé Cauwelier <herve@itaapy.com>
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
from itools.handlers import File, register_handler_class



def rtf_parse(data):
    # 0 = default
    # 1 = keyword
    # 2 = text
    state = 0
    buffer = []

    for c in data:
        if state == 0:
            if c == '\\':
                buffer = [c]
                state = 1
        elif state == 1:
            if c in '{}':
                yield ''.join(buffer)
                buffer = []
                state = 0
            elif c == '\\':
                yield ''.join(buffer)
                buffer = [c]
                state = 1
            elif c == ' ':
                yield ''.join(buffer)
                buffer = []
                state = 2
            elif c == "'":
                buffer = ['=']
                state = 2
            elif c == '~':
                yield '\\~'
                buffer = []
                state = 2
            else:
                buffer.append(c)
        elif state == 2:
            if c == '\\':
                if buffer:
                    yield ''.join(buffer)
                buffer = [c]
                state = 1
            elif c in '{}':
                if buffer:
                    yield ''.join(buffer)
                    buffer = []
                state = 0
            elif c in '\r\n':
                pass
            else:
                buffer.append(c)



def rtf_to_text(data):
    if not isinstance(data, str):
        raise ValueError, "string data is expected"
    if not data:
        raise ValueError, "data is empty"
    if not data.startswith('{\\rtf'):
        raise ValueError, "data is not RTF"

    parser = rtf_parse(data)
    text = []

    # Read header
    for word in parser:
        if word in ('\\title', '\\author', '\\operator', '\\company'):
            text.append(parser.next())
            text.append('\n')
        elif word in ('\\sectd', '\\pard', '\\plain'):
            break

    # Read body
    for word in parser:
        if word == '\\pntxta' or word == '\\pntxtb':
            # Skip noise
            parser.next()
        elif word[0] not in '\\{}':
            text.append(word)
        elif word == '\\par':
            text.append('\n')
        elif word in ('\t', '\\tab', '\\emspace', '\\enspace', '\\qmspace',
                      '\\~'):
            text.append(' ')
        elif word in ('\\emdash', '\\endash', '\\bullet', '\\_'):
            text.append('-')
        elif word in ('\\lquote', '\\rquote'):
            text.append("'")
        elif word in ('\\ldblquote', '\\rdblquote'):
            text.append('"')
        elif word in ('\\{', '\\}', '\\\\'):
            text.append(word[1])

    text = ''.join(text)
    text = text.decode('quopri_codec')
    text = unicode(text, 'cp1252')
    return text




###########################################################################
# Handler
###########################################################################
class RTF(File):

    class_mimetypes = ['text/rtf']
    class_extension = 'rtf'


    def to_text(self):
        return rtf_to_text(self.to_str())


# Register
register_handler_class(RTF)
