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
    """Make a sentence normalizing whitespaces or, if keep_spaces is True; a
    sentence as raw text.
    """
    if keep_spaces:
        return u''.join(sentence)
    sentence = u''.join(sentence)
    tmp_sentence1 = sentence.rstrip()
    tmp_sentence2 = sentence.lstrip()
    res_sentence = u' '.join(sentence.split()) # Strip
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

    new_segment_structure = segment_structure
    if segment_structure[0][2] == segment_structure[-1][2] and \
       segment_structure[0][2] != TEXT_ID and len(new_segment_structure) > 1:
        new_segment_structure = list(segment_structure)
        while len(new_segment_structure) > 1 and \
              new_segment_structure[0][2] == new_segment_structure[-1][2] and \
              new_segment_structure[0][2] != TEXT_ID:
            new_segment_structure.pop(0)
            new_segment_structure.pop()
    return new_segment_structure



def _rm_surrounding_spaces(segment_structure, keep_spaces=False):
    """This function returns a new segment_structure which no longer contains
    surrounding spaces.
    """
    if keep_spaces is False and len(segment_structure) > 1:
        # We remove all empty element which starts the structure
        while not segment_structure[0][1].strip():
            segment_structure.pop(0)
        # We remove all empty element which finish the structure
        while not segment_structure[-1][1].strip():
            segment_structure.pop()
    return segment_structure



def _get_surrounding_spaces(segment_structure, keep_spaces=False):
    """This function returns a new segment_structure which no longer contains
    surrounding spaces.
    """
    start_index = 0
    end_index = -1
    nb_spaces_left = 0
    nb_spaces_right = 0
    if keep_spaces is False and len(segment_structure) > 1:
        # We remove all empty element which starts the structure
        while not segment_structure[start_index][1].strip():
            nb_spaces_left += 1
            start_index += 1
        # We remove all empty element which finish the structure
        while not segment_structure[end_index][1].strip():
            nb_spaces_right +=1
            end_index -= 1
    segment_structure = _rm_surrounding_spaces(segment_structure, keep_spaces)
    return segment_structure, (nb_spaces_left, nb_spaces_right)



def _reinsert_spaces(segment_structure, spaces_positions):
    """Put spaces in the segment structure.
    'spaces_positions' is a tuple like (x, y). We insert x spaces in front of
    the list and y spaces at the end of the list.
    """
    for space_position in range(spaces_positions[0]):
        segment_structure.insert(0, (TEXT, u' ', TEXT_ID))
    for space_position in range(spaces_positions[1]):
        segment_structure.append((TEXT, u' ', TEXT_ID))
    return segment_structure



def _reinsert_format(segment_structure, formats):
    """Re-inject formats into the segment_structure.
    'formats' is a tuple like (start_format, end_format).
    """
    segment_structure.insert(0, formats[0])
    segment_structure.append(formats[1])
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
    if segment_translations and type(segment_translations[0]) is str:
        seg_struct = []
        for translation in segment_translations:
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
    surrounding format, the generator reiterates on the segment as if it
    was a new message. Indeed, there may be some new segments in this new
    message.
    """

    for segment_structure, line_offset in _split_message(message, keep_spaces):
        segment_structure = \
            _rm_surrounding_spaces(segment_structure, keep_spaces)
        new_seg_struct = \
            _rm_surrounding_format(segment_structure, keep_spaces)
        if new_seg_struct != segment_structure:
            new_message = _reconstruct_message(new_seg_struct)
            for segment, new_offset in get_segments(new_message, keep_spaces):
                yield segment, line_offset + new_offset
        else:
            segment = _reconstruct_segment(segment_structure,
                                           keep_spaces)
            if segment:
                yield segment, line_offset



def translate_message(message, catalog, keep_spaces):
    """Returns translation's segments.
    segment_dict is a dictionnary which map segments to their corresponding
    translation. This method is recursive.
    """
    translation_dict = {}
    for segment, line_offset in get_segments(message, keep_spaces):
        segment_translation = catalog.gettext(segment)
        translation_dict[segment] = segment_translation

    translation = _translate_segments(message, translation_dict, keep_spaces)
    translation = list(translation)
    translation = u''.join(translation)

    return translation.encode('utf-8')



def _translate_segments(message, translation_dict, keep_spaces):
    for seg_struct, line_offset in _split_message(message, keep_spaces):
        seg_struct, spaces_pos = \
            _get_surrounding_spaces(seg_struct, keep_spaces)
        new_seg_struct = _rm_surrounding_format(seg_struct, keep_spaces)
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
            segment_translations = \
                _translate_segments(new_message, translation_dict, keep_spaces)
            segment_translations = list(segment_translations)
            seg_struct = _translation_to_struct(segment_translations)
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


