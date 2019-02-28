# -*- coding: UTF-8 -*-
# Copyright (C) 2007, 2011-2012 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2008-2009 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2010 Norman Khine <khinester@aqoon.local>
# Copyright (C) 2011 Henry Obein <henry.obein@gmail.com>
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

# Import from the Standard Library
import unicodedata



src = (ur"""ÄÅÁÀÂÃĀäåáàâãāăÇçÉÈÊËĒéèêëēğÍÌÎÏĪíìîïīıļÑñÖÓÒÔÕØŌöóòôõøōőÜÚÙÛŪüúùûū"""
       ur"""ŞşšţÝŸȲýÿȳŽž°«»’""")
dst = (ur"""AAAAAAAaaaaaaaaCcEEEEEeeeeegIIIIIiiiiiilNnOOOOOOOooooooooUUUUUuuuuu"""
       ur"""SsstYYYyyyZz----""")

transmap = {}
for i in range(len(src)):
    a, b = src[i], dst[i]
    transmap[ord(a)] = b
transmap[ord(u'æ')] = u'ae'
transmap[ord(u'Æ')] = u'AE'
transmap[ord(u'œ')] = u'oe'
transmap[ord(u'Œ')] = u'OE'
transmap[ord(u'ß')] = u'ss'


def checkid(id, soft=True):
    """Turn a bytestring or unicode into an identifier only composed of
    alphanumerical characters and a limited list of signs.

    It only supports Latin-based alphabets.
    """
    if type(id) is str:
        id = unicode(id, 'utf8')

    # Normalize unicode
    id = unicodedata.normalize('NFKC', id)

    # Strip diacritics
    id = id.strip().translate(transmap)

    # Check for unallowed characters
    if soft:
        allowed_characters = set([u'.', u'-', u'_', u'@'])
        id = [ x if (x.isalnum() or x in allowed_characters) else u'-'
               for x in id ]
        id = u''.join(id)

    # Merge hyphens
    id = id.split(u'-')
    id = u'-'.join([x for x in id if x])
    id = id.strip('-')

    # Check wether the id is empty
    if len(id) == 0:
        return None

    # No mixed case
    id = id.lower()
    # Most FS are limited in 255 chars per name
    # (keep space for ".metadata" extension)
    id = id[:246]
    # Return a safe ASCII bytestring
    return str(id)
