# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
# Copyright (C) 2007 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
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
from string import Template
from thread import get_ident, allocate_lock
from time import strptime

# Import from itools
from itools.datatypes import is_datatype, Enumerate
from itools.http import Response
from itools.i18n import AcceptLanguageType
from itools.uri import get_reference


class FormError(Exception):
    """Raised when a form is invalid (missing or invalid fields)"""

    def __init__(self, missing, invalid):
          self.missing = missing
          self.invalid = invalid


class Context(object):

    user = None
    object = None


    def __init__(self, request):
        self.request = request
        self.response = Response()


    def init(self):
        """To process a request it must be loaded, in the first place.
        """
        request = self.request
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
            self.method = path[-1].params[0]
        else:
            self.path = path
            self.method = request.method

        # Language negotiation
        headers = request.headers
        if 'accept-language' in headers:
            # FIXME Done this way the programmer may modify the request object
            # TODO The 'Accept-Language' header should be deserialized here,
            # not in the 'Request' object.
            self.accept_language = headers['accept-language']
        else:
            self.accept_language = AcceptLanguageType.decode('')


    ########################################################################
    # API
    ########################################################################
    def redirect(self, reference, status=302):
        reference = self.uri.resolve(reference)
        self.response.redirect(reference, status)


    ########################################################################
    # API / parameters
    def get_form_keys(self):
        return self.request.form.keys()


    def get_form_value(self, name, default=None, type=None):
        value = self.request.get_parameter(name, default=default, type=type)
        if isinstance(value, list):
            if value:
                return value[0]
            return None
        return value


    def get_form_values(self, name, default=[], type=None):
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


    ########################################################################
    # API / cookies (client side sessions)
    def get_cookie(self, name, type=None):
        request, response = self.request, self.response
        # Get the value
        cookie = response.get_cookie(name)
        if cookie is None:
            value = request.get_cookie(name)
        else:
            # Check expiration time
            expires = cookie.expires
            if expires is not None:
                expires = expires[5:-4]
                expires = strptime(expires, '%d-%b-%y %H:%M:%S')
                year, month, day, hour, min, sec, kk, kk, kk = expires
                expires = datetime(year, month, day, hour, min, sec)
                if expires < datetime.now():
                    return None

            value = cookie.value

        if type is None:
            return value

        # Deserialize
        if value is None:
            return type.default
        return type.decode(value)


    def has_cookie(self, name):
        return self.get_cookie(name) is not None


    def set_cookie(self, name, value, **kw):
        self.response.set_cookie(name, value, **kw)


    def del_cookie(self, name):
        self.response.del_cookie(name)


    ########################################################################
    # API / high level
    def come_back(self, message, goto=None, keep=[], **kw):
        """This is a handy method that builds a URI object from some
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
        for key, value in self.request.form.items():
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
            if (key is True) or (key in keep):
                form[key] = value
        if form:
            goto = goto.replace(**form)
        # Translate the source message
        if message:
            message = self.object.gettext(message)
            message = Template(message).substitute(kw)
            return goto.replace(message=message)
        return goto


    def build_form_namespace(self, schema):
        """This utility method builds a namespace suitable to use to produce
        an HTML form. Its input data is a dictionnary that defines the form
        variables to consider:

          {'toto': Unicode(mandatory=True, multiple=False, default=u'toto'),
           'tata': Unicode(mandatory=True, multiple=False, default=u'tata')}

        Every element specifies the datatype of the field.
        The output is like:

            {<field name>: {'value': <field value>, 'class': <CSS class>}
             ...}
        """
        namespace = {}
        for name in schema:
            datatype = schema[name]
            # Value
            if getattr(datatype, 'multiple', False):
                value = self.get_form_values(name)
            else:
                value = self.get_form_value(name)
            # cls
            cls = []
            if getattr(datatype, 'mandatory', False):
                cls.append('field_required')
            if self.form_is_missing(name, datatype):
                cls.append('missing')
            elif self.form_is_invalid(name, datatype):
                cls.append('missing')
            cls = ' '.join(cls) or None
            namespace[name] = {'name': name, 'value': value, 'class': cls}
        return namespace


    def check_form_input(self, schema):
        """
        Form checks the request form and collect inputs consider the schema.
        This method also checks the request form and raise an FormError if
        there is something wrong (a mandatory field is missing, or a
        value is not valid) or None if everything is ok.

        Its input data is a list (fields) that defines the form variables to
          {'toto': Unicode(mandatory=True, multiple=False, default=u'toto'),
           'tata': Unicode(mandatory=True, multiple=False, default=u'tata')}
        """
        # TODO manage multiple Datatype - get_form_values
        values = {}
        invalid = []
        missing = []
        for name in schema:
            datatype = schema[name]
            if self.form_is_missing(name, datatype):
                missing.append(name)
            if self.form_is_invalid(name, datatype):
                invalid.append(name)
            if getattr(datatype, 'multiple', False):
                value = self.get_form_values(name, datatype.default, datatype)
            else:
                value = self.get_form_value(name, datatype.default, datatype)
            values[name] = value
        if missing or invalid:
            raise FormError(missing, invalid)
        return values


    def form_is_invalid(self, name, datatype):
        """Check if a form is invalid or not (Referred to its datatype)"""
        value = self.get_form_value(name)
        if not self.get_form_keys():
            return False
        if getattr(datatype, 'mandatory', False):
            if not datatype.is_valid(value):
                return True
        else:
            if value:
                if not datatype.is_valid(value):
                    return True
        return False


    def form_is_missing(self, name, datatype):
        """Check if a form is missing or not."""
        value = self.get_form_value(name)
        if not self.get_form_keys():
            return False
        if getattr(datatype, 'mandatory', False):
            if value is None:
                return True
            if isinstance(value, (str, unicode)):
                value = value.strip()
                if not value:
                    return True
            return False
        else:
            return False


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
