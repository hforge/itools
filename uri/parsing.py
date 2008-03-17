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

# Import from itools
from itools.abnf import build_grammar, BaseContext, Parser


###########################################################################
# ABNF Syntax (RFC 3986, Appendix A)
###########################################################################
grammar = build_grammar(
    'URI = scheme ":" hier-part [ "?" query ] [ "#" fragment ]\r\n'
    'hier-part = "//" authority path-abempty\r\n'
    '          / path-absolute\r\n'
    '          / path-rootless\r\n'
    '          / path-empty\r\n'
    'URI-reference = URI / relative-ref\r\n'
    'absolute-URI = scheme ":" hier-part [ "?" query ]\r\n'
    'relative-ref = relative-part [ "?" query ] [ "#" fragment ]\r\n'
    'relative-part = "//" authority path-abempty\r\n'
    '              / path-absolute\r\n'
    '              / path-noscheme\r\n'
    '              / path-empty\r\n'
    'scheme = ALPHA *( ALPHA / DIGIT / "+" / "-" / "." )\r\n'
    'authority = [ userinfo "@" ] host [ ":" port ]\r\n'
    'userinfo = *( unreserved / pct-encoded / sub-delims / ":" )\r\n'
    'host = IP-literal / IPv4address / reg-name\r\n'
    'port = *DIGIT\r\n'
    'IP-literal = "[" ( IPv6address / IPvFuture ) "]"\r\n'
    'IPvFuture = "v" 1*HEXDIG "." 1*( unreserved / sub-delims / ":" )\r\n'
    'IPv6address = 6( h16 ":" ) ls32\r\n'
    '            / "::" 5( h16 ":" ) ls32\r\n'
    '            / [ h16 ] "::" 4( h16 ":" ) ls32\r\n'
    '            / [ *1( h16 ":" ) h16 ] "::" 3( h16 ":" ) ls32\r\n'
    '            / [ *2( h16 ":" ) h16 ] "::" 2( h16 ":" ) ls32\r\n'
    '            / [ *3( h16 ":" ) h16 ] "::" h16 ":" ls32\r\n'
    '            / [ *4( h16 ":" ) h16 ] "::" ls32\r\n'
    '            / [ *5( h16 ":" ) h16 ] "::" h16\r\n'
    '            / [ *6( h16 ":" ) h16 ] "::"\r\n'
    'h16 = 1*4HEXDIG\r\n'
    'ls32 = ( h16 ":" h16 ) / IPv4address\r\n'
    'IPv4address = dec-octet "." dec-octet "." dec-octet "." dec-octet\r\n'
    'dec-octet = DIGIT ; 0-9\r\n'
    '          / %x31-39 DIGIT ; 10-99\r\n'
    '          / "1" 2DIGIT ; 100-199\r\n'
    '          / "2" %x30-34 DIGIT ; 200-249\r\n'
    '          / "25" %x30-35 ; 250-255\r\n'
    'reg-name = *( unreserved / pct-encoded / sub-delims )\r\n'
    'path = path-abempty ; begins with "/" or is empty\r\n'
    '     / path-absolute ; begins with "/" but not "//"\r\n'
    '     / path-noscheme ; begins with a non-colon segment\r\n'
    '     / path-rootless ; begins with a segment\r\n'
    '     / path-empty ; zero characters\r\n'
    'path-abempty = *( "/" segment )\r\n'
    'path-absolute = "/" [ segment-nz *( "/" segment ) ]\r\n'
    'path-noscheme = segment-nz-nc *( "/" segment )\r\n'
    'path-rootless = segment-nz *( "/" segment )\r\n'
    'path-empty = 0<pchar>\r\n'
    'segment = *pchar\r\n'
    'segment-nz = 1*pchar\r\n'
    'segment-nz-nc = 1*( unreserved / pct-encoded / sub-delims / "@" )\r\n'
    '              ; non-zero-length segment without any colon ":"\r\n'
    'pchar = unreserved / pct-encoded / sub-delims / ":" / "@"\r\n'
    'query = *( pchar / "/" / "?" )\r\n'
    'fragment = *( pchar / "/" / "?" )\r\n'
    'pct-encoded = "%" HEXDIG HEXDIG\r\n'
    'unreserved = ALPHA / DIGIT / "-" / "." / "_" / "~"\r\n'
    'reserved = gen-delims / sub-delims\r\n'
    'gen-delims = ":" / "/" / "?" / "#" / "[" / "]" / "@"\r\n'
    'sub-delims = "!" / "$" / "&" / "\'" / "(" / ")"\r\n'
    '           / "*" / "+" / "," / ";" / "="\r\n'
    )


###########################################################################
# Semantic Level
###########################################################################
class URIContext(BaseContext):

    def __init__(self, data):
        BaseContext.__init__(self, data)
        self.x_scheme = ''
        self.x_authority = ''
        self.x_path = ''
        self.x_query = ''
        self.x_fragment = ''


    def scheme(self, start, end, *args):
        self.x_scheme = self.data[start:end]
        return self.data[start:end]


    def authority(self, start, end, *args):
        self.x_authority = self.data[start:end]
        return self.data[start:end]


    def path_abempty(self, start, end, *args):
        self.x_path = self.data[start:end]
        return self.data[start:end]


    def query(self, start, end, *args):
        self.x_query = self.data[start:end]
        return self.data[start:end]


    def fragment(self, start, end, *args):
        self.x_fragment = self.data[start:end]
        return self.data[start:end]


    def URI_reference(self, start, end, *args):
        return (self.x_scheme, self.x_authority, self.x_path, self.x_query,
                self.x_fragment)


parse_uri = Parser(grammar, URIContext, 'URI-reference')
