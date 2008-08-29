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



TEXT_ID, TEXT, START_FORMAT, END_FORMAT = range(-1,3)

def _normalize(sentence, keep_spaces=False):
    """Make a sentence normalizing whitespaces or, if keep_spaces is True; a
    sentence as raw text.
    """
    if keep_spaces:
        return sentence
    tmp_sentence1 = sentence.rstrip()
    tmp_sentence2 = sentence.lstrip()
    # Normalize: '   text   text2' -> ' text text2'
    res_sentence = u' '.join(sentence.split())
    if tmp_sentence1 != sentence:
        res_sentence = res_sentence + u' '
    if tmp_sentence2 != sentence:
        res_sentence = u' ' + res_sentence
    return res_sentence



def _rm_enclosing_format(segment_structure, keep_spaces=False):
    """This function returns a tuple of two elements. The first element is the
    new segment_structure, then a boolean that indicates whether the
    segment_structure changed.
    """
    first, last = segment_structure[0], segment_structure[-1]
    n = len(segment_structure)

    # Check there is at least one enclosing format to remove
    if n <= 1 or first[2] == TEXT_ID or first[2] != last[2]:
        return segment_structure

    # Make a copy
    segment_structure = list(segment_structure)

    # Remove enclosing format
    while n > 1 and first[2] != TEXT_ID and first[2] == last[2]:
        segment_structure.pop(0)
        segment_structure.pop()
        n -= 2
        # Next (check we did not reach the empty list)
        if n == 0:
            break
        first, last = segment_structure[0], segment_structure[-1]

    return segment_structure



def _rm_enclosing_spaces(segment_structure, keep_spaces=False):
    """This function returns a new segment_structure which no longer contains
    enclosing spaces.
    """
    if keep_spaces is True or len(segment_structure) <= 1:
        return segment_structure

    # We remove all empty element which starts the structure
    while not segment_structure[0][1].strip():
        segment_structure.pop(0)
    # We remove all empty element which finish the structure
    while not segment_structure[-1][1].strip():
        segment_structure.pop()
    return segment_structure



def _get_enclosing_spaces(segment_structure, keep_spaces=False):
    """This function returns a new segment_structure which no longer contains
    enclosing spaces.
    """
    nb_left_spaces = nb_right_spaces = 0
    if keep_spaces is True or len(segment_structure) <= 1:
        return segment_structure, (nb_left_spaces, nb_right_spaces)

    # We remove all empty element which starts the structure
    while not segment_structure[nb_left_spaces][1].strip():
        nb_left_spaces += 1
    # We remove all empty element which finish the structure
    while not segment_structure[nb_right_spaces][1].strip():
        nb_right_spaces +=1
    segment_structure = _rm_enclosing_spaces(segment_structure, keep_spaces)
    return segment_structure, (nb_left_spaces, nb_right_spaces)



def _reinsert_spaces(segment_structure, spaces_positions):
    """Put spaces in the segment structure.
    'spaces_positions' is a tuple like (x, y). We insert x spaces in front of
    the list and y spaces at the end of the list.
    """
    nb_left_spaces, nb_right_spaces = spaces_positions
    for space_position in range(nb_left_spaces):
        segment_structure.insert(0, (TEXT, u' ', TEXT_ID))
    for space_position in range(nb_right_spaces):
        segment_structure.append((TEXT, u' ', TEXT_ID))
    return segment_structure



def _reinsert_format(segment_structure, formats):
    """Re-inject formats into the segment_structure.
    'formats' is a tuple like (start_format, end_format).
    """
    starting, ending = formats
    segment_structure.insert(0, starting)
    segment_structure.append(ending)
    return segment_structure



def _reconstruct_message(segment_structure):
    """Take a segment_structure and rebuild a new Message object.
    """
    message = Message()
    for seg_struct in segment_structure:
        if seg_struct[0] == TEXT:
            message.append_text(seg_struct[1])
        elif seg_struct[0] == START_FORMAT:
            message.append_start_format(seg_struct[1])
        elif seg_struct[0] == END_FORMAT:
            message.append_end_format(seg_struct[1])
    return message



def _reconstruct_segment(segment_structure, keep_spaces=False):
    """Take a segment_structure and rebuild a new segment (str).
    """
    segment = u''
    for seg_struct in segment_structure:
        segment = segment + seg_struct[1]
    if keep_spaces is False:
        segment = segment.strip()
    return segment



def _translation_to_struct(segment_translations):
    """_translation_to_struct
    """
    seg_struct = segment_translations
    if segment_translations \
        and isinstance(segment_translations[0], (str, unicode)):
        seg_struct = []
        for translation in segment_translations:
            translation_tuple = (TEXT, translation, TEXT_ID)
            seg_struct.append(translation_tuple)
    return seg_struct


def _split_message(message, srx_handler):
    # Concatenation!
    text = []
    for type, value, line in message:
        if type == TEXT:
            text.append(value)
    text = ''.join(text)

    # Get the rules
    if srx_handler is None:
        srx_handler = SRXFile(get_abspath('srx/srx_example.srx', 'itools'))
    # XXX we must handle the language here!
    rules = srx_handler.get_compiled_rules('Default')

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


def get_segments(message, keep_spaces=False, srx_handler=None):
    """This is a generator that iters over the message. First it segment
    the message and get back the corresponding segments. Then it remove the
    potentially enclosing format element from the segment. If there was
    enclosing format, the generator reiterates on the segment as if it
    was a new message. Indeed, there may be some new segments in this new
    message.
    """

    for segment_structure, line_offset in _split_message(message,
                                                         srx_handler):
        segment_structure = \
            _rm_enclosing_spaces(segment_structure, keep_spaces)
        new_seg_struct = \
            _rm_enclosing_format(segment_structure, keep_spaces)
        if new_seg_struct != segment_structure:
            new_message = _reconstruct_message(new_seg_struct)
            for segment, new_offset in get_segments(new_message, keep_spaces,
                                                    srx_handler=None):
                yield segment, line_offset + new_offset
        else:
            segment = _reconstruct_segment(segment_structure,
                                           keep_spaces)
            if segment:
                yield segment, line_offset



def translate_message(message, catalog, keep_spaces, srx_handler=None):
    """Returns translation's segments.
    segment_dict is a dictionnary which map segments to their corresponding
    translation. This method is recursive.
    """
    translation_dict = {}
    for segment, line_offset in get_segments(message, keep_spaces,
                                             srx_handler):
        segment_translation = catalog.gettext(segment)
        translation_dict[segment] = segment_translation

    translation = _translate_segments(message, translation_dict, keep_spaces)
    translation = list(translation)
    translation = u''.join(translation)

    return translation.encode('utf-8')



def _translate_segments(message, translation_dict, keep_spaces,
                        srx_handler=None):
    for seg_struct, line_offset in _split_message(message, srx_handler):
        seg_struct, spaces_pos = \
            _get_enclosing_spaces(seg_struct, keep_spaces)
        new_seg_struct = _rm_enclosing_format(seg_struct, keep_spaces)
        if new_seg_struct is seg_struct:
            segment = _reconstruct_segment(seg_struct, keep_spaces)
            if segment:
                raw_segment = _reconstruct_segment(seg_struct, True)
                translation = translation_dict[segment]
                translation = raw_segment.replace(segment, translation)
                yield translation
        else:
            start_format = seg_struct.pop(0)
            end_format = seg_struct.pop()
            new_message = _reconstruct_message(seg_struct)
            segment_translations = _translate_segments(new_message,
                                            translation_dict, keep_spaces)
            segment_translations = list(segment_translations)
            seg_struct = _translation_to_struct(segment_translations)
            formats = (start_format, end_format)
            seg_struct = _reinsert_format(seg_struct, formats)
            seg_struct = _reinsert_spaces(seg_struct, spaces_pos)
            translation = _reconstruct_segment(seg_struct, True)
            yield translation



class Message(list):
    """A 'Message' object represents a text to be processed. It is a complex
    object instead of just a string to allow us to deal with formatted text.

    A message is made of atoms, an atom is a unit that can not be splitted.
    It is either a letter or an object that represents a formatted block,
    like an xml node (e.g. '<em>hello world</em>').
    """

    def append_text(self, text, line):
        """The parameter "text" must be an unicode string.
        """
        if self and (self[-1][0] == TEXT):
            last = self[-1]
            self[-1] = TEXT, last[1] + text, last[2]
        else:
            list.append(self, (TEXT, text, line))


    def append_start_format(self, value, line):
        self.append((START_FORMAT, value, line))


    def append_end_format(self, value, line):
        self.append((END_FORMAT, value, line))


    def get_line(self):
        if self:
            return self[0][2]
        else:
            return None

