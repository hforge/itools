# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004 Thierry Fromon <from.t@free.fr>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA


keeping_punctuation = [ u'¡', u'¿']
rubbish_punctuation = [u'.', u',', u';', u'?', '!', u"'", u'"']

French_base = [u'que', u"qu'", u'à', u'le', u'les', u'du', u'de', u'un',u'une',
               u'des', u'je', u'tu', u'il', u'ils', u'vous', u'elle', u'elles',
               u'nous', u'mais', u'où',  u'et', u'donc', u'est' u'aux']
French_char = [u'ê', u'ç', ]

Deutch_base = []
Deutch_char = [u'ß', u'ä', u'ü', u'ö']

Spanish_base = [u'como',u'de', u'del', u'una', u'al', u'el', u'está' u'los',
                u'por',
                u'es', u'con', u'o', u'su'] + keeping_punctuation
Spainish_char = [u'ó', u'ú', u'í', u'ñ']

English_base = [u'but', u'of', u'no', u'on', u'their', u'as', u'this',
                u'an', u'when', u'where'  u'as', u'and', u'or', u'that',
                u'the', u'to', u'in', u'i',u'you', u'it', u'he', u'she',
                u'your', u'are', u'is', 's', u'from' ]
English_char = []


language = (('French', French_base, French_char),
            ('Deutch', Deutch_base, Deutch_char),
            ('Spanish', Spanish_base, Spainish_char),
            ('English', English_base, English_char))


class Char(object):
    def __init__(self, language, lexeme=''):
        self.language = language
        self.lexeme = lexeme


class StatSpecialChar(Char):
    def __init__(self, text):
        self.text = text.upper().swapcase()


    def stat_special_char(self):
        """
        return percent of special char for specific language
        """
        stat = {}
        for lang in language:
            n  = 0
            for special_char in lang[2]:
                n = n + self.text.count(special_char)
            if len(self.text) != 0:
                percent = (n*4000)/len(self.text)
                percent = min (100, percent)
            else:
                percent = 0
            stat[lang[0]] = percent
        return stat


class Token(object):
    def __init__(self, id, lexeme=''):
        self.id = id
        self.lexeme = lexeme



class Select_token(Token):
    def __init__(self, text):
        self.text = text
        for i in rubbish_punctuation:
            self.text = self.text.replace(i , ' ')
        for i in keeping_punctuation:
            self.text = self.text.replace(i , ' '+i+' ')
        self.index = 0


    def get_token(self):
        """
        return only word with latin char or keeping_punctuation 
        """
        lexeme, token = '', ''
        if self.index == len(self.text):
            return Token('EOF', '')
        while self.index < len(self.text):
            c = self.text[self.index]
            self.index += 1
            lexeme = lexeme + c
            if c == ' ' or self.index == len(self.text):
                token = lexeme.upper().swapcase()
                return Token('word', token)
            if not(c.isalpha() or c in keeping_punctuation):
                lexeme , token = '', ''


    def compare(self):
        """
        return percent of word for specific language
        """
        token =self.get_token()
        stat = {}
        for lang in language:
             slang = lang[0]
             stat[slang] = 0
        number_word = 0
        while token.id != 'EOF':
            if token.lexeme not in ['', ' ']:
                token_word  = token.lexeme.strip()
                number_word = number_word + 1
                for lang in language:
                    slang = lang[0] 
                    if token_word in lang[1]:
                        stat[slang] = stat[slang] + 1
            token = self.get_token()
        for lang in language:
            slang = lang[0]
            if number_word != 0:
                percent = (stat[slang]*200)/number_word
                percent = min (100, percent)
            else:
                percent = 0
            stat[slang] = percent
        return stat


class Language(object):
    def __init__(self, text):
        self.text = text


    def percent(self):
        """
        return with percent the tow early language
        """
        first_percent, second_percent = 0, 0
        first_lang, second_lang = '', ''
        word = Select_token(self.text)
        char = StatSpecialChar(self.text)
        words = word.compare()
        chars = char.stat_special_char()
        for lang in language:
            slang = lang[0]
            if len(self.text) < 75:
                 percent = min(words[slang] + chars[slang], 99)
            elif len(self.text) < 500:
                percent = min(1.2*words[slang] + 2*chars[slang], 99)
            else:
                percent = min(1.6*words[slang] + 4*chars[slang], 99)
            #print (slang, words[slang], chars[slang])
            if percent > first_percent:
                second_percent, second_lang = first_percent, first_lang 
                first_percent, first_lang = percent, slang
            elif percent > second_percent:
                second_percent, second_lang = percent, slang
        return ((first_lang, int(first_percent)),
                (second_lang, int(second_percent)))


