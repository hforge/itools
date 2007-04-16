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
stop_sentences =[u'.', u';', u':', u'!', u'?']
abbreviations = [u'Inc', u'Md', u'Mr', u'Dr']


TEXT, FORMAT = range(2)



class Message(list):
    """
    A 'Message' object represents a text to be processed. It is a complex
    object instead of just an string to allow us to deal with formatted text.

    A message is made of atoms, an atom is a unit that can not be splitted.
    It is either a letter or an object that represents a formatted block,
    like an xml node (e.g. '<em>hello world</em>').
    """

    def __init__(self, x=[]):
        # Coerce str to unicode
        if isinstance(x, str):
            x = unicode(x)
        # Initialize
        if isinstance(x, unicode):
            list.__init__(self)
            self.append_text(x)
        else:
            list.__init__(self, x)


    def append_text(self, x):
        # Coerce str to unicode
        if isinstance(x, str):
            x = unicode(x)
        # Append
        list.append(self, (TEXT, x))


    def append_format(self, x):
        list.append(self, (FORMAT, x))


    def normalize(self):
        """
        Concatenates adjacent text nodes.
        """
        i = 0
        while i < len(self) - 1:
            this, next = self[i], self[i+1]
            if this[0] == TEXT and next[0] == TEXT:
                self[i] = (TEXT, this[1] + next[1])
                del self[i+1]
            else:
                i = i + 1


    def lstrip(self):
        """Left strip"""
        if len(self) == 0:
            return ''
        type, value = self[0]
        if type == TEXT and value.strip() == u'':
            del self[0]
        return value


    def rstrip(self):
        """Right strip"""
        if len(self) == 0:
            return ''
        type, value = self[-1]
        if type == TEXT and value.strip() == u'':
            del self[-1]
        return value


    def has_text_to_translate(self):
        for type, value in self:
            if type == TEXT:
                if value.strip():
                    return True
        return False


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


    def get_words(self):
        """
        This is a lexical analyzer that explits the message in words, spaces,
        stop words and stop sentences. It is a generator.

        It is a four state automaton:

        trans. atom            yield
        ====== ====            ============
        0 -> 0 [stop word]     stop word
        0 -> 1 [space]
        0 -> 2 [alpha-numeric]
        0 -> 3 [stop sentence]
        1 -> 0 [stop word]     space, stop word
        1 -> 1 [space]
        1 -> 2 [alpha-numeric] space
        1 -> 3 [stop sentence] space
        2 -> 0 [stop word]     word, stop word
        2 -> 1 [space]         word
        2 -> 2 [alpha-numeric]
        2 -> 3 [stop-sentence] word
        3 -> 0 [stop word]     stop sentence, stop word
        3 -> 1 [space]         stop sentence
        3 -> 2 [alpha-numeric] stop sentence
        3 -> 3 [stop-sentence]

        By an 'stop word' we understand anything that is not an space, nor
        an alpha-numeric character, nor an 'stop-sentence'.

        An 'stop-sentence' is a sequence of the characters '.', ';', ':',
        '?' and '!', followed by an space. Except when it is just a '.' and
        it is preceeded by an abbreviation (a word like Mr or Inc).

        The local variables used are:

         - token: keeps the previous token (to check for abbreviattions, we
           need to remember the last token)

         - state: the automaton state

         - lexeme: the token's lexeme
        """
        token = None
        state, lexeme = 0, u''
        for type, atom in self.get_atoms():
            if state == 0:
                if type == TEXT:
                    if atom.isspace():
                        state, lexeme = 1, atom
                    elif atom.isalnum():
                        state, lexeme = 2, atom
                    elif atom in stop_sentences:
                        state, lexeme = 3, atom
                    else:
                        token = STOP_WORD, atom
                        yield token
                else:
                    state, lexeme = 2, atom
            elif state == 1:
                if type == TEXT:
                    if atom.isspace():
                        lexeme += atom
                    elif atom.isalnum():
                        token = SPACE, lexeme
                        yield token
                        state, lexeme = 2, atom
                    elif atom in stop_sentences:
                        token = SPACE, lexeme
                        yield token
                        state, lexeme = 3, atom
                    else:
                        yield SPACE, lexeme
                        token = STOP_WORD, atom
                        yield token
                        state, lexeme = 0, ''
                else:
                    token = SPACE, lexeme
                    yield token
                    state, lexeme = 2, atom
            elif state == 2:
                if type == TEXT:
                    if atom.isspace():
                        token = WORD, lexeme
                        yield token
                        state, lexeme = 1, atom
                    elif atom.isalnum():
                        lexeme += atom
                    elif atom in stop_sentences:
                        token = WORD, lexeme
                        yield token
                        state, lexeme = 3, atom
                    else:
                        yield WORD, lexeme
                        token = STOP_WORD, atom
                        yield token
                        state, lexeme = 0, ''
                else:
                    lexeme += atom
            elif state == 3:
                if type == TEXT:
                    if atom.isspace():
                        if lexeme == '.':
                            if token is None \
                               or len(token[1]) == 1 \
                               or token[1] in abbreviations:
                                token = WORD, lexeme
                                yield token
                            else:
                                token = STOP_SENTENCE, lexeme
                                yield token
                        else:
                            token = STOP_SENTENCE, lexeme
                            yield token
                        state, lexeme = 1, atom
                    elif atom.isalnum():
                        lexeme += atom
                        state = 2
                    elif atom in stop_sentences:
                        lexeme += atom
                    else:
                        yield WORD, lexeme
                        token = STOP_WORD, atom
                        yield token
                        state, lexeme = 0, u''
                else:
                    lexeme += atom
                    state = 2

        if state == 1:
            yield SPACE, lexeme
        elif state == 2:
            yield WORD, lexeme
        elif state == 3:
            yield STOP_SENTENCE, lexeme


    def get_segments(self, keep_spaces=False):
        """
        This is the syntactical analyser that splits the message in segments
        (sentences). It is a generator.
        """
        state = 0
        sentence = u''
        for token_id, lexeme in self.get_words():
            if keep_spaces is False and token_id == SPACE:
                lexeme = ' '
            sentence += lexeme
            if token_id == STOP_SENTENCE:
                if keep_spaces is False:
                    sentence = sentence.strip()
                yield sentence
                sentence = u''
        if keep_spaces is False:
            sentence = sentence.strip()
        if sentence:
            yield sentence
