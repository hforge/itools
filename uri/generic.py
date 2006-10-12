# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


"""
This module aims to implement the URI standard as specified by RFC2396,
see http://www.ietf.org/rfc/rfc2396.txt

Other related RFCs include:

 - The URN scheme, http://www.ietf.org/rfc/rfc2141.txt

 - List of URI schemes: http://www.iana.org/assignments/uri-schemes

 - Registration of new schemes, http://www.ietf.org/rfc/rfc2717.txt
"""

# XXX A resource should be an inmutable object, at least its components
# (scheme, authority, path, query and fragment). Then we could get rid
# of the copy method. And this change woule easy the way to a datetime
# like API.

# Import from the Standard Library
from copy import copy
from urlparse import urlsplit, urlunsplit
import urllib


##########################################################################
# Authority
##########################################################################

class Authority(object):
    """
    There are two types of authorities: registry based and server-based;
    right now only server-based are supported (XXX).

    The userinfo component could be further processed.
    """

    def __init__(self, auth):
        # The userinfo
        if '@' in auth:
            self.userinfo, auth = auth.split('@', 1)
        else:
            self.userinfo = None
        # host:port
        if ':' in auth:
            self.host, self.port = auth.split(':', 1)
        else:
            self.host = auth
            self.port = None


    def __str__(self):
        # userinfo@host
        if self.userinfo is not None:
            auth = '%s@%s' % (self.userinfo, self.host)
        else:
            auth = self.host
        # The port
        if self.port is not None:
            return auth + ':' + self.port
        return auth


    def __eq__(self, other):
        return str(self) == str(other)


    def __hash__(self):
        return hash(str(self))


    def __nonzero__(self):
        return bool(str(self))



#########################################################################
# Path
##########################################################################

def normalize_path(path):
    """
    Normalize the path (we don't use os.path because on Windows it
    converts forward slashes to back slashes).

    Examples:

      'a//b/c'     -> 'a/b/c'
      'a/./b/c'    -> 'a/b/c'
      'a/b/c/../d' -> 'a/b/d'
      '/../a/b/c ' -> '/a/b/c'
      '.'          -> ''
    """
    if not isinstance(path, str) and not isinstance(path, unicode):
        raise TypeError, 'path must be an string, not a %s' % type(path)

    # Does the path start by an slash? i.e.: is it absolute?
    startswith_slash = path.startswith('/')

    # Does the path end by an slash? (relevant to resolve URLs)
    endswith_slash = path.endswith('/') or path.endswith('/.')

    # Split the path http://a//
    path = path.split('/')

    # Transform '//' and '/./' to '/'
    path = [ x for x in path if x not in ('', '.') ]

    # Transform 'a/..' to ''
    stack = []
    for segment in path:
        if segment == '..' and stack and stack[-1] != '..':
            stack.pop()
        else:
            stack.append(segment)
    path = stack

    # Absolute or Relative
    if startswith_slash:
        # Absolute path, remove '..' at the beginning
        while path and path[0] == '..':
            path = path[1:]

    path = '/'.join(path)
    if path:
        if startswith_slash:
            path = '/' + path
        if endswith_slash:
            path = path + '/'
        return path
    else:
        if startswith_slash:
            return '/'
        return ''



class Segment(object):

    def __init__(self, segment=''):
        if isinstance(segment, Segment):
            self.name = segment.name
            self.param = segment.param
        elif isinstance(segment, str) or isinstance(segment, unicode):
            if ';' in segment:
                self.name, self.param = segment.split(';', 1)
            else:
                self.name = segment
                self.param = None
        else:
            raise TypeError, \
                  'segment or string expected, "%s" found' % type(segment)


    def __str__(self):
        if self.param is not None:
            return '%s;%s' % (self.name, self.param)
        return self.name



class Path(list):
    """
    A path is a sequence of segments. A segment is has a name and,
    optionally a parameter.

    A path may start and/or end by an slash. This information is only
    useful when resolving paths. When a path starts by an slash it is
    called an absolute path, otherwise it is called a relative path.
    """

    def __init__(self, path):
        if isinstance(path, Segment):
            path = str(path)
        elif isinstance(path, tuple) or isinstance(path, list):
            path = '/'.join([ str(x) for x in path ])

        path = normalize_path(path)

        # Absolute or relative
        self.startswith_slash = path.startswith('/')
        if self.startswith_slash:
            path = path[1:]
        self.endswith_slash = path.endswith('/')
        if self.endswith_slash:
            path = path[:-1]

        if path != '':
            path = [ Segment(x) for x in path.split('/') ]
            list.__init__(self, path)


    def __getslice__(self, a, b):
         slice = Path(list.__getslice__(self, a, b))
         slice.startswith_slash = self.startswith_slash
         return slice


    def __add__(self, path):
        raise NotImplementedError, \
              'paths can not be added, use resolve2 instead'


    ##########################################################################
    # API
    def __repr__(self):
        return '<itools.uri.Path at %s>' % hex(id(self))


    def __str__(self):
        path = ''
        if self.startswith_slash:
            path = '/'
        path += '/'.join([ str(x) for x in self ])
        if self.endswith_slash:
            path += '/'
        if len(path) == 0:
            return '.'
        return path


    def __ne__(self, other):
        if isinstance(other, str):
            other = Path(other)

        return str(self) != str(other)


    def __eq__(self, other):
        if isinstance(other, str):
            other = Path(other)

        return str(self) == str(other)


    def __hash__(self):
        return hash(str(self))


    def is_absolute(self):
        return self.startswith_slash


    def is_relative(self):
        return not self.startswith_slash


    def resolve(self, path):
        """
        Resolve the path following the standard (RFC2396). This is to say,
        it takes into account the trailing slash, so:

          Path('/a/b').resolve('c') => Path('/a/c')
          Path('/a/b/').resolve('c') => Path('/a/b/c')
        """
        if not isinstance(path, Path):
            path = Path(path)

        if path.is_absolute():
            return path

        if self.endswith_slash:
            return Path('%s/%s' % (self, path))

        return Path('%s/../%s' % (self, path))


    def resolve2(self, path):
        """
        This method provides an alternative to the standards resolution
        algorithm. The difference is that it not takes into account the
        trailing slash (it behaves like if always there was a trailing
        slash):

          Path('/a/b').resolve('c') => Path('/a/b/c')
          Path('/a/b/').resolve('c') => Path('/a/b/c')

        Very, very practical.
        """
        if not isinstance(path, Path):
            path = Path(path)

        if path.is_absolute():
            return path

        return Path('%s/%s' % (self, path))


    def get_prefix(self, path):
        """
        Returns the common prefix of two paths, for example:

          >>> print Path('a/b/c').get_prefix(Path('a/b/d/e'))
          a/b

        XXX When there are parameters (e.g. a/b;lang=es/c) it is undefined.
        """
        if not isinstance(path, Path):
            path = Path(path)

        i = 0
        while i < len(self) and i < len(path) and self[i].name == path[i].name:
            i = i + 1
        return self[:i]


    def get_pathto(self, path):
        """
        Returns the relative path from 'self' to 'path'. This operation is
        the complement of 'resolve2'. So, if 'x = a.get_pathto(b)', then
        'b = a.resolve2(x)'.
        """
        if not isinstance(path, Path):
            path = Path(path)

        prefix = self.get_prefix(path)
        i = len(prefix)
        return Path(((['..'] * len(self[i:])) + path[i:]) or ['.'])


    def get_pathtoroot(self):
        """
        Returns the path from the tail to the head, for example: '../../..'
        """
        return Path('../' * (len(self) - 1))



#########################################################################
# Query
##########################################################################

class Query(object):
    """
    Implements the 'application/x-www-form-urlencoded' content type (see
    http://www.w3.org/TR/REC-html40/interact/forms.html#h-17.13.4.1). The
    information decode as a dictionary.

    XXX This is not specified by RFC2396, so maybe we should not parse the
    query for the generic case.

    XXX The Python functions 'cgi.parse_qs' and 'urllib.urlencode' provide
    similar functionality, maybe we should just be a thin wrapper around
    them.
    """

    default = {}


    @staticmethod
    def decode(data):
        query = {}
        if data:
            for x in data.split('&'):
                if x:
                    if '=' in x:
                        key, value = x.split('=', 1)
                        value = urllib.unquote_plus(value)
                    else:
                        key, value = x, None

                    key = urllib.unquote_plus(key)
                    if key in query:
                        old_value = query[key]
                        if isinstance(old_value, list):
                            old_value.append(value)
                        else:
                            value = [old_value, value]
                            query[key] = value
                    else:
                        query[key] = value
        return query


    @staticmethod
    def encode(query):
        line = []
        for key, value in query.items():
            key = urllib.quote_plus(key)
            if value is None:
                line.append(key)
            elif isinstance(value, list):
                for x in value:
                    if isinstance(x, unicode):
                        x = x.encode('UTF-8')
                    line.append('%s=%s' % (key, urllib.quote_plus(x)))
            else:
                if isinstance(value, unicode):
                    value = value.encode('UTF-8')
                line.append('%s=%s' % (key, urllib.quote_plus(value)))
        return '&'.join(line)



##########################################################################
# Generic references
##########################################################################

class Reference(object):
    """
    A common URI reference is made of five components:

    - the scheme
    - the authority
    - the path
    - the query
    - the fragment

    Its syntax is:

      <scheme>://<authority><path>?<query>#<fragment>

    Not all the components must be present, examples of possible references
    include:

    http://www.example.com
    http://www.ietf.org/rfc/rfc2616.txt
    /rfc/rfc2616.txt
    XXX
    """

    def __init__(self, scheme, authority, path, query, fragment=None):
        self.scheme = scheme
        self.authority = authority
        self.path = path
        self.query = query
        self.fragment = fragment


##    def get_netpath(self):
##        return NetPath('//%s/%s' % (self.authority, self.path))
##
##    netpath = property(get_netpath, None, None, '')


    def __str__(self):
        path = str(self.path)
        if path == '.':
            path = ''
        query = Query.encode(self.query)
        reference = urlunsplit((self.scheme, str(self.authority), path, query,
                                self.fragment))
        if reference == '':
            if self.fragment is not None:
                return '#'
            return '.'
        return reference


    def __eq__(self, other):
        return str(self) == str(other)


    def __hash__(self):
        return hash(str(self))


    def resolve(self, reference):
        """
        Resolve the given relative URI, this URI (self) is considered to be
        the base.

        If the given uri is not relative, it is returned. If 'self' is not
        absolute, the result is undefined.
        """
        if not isinstance(reference, Reference):
            reference = GenericDataType.decode(reference)

        # Absolute URI
        if reference.scheme:
            return reference

        # Network path
        if reference.authority:
            return Reference(self.scheme,
                             copy(reference.authority),
                             copy(reference.path),
                             copy(reference.query),
                             reference.fragment)

        # Absolute path
        if reference.path.is_absolute():
            return Reference(self.scheme,
                             copy(self.authority),
                             copy(reference.path),
                             copy(reference.query),
                             reference.fragment)

        # Internal references
        if isinstance(reference, EmptyReference):
            return Reference(self.scheme,
                             copy(self.authority),
                             copy(self.path),
                             copy(self.query),
                             None)

        if reference.fragment and not reference.path and not reference.query:
            return Reference(self.scheme,
                             copy(self.authority),
                             copy(self.path),
                             copy(self.query),
                             reference.fragment)

        # Relative path
        return Reference(self.scheme,
                         copy(self.authority),
                         self.path.resolve(reference.path),
                         copy(reference.query),
                         reference.fragment)


    def resolve2(self, reference):
        """
        This is much like 'resolv', but uses 'Path.resolve2' method instead.

        XXX Too much code is duplicated, the only difference beween 'resolve'
        and 'resolve2' is one character. Refactor!
        """
        if not isinstance(reference, Reference):
            reference = GenericDataType.decode(reference)

        # Absolute URI
        if reference.scheme:
            return reference

        # Network path
        if reference.authority:
            return Reference(self.scheme,
                             copy(reference.authority),
                             copy(reference.path),
                             copy(reference.query),
                             reference.fragment)

        # Absolute path
        if reference.path.is_absolute():
            return Reference(self.scheme,
                             copy(self.authority),
                             copy(reference.path),
                             copy(reference.query),
                             reference.fragment)

        # Internal references
        if isinstance(reference, EmptyReference):
            return Reference(self.scheme,
                             copy(self.authority),
                             copy(self.path),
                             copy(self.query),
                             None)

        if reference.fragment and not reference.path and not reference.query:
            return Reference(self.scheme,
                             copy(self.authority),
                             copy(self.path),
                             copy(self.query),
                             reference.fragment)

        # Relative path
        return Reference(self.scheme,
                         copy(self.authority),
                         self.path.resolve2(reference.path),
                         copy(reference.query),
                         reference.fragment)


    def replace(self, **kw):
        """
        This method returns a new uri reference, equal to this one, but
        with the given keyword parameters set in the query.
        """
        query = copy(self.query)
        query.update(kw)
        return Reference(self.scheme, self.authority, self.path, query,
                         self.fragment)



class EmptyReference(Reference):

    scheme = None
    authority = None
    path = Path('')
    query = None
    fragment = None


    def __init__(self):
        pass


    def __str__(self):
        return ''


##########################################################################
# Factory
##########################################################################

class GenericDataType(object):

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
        scheme, authority, path, query, fragment = urlsplit(data)
        # The authority
        authority = urllib.unquote(authority)
        authority = Authority(authority)
        # The path
        path = urllib.unquote(path)
        # The query
        try:
            query = Query.decode(query)
        except ValueError:
            pass
        # The fragment
        if fragment == '':
            fragment = None

        return Reference(scheme, authority, Path(path), query, fragment)
