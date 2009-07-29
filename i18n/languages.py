# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


languages = {
    'aa': u'Afar',
    'ab': u'Abkhazian',
    'af': u'Afrikaans',
    'am': u'Amharic',
    'ar': u'Arabic',
    'as': u'Assamese',
    'ay': u'Aymara',
    'az': u'Azerbaijani',
    'ba': u'Bashkir',
    'be': u'Belarusian',
    'bg': u'Bulgarian',
    'bh': u'Bihari',
    'bi': u'Bislama',
    'bn': u'Bengali',
    'bo': u'Tibetan',
    'br': u'Breton',
    'bs': u'Bosnian',
    'ca': u'Catalan',
    'co': u'Corsican',
    'cs': u'Czech',
    'cy': u'Welsh',
    'da': u'Danish',
    'de': u'German',
    'de-AU': u'German/Austria',
    'de-DE': u'German/Germany',
    'de-CH': u'German/Switzerland',
    'dz': u'Bhutani',
    'el': u'Greek',
    'en': u'English',
    'en-GB': u'English/United Kingdom',
    'en-US': u'English/United States',
    'eo': u'Esperanto',
    'es': u'Spanish',
    'es-AR': u'Spanish/Argentina',
    'es-CO': u'Spanish/Colombia',
    'es-MX': u'Spanish/Mexico',
    'es-ES': u'Spanish/Spain',
    'et': u'Estonian',
    'eu': u'Basque',
    'fa': u'Persian',
    'fi': u'Finnish',
    'fj': u'Fiji',
    'fo': u'Faroese',
    'fr': u'French',
    'fr-BE': u'French/Belgium',
    'fr-CA': u'French/Canada',
    'fr-FR': u'French/France',
    'fr-CH': u'French/Switzerland',
    'fy': u'Frisian',
    'ga': u'Irish',
    'gd': u'Scots Gaelic',
    'gl': u'Galician',
    'gn': u'Guarani',
    'gu': u'Gujarati',
    'ha': u'Hausa',
    'he': u'Hebrew',
    'hi': u'Hindi',
    'hr': u'Croatian',
    'hu': u'Hungarian',
    'hy': u'Armenian',
    'ia': u'Interlingua',
    'id': u'Indonesian',
    'ie': u'Interlingue',
    'ik': u'Inupiak',
    'is': u'Icelandic',
    'it': u'Italian',
    'iu': u'Inuktitut',
    'ja': u'Japanese',
    'jw': u'Javanese',
    'ka': u'Georgian',
    'kk': u'Kazakh',
    'kl': u'Greenlandic',
    'km': u'Cambodian',
    'kn': u'Kannada',
    'ko': u'Korean',
    'ks': u'Kashmiri',
    'ku': u'Kurdish',
    'kw': u'Cornish',
    'ky': u'Kirghiz',
    'la': u'Latin',
    'lb': u'Luxembourgish',
    'ln': u'Lingala',
    'lo': u'Laothian',
    'lt': u'Lithuanian',
    'lv': u'Latvian',
    'mg': u'Malagasy',
    'mi': u'Maori',
    'mk': u'Macedonian',
    'ml': u'Malayalam',
    'mn': u'Mongolian',
    'mo': u'Moldavian',
    'mr': u'Marathi',
    'ms': u'Malay',
    'mt': u'Maltese',
    'my': u'Burmese',
    'na': u'Nauru',
    'ne': u'Nepali',
    'nl': u'Dutch',
    'nl-BE': u'Dutch/Belgium',
    'no': u'Norwegian',
    'oc': u'Occitan',
    'om': u'Oromo',
    'or': u'Oriya',
    'pa': u'Punjabi',
    'pl': u'Polish',
    'ps': u'Pashto',
    'pt': u'Portuguese',
    'pt-BR': u'Portuguese/Brazil',
    'qu': u'Quechua',
    'rm': u'Rhaeto-Romance',
    'rn': u'Kirundi',
    'ro': u'Romanian',
    'ru': u'Russian',
    'rw': u'Kinyarwanda',
    'sa': u'Sanskrit',
    'sd': u'Sindhi',
    'se': u'Northern Saami',
    'sg': u'Sangho',
    'sh': u'Serbo-Croatian',
    'si': u'Sinhalese',
    'sk': u'Slovak',
    'sl': u'Slovenian',
    'sm': u'Samoan',
    'sn': u'Shona',
    'so': u'Somali',
    'sq': u'Albanian',
    'sr': u'Serbian',
    'ss': u'Siswati',
    'st': u'Sesotho',
    'su': u'Sundanese',
    'sv': u'Swedish',
    'sw': u'Swahili',
    'ta': u'Tamil',
    'te': u'Telugu',
    'tg': u'Tajik',
    'th': u'Thai',
    'ti': u'Tigrinya',
    'tk': u'Turkmen',
    'tl': u'Tagalog',
    'tn': u'Setswana',
    'to': u'Tonga',
    'tr': u'Turkish',
    'ts': u'Tsonga',
    'tt': u'Tatar',
    'tw': u'Twi',
    'ug': u'Uighur',
    'uk': u'Ukrainian',
    'ur': u'Urdu',
    'uz': u'Uzbek',
    'vi': u'Vietnamese',
    'vo': u'Volapuk',
    'wo': u'Wolof',
    'xh': u'Xhosa',
    'yi': u'Yiddish',
    'yo': u'Yoruba',
    'za': u'Zhuang',
    'zh': u'Chinese',
    'zh-CN': u'Chinese/China',
    'zh-TW': u'Chinese/Taiwan',
    'zu': u'Zulu',
    }


langs = [ {'code': x, 'name': languages[x]} for x in sorted(languages.keys()) ]


###########################################################################
# API
###########################################################################
def has_language(code):
    return code in languages


def get_languages():
    """Returns a list of tuples with the code and the name of each language.
    """
    return [ x.copy() for x in langs ]



def get_language_name(code):
    """Returns the name of a language.
    """
    # FIXME The value returned should be a MSG object, but the MSG class comes
    # from the itools.gettext module, which is higher level than itools.i18n
    if code in languages:
        return languages[code]
    return u'???'

