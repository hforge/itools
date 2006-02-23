# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


# Import from Python
import datetime
import struct
import sys


"""
This module provides the serialization routines that allow to read and
write values from and to the resources.

For every type of value there are two functions, encode_<type> and
decode_<type>. The first one (encode) takes a value and returns the
byte string that represents it, the second one (decode) takes a byte
string and returns the value it represents.

Most of the values are of fixed size (byte, uint32, link, etc.), though
some are variable length (vints and strings). The decode functions behave
differently wether the value the decode is fixed or variable length. If
it is fixed length the given byte string must match the length of the
type. If it is variable length the given string may contain other values
after the requested one, hence the decode function returns a two elements
tuple, where the first element is the decoded value and the second one
is the data that remains and does not belong to the value.
"""


def encode_byte(value):
    return chr(value)


def decode_byte(data):
    return ord(data)


def encode_uint32(value):
    return struct.pack('>I', value)


def decode_uint32(data):
    return int(struct.unpack('>I', data)[0])


# Variable legth integers. Example
#
#   9831 = 0010 0110 0110 0111
#
# (1) Split by groups of seven bits:
#
#   00 1001100 1100111
#
# (2) Remove the left group if zero:
#
#   1001100 1100111
#
# (3) Fill bytes with a zero for the first one, 1 for the rest:
#
#   01001100 11100111
#   ^        ^
#
# (4) Swap order:
#
#   11100111 01001100
#   ^        ^
#
# This is to say, the first bit says wether there is or not a byte after.

def encode_vint(value):
    if value == 0:
        return '\x00'
    bytes = []
    while value:
        byte = value & 127
        bytes.append(byte)
        value = value >> 7
    data = ''
    for byte in bytes[:-1]:
        data += chr(byte | 128)
    return data + chr(bytes[-1])


def decode_vint(data):
    byte = decode_byte(data[0])
    x = byte & 0x7F

    i = 1
    while byte & 0x80:
        byte = decode_byte(data[i])
        x |= (byte & 0x7F) << (i * 7)
        i = i + 1
    # Being a variable length value, it returns a tuple, where the first
    # item is the decoded value and the second one is the data that remains
    # to analyze.
    return int(x), data[i:]


# Characters are represented using the Python's internal unicode codec,
# which may be UCS-2 or UCS-4, fixed-length encodings.

# XXX This actually does not work for non-ascci characters, because:
#
#  >>> u'é'.encode('unicode_internal')
#  '\xc3\x00\x00\x00\xa9\x00\x00\x00'
#
# That is, a 8 byte length string, instead of just 4 bytes

if u''.encode('utf-16') == '\xff\xfe':
    # Little Endian
    if sys.maxunicode == 65535:
        # UCS 2
        def encode_character(value):
            return value.encode('unicode_internal') + '\x00\x00'


        def decode_character(data):
            return unicode(data[:2], 'unicode_internal')
    else:
        # UCS 4
        def encode_character(value):
            return value.encode('unicode_internal')


        def decode_character(data):
            return unicode(data, 'unicode_internal')
else:
    # Big endian
    if sys.maxunicode == 65535:
        # UCS 2
        def encode_character(value):
            return value.encode('unicode_internal')[::-1] + '\x00\x00'


        def decode_character(data):
            return unicode(data[:2][::-1], 'unicode_internal')
    else:
        # UCS 4
        def encode_character(value):
            return value.encode('unicode_internal')[::-1]


        def decode_character(data):
            return unicode(data[::-1], 'unicode_internal')


# Strings start by a variable length vint, which contains the number of bytes
# that make up the string, and by the UTF-8 encoded string.
def encode_string(value):
    if isinstance(value, unicode):
        value = value.encode('utf8')

    length = encode_vint(len(value))
    return length + value


def decode_string(data):
    length, data = decode_vint(data)
    return unicode(data[:length], 'utf8'), data[length:]


# Links are unsigned integers used to build lists. There is only one thing
# that make they different from regular unsigned integers, the last number
# is reserved and represents None, the end of the list.
def encode_link(value):
    if value is None:
        return '\xFF\xFF\xFF\xFF'
    return struct.pack('>I', value)


def decode_link(data):
    if data == '\xFF\xFF\xFF\xFF':
        return None
    return int(struct.unpack('>I', data)[0])


# The first four bytes of every resource contain the version number. The
# version number is expressed as a date, whose compact human readable format
# is '20040723' (see at any handler class_version attribute). In the resource
# it is stored as the proleptic Gregorian ordinal.
def encode_version(value):
    year, month, day = int(value[:4]), int(value[4:6]), int(value[6:])
    date = datetime.date(year, month, day)
    ordinal = date.toordinal()
    return struct.pack('>I', ordinal)


def decode_version(data):
    ordinal = struct.unpack('>I', data)[0]
    date = datetime.date.fromordinal(ordinal)
    return date.strftime('%Y%m%d')
