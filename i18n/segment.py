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


WORD, SPACE, STOP_WORD, STOP_SENTENCE = range(4)
stop_sentences = set([u'.', u';', u'!', u'?'])
abbreviations = set([u'Inc', u'Md', u'Mr', u'Dr'])


TEXT, FORMAT = range(2)



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


    def append_text(self, x):
        # Coerce str to unicode
        if isinstance(x, str):
            x = unicode(x)
        # Append
        if self and (self[-1][0] == TEXT):
            self[-1] = TEXT, self[-1][1] + x
        else:
            list.append(self, (TEXT, x))


    def append_format(self, x):
        list.append(self, (FORMAT, x))


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
        (dot, semicolon, exclamation or question mark) followed by an
        space.

        Exceptions to this rule: abbreviations and accronyms.
        """
        # FIXME keep_spaces is not used, so remove it
        sentence = []
        word = None
        word_stop = True
        last = None
        for type, atom in self.get_atoms():
            sentence.append(atom)
            if type == TEXT:
                if atom.isspace():
                    word_stop = True
                    # Stop Sentence
                    if last in stop_sentences:
                        # Consider exceptions (accronyms and abbreviations)
                        if last == u'.':
                            if len(word) == 1 and word.isupper():
                                continue
                            if word in abbreviations:
                                continue
                        # Send sentence
                        sentence = u''.join(sentence)
                        sentence = u' '.join(sentence.split()) # Strip
                        yield sentence
                        sentence = []
                elif atom.isalnum():
                    if word_stop is True:
                        word = atom
                        word_stop = False
                    else:
                        word += atom
                else:
                    word_stop = True
                # Next
                last = atom
            elif type == FORMAT:
                pass

        # Send laste sentence
        sentence = u''.join(sentence)
        sentence = u' '.join(sentence.split()) # Strip
        if sentence:
            yield sentence

