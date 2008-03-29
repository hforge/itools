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

# Import from the Standard Library
from urllib import unquote

# Import from itools
from itools.abnf import build_grammar, get_parser, BaseContext
from generic import Authority, EmptyReference, Path, Reference, decode_query


###########################################################################
# ABNF Syntax (RFC 3986, Appendix A)
###########################################################################
uri_grammar = (
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

    def scheme(self, start, end, *args):
        return self.data[start:end]


    def authority(self, start, end, *args):
        return self.data[start:end]


    def path_abempty(self, start, end, *args):
        return self.data[start:end]


    def query(self, start, end, *args):
        return self.data[start:end]


    def fragment(self, start, end, *args):
        return self.data[start:end]


    def hier_part(self, start, end, authority, path):
        return authority, path


    def relative_part(self, start, end, authority, path):
        return authority, path


    def URI(self, start, end, scheme, hier_part, query, fragment):
        query = query and query[0] or ''
        fragment = fragment and fragment[0] or ''
        return scheme, hier_part[0], hier_part[1], query, fragment


    def relative_ref(self, start, end, relative_part, query, fragment):
        query = query and query[0] or ''
        fragment = fragment and fragment[0] or ''
        return ('', relative_part[0], relative_part[1], query, fragment)


    def URI_reference(self, start, end, uri):
        return uri


uri_grammar = build_grammar(uri_grammar, URIContext)
uri_parser = get_parser(uri_grammar, 'URI-reference')
parse_uri = uri_parser.run



class GenericDataType2(object):

    @staticmethod
    def decode(data):
        if isinstance(data, Path):
            return Reference('', Authority(''), data, {}, None)

        if not isinstance(data, (str, unicode)):
            raise TypeError, 'unexpected %s' % type(data)

        # Special case, the empty reference
        if data == '':
            return EmptyReference()

        # Special case, the empty fragment
        if data == '#':
            return Reference('', Authority(''), Path(''), {}, '')

        # All other cases, split the reference in its components
        scheme, authority, path, query, fragment = parse_uri(data)

        # Some special cases for Windows paths
        if len(scheme) == 1:
            # found a windows drive name instead of path, because urlsplit
            # thinks the scheme is "c" for Windows paths like "c:/a/b"
            path = "%s:%s" % (scheme, path)
            scheme = "file"
        elif len(path) > 3 and path[0] == '/' and path[2] == ':':
            # urlsplit also doesn't correctly handle windows path in url
            # form like "file:///c:/a/b" -- it thinks the path is "/c:/a/b",
            # which to be correct requires removing the leading slash.  Also
            # normalize the drive letter to lower case
            path = "%s:%s" % (path[1].lower(), path[3:])

        # The path
        if path:
            path = unquote(path)
        elif authority:
            path = '/'
        # The authority
        authority = unquote(authority)
        authority = Authority(authority)
        # The query
        try:
            query = decode_query(query)
        except ValueError:
            pass
        # The fragment
        if fragment == '':
            fragment = None

        return Reference(scheme, authority, Path(path), query, fragment)
