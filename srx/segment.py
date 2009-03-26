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


SPACE = ' \t\r\n'


def isspace(text):
    if len(text) == 0:
        return False
    if text.strip(SPACE):
        return False
    return True


def collapse(text):
    """Sequences of white-space characters are normalized to one ' ' char.
    """
    collapsed_text = []

    state = 0
    for c in text:
        if state == 0:
            if c in SPACE:
                collapsed_text.append(' ')
                state = 1
            else:
                collapsed_text.append(c)
        else:
            if c not in SPACE:
                state = 0
                collapsed_text.append(c)

    return ''.join(collapsed_text)



def _remove_spaces(left, center, right, keep_spaces):
    # (1) Move only "spaces" surrounding the center to left and right
    if center:
        # Begin
        type, value, line = center[0]
        if type == TEXT:
            text, context = value

            new_start = 0
            for c in text:
                if isspace(c):
                    # Move the character
                    left.append_text(c, line, None)
                    new_start += 1
                    if c == '\n':
                        line += 1
                else:
                    break
            center[0] = type, (text[new_start:], context), line

        # End
        type, value, line = center[-1]
        if type == TEXT:
            text, context = value

            new_end = len(text)
            moved_text = u''
            for c in reversed(text):
                if isspace(c):
                    # Move the character
                    moved_text = c + moved_text
                    new_end -= 1
                else:
                    break
            # Append to right
            if moved_text:
                text = text[:new_end]
                if right and right[0][0] == TEXT:
                    right_text, right_context = right[0][1]
                    right[0] = (TEXT, (moved_text+right_text, right_context),
                                right[0][2] - moved_text.count('\n'))
                else:
                    right.insert(0, (TEXT, (moved_text, None),
                                 line + text.count('\n')))
                center[-1] = type, (text, context), line

    # (2) Remove eventually all "double spaces" in the text
    if not keep_spaces:
        for i, (type, value, line) in enumerate(center):
            if type == TEXT and value[0]:
                text, context = value

                # Begin and End
                if i > 0 and text and isspace(text[0]):
                    begin = u' '
                else:
                    begin = u''
                if i < len(center) - 1 and isspace(text[-1]):
                    end = u' '
                else:
                    end = u''

                # Compute the new "line" argument
                for c in text:
                    if not isspace(c):
                        break
                    if c == '\n':
                        line += 1

                # Clean
                text = text.strip(SPACE)
                text = collapse(text)

                # And store the new value
                center[i] = (type, (begin + text + end, context), line)

    return left, center, right


def _clean_message(message, keep_spaces):
    # The results
    left = Message()
    center = Message(message)
    right = Message()

    # (1) Remove the "spaces" TEXT before and after the message
    while (center and center[0][0] == TEXT and
           center[0][1][0].strip(SPACE) == ''):
        left.append(center.pop(0))
    while (center and center[-1][0] == TEXT and
           center[-1][1][0].strip(SPACE) == ''):
        right.insert(0, center.pop())

    # (2) Remove start/end couples before and after the message
    while (len(center) >= 2 and center[0][0] == START_FORMAT and
           center[1][0] == END_FORMAT and center[0][1][1] == center[1][1][1]):
           left.append(center.pop(0))
           left.append(center.pop(0))
    while (len(center) >= 2 and center[-2][0] == START_FORMAT and
           center[-1][0] == END_FORMAT and
           center[-2][1][1] == center[-1][1][1]):
           right.insert(0, center.pop())
           right.insert(0, center.pop())

    # (3) Remove enclosing format
    while center:
        if (center[0][0] == START_FORMAT and center[-1][0] == END_FORMAT and
            center[0][1][1] == center[-1][1][1]):
            left.append(center.pop(0))
            right.insert(0, center.pop())
        else:
            break

    # (4) Remove the spaces
    left, center, right = _remove_spaces(left, center, right, keep_spaces)

    return left, center, right


def _split_message(message, srx_handler=None):
    # Concatenation!
    concat_text = []
    for type, value, line in message:
        if type == TEXT:
            concat_text.append(value[0])
    concat_text = u''.join(concat_text)

    # Get the rules
    if srx_handler is None:
        srx_handler = SRXFile(get_abspath('srx/default.srx', 'itools'))
    # XXX we must handle the language here!
    rules = srx_handler.get_compiled_rules('en')

    # Get the breaks
    breaks = set()
    no_breaks = set()
    for break_value, regexp in rules:
        for match in regexp.finditer(concat_text):
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
            text, context = value
            if forbidden_break:
                current_message.append_text(text, line, context)
                current_length += len(text)
            else:
                line_offset = 0
                for absolute_pos in breaks:
                    pos = absolute_pos - current_length
                    if 0 <= pos and pos < len(text):
                        before = text[:pos]
                        text = text[pos:]
                        # Add before to the current message
                        if before:
                            current_message.append_text(before,
                                                        line + line_offset,
                                                        context)
                            current_length += len(before)
                            line_offset += before.count('\n')
                        # Send the message if it is not empty
                        if current_message:
                            yield current_message
                            current_message = Message()
                if text:
                    current_length += len(text)
                    current_message.append_text(text, line + line_offset,
                                                context)
        elif type == START_FORMAT:
            forbidden_break = True
            current_message.append_start_format(value[0], value[1], line)
        elif type == END_FORMAT:
            forbidden_break = False
            current_message.append_end_format(value[0], value[1], line)

    # Send the last message
    if current_message:
        yield current_message


def _translate_format(message, catalog):
    for type, value, line in message:
        if type != TEXT:
            for i, (text, translatable, context) in enumerate(value[0]):
                if translatable and text.strip(SPACE):
                    translation = catalog.gettext(((TEXT, text),), context)
                    value[0][i] = (translation[0][1], True, context)


def _translate_message(message, catalog):
    # Save the formats
    id2tags = {}
    for type, value, line in message:
        if type != TEXT:
            id = value[1]
            id2tags[type, id] = (type, value, line)

    # Translation
    translation = catalog.gettext(message.to_unit(), message.get_context())
    result = Message()
    for type, value in translation:
        if type == TEXT:
            # The line parameter is not good
            result.append_text(value)
        else:
            result.append(id2tags[type, value])

    return result


###########################################################################
# API
###########################################################################
def get_segments(message, keep_spaces=False, srx_handler=None):
    for sub_message in _split_message(message, srx_handler):
        left, center, right = _clean_message(sub_message, keep_spaces)

        todo = left+right

        if center != sub_message:
            for value, context, line in get_segments(center, keep_spaces,
                                                     srx_handler):
                yield value, context, line
        else:
            # Is there a human text in this center ?
            for type, value, line in center:
                # XXX A more complex test here
                if type == TEXT and value[0].strip(SPACE):
                    yield (center.to_unit(), center.get_context(),
                           center.get_line())
                    break
            todo.extend(center)

        # And finally, the units in start / end formats
        for type, value, line in todo:
            if type != TEXT:
                for (text, translatable, context) in value[0]:
                    if translatable and text.strip(SPACE):
                        yield ((TEXT, text),), context, line


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
            # Is there a human text in this center ?
            for type, value, line in center:
                # XXX A more complex test here
                if type == TEXT and value[0].strip(SPACE):
                    center = _translate_message(center, catalog)
                    break
            _translate_format(center, catalog)
            center = center.to_str()

        translated_message.extend([left, center, right])
    return u''.join(translated_message)


class Message(list):
    """A 'Message' object represents a text to be processed. It is a complex
    object instead of just a string to allow us to deal with formatted text.
    """

    def append_text(self, text, line=1, context=None):
        """The parameter "text" must be an unicode string.
        """
        # Merge the TEXT with the last one
        if self and (self[-1][0] == TEXT):
            trash, (last_text, last_context), last_line = self[-1]

            if last_context is not None:
                context = last_context

            self[-1] = TEXT, (last_text + text, context), last_line
        # A new TEXT !
        else:
            list.append(self, (TEXT, (text, context), line))


    def append_start_format(self, content, id, line=1):
        """value=[(u'...', translatable, context), ...]
        """
        self.append((START_FORMAT, (content, id), line))


    def append_end_format(self, content, id, line=1):
        """value=idem as start_format
        """
        self.append((END_FORMAT, (content, id), line))


    def get_line(self):
        if self:
            return self[0][2]
        else:
            return None


    def get_context(self):
         # Return the first context != None
         # or None
        if self:
            for type, value, line in self:
                if type == TEXT and value[1] is not None:
                    return value[1]
        return None


    def to_str(self):
        result = []
        for type, value, line in self:
            if type == TEXT:
                result.append(value[0])
            else:
                for text, translatable, context in value[0]:
                    result.append(text)
        return u''.join(result)


    def to_unit(self):
        result = []
        for type, value, line in self:
            if type == TEXT:
                result.append((TEXT, value[0]))
            else:
                result.append((type, value[1]))
        return tuple(result)

