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


src = (r"""ÄÅÁÀÂÃĀäåáàâãāăČÇçÉÈÊËĒéèėêëēğÍÌÎÏĪíìîïīıļÑñÖÓÒÔÕØŌöóòôõøōőÜÚÙÛŪüúùûū"""
       r"""ŞşšţÝŸȲýÿȳŽž°«»’""")
dst = (r"""AAAAAAAaaaaaaaaCCcEEEEEeeeeeegIIIIIiiiiiilNnOOOOOOOooooooooUUUUUuuuuu"""
       r"""SsstYYYyyyZz----""")

transmap = {}
for i in range(len(src)):
    a, b = src[i], dst[i]
    transmap[ord(a)] = b
transmap[ord('æ')] = 'ae'
transmap[ord('Æ')] = 'AE'
transmap[ord('œ')] = 'oe'
transmap[ord('Œ')] = 'OE'
transmap[ord('ß')] = 'ss'


def checkid(_id, soft=True):
    """Turn a bytestring or unicode into an identifier only composed of
    alphanumerical characters and a limited list of signs.

    It only supports Latin-based alphabets.
    """
    if type(_id) is str:
        _id = _id

    # Normalize unicode
    _id = unicodedata.normalize('NFKC', _id)

    # Strip diacritics
    _id = _id.strip().translate(transmap)

    # Check for unallowed characters
    if soft:
        allowed_characters = {'.', '-', '_', '@'}
        _id = [ x if (x.isalnum() or x in allowed_characters) else '-'
               for x in _id]
        _id = ''.join(_id)

    # Merge hyphens
    _id = _id.split('-')
    _id = '-'.join([x for x in _id if x])
    _id = _id.strip('-')

    # Check wether the _id is empty
    if len(_id) == 0:
        return None

    # No mixed case
    _id = _id.lower()
    # Most FS are limited in 255 chars per name
    # (keep space for ".metadata" extension)
    _id = _id[:246]
    # Return a safe ASCII bytestring
    return str(_id)
