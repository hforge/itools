# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008 Romain Gauthier <romain.gauthier@itaapy.com>
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
from srx import SRXFile

# Constants
TEXT, START_FORMAT, END_FORMAT = range(3)


def _remove_spaces(left, center, right, keep_spaces):
    # Move only "spaces" surrounding the center to left and right
    if center:
        # Begin
        type, value, line = center[0]
        if type == TEXT:
            new_start = 0
            for c in value:
                if c.isspace():
                    # Move the character
                    left.append_text(c, line)
                    new_start += 1
                    if c == '\n':
                        line += 1
                else:
                    break
            center[0] = type, value[new_start:], line

        # End
        type, value, line = center[-1]
        if type == TEXT:
            new_end = len(value)
            text = u''
            for c in reversed(value):
                if c.isspace():
                    # Move the character
                    text = c + text
                    new_end -= 1
                else:
                    break
            # Append to right
            if text:
                value = value[:new_end]
                if right and right[0][0] == TEXT:
                    right[0] = (TEXT, text+right[0][1], right[0][2] -
                                text.count('\n'))
                else:
                    right.insert(0, (TEXT, text, line + value.count('\n')))
                center[-1] = type, value, line

    # Remove eventually all "double spaces" in the text
    if not keep_spaces:
        for i, (type, value, line) in enumerate(center):
            if type == TEXT:
                # Begin and End
                if i > 0 and value and value[0].isspace():
                    begin = u' '
                else:
                    begin = u''
                if i < len(center) - 1 and value[-1].isspace():
                    end = u' '
                else:
                    end = u''

                # Compute the new "line" argument
                for c in value:
                    if not c.isspace():
                        break
                    if c == '\n':
                        line += 1

                # Clean
                value = u' '.join(value.split())

                # And store the new value
                center[i] = (type, begin + value + end, line)

    return left, center, right


def _clean_message(message, keep_spaces):
    # The results
    left = Message()
    center = Message(message)
    right = Message()

    # Remove the "spaces" TEXT after and before the message
    while center and center[0][0] == TEXT and center[0][1].strip() == '':
        left.append(center.pop(0))
    while center and center[-1][0] == TEXT and center[-1][1].strip() == '':
        right.insert(0, center.pop())

    # Remove enclosing format
    while center:
        if (center[0][0] == START_FORMAT and center[-1][0] == END_FORMAT and
            center[0][1][1] == center[-1][1][1]):
            left.append(center.pop(0))
            right.insert(0, center.pop())
        else:
            break

    # Remove the spaces
    left, center, right = _remove_spaces(left, center, right, keep_spaces)

    return left, center, right


def _split_message(message, srx_handler=None):
    # Concatenation!
    text = []
    for type, value, line in message:
        if type == TEXT:
            text.append(value)
    text = u''.join(text)

    # Get the rules
    if srx_handler is None:
        srx_handler = SRXFile(get_abspath('srx/default.srx', 'itools'))
    # XXX we must handle the language here!
    rules = srx_handler.get_compiled_rules('en')

    # Get the breaks
    breaks = set()
    no_breaks = set()
    for break_value, regexp in rules:
        for match in regexp.finditer(text):
            pos = match.end()
            if break_value and pos not in no_breaks:
                breaks.add(pos)
            if not break_value and pos not in breaks:
                no_breaks.add(pos)
    breaks = list(breaks)
    breaks.sort()

    # And now cut the message
    forbidden_break = False
    current_message = Message()
    current_length = 0
    for type, value, line in message:
        if type == TEXT:
            if forbidden_break:
                current_message.append_text(value, line)
                current_length += len(value)
            else:
                line_offset = 0
                for absolute_pos in breaks:
                    pos = absolute_pos - current_length
                    if 0 <= pos and pos < len(value):
                        before = value[:pos]
                        value = value[pos:]
                        # Add before to the current message
                        if before:
                            current_message.append_text(before,
                                                        line + line_offset)
                            current_length += len(before)
                            line_offset += before.count('\n')
                        # Send the message if it is not empty
                        if current_message:
                            yield current_message
                            current_message = Message()
                if value:
                    current_length += len(value)
                    current_message.append_text(value, line + line_offset)
        elif type == START_FORMAT:
            forbidden_break = True
            current_message.append_start_format(value, line)
        elif type == END_FORMAT:
            forbidden_break = False
            current_message.append_end_format(value, line)

    # Send the last message
    if current_message:
        yield current_message


def _translate_format(message, catalog):
    for type, value, line in message:
        if type != TEXT:
            for i, (text, translatable) in enumerate(value[0]):
                if translatable:
                    text = catalog.gettext(text)
                    value[0][i] = (text, False)


###########################################################################
# API
###########################################################################
def get_segments(message, keep_spaces=False, srx_handler=None):
    for sub_message in _split_message(message, srx_handler):
        left, center, right = _clean_message(sub_message, keep_spaces)

        todo = left+right

        if center != sub_message:
            for value, line in get_segments(center, keep_spaces,
                                            srx_handler):
                yield value, line
        else:
            # Is center good ?
            for type, value, line in center:
                if type == TEXT and value.strip():
                    yield center.to_str(), center.get_line()
                    break
            else:
                # Not good!
                todo.extend(center)

        # And finally, the units in start / end formats
        for type, value, line in todo:
            if type != TEXT:
                for (text, translatable) in value[0]:
                    if translatable:
                        yield text, line


def translate_message(message, catalog, keep_spaces=False, srx_handler=None):
    translated_message = []
    for sub_message in _split_message(message, srx_handler):
        left, center, right = _clean_message(sub_message, keep_spaces)

        _translate_format(left, catalog)
        left = left.to_str()

        _translate_format(right, catalog)
        right = right.to_str()

        if center != sub_message:
            center = translate_message(center, catalog, keep_spaces,
                                       srx_handler)
        else:
            # Is center good ?
            for type, value, line in center:
                if type == TEXT and value.strip():
                    center = catalog.gettext(center.to_str())
                    break
            else:
                # Not Good
                _translate_format(center, catalog)
                center = center.to_str()

        translated_message.extend([left, center, right])
    return u''.join(translated_message)



class Message(list):
    """A 'Message' object represents a text to be processed. It is a complex
    object instead of just a string to allow us to deal with formatted text.
    """

    def append_text(self, text, line=1):
        """The parameter "text" must be an unicode string.
        """
        if self and (self[-1][0] == TEXT):
            last = self[-1]
            self[-1] = TEXT, last[1] + text, last[2]
        else:
            list.append(self, (TEXT, text, line))


    def append_start_format(self, value, line=1):
        """value=([(u'...', True), ...], id)
            True -> is translatable
            False -> not translatable
        """
        self.append((START_FORMAT, value, line))


    def append_end_format(self, value, line=1):
        """value=idem as start_format
        """
        self.append((END_FORMAT, value, line))


    def get_line(self):
        if self:
            return self[0][2]
        else:
            return None

    def to_str(self):
        result = []
        for type, value, line in self:
            if type == TEXT:
                result.append(value)
            else:
                for text, translatable in value[0]:
                    result.append(text)
        return u''.join(result)

