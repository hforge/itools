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


stop_sentences = set([u'.', u';', u'!', u'?', u':'])
abbreviations = set([u'Inc', u'Md', u'Mr', u'Dr'])


TEXT, START_FORMAT, END_FORMAT = range(3)
TEXT_ID = -1

def _is_sentence_done(last_char, last_word):
    if last_char not in stop_sentences:
        return False

    # Consider exceptions
    if last_char == u'.':
        # Acronyms
        if len(last_word) == 1 and last_word.isupper():
            return False
        # Abbreviations
        if last_word in abbreviations:
            return False

    return True



def _make_sentence(sentence, keep_spaces=False):
    """Make a sentence normalizing whitespaces or, if keep_spaces is True, a
    sentence as raw text.
    """
    if keep_spaces:
        return u''.join(sentence)
    sentence = u''.join(sentence)
    # Right spaces
    tmp_sentence1 = sentence.rstrip()
    # Left spaces
    tmp_sentence2 = sentence.lstrip()
    # Remove surrounding spaces
    res_sentence = u' '.join(sentence.split())
    # Check the differences
    if tmp_sentence1 != sentence:
        res_sentence = res_sentence + u' '
    if tmp_sentence2 != sentence:
        res_sentence = u' ' + res_sentence
    return res_sentence



def _rm_surrounding_format(segment_structure, keep_spaces=False):
    """This function returns a tuple of two elements. The first element is the
    new segment_structure, then a boolean that indicates whether the
    segment_structure changed.
    """
    first, last = segment_structure[0], segment_structure[-1]
    n = len(segment_structure)

    # Check there is at least one surrounding format to remove
    if n <= 1 or first[2] == TEXT_ID or first[2] != last[2]:
        return segment_structure

    # Make a copy
    segment_structure = list(segment_structure)

    # Remove surrounding format
    while n > 1 and first[2] != TEXT_ID and first[2] == last[2]:
        segment_structure.pop(0)
        segment_structure.pop()
        n -= 2
        # Next (check we did not reach the empty list)
        if n == 0:
            break
        first, last = segment_structure[0], segment_structure[-1]

    return segment_structure



def _rm_surrounding_spaces(segment_structure, keep_spaces=False):
    """This function returns a new segment_structure which no longer contains
    surrounding spaces.
    """
    n = len(segment_structure)
    first, last = segment_structure[0], segment_structure[-1]
    if keep_spaces is False and n > 1:
        # We remove all empty element which starts the structure
        empty = not first[1].strip()
        while empty:
            segment_structure.pop(0)
            first = segment_structure[0]
            empty = not first[1].strip()
        # We remove all empty element which finish the structure
        empty = not last[1].strip()
        while empty:
            segment_structure.pop()
            last = segment_structure[-1]
            empty = not last[1].strip()
    return segment_structure



def _get_surrounding_spaces(segment_structure, keep_spaces=False):
    """This function returns a new segment_structure which no longer contains
    surrounding spaces. In addition, the function also returns the number of
    spaces removed (at the beginning and the end of the structure)
    """
    start_index = 0
    end_index = -1
    nb_spaces_left = nb_spaces_right = 0
    first, last = segment_structure[0], segment_structure[-1]

    if keep_spaces is False and len(segment_structure) > 1:
        # We count all empty elements which starts the structure
        empty = not first[1].strip()
        while empty:
            nb_spaces_left += 1
            start_index += 1
            first = segment_structure[start_index]
            empty = not first[1].strip()
        # We count all empty elements which finish the structure
        empty = not last[1].strip()
        while empty:
            nb_spaces_right +=1
            end_index -= 1
            last = segment_structure[end_index]
            empty = not last[1].strip()
    segment_structure = _rm_surrounding_spaces(segment_structure, keep_spaces)
    return segment_structure, (nb_spaces_left, nb_spaces_right)



def _reinsert_spaces(segment_structure, spaces_positions):
    """Put spaces in the segment structure.
    'spaces_positions' is a tuple like (x, y). We insert x spaces at the
    beginning the list and y spaces at the end of the list.
    """
    if spaces_positions == (0,0):
        return segment_structure

    nb_start, nb_end = spaces_positions
    # Insert starting spaces
    for space_position in range(nb_start):
        segment_structure.insert(0, (TEXT, u' ', TEXT_ID))
    # Insert ending spaces
    for space_position in range(nb_end):
        segment_structure.append((TEXT, u' ', TEXT_ID))
    return segment_structure



def _reinsert_format(segment_structure, formats):
    """Re-inject formats into the segment_structure.
    'formats' is a tuple like (start_format, end_format).
    """
    start_format, end_format = formats
    #Make a copy
    segment_structure = segment_structure[:]
    segment_structure.insert(0, start_format)
    segment_structure.append(end_format)
    return segment_structure



def _reconstruct_message(segment_structure):
    """Take a segment_structure and rebuild a new Message object.
    """
    message = Message()
    for seg_struct in segment_structure:
        type, value, id  = seg_struct
        if type == TEXT:
            message.append_text(value)
        elif type == START_FORMAT:
            message.append_start_format(value)
        elif type == END_FORMAT:
            message.append_end_format(value)
    return message



def _reconstruct_segment(segment_structure, keep_spaces=False):
    """Take a segment_structure and rebuild a new segment (str).
    """
    segment = u''
    for seg_struct in segment_structure:
        segment += seg_struct[1]
    if keep_spaces is False:
        segment = segment.strip()
    return segment



def _translations_to_struct(translations):
    """Transform a translation string into a segment structure
    """
    seg_struct = translations
    is_string = isinstance(translations[0], (str, unicode))
    if translations and is_string:
        seg_struct = []
        for translation in translations:
            translation_tuple = (TEXT, translation, TEXT_ID)
            seg_struct.append(translation_tuple)
    return seg_struct



def _split_message(message, keep_spaces=False):
    """ We consider a sentence ends by an special puntuation character
    (dot, colon, semicolon, exclamation or question mark) followed by
    an space.

    Exceptions to this rule: abbreviations and accronyms.

    This method return a special structure. This is a list which each
    sub-list represent a segment. The sub-list contains tuples. Each tuples
    is an element that can be a format element (e.g. '<em>') or raw text
    with some others informations (type and id).
    for example, the message : Text. <text:span>Text2.</text:span>
    will give :

    [
      [(TEXT, "Text.", TEXT_ID)],
      [(START_FORMAT, '<text:span>', 1), (TEXT, 'Text2.', TEXT_ID),
       (END_FORMAT, </text:span>, 1)]
    ]

    In addition, the function add an offset for each segment, that say where to find the
    segment from the first line of the message.
    """

    format = 0
    sentence = []
    sub_sentence = []
    sentence_done = False
    last_word = None
    word_stop = True
    last_char = None
    sub_structure = []
    stack_id = []
    offset = 0
    line_offset = 0
    if message and message[0][1][0] == '\n':
        line_offset = 1

    for type, atom in message.get_atoms():
        if type == TEXT:
            if atom == '\n':
                if not _make_sentence(sub_sentence, True).strip():
                    line_offset = max(offset,line_offset)
                offset += 1
            sub_sentence.append(atom)
            if atom.isspace():
                word_stop = True
                # Sentence End
                sentence_done = _is_sentence_done(last_char, last_word)
                if sentence_done and not stack_id:
                    sub_structure.append(
                        (TEXT, _make_sentence(sub_sentence, keep_spaces),
                         TEXT_ID))
                    yield sub_structure, line_offset
                    line_offset = offset
                    sub_sentence = []
                    sub_structure = []
                    sentence_done = False
            elif atom.isalnum():
                if word_stop is True:
                    last_word = atom
                    word_stop = False
                else:
                    last_word += atom
            else:
                word_stop = True
            # Next
            last_char = atom
        elif type == START_FORMAT:
            format += 1
            stack_id.append(format)
            if sub_sentence:
                sub_structure.append(
                    (TEXT, _make_sentence(sub_sentence, keep_spaces),
                     TEXT_ID))
                sub_sentence = []
            id = format
            sub_structure.append((START_FORMAT, u''.join(atom), id))
        elif type == END_FORMAT:
            if sub_sentence:
                sub_structure.append(
                    (TEXT, _make_sentence(sub_sentence, keep_spaces),
                     TEXT_ID))
                sub_sentence = []
            id = stack_id.pop()
            sub_structure.append((END_FORMAT, u''.join(atom), id))
            if not stack_id and sentence_done is True:
                sentence_done = False
    # Send last sentence
    if sub_sentence:
        sub_structure.append(
            (TEXT, _make_sentence(sub_sentence, keep_spaces),
             TEXT_ID))
    if sub_structure:
        yield sub_structure, line_offset



def get_segments(message, keep_spaces=False):
    """This is a generator that iters over the message. First it segment
    the message and get back the corresponding segments. Then it remove the
    potentially surrounding format element from the segment. If there was
    surrounding format, recursion is used to process the last segment as if it
    was a new message. Indeed, there may be some new segments in this new
    message.
    """

    # Some alias
    _rm_spaces = _rm_surrounding_spaces
    _rm_format = _rm_surrounding_format
    for seg_struct, offset in _split_message(message, keep_spaces):
        # Remove pointless element (i.e. which don't need be show)
        seg_struct = _rm_spaces(seg_struct, keep_spaces)
        new_seg_struct = _rm_format(seg_struct, keep_spaces)
        # Check if the new structure has changed
        if new_seg_struct != seg_struct:
            # Process the segment as a message to get potentially sub-segments
            new_message = _reconstruct_message(new_seg_struct)
            for segment, new_offset in get_segments(new_message, keep_spaces):
                yield segment, offset + new_offset
        else:
            segment = _reconstruct_segment(seg_struct, keep_spaces)
            if segment:
                yield segment, offset



def translate_message(message, catalog, keep_spaces):
    """Translate a message (text which contains several segments)"""
    translation_dict = {}
    for segment, offset in get_segments(message, keep_spaces):
        translation = catalog.gettext(segment)
        translation_dict[segment] = translation
    translation = _translate_segments(message, translation_dict, keep_spaces)
    translation = list(translation)
    translation = u''.join(translation)
    return translation.encode('utf-8')



def _translate_segments(message, translation_dict, keep_spaces):
    """Do Translation segment by segment and use recursion to translate
    sub-segments if there is pointless format. translation_dict is a
    dictionnary which map segments to their translations.
    """
    # Some alias
    _rm_spaces = _get_surrounding_spaces
    _rm_format = _rm_surrounding_format
    for seg_struct, offset in _split_message(message, keep_spaces):
        # Remove spaces and store their position
        seg_struct, spaces_pos = _rm_spaces(seg_struct, keep_spaces)
        new_seg_struct = _rm_format(seg_struct, keep_spaces)
        # Check if the new segment has changed
        if new_seg_struct is seg_struct:
            segment = _reconstruct_segment(seg_struct, keep_spaces)
            if segment:
                raw_segment = _reconstruct_segment(seg_struct, True)
                translation = translation_dict[segment]
                translation = raw_segment.replace(segment, translation)
                yield translation
        else:
            # Simply remove surrounding format and store them
            start_format = seg_struct.pop(0)
            end_format = seg_struct.pop()
            # Process the new segment as a message for potentially sub-segments
            new_message = _reconstruct_message(seg_struct)
            seg_trans = \
                _translate_segments(new_message, translation_dict, keep_spaces)
            seg_trans = list(seg_trans)
            # We transform translation as string to the usually used structure
            seg_struct = _translations_to_struct(seg_trans)
            # Re-insert the previously removed formats and spaces
            seg_struct = \
                _reinsert_format(seg_struct, (start_format, end_format))
            seg_struct = _reinsert_spaces(seg_struct, spaces_pos)
            translation = _reconstruct_segment(seg_struct, True)
            yield translation



class Message(list):
    """A 'Message' object represents a text to be processed. It is a complex
    object instead of just an string to allow us to deal with formatted text.

    A message is made of atoms, an atom is a unit that can not be splitted.
    It is either a letter or an object that represents a formatted block,
    like an xml node (e.g. '<em>hello world</em>').
    """

    def append_text(self, text):
        """The parameter "text" must be a unicode string.
        """
        # Append
        if self and (self[-1][0] == TEXT):
            self[-1] = TEXT, self[-1][1] + text
        else:
            list.append(self, (TEXT, text))


    def append_start_format(self, x):
        list.append(self, (START_FORMAT, x))


    def append_end_format(self, x):
        list.append(self, (END_FORMAT, x))


    def get_atoms(self):
        """This is a generator that iters over the message and returns each
        time an atom.
        """
        for type, value in self:
            if type == TEXT:
                for letter in value:
                    yield TEXT, letter
            else:
                yield type, value


