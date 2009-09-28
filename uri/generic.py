# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Rob McMullen <rob.mcmullen@gmail.com>
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
This module aims to implement the URI standard as specified by RFC2396,
see http://www.ietf.org/rfc/rfc2396.txt


Other related RFCs include:

 - The URN scheme, http://www.ietf.org/rfc/rfc2141.txt

 - List of URI schemes: http://www.iana.org/assignments/uri-schemes

 - Registration of new schemes, http://www.ietf.org/rfc/rfc2717.txt
"""

# TODO Consider a C library, for instance: http://uriparser.sourceforge.net/

# TODO Check against (latest) RFC 3986: http://www.faqs.org/rfcs/rfc3986.html

# TODO A URI reference should be an inmutable object, at least its components
# (scheme, authority, path, query and fragment). Then we could get rid of the
# copy method. And this change would easy the way to a datetime like API.

# NOTE The RFC supports one letter schemes, but there are not official one
# letter schemes (http://www.iana.org/assignments/uri-schemes.html), and
# they are rarely used in practice.  Also, one letter schemes conflict with
# windows paths; for this reasons we do not support one letter schemes.

# Import from the Standard Library
from copy import copy
from urlparse import urlsplit, urlunsplit
from urllib import quote_plus, unquote, unquote_plus


#########################################################################
# Path
##########################################################################

def _normalize_path(path):
    if type(path) is not str:
        raise TypeError, 'path must be an string, not a %s' % type(path)

    # Does the path start and/or end with an slash?
    startswith_slash = endswith_slash = False
    if path:
        startswith_slash = (path[0] == '/')
        if path[-1] == '/':
            endswith_slash = True
        elif len(path) > 1 and path[-2] == '/' and path[-1] == '.':
            endswith_slash = True

    # Reduce '//', '/./' and 'a/..'
    stack = []
    for name in path.split('/'):
        # Reduce '//' and '/./' to '/'
        if name == '' or name == '.':
            continue
        # Reduce 'a/..' to ''
        if name == '..' and stack and stack[-1] != '..':
            stack.pop()
        else:
            stack.append(name)
    path = stack

    # Absolute path: remove '..' at the beginning
    if startswith_slash:
        while path and path[0] == '..':
            del path[0]

    # Ok
    return startswith_slash, path, endswith_slash


def normalize_path(path):
    """Normalize the path (we don't use os.path because on Windows it
    converts forward slashes to back slashes).

    Examples:

      'a//b/c'     -> 'a/b/c'
      'a/./b/c'    -> 'a/b/c'
      'a/b/c/../d' -> 'a/b/d'
      '/../a/b/c ' -> '/a/b/c'
      '.'          -> ''
    """
    startswith_slash, path, endswith_slash = _normalize_path(path)

    # len > 0
    if path:
        path = '/'.join(path)
        if startswith_slash:
            path = '/' + path
        if endswith_slash:
            path = path + '/'
        return path

    # len = 0
    if startswith_slash:
        return '/'
    return ''



class Path(list):
    """A path is a sequence of segments. A segment is has a name and,
    optionally one or more parameters.

    A path may start and/or end by an slash. This information is only
    useful when resolving paths. When a path starts by an slash it is
    called an absolute path, otherwise it is called a relative path.
    """

    __slots__ = ['startswith_slash', 'endswith_slash']


    def __init__(self, path):
        if type(path) is str:
            startswith_slash, path, endswith_slash = _normalize_path(path)
            self.startswith_slash = startswith_slash
            self.endswith_slash = path and endswith_slash
        else:
            # XXX Here the path is not normalized:
            #
            #   >>> print Path(['a', '..', 'b'])
            #   a/../b
            self.startswith_slash = False
            self.endswith_slash = False
            path = [ str(x) for x in path ]

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
        path = '/' if self.startswith_slash else ''

        path += '/'.join(self)
        if self.endswith_slash:
            path += '/'

        return path if path else '.'


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


    def get_name(self):
        if len(self) > 0:
            return self[-1]
        return ''


    def resolve(self, path):
        """Resolve the path following the standard (RFC2396). This is to say,
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
        """This method provides an alternative to the standards resolution
        algorithm. The difference is that it not takes into account the
        trailing slash (it behaves like if always there was a trailing
        slash):

          Path('/a/b').resolve('c') => Path('/a/b/c')
          Path('/a/b/').resolve('c') => Path('/a/b/c')

        Very, very practical.
        """
        if type(path) is not Path:
            path = Path(path)

        if path.startswith_slash:
            return path

        # Resolve
        new_path = Path(self)
        new_path.startswith_slash = self.startswith_slash
        new_path.endswith_slash = path.startswith_slash
        for name in path:
            if name == '..':
                if new_path:
                    new_path.pop()
                elif not new_path.startswith_slash:
                    new_path.append(name)
            else:
                new_path.append(name)
        return new_path


    def resolve_name(self, name):
        """This is a particular case of the 'resolve2' method, where the
        reference is known to be a relative path of length = 1.
        """
        if not isinstance(name, str):
            raise TypeError, 'unexpected value "%s"' % repr(name)

        # Relative path
        path = copy(self)
        path.append(name)
        path.endswith_slash = False
        return path


    def get_prefix(self, path):
        """Returns the common prefix of two paths, for example:

          >>> print Path('a/b/c').get_prefix(Path('a/b/d/e'))
          a/b

        XXX When there are parameters (e.g. a/b;lang=es/c) it is undefined.
        """
        if not isinstance(path, Path):
            path = Path(path)

        i = 0
        while i < len(self) and i < len(path) and self[i] == path[i]:
            i = i + 1
        return self[:i]


    def get_pathto(self, path):
        """Returns the relative path from 'self' to 'path'. This operation is
        the complement of 'resolve2'. So, if 'x = a.get_pathto(b)', then
        'b = a.resolve2(x)'.
        """
        if not isinstance(path, Path):
            path = Path(path)

        prefix = self.get_prefix(path)
        i = len(prefix)
        return Path(((['..'] * len(self[i:])) + path[i:]) or [])


    def get_pathtoroot(self):
        """Returns the path from the tail to the head, for example: '../../..'
        """
        return Path('../' * (len(self) - 1))



#########################################################################
# Query
##########################################################################

# Implements the 'application/x-www-form-urlencoded' content type (see
# http://www.w3.org/TR/REC-html40/interact/forms.html#h-17.13.4.1). The
# information decode as a dictionary.

# XXX This is not specified by RFC2396, so maybe we should not parse the
# query for the generic case.

# XXX The Python functions 'cgi.parse_qs' and 'urllib.urlencode' provide
# similar functionality, maybe we should just be a thin wrapper around
# them.
def decode_query(data, schema=None):
    """Decodes a query as defined by the "application/x-www-form-urlencoded"
    content type.

    The value expected is a byte string like "a=1&b=2"; the value returned
    is a dictonary like {'a': 1, 'b': 2}.

    See http://www.w3.org/TR/REC-html40/interact/forms.html#h-17.13.4.1
    for details.
    """
    query = {}
    if data:
        if schema is None:
            schema = {}

        for x in data.split('&'):
            if x:
                if '=' in x:
                    key, value = x.split('=', 1)
                    value = unquote_plus(value)
                else:
                    key, value = x, None

                key = unquote_plus(key)
                datatype = schema.get(key)
                if datatype is not None:
                    value = datatype.decode(value)
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



def encode_query(query, schema=None):
    """This method encodes a query as defined by the
    "application/x-www-form-urlencoded" content type (see
    http://www.w3.org/TR/REC-html40/interact/forms.html#h-17.13.4.1 for
    details)

    The value expected is a dictonary like {'a': 1, 'b': 2}.
    The value returned is a byte string like "a=1&b=2".
    """
    if schema is None:
        schema = {}

    line = []
    for key in query:
        value = query[key]
        key = quote_plus(key)

        # XXX As of the application/x-www-form-urlencoded content type,
        # it has not sense to have a parameter without a value, so
        # "?a&b=1" should be the same as "?b=1" (check the spec).
        # But for the tests defined by RFC2396 to pass, we must preserve
        # these empty parameters.
        if value is None:
            line.append(key)
            continue

        # A list
        datatype = schema.get(key)
        if isinstance(value, list):
            for x in value:
                if datatype is not None:
                    x = datatype.encode(x)
                line.append('%s=%s' % (key, quote_plus(x)))
            continue

        # A singleton
        if datatype is not None:
            value = datatype.encode(value)
        line.append('%s=%s' % (key, quote_plus(value)))

    return '&'.join(line)



##########################################################################
# Generic references
##########################################################################

class Reference(object):
    """A common URI reference is made of five components:

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

    __slots__ = ['scheme', 'authority', 'path', 'query', 'fragment']


    def __init__(self, scheme, authority, path, query, fragment=None):
        self.scheme = scheme
        self.authority = authority
        self.path = path
        self.query = query
        self.fragment = fragment


##    @property
##    def netpath(self):
##        return NetPath('//%s/%s' % (self.authority, self.path))


    def __str__(self):
        path = str(self.path)
        if path == '.':
            path = ''
        query = encode_query(self.query)
        reference = urlunsplit((self.scheme, self.authority, path, query,
                                self.fragment))
        if reference == '':
            if self.fragment is not None:
                return '#'
            return '.'
        return reference


    def __eq__(self, other):
        return str(self) == str(other)


    def __ne__(self, other):
        return str(self) != str(other)


    def __hash__(self):
        return hash(str(self))


    def resolve(self, reference):
        """Resolve the given relative URI, this URI (self) is considered to be
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
            return Reference(self.scheme, reference.authority,
                             copy(reference.path),
                             copy(reference.query),
                             reference.fragment)

        # Absolute path
        if reference.path.is_absolute():
            return Reference(self.scheme, self.authority,
                             copy(reference.path),
                             copy(reference.query),
                             reference.fragment)

        # Internal references
        if reference is empty_reference:
            return Reference(self.scheme, self.authority,
                             copy(self.path),
                             self.query.copy(),
                             None)

        if reference.fragment and not reference.path and not reference.query:
            return Reference(self.scheme, self.authority,
                             copy(self.path),
                             copy(self.query),
                             reference.fragment)

        # Relative path
        return Reference(self.scheme, self.authority,
                         self.path.resolve(reference.path),
                         copy(reference.query),
                         reference.fragment)


    def resolve2(self, reference):
        """This is much like 'resolve', but uses 'Path.resolve2' method
        instead.

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
            return Reference(self.scheme, reference.authority,
                             copy(reference.path),
                             copy(reference.query),
                             reference.fragment)

        # Absolute path
        if reference.path.is_absolute():
            return Reference(self.scheme, self.authority,
                             copy(reference.path),
                             copy(reference.query),
                             reference.fragment)

        # Internal references
        if reference is empty_reference:
            return Reference(self.scheme, self.authority,
                             copy(self.path),
                             copy(self.query),
                             None)

        if reference.fragment and not reference.path and not reference.query:
            return Reference(self.scheme, self.authority,
                             copy(self.path),
                             copy(self.query),
                             reference.fragment)

        # Relative path
        return Reference(self.scheme, self.authority,
                         self.path.resolve2(reference.path),
                         copy(reference.query),
                         reference.fragment)


    def resolve_name(self, name):
        """This is a particular case of the 'resolve2' method, where the
        reference is known to be a relative path of length = 1.
        """
        path = self.path.resolve_name(name)
        return Reference(self.scheme, self.authority, path, {})


    def replace(self, **kw):
        """This method returns a new uri reference, equal to this one, but
        with the given keyword parameters set in the query.
        """
        query = copy(self.query)
        for key in kw:
            value = kw[key]
            # If value is 'None', remove the key
            if value is None:
                if key in query:
                    del query[key]
                continue
            # Coerce
            value_type = type(value)
            if value_type is int:
                value = str(value)
            elif value_type is unicode:
                value = value.encode('utf-8')
            elif value_type is not str:
                raise TypeError, 'unexepected %s value' % type
            # Update
            query[key] = value
        # Ok
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


empty_reference = EmptyReference()


##########################################################################
# Factory
##########################################################################

class GenericDataType(object):

    @staticmethod
    def decode(data):
        data_type = type(data)
        if data_type is Path:
            return Reference('', '', data, {}, None)

        if data_type is not str:
            raise TypeError, 'unexpected %s' % type(data)

        # Special case, the empty reference
        if data == '':
            return empty_reference

        # Special case, the empty fragment
        if data == '#':
            return Reference('', '', Path(''), {}, '')

        # All other cases, split the reference in its components
        scheme, authority, path, query, fragment = urlsplit(data)

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
        # The query
        try:
            query = decode_query(query)
        except ValueError:
            pass
        # The fragment
        if fragment == '':
            fragment = None

        return Reference(scheme, authority, Path(path), query, fragment)
