# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


# Import from Python
import datetime
from urllib import urlencode
from urlparse import urlsplit

# Import from itools
from itools import uri



class Request(object):
    """
    Wrapp the Zope request object to add our own help methods.
    """

    def __init__(self, zope_request):
        self.zope_request = zope_request

        # The URI
        query = zope_request.environ.get('QUERY_STRING', '')
        query = uri.Query(query)
        # The scheme
        scheme = 'http'
        # The authority
        if 'REAL_HOST' in query:
            authority = query.pop('REAL_HOST')
        else:
            authority = zope_request['HTTP_HOST']
        # The path
        if 'REAL_PATH' in query:
            path = query.pop('REAL_PATH')
        else:
            path = zope_request.environ['PATH_INFO']
        # The query
        query = str(query)
        # The fragment
        fragment = ''
        # The URI
        uri_string = '%s://%s/%s?%s#%s' % (scheme, authority, path, query,
                                          fragment)
        self.uri = uri.get_reference(uri_string)

        # The referer
        referer = zope_request.environ.get('HTTP_REFERER')
        if referer is None:
            self.referer = None
        else:
            self.referer = uri.get_reference(referer)


    # XXX Just for backwards compatibility, so the request object can be
    # used as if it was the Zope request. Zope does really black magic
    # in the 'HTTPRequest.get' method (bullshit).
    def __getattr__(self, name):
        return getattr(self.zope_request, name)


    def __getitem__(self, name):
        return self.zope_request[name]


    def __setitem__(self, name, value):
        self.zope_request[name] = value


    def get(self, name, default=None):
        # XXX Maybe this one should just call 'zope_request.get'
        try:
            return self[name]
        except KeyError:
            return default


    ########################################################################
    # Accept
    ########################################################################
    def get_accept_language(self):
        return self.zope_request.other['AcceptLanguage']

    accept_language = property(get_accept_language, None, None, "")


    def get_accept_charset(self):
        return self.zope_request.other['AcceptCharset']

    accept_charset = property(get_accept_charset, None, None, "")


    ########################################################################
    # Form
    ########################################################################
    def get_form(self):
        return self.zope_request.form

    form = property(get_form, None, None, "")


    ########################################################################
    # Cookies
    ########################################################################
    def get_cookies(self):
        return self.zope_request.cookies

    cookies = property(get_cookies, None, None, "")


    ########################################################################
    # Environ
    ########################################################################
    def get_environ(self):
        return self.zope_request.environ

    environ = property(get_environ, None, None, "")


    ########################################################################
    # Other
    ########################################################################
    def get_other(self):
        return self.zope_request.other

    other = property(get_other, None, None, "")


    ########################################################################
    # And more (XXX move to uri??)
    ########################################################################
    def build_url(self, url=None, preserve=[], **kw):
        """
        Builds and returns a new url from the one we are now. Preserves only
        the query parameters that start with any of the specified prefixes in
        the 'preserve' argument. The keywords argument is used to add or
        modify query parameters.
        """
        if url is None:
            url = self.uri.path[-1]

        query = []
        # Preserve request parameters that start with any of the prefixes.
        for key, value in self.form.items():
            for prefix in preserve:
                if key.startswith(prefix):
                    query.append((key, value))
                    break

        # Modify the parameters
        for key in kw:
            for i, x in enumerate(query):
                if x is not None and x[0] == key:
                    query[i] = None
        query = [ x for x in query if x is not None ]
        for key, value in kw.items():
            query.append((key, value))

        # Keep the type
        new_query = []
        for key, value in query:
            if isinstance(value, str):
                new_query.append((key, value))
            elif isinstance(value, unicode):
                value = value.encode('utf8')
                new_query.append(('%s:utf8:ustring' % key, value))
            elif isinstance(value, int):
                new_query(('%s:int' % key, str(value)))
            elif isinstance(value, list):
                for x in value:
                    # XXX Should coerce too
                    new_query.append(('%s:list' % key, x))
            else:
                # XXX More types needed!!
                new_query.append((key, str(value)))

        # Re-build the query string
        query_string = urlencode(new_query)

        # Build the new url
        if query_string:
            url = '%s?%s' % (url, query_string)

        return url
