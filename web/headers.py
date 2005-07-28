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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA

# Import from itools
from itools import types


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



class Parameters(object):

    def decode(cls, data):
        parameters = {}
        for name, value in read_parameters(data):
            parameters[name] = value

        return parameters

    decode = classmethod(decode)


    def encode(cls, parameters):
        parameters = [ '%s=%s' % (attribute, value)
                       for attribute, value in parameters.items() ]
        return '; '.join(parameters)

    encode = classmethod(encode)



#############################################################################
# Other
class ValueWithParameters(object):

    def decode(cls, value):
        if ';' in value:
            value, parameters = value.split(';', 1)
            parameters = Parameters.decode(parameters)
        else:
            parameters = {}
        return value.strip(), parameters

    decode = classmethod(decode)


    def encode(cls, value):
        value, parameters = value
        return '%s; %s' % (value, Parameters.encode(parameters))

    encode = classmethod(encode)



#############################################################################
# Headers
#############################################################################

headers = {
    # General headers
    'Cache-Control': types.String,
    'Connection': types.String,
    'Date': types.String,
    'Pragma': types.String,
    'Trailer': types.String,
    'Transfer-Encoding': types.String,
    'Upgrade': types.String,
    'Via': types.String,
    'Warning': types.String,
    # Request headers
    'Accept': types.String,
    'Accept-Charset': types.String,
    'Accept-Encoding': types.String,
    'Accept-Language': types.String,
    'Authorization': types.String,
    'Expect': types.String,
    'From': types.String,
    'Host': types.String,
    'If-Match': types.String,
    'If-Modified-Since': types.String,
    'If-None-Match': types.String,
    'If-Range': types.String,
    'If-Unmodified-Since': types.String,
    'Max-Forwards': types.String,
    'Proxy-Authorization': types.String,
    'Range': types.String,
    'Referer': types.URI,
    'TE': types.String,
    'User-Agent': types.String,
    # Response headers
    'Accept-Ranges': types.String,
    'Age': types.String,
    'ETag': types.String,
    'Location': types.String,
    'Proxy-Authenticate': types.String,
    'Retry-After': types.String,
    'Server': types.String,
    'Vary': types.String,
    'WWW-Authenticate': types.String,
    # Entity headers
    'Allow': types.String,
    'Content-Encoding': types.String,
    'Content-Language': types.String,
    'Content-Length': types.String,
    'Content-Location': types.String,
    'Content-MD5': types.String,
    'Content-Range': types.String,
    'Content-Type': ValueWithParameters,
    'Expires': types.String,
    'Last-Modified': types.String,
    'extension-header': types.String,
    # Non standard headers
    'Content-Disposition': ValueWithParameters,
    }



def get_type(name):
    return headers.get(name, types.String)
