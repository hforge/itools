# -*- coding: UTF-8 -*-
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA


stop_sentences = set([u'.', u';', u'!', u'?', u':'])
abbreviations = set([u'Inc', u'Md', u'Mr', u'Dr'])


TEXT, START_FORMAT, END_FORMAT = range(3)


def is_sentence_done(last_char, last_word):
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



def make_sentence(sentence):
    sentence = u''.join(sentence)
    sentence = u' '.join(sentence.split()) # Strip
    return sentence



class Message(list):
    """
    A 'Message' object represents a text to be processed. It is a complex
    object instead of just an string to allow us to deal with formatted text.

    A message is made of atoms, an atom is a unit that can not be splitted.
    It is either a letter or an object that represents a formatted block,
    like an xml node (e.g. '<em>hello world</em>').
    """

    def __init__(self):
        list.__init__(self)


    def append_text(self, text):
        """
        The parameter "text" must be a unicode string.
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
        """
        This is a generator that iters over the message and returns each
        time an atom.
        """
        for type, value in self:
            if type == TEXT:
                for letter in value:
                    yield TEXT, letter
            else:
                yield type, value


    def get_segments(self, keep_spaces=None):
        """
        We consider a sentence ends by an special puntuation character
        (dot, colon, semicolon, exclamation or question mark) followed by
        an space.

        Exceptions to this rule: abbreviations and accronyms.
        """
        # FIXME keep_spaces is not used, so remove it
        format = 0
        sentence = []
        sentence_done = False
        last_word = None
        word_stop = True
        last_char = None
        for type, atom in self.get_atoms():
            sentence.append(atom)
            if type == TEXT:
                if atom.isspace():
                    word_stop = True
                    # Sentence End
                    if is_sentence_done(last_char, last_word):
                        if format == 0:
                            yield make_sentence(sentence)
                            sentence = []
                            sentence_done = False
                        else:
                            sentence_done = True
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
            elif type == END_FORMAT:
                format -= 1
                if format == 0 and sentence_done is True:
                    yield make_sentence(sentence)
                    sentence = []
                    sentence_done = False

        # Send last sentence
        sentence = make_sentence(sentence)
        if sentence:
            yield sentence

