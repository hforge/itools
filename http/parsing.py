# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

"""
Parsing primitives.
"""

UNEXPECTED_CHAR = 'unexpected character "%s"'


ctls = set([ chr(x) for x in range(32) ] + [chr(127)])
tspecials = set('()<>@,;:\\"/[]?={} \t')
ctls_tspecials = ctls | tspecials
white_space = ' \t'


def lookup_char(char, data):
    return (data and data[0] == char)



def read_char(char, data):
    if not data:
        raise ValueError, 'unexpected end-of-data'
    if data[0] != char:
        raise ValueError, UNEXPECTED_CHAR % data[0]
    return data[1:]



def read_opaque(data, delimiters):
    index = 0
    n = len(data)
    while index < n:
        # End mark
        if data[index] in delimiters:
            return data[:index], data[index:]
        # Next
        index += 1

    # End-Of-Data
    return data, ''



def read_white_space(data):
    index = 0
    n = len(data)
    while index < n:
        # End mark
        if data[index] not in white_space:
            value = data[:index]
            return value, data[index:]
        # Next
        index += 1

    # End-Of-Data
    return data, ''



def read_token(data):
    if data[0] in ctls_tspecials:
        raise ValueError, UNEXPECTED_CHAR % data[0]
    index = 1

    n = len(data)
    while index < n:
        # End mark
        if data[index] in ctls_tspecials:
            value = data[:index]
            return value, data[index:]
        # Next
        index += 1

    # End-Of-Data
    return data, ''



def read_quoted_string(data):
    """Implementes quoted-strings as defined by RFC 2068 Section 2.2.
    Returns the value of the quoted string, and the continuation.
    """
    # Read the opening quote
    data = read_char('"', data)

    # Read the quoted string
    # FIXME Remains to interpret the escape character (\)
    index = 0
    n = len(data)
    while index < n:
        # End mark
        if data[index] == '"':
            value = data[:index]
            index += 1
            return value, data[index:]
        # Next
        index += 1

    # End-Of-Data
    raise ValueError, 'expected double-quote (") not found'



def read_token_or_quoted_string(data):
    if data[0] == '"':
        return read_quoted_string(data)
    return read_token(data)



def read_parameter(data):
    # name
    name, data = read_token(data)
    name = name.lower()
    # =
    white, data = read_white_space(data)
    data = read_char('=', data)
    white, data = read_white_space(data)
    # value
    value, data = read_token_or_quoted_string(data)
    return (name, value), data



def read_parameters(data):
    parameters = {}
    while data:
        # End mark
        if data[0] != ';':
            return parameters, data
        data = data[1:]
        # White Space
        white, data = read_white_space(data)
        # Parameter
        parameter, data = read_parameter(data)
        name, value = parameter
        parameters[name] = value
        # White Space
        white, data = read_white_space(data)

    # End-Of-Data
    return parameters, ''



def read_media_type(data):
    type, data = read_token(data)
    data = read_char('/', data)
    subtype, data = read_token(data)
    return (type, subtype), data

