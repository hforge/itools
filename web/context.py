# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
# Copyright (C) 2007 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2007-2008 Sylvain Taverne <sylvain@itaapy.com>
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
from thread import get_ident, allocate_lock
from time import strptime

# Import from itools
from itools.datatypes import String
from itools.http import Response, Unauthorized
from itools.i18n import AcceptLanguageType
from itools.uri import get_reference
from itools.utils import freeze
from messages import ERROR



class FormError(StandardError):
    """Raised when a form is invalid (missing or invalid fields).
    """

    def __init__(self, missing=None, invalid=None):
          self.missing = missing or []
          self.invalid = invalid or []


    def get_message(self):
        msg = (u'${missing} field(s) are missing and ${invalid} field(s) '
               u'are invalid')
        missing = len(self.missing)
        invalid = len(self.invalid)
        return ERROR(msg, missing=missing, invalid=invalid)


    def __str__(self):
        return self.get_message().gettext()



class Context(object):

    user = None
    resource = None


    def __init__(self, request):
        self.request = request
        self.response = Response()

        # Read the origin host
        if request.has_header('X-Forwarded-Host'):
            host = request.get_header('X-Forwarded-Host')
        elif request.has_header('Host'):
            host = request.get_header('Host')
        else:
            # XXX We should return a 400 response with HTTP 1.1
            # XXX What to do with 1.0?
            host = None

        if request.has_header('X_FORWARDED_PROTO'):
            scheme = request.get_header('X_FORWARDED_PROTO')
        else:
            # By default http
            scheme = 'http'

        # The requested uri
        reference = '%s://%s%s' % (scheme, host, request.request_uri)
        self.uri = get_reference(reference)

        # Split the path into path and method ("a/b/c/;view")
        path = request.request_uri.path
        if path and path[-1].name == '':
            self.path = path[:-1]
            self.view_name = path[-1].params[0]
        else:
            self.path = path
            self.view_name = None

        # Language negotiation
        headers = request.headers
        if 'accept-language' in headers:
            # FIXME Done this way the programmer may modify the request object
            # TODO The 'Accept-Language' header should be deserialized here,
            # not in the 'Request' object.
            self.accept_language = headers['accept-language']
        else:
            self.accept_language = AcceptLanguageType.decode('')


    def get_link(self, resource):
        """Return a link to the given resource, from the given context.
        """
        # FIXME This method should give an error if the given resource is
        # not within the site root.
        site_root = self.site_root
        return '/%s' % site_root.get_pathto(resource)


    #######################################################################
    # API / Redirect
    #######################################################################
    def redirect(self, reference, status=302):
        reference = self.uri.resolve(reference)
        self.response.redirect(reference, status)


    def come_back(self, message, goto=None, keep=freeze([]), **kw):
        """This is a handy method that builds a resource URI from some
        parameters.  It exists to make short some common patterns.
        """
        # By default we come back to the referrer
        if goto is None:
            goto = self.request.referrer
            # Replace goto if no referrer
            if goto is None:
                uri = str(self.uri)
                if '/;' in uri:
                    goto = uri.split('/;')[0]
                    goto = get_reference(goto)
        elif isinstance(goto, str):
            goto = get_reference(goto)
        # Preserve some form values
        form = {}
        for key, value in self.request.get_form().items():
            # Be robust
            if not key:
                continue
            # Omit methods
            if key[0] == ';':
                continue
            # Omit files
            if isinstance(value, tuple) and len(value) == 3:
                continue
            # Keep form field
            if (keep is True) or (key in keep):
                form[key] = value
        if form:
            goto = goto.replace(**form)
        # Translate the source message
        if message:
            message = message.gettext(**kw)
            return goto.replace(message=message)
        return goto


    #######################################################################
    # API / Forms
    #######################################################################
    def get_query_value(self, name, type=String, default=None):
        """Returns the value for the given name from the query.  Useful for
        POST requests.
        """
        form = self.uri.query
        return get_form_value(form, name, type, default)


    def get_form_value(self, name, type=String, default=None):
        form = self.request.get_form()
        return get_form_value(form, name, type, default)


    def get_form_keys(self):
        return self.request.get_form().keys()


    # FIXME Obsolete since 0.20.4, to be removed by the next major release
    def get_form_values(self, name, default=freeze([]), type=None):
        request = self.request
        if request.has_parameter(name):
            value = request.get_parameter(name)
            if not isinstance(value, list):
                value = [value]

            if type is None:
                return value
            return [ type.decode(x) for x in value ]

        return default


    def has_form_value(self, name):
        return self.request.has_parameter(name)


    #######################################################################
    # API / Cookies
    #######################################################################
    def get_cookie(self, name, type=None):
        request, response = self.request, self.response
        # Get the value
        cookie = response.get_cookie(name)
        if cookie is None:
            cookie = request.get_cookie(name)
            if cookie is None:
                value = None
            else:
                value = cookie.value
        else:
            # Check expiration time
            value = cookie.value
            expires = cookie.expires
            if expires is not None:
                expires = expires[5:-4]
                expires = strptime(expires, '%d-%b-%y %H:%M:%S')
                year, month, day, hour, min, sec, kk, kk, kk = expires
                expires = datetime(year, month, day, hour, min, sec)
                if expires < datetime.now():
                    value = None

        if type is None:
            return value

        # Deserialize
        if value is None:
            return type.get_default()
        return type.decode(value)


    def has_cookie(self, name):
        return self.get_cookie(name) is not None


    def set_cookie(self, name, value, **kw):
        self.response.set_cookie(name, value, **kw)


    def del_cookie(self, name):
        self.response.del_cookie(name)


    #######################################################################
    # API / Utilities
    #######################################################################
    def agent_is_a_robot(self):
        footprints = [
            'Ask Jeeves/Teoma', 'Bot/', 'crawler', 'Crawler',
            'freshmeat.net URI validator', 'Gigabot', 'Google',
            'LinkChecker', 'msnbot', 'Python-urllib', 'Yahoo', 'Wget',
            'Zope External Editor']

        user_agent = self.request.get_header('User-Agent')
        for footprint in footprints:
            if footprint in user_agent:
                return True
        return False


###########################################################################
# One context per thread
###########################################################################
contexts = {}
contexts_lock = allocate_lock()


def set_context(context):
    ident = get_ident()

    contexts_lock.acquire()
    try:
        contexts[ident] = context
    finally:
        contexts_lock.release()


def has_context():
    return get_ident() in contexts


def get_context():
    return contexts.get(get_ident())


def del_context():
    ident = get_ident()

    contexts_lock.acquire()
    try:
        del contexts[ident]
    finally:
        contexts_lock.release()



#######################################################################
# Internationalization
#######################################################################
def select_language(languages):
    accept = get_context().accept_language
    return accept.select_language(languages)


#######################################################################
# Get from the form or query
#######################################################################
def get_form_value(form, name, type=String, default=None):
    # Figure out the default value
    is_multiple = getattr(type, 'multiple', False)
    if default is None:
        default = type.get_default()

    # Missing
    is_mandatory = getattr(type, 'mandatory', False)
    is_missing = name not in form
    if is_missing:
        # Mandatory: raise an error
        if is_mandatory and is_missing:
            raise FormError(missing=[name])
        # Optional: return the default value
        return default

    # Multiple values
    if is_multiple:
        value = form.get(name)
        if not isinstance(value, list):
            value = [value]
        try:
            values = [ type.decode(x) for x in value ]
        except:
            raise FormError(invalid=[name])
        # Check the values are valid
        for value in values:
            if not type.is_valid(value):
                raise FormError(invalid=[name])
        return values

    # Single value
    value = form.get(name)
    if isinstance(value, list):
        value = value[0]
    try:
        value = type.decode(value)
    except:
        raise FormError(invalid=[name])

    # We consider that if the type deserializes the value to None, then we
    # must use the default.
    if value is None:
        if is_mandatory:
            raise FormError(missing=[name])
        return default

    # We consider a blank string to be a missing value (FIXME not reliable).
    is_blank = isinstance(value, (str, unicode)) and not value.strip()
    if is_blank:
        if is_mandatory:
           raise FormError(missing=[name])
    elif not type.is_valid(value):
        raise FormError(invalid=[name])
    return value
