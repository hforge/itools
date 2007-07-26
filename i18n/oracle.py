# -*- coding: UTF-8 -*-
# Copyright (C) 2004 Thierry Fromon  <from.t@free.fr>
# Copyright (C) 2004, 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

###########################################################################
# To add a new language, edit the dictionaries below:
# 
#   - positive_chars
# 
#     Defines special characters (like accentuated characters) that belong
#     to the language.
# 
#   - negative_chars
# 
#     Defines special characters (like accentuated characters) that do not
#     belong to the language.
# 
#   - positive_words
# 
#     Defines common words that belong to the language.
# 
#   - negative_words
# 
#     Defines some words that do not belong to the language.
###########################################################################
positive_chars = {
    u'¡': ['es'],
    u'¿': ['es'],
    u'ä': ['de'],
    u'ß': ['de'],
    u'ç': ['fr'],
    u'ê': ['fr'],
    u'í': ['es'],
    u'ñ': ['es'],
    u'ö': ['de'],
    u'ó': ['es'],
    u'ü': ['de'],
    u'ú': ['es'],
}

negative_chars = {}


positive_words = {
    u'à': ['fr'],
    u'al': ['es'],
    u'an': ['en'],
    u'and': ['en'],
    u'are': ['en'],
    u'as': ['en'],
    u'aux': ['fr'],
    u'but': ['en'],
    u'como': ['es'],
    u'con': ['es'],
    u'de': ['es', 'fr'],
    u'del': ['es'],
    u'des': ['fr'],
    u'donc': ['fr'],
    u'du': ['fr'],
    u'el': ['es'],
    u'elle': ['fr'],
    u'elles': ['fr'],
    u'es': ['es'],
    u'est': ['fr'],
    u'está': ['es'],
    u'et': ['fr'],
    u'from': ['en'],
    u'hay': ['es'],
    u'he': ['en', 'es'],
    u'i': ['en'],
    u'il': ['fr'],
    u'ils': ['fr'],
    u'in': ['en'],
    u'is': ['en'],
    u'it': ['en'],
    u'je': ['fr'],
    u'las': ['es'],
    u'le': ['es', 'fr'],
    u'lo': ['es'],
    u'les': ['es', 'fr'],
    u'los': ['es'],
    u'mais': ['fr'],
    u'no': ['en', 'es'],
    u'nous': ['fr'],
    u'nueva': ['es'],
    u'o': ['es'],
    u'of': ['en'],
    u'on': ['en'],
    u'or': ['en'],
    u'où': ['fr'],
    u'para': ['es'],
    u'pero': ['es'],
    u'por': ['es'],
    u'que': ['es', 'fr'],
    u'qué': ['es'],
    u'she': ['en'],
    u'su': ['es'],
    u'sur': ['fr'],
    u'that': ['en'],
    u'the': ['en'],
    u'their': ['en'],
    u'this': ['en'],
    u'to': ['en'],
    u'tu': ['es', 'fr'],
    u'un': ['es', 'fr'],
    u'una': ['es'],
    u'une': ['fr'],
    u'vous': ['fr'],
    u'when': ['en'],
    u'where': ['en'],
    u'y': ['es'],
    u'you': ['en'],
    u'your': ['en'],
}


negative_words = {
    u'du': ['es'],
}


# One thousand words should be enough
MAX_WORDS = 1000


###########################################################################
# The Code
###########################################################################
def guess_language(text):
    chars = {}
    words = {}

    # Number of chars and words analyzed
    n_chars = 0
    n_words = 0

    # Look for special chars and words in the given text
    word = u''
    for c in text:
        n_chars += 1
        c = c.lower()
        # Characters
        for language in positive_chars.get(c, []):
            chars.setdefault(language, 0)
            chars[language] += 1
        for language in negative_chars.get(c, []):
            chars.setdefault(language, 0)
            chars[language] -= 2
        # Words
        if c.isalpha():
            word += c
        elif word:
            for language in positive_words.get(word, []):
                words.setdefault(language, 0)
                words[language] += 1
            for language in negative_words.get(word, []):
                words.setdefault(language, 0)
                words[language] -= 2
            word = u''
            # Check limit
            n_words += 1
            if n_words >= MAX_WORDS:
                break

    # If we found nothing...
    if not chars and not words:
        return None

    # Depending on the length of the text, the weight given to chars and
    # words changes. The minimum distance between two languages too.
    if n_chars < 75:
        w_weight, c_weight, distance = 1.0, 1.0, 1.0
    elif n_chars < 500:
        w_weight, c_weight, distance = 1.2, 2.0, 2.0
    else:
        w_weight, c_weight, distance = 1.6, 4.0, 4.0

    # Calculate the chances the text is written in any language.
    languages = []
    for lang in set(chars.keys()) | set(words.keys()):
        p = w_weight*words.get(lang, 0) + c_weight*chars.get(lang, 0)
        languages.append((p, lang))
    languages.sort()

    # Pick the most probable language, unless the distance to the second is
    # too small.
    n = len(languages)
    if n == 0:
        return None
    if n == 1:
        return languages[0][1]
    if languages[-1][0] - languages[-2][0] >= distance:
        return languages[-1][1]
     
    return None

