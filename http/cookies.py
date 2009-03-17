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

# Import from the Standard Library
from datetime import datetime

# Import from itools
from itools.datatypes import DataType, HTTPDate
from parsing import lookup_char, read_char, read_opaque, read_quoted_string
from parsing import read_token, read_white_space

"""
Partial implementation of HTTP Cookies.

Support for cookies varies from software to software, standards are in
general very poorly implemeted.

This is a list of related documents:

 - Netscape Cookies
   http://wp.netscape.com/newsref/std/cookie_spec.html

 - RFC 2109
   http://www.ietf.org/rfc/rfc2109.txt

 - RFC 2965
   http://www.ietf.org/rfc/rfc2965.txt

 - Wikipedia entry for cookies
   http://en.wikipedia.org/wiki/HTTP_cookie
"""

# TODO We need to make up a list of the browsers (or other software, like
# servers) we want to support, and document how they handle cookies, so we
# can properly communicate with them:
#
# - Firefox
#   https://bugzilla.mozilla.org/show_bug.cgi?id=208985
#


###########################################################################
# Parsing
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

def read_parameter(data):
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



###########################################################################
# Values
###########################################################################

class Cookie(object):

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


###########################################################################
# Data Types
###########################################################################

class CookieDataType(DataType):

    @staticmethod
    def decode(data):
        # Parse the cookie string
        parameters = []
        while data:
            # parameter whitespace
            value, data = read_parameter(data)
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
        cookie, data = read_parameter(data)
        name, value = cookie
        # White Space
        white, data = read_white_space(data)
        # Parameters
        parameters, data = read_parameters(data)

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

