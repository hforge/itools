# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from the Standard Library
from datetime import datetime
import time

# Import from itools
from itools.datatypes import DataType, Integer, String, URI
from itools.i18n import accept


#############################################################################
# Types
#############################################################################

class HTTPDate(DataType):
    # XXX As specified by RFC 1945 (HTTP 1.0), should check HTTP 1.1
    # XXX The '%a', '%A' and '%b' format variables depend on the locale
    # (that's what the Python docs say), so what happens if the locale
    # in the server is not in English?

    @staticmethod
    def decode(data):
        formats = [
            # RFC-1123 (updates RFC-822, which uses two-digits years)
            '%a, %d %b %Y %H:%M:%S GMT',
            # RFC-850
            '%A, %d-%b-%y %H:%M:%S GMT',
            # ANSI C's asctime() format
            '%a %b  %d %H:%M:%S %Y',
            # Non-Standard formats, sent by some clients
            # Variation of RFC-1123, uses full day name (sent by Netscape 4)
            '%A, %d %b %Y %H:%M:%S GMT',
            # Variation of RFC-850, uses full month name and full year
            # (unkown sender)
            '%A, %d-%B-%Y %H:%M:%S GMT',
            ]
        for format in formats:
            try:
                tm = time.strptime(data, format)
            except ValueError:
                pass
            else:
                break
        else:
            raise ValueError, 'date "%s" is not an HTTP-Date' % data

        year, mon, mday, hour, min, sec, wday, yday, isdst = tm
        return datetime(year, mon, mday, hour, min, sec)


    @staticmethod
    def encode(value):
        return value.strftime('%a, %d %b %Y %H:%M:%S GMT')



class If_Modified_Since(HTTPDate):

    @staticmethod
    def decode(data):
        # Some browsers add a "length" parameter to the "If-Modified-Since"
        # header, it is an extension to the HTTP 1.0 protocol by Netscape,
        # http://www.squid-cache.org/mail-archive/squid-users/200307/0122.html
        if ';' in data:
            data = data.split(';')[0]
        return HTTPDate.decode(data)



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
        if not data:
            return {}

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
    # General headers (HTTP 1.0)
    'date': HTTPDate,
    'pragma': String,
    # General headers (HTTP 1.1)
    'cache-control': String,
    'connection': String,
    'trailer': String,
    'transfer-encoding': String,
    'upgrade': String,
    'via': String,
    'warning': String,
    # Request headers (HTTP 1.0)
    'authorization': String,
    'from': String,
    'if-modified-since': If_Modified_Since,
    'referer': URI,
    'user-agent': String,
    # Request headers (HTTP 1.1)
    'accept': String,
    'accept-charset': accept.AcceptCharsetType,
    'accept-encoding': String,
    'accept-language': accept.AcceptLanguageType,
    'expect': String,
    'host': String,
    'if-match': String,
    'if-none-match': String,
    'if-range': String,
    'if-unmodified-since': HTTPDate,
    'max-forwards': String,
    'proxy-authorization': String,
    'range': String,
    'te': String,
    # Response headers (HTTP 1.0)
    'location': URI,
    'server': String,
    'www-authenticate': String,
    # Response headers (HTTP 1.1)
    'accept-ranges': String,
    'age': String,
    'etag': String,
    'proxy-authenticate': String,
    'retry-after': String,
    'vary': String,
    # Entity headers (HTTP 1.0)
    'allow': String,
    'content-encoding': String,
    'content-length': Integer,
    'content-type': ValueWithParameters,
    'expires': HTTPDate,
    'last-modified': HTTPDate,
    # Entity headers (HTTP 1.1)
    'content-language': String,
    'content-location': String,
    'content-md5': String,
    'content-range': String,
    # Non standard headers
    'content-disposition': ValueWithParameters,
    'cookie': Cookie,
    }



def get_type(name):
    return headers.get(name, String)
