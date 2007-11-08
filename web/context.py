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
from copy import deepcopy
import datetime
from string import Template
from thread import get_ident, allocate_lock
from time import strptime

# Import from itools
from itools.uri import Path, get_reference
from itools.datatypes import Enumerate, is_datatype
from itools.i18n import AcceptLanguageType
from itools.schemas import get_datatype
from itools.http import Response



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


    # FIXME Obsolete. To be removed by 0.17
    def get_accept_language(self):
        return self.accept_language


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
                expires = datetime.datetime(year, month, day, hour, min, sec)

                if expires < datetime.datetime.now():
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
        """
        This is a handy method that builds a URI object from some parameters.
        It exists to make short some common patterns.
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
            # Omit methods
            if key[0] == ';':
                continue
            # Omit files
            if isinstance(value, tuple) and len(value) == 3:
                continue
            # Keep form field
            if key in keep:
                form[key] = value
        if form:
            goto = goto.replace(**form)
        # Translate the source message
        if message:
            message = self.handler.gettext(message)
            message = Template(message).substitute(kw)
            return goto.replace(message=message)
        return goto


    def build_form_namespace(self, fields):
        """
        This utility method builds a namespace suitable to use to produce
        an HTML form. Its input data is a list (fields) that defines the
        form variables to consider:

            [(<field name>, <is field required>),
             ...]

        Every element of the list is a tuple with the name of the field
        and a boolean value that specifies whether the field is mandatory
        or not.

        The output is like:

            {<field name>: {'value': <field value>,
                            'class': <CSS class>}
             ...}
        """
        namespace = {}
        for field in fields:
            if len(field) == 2:
                field, is_mandatory = field
                datatype = get_datatype(field)
            else:
                field, is_mandatory, datatype = field
            # The value
            value = self.get_form_value(field)
            # The style
            # Is the field required
            cls = []
            if is_mandatory:
                cls.append('field_required')
            # Missing or not valid
            if self.has_form_value(field):
                if is_mandatory and not value:
                    cls.append('missing')
                elif value and not datatype.is_valid(value):
                    cls.append('missing')
            # Enumerate
            if is_datatype(datatype, Enumerate):
                value = datatype.get_namespace(value)
            if cls:
                cls = ' '.join(cls)
            else:
                cls = None
            namespace[field] = {'value': value, 'class': cls}

        return namespace


    def check_form_input(self, fields):
        """
        This utility method checks the request form and returns an error
        code if there is something wrong (a mandatory field is missing,
        or a value is not valid) or None if everything is ok.

        Its input data is a list (fields) that defines the form variables
        to consider:

            [(<field name>, <is field required>[ , <datatype>]),
             ...]

        Every element of the list is a tuple with the name of the field
        and a boolean value that specifies whether the field is mandatory
        or not.
        """
        message = (
            u'Some required fields are missing, or some values are not valid.'
            u' Please correct them and continue.')
        # Check mandatory fields
        for field in fields:
            if len(field) == 2:
                field, is_mandatory = field
                datatype = get_datatype(field)
            else:
                field, is_mandatory, datatype = field

            try:
                value = self.get_form_value(field, type=datatype)
            except:
                return message

            if is_mandatory:
                if value is None:
                    return message
                if isinstance(value, (str, unicode)):
                    value = value.strip()
                    if not value:
                        return message
                if not datatype.is_valid(value):
                    return message
            else:
                if value:
                    if not datatype.is_valid(value):
                        return message
        return None



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
