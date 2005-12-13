# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from itools
from itools.datatypes import DataType, Integer, String, URI
from itools.i18n import accept


#############################################################################
# Types
#############################################################################


#############################################################################
# Parameters

def read_parameters(data):
    name = value = ''
    state = 0
    for byte in data:
        if state == 0:
            if byte == ' ':
                pass
            elif byte == '=':
                state = 1
            else:
                name += byte
        elif state == 1:
            if byte == ' ':
                pass
            elif byte == '"':
                state = 2
            else:
                value = byte
                state = 3
        elif state == 2:
            if byte == '"':
                state = 4
            else:
                value += byte
        elif state == 3:
            if byte == ' ' or byte == ';':
                yield name, value
                name = value = ''
                state = 0
            else:
                value += byte
        elif state == 4:
            if byte == ' ':
                pass
            elif byte == ';':
                yield name, value
                name = value = ''
                state = 0
            else:
                raise ValueError
    yield name, value



class Parameters(DataType):

    @staticmethod
    def decode(data):
        parameters = {}
        for name, value in read_parameters(data):
            parameters[name] = value

        return parameters


    @staticmethod
    def encode(parameters):
        parameters = [ '%s=%s' % (attribute, value)
                       for attribute, value in parameters.items() ]
        return '; '.join(parameters)



#############################################################################
# Other
class ValueWithParameters(DataType):

    @staticmethod
    def decode(value):
        if ';' in value:
            value, parameters = value.split(';', 1)
            parameters = Parameters.decode(parameters)
        else:
            parameters = {}
        return value.strip(), parameters


    @staticmethod
    def encode(value):
        value, parameters = value
        return '%s; %s' % (value, Parameters.encode(parameters))


#############################################################################
# Cookies
#############################################################################
class Cookie(DataType):
    # XXX Not robust

    @staticmethod
    def decode(data):
        cookies = {}
        for x in data.split(';'):
            name, value = x.strip().split('=')
            cookies[name] = value[1:-1]

        return cookies


    @staticmethod
    def encode(value):
        return '; '.join([ '%s="%s"' % (name, value)
                           for name, value in value.items() ])


#############################################################################
# Headers
#############################################################################

headers = {
    # General headers
    'Cache-Control': String,
    'Connection': String,
    'Date': String,
    'Pragma': String,
    'Trailer': String,
    'Transfer-Encoding': String,
    'Upgrade': String,
    'Via': String,
    'Warning': String,
    # Request headers
    'Accept': String,
    'Accept-Charset': String,
    'Accept-Encoding': String,
    'Accept-Language': accept.AcceptLanguageType,
    'Authorization': String,
    'Expect': String,
    'From': String,
    'Host': String,
    'If-Match': String,
    'If-Modified-Since': String,
    'If-None-Match': String,
    'If-Range': String,
    'If-Unmodified-Since': String,
    'Max-Forwards': String,
    'Proxy-Authorization': String,
    'Range': String,
    'Referer': URI,
    'TE': String,
    'User-Agent': String,
    # Response headers
    'Accept-Ranges': String,
    'Age': String,
    'ETag': String,
    'Location': URI,
    'Proxy-Authenticate': String,
    'Retry-After': String,
    'Server': String,
    'Vary': String,
    'WWW-Authenticate': String,
    # Entity headers
    'Allow': String,
    'Content-Encoding': String,
    'Content-Language': String,
    'Content-Length': Integer,
    'Content-Location': String,
    'Content-MD5': String,
    'Content-Range': String,
    'Content-Type': ValueWithParameters,
    'Expires': String,
    'Last-Modified': String,
    'extension-header': String,
    # Non standard headers
    'Content-Disposition': ValueWithParameters,
    'Cookie': Cookie,
    }



def get_type(name):
    return headers.get(name, String)
