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
from datetime import datetime

# Import from itools
from itools.datatypes import DataType, Integer, String, URI, HTTPDate

"""
Implementation of standard HTTP headers.
"""


###########################################################################
# Parsing functions
###########################################################################
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



def read_parameters(data, read_parameter=read_parameter):
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




###########################################################################
# Cookies
#
# Support for cookies varies from software to software, standards are in
# general very poorly implemeted.
#
# This is a list of related documents:
#
#  - Netscape Cookies
#    http://wp.netscape.com/newsref/std/cookie_spec.html
#
#  - RFC 2109
#    http://www.ietf.org/rfc/rfc2109.txt
#
#  - RFC 2965
#    http://www.ietf.org/rfc/rfc2965.txt
#
#  - Wikipedia entry for cookies
#    http://en.wikipedia.org/wiki/HTTP_cookie
#
# TODO Use SoupCookie
#
###########################################################################

# The parsing functions defined here must be robust to values not conformed
# to the standards (RFCs).  In particular they must be able to handler the
# cookie values sent by today's browsers.
#
# Syntax:
#
#   parameters    : parameter (; parameter)*
#
#   parameter     : name=value
#   name          : token
#   value         : quoted-string | opaque-string
#
#   token         : as defined by RFC 1945 Section 2.2
#   quoted-string : as defined by RFC 1945 Section 2.2
#   opaque-string : any character except ";"
#

def read_cookie_parameter(data):
    # name
    name, data = read_token(data)
    name = name.lower()
    # =
    white, data = read_white_space(data)
    if lookup_char('=', data) is False:
        # Garbage, try to recover from error (may fail)
        garbage, data = read_opaque(data, ';')
        return None, data
    data = data[1:]
    white, data = read_white_space(data)
    # value
    if data and data[0] == '"':
        value, data = read_quoted_string(data)
    else:
        value, data = read_opaque(data, ';')

    return (name, value), data



class Cookie(object):
    __hash__ = None

    def __init__(self, value, comment=None, domain=None, max_age=None,
                 path=None, secure=None, version=None, commenturl=None,
                 discard=None, port=None, expires=None):
        self.value = value
        # Parameters (RFC 2109)
        self.comment = comment
        self.domain = domain
        self.max_age = max_age
        self.path = path
        self.secure = secure
        self.version = version
        # Parameters (RFC 2965)
        self.commenturl = commenturl
        self.discard = discard
        self.port = port
        # Not standard
        self.expires = expires


    def __eq__(self, other):
        names = ['value', 'comment', 'domain', 'max_age', 'path', 'secure',
                 'version', 'commenturl', 'discard', 'port', 'expires']
        for name in names:
            if getattr(self, name) != getattr(other, name):
                return False
        return True


    def __str__(self):
        output = ['"%s"' % self.value]
        if self.path is not None:
            output.append('$Path="%s"' % self.path)
        if self.domain is not None:
            output.append('$Domain="%s"' % self.domain)
        return '; '.join(output)



class CookieDataType(DataType):

    @staticmethod
    def decode(data):
        # Parse the cookie string
        parameters = []
        while data:
            # parameter whitespace
            value, data = read_cookie_parameter(data)
            white, data = read_white_space(data)
            # ; whitespace
            if data:
                data = read_char(';', data)
                white, data = read_white_space(data)
            # Skip garbage
            if value is None:
                continue
            # Ok
            parameters.append(value)

        # Cookies
        cookies = {}
        n = len(parameters)
        index = 0
        while index < n:
            cookie_name, cookie_value = parameters[index]
            cookie = Cookie(cookie_value)
            cookies[cookie_name] = cookie
            # Next
            index += 1
            # $path
            if index < n:
                name, value = parameters[index]
                if name == '$path':
                    cookie.path = value
                    index += 1
            # $domain
            if index < n:
                name, value = parameters[index]
                if name == '$domain':
                    cookie.domain = value
                    index += 1

        return cookies


    @staticmethod
    def encode(cookies):
        output = []
        # Cookies
        for name in cookies:
            cookie = cookies[name]
            output.append('%s=%s' % (name, cookie))

        return '; '.join(output)



class SetCookieDataType(DataType):

    @staticmethod
    def decode(data):
        cookies = {}
        # Cookie
        cookie, data = read_cookie_parameter(data)
        name, value = cookie
        # White Space
        white, data = read_white_space(data)
        # Parameters
        parameters, data = read_parameters(data, read_cookie_parameter)

        # FIXME There may be more cookies (comma separated)
        cookies[name] = Cookie(value, **parameters)
        if data:
            raise ValueError, 'unexpected string "%s"' % data

        return cookies


    @staticmethod
    def encode(cookies):
        output = []
        for name in cookies:
            cookie = cookies[name]
            aux = []
            aux.append('%s="%s"' % (name, cookie.value))
            # The parameters
            expires = cookie.expires
            if expires is not None:
                if isinstance(expires, datetime):
                    expires = HTTPDate.encode(expires)
                aux.append('expires=%s' % expires)
            if cookie.domain is not None:
                aux.append('domain=%s' % cookie.domain)
            if cookie.path is not None:
                aux.append('path=%s' % cookie.path)
            else:
                aux.append('path=/')
            if cookie.max_age is not None:
                aux.append('max-age="%s"' % cookie.max_age)
            if cookie.comment is not None:
                aux.append('comment="%s"' % cookie.comment)
            if cookie.secure is not None:
                aux.append('secure="%s"' % cookie.secure)
            # The value
            output.append('; '.join(aux))
        return ', '.join(output)



###########################################################################
# Datatypes
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



class ContentDisposition(DataType):
    """RFC 2183 (Content-Disposition)
    """

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
    'authorization': String,
    'from': String,
    'if-modified-since': IfModifiedSince,
    'referer': URI,
    'user-agent': String,
    # Request headers (HTTP 1.1)
    'accept': String,
    'accept-charset': String,
    'accept-encoding': String,
    'accept-language': String,
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
    # mod_proxy
    'x-forwarded-for': String,
    }



def get_type(name):
    return headers.get(name, String)
