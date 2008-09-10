# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Hervé Cauwelier <herve@itaapy.com>
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
from base64 import decodestring, encodestring

# Import from itools
from itools.datatypes import DataType, Integer, String, URI, HTTPDate
from itools.i18n import AcceptLanguageType
from cookies import CookieDataType, SetCookieDataType
from parsing import (read_media_type, read_parameters, read_token,
    read_white_space)

"""
Implementation of standard HTTP headers.
"""


###########################################################################
# HTTP 1.0
###########################################################################
class IfModifiedSince(HTTPDate):

    @staticmethod
    def decode(data):
        # Some browsers add a "length" parameter to the "If-Modified-Since"
        # header, it is an extension to the HTTP 1.0 protocol by Netscape,
        # http://www.squid-cache.org/mail-archive/squid-users/200307/0122.html
        if ';' in data:
            data = data.split(';')[0]
        return HTTPDate.decode(data)



class ContentType(DataType):

    @staticmethod
    def decode(data):
        # Value
        value, data = read_media_type(data)
        value = '%s/%s' % value
        # White Space
        white, data = read_white_space(data)
        if not data:
            return value, {}
        # Parameters
        if data[0] != ';':
            raise ValueError, UNEXPECTED_CHAR % data[0]
        parameters, data = read_parameters(data)
        if data:
            raise ValueError, 'unexpected string "%s"' % data

        return value, parameters


    @staticmethod
    def encode(value):
        value, parameters = value
        parameters = [ '; %s="%s"' % x for x in parameters.items() ]
        parameters = ''.join(parameters)
        return '%s%s' % (value, parameters)



class Authorization(DataType):

    @staticmethod
    def decode(data):
        data = data.lstrip()
        if data.startswith('Basic '):
            b64auth = data[len('Basic '):]
            username, password = decodestring(b64auth).split(':', 1)
            return 'basic', (username, password)
        raise NotImplementedError, 'XXX'


    @staticmethod
    def encode(value):
        method, value = value
        if method == 'basic':
            username, password = value
            if ':' in username:
                raise ValueError, 'XXX'
            return 'Basic %s' % encodestring('%s:%s' % value)
        raise NotImplementedError, 'XXX'



###########################################################################
# RFC 2183 (Content-Disposition)
###########################################################################
class ContentDisposition(DataType):

    @staticmethod
    def decode(data):
        # Value
        value, data = read_token(data)
        # White Space
        white, data = read_white_space(data)
        if not data:
            return value, {}
        # Parameters
        if data[0] != ';':
            raise ValueError, UNEXPECTED_CHAR % data[0]
        parameters, data = read_parameters(data)
        if data:
            raise ValueError, 'unexpected string "%s"' % data

        return value, parameters


    @staticmethod
    def encode(value):
        value, parameters = value
        parameters = [ '; %s="%s"' % x for x in parameters.items() ]
        parameters = ''.join(parameters)
        return '%s%s' % (value, parameters)



###########################################################################
# Headers
###########################################################################
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
    'authorization': Authorization,
    'from': String,
    'if-modified-since': IfModifiedSince,
    'referer': URI,
    'user-agent': String,
    # Request headers (HTTP 1.1)
    'accept': String,
    'accept-charset': String,
    'accept-encoding': String,
    'accept-language': AcceptLanguageType,
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
    'content-type': ContentType,
    'expires': HTTPDate,
    'last-modified': HTTPDate,
    # Entity headers (HTTP 1.1)
    'content-language': String,
    'content-location': String,
    'content-md5': String,
    'content-range': String,
    # RFC 2109
    'cookie': CookieDataType,
    'set-cookie': SetCookieDataType,
    # RFC 2183
    'content-disposition': ContentDisposition,
    }



def get_type(name):
    return headers.get(name, String)
