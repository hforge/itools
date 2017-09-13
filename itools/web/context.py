# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2012 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2006, 2008-2011 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2007 Nicolas Deram <nderam@gmail.com>
# Copyright (C) 2007, 2009, 2011 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2007-2008, 2010 Sylvain Taverne <taverne.sylvain@gmail.com>
# Copyright (C) 2009-2011 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2010 Alexis Huet <alexis@itaapy.com>
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
import json
from copy import deepcopy
from base64 import decodestring, encodestring
from datetime import datetime, timedelta
from hashlib import sha224
from time import time
from urllib import quote, unquote

# Import from pytz
from pytz import timezone

# Import from itools
from itools.core import fixed_offset, is_prototype, local_tz
from itools.core import freeze, prototype, proto_lazy_property
from itools.database.fields import get_field_and_datatype
from itools.datatypes import String, HTTPDate
from itools.i18n import AcceptLanguageType, format_number
from itools.i18n import format_datetime, format_date, format_time
from itools.log import Logger, log_error, log_warning
from itools.uri import decode_query, get_reference, Path, Reference
from itools.validators import ValidationError

# Local imports
from entities import Entity
from exceptions import FormError
from headers import get_type, Cookie, SetCookieDataType
from messages import ERROR
from utils import NewJSONEncoder, fix_json, reason_phrases
from router import RequestMethod


class Context(prototype):

    cookies = {}
    method = None
    mtime = None # Last-Modified
    uri = None
    user = None
    resource = None
    server = None
    status = None # response status
    styles = []
    scripts = []
    view = None
    entity = None
    soup_message = None
    path_query_base = None
    form = {}
    form_error = None
    commit = True


    def init_context(self):
        soup_message = self.soup_message
        path = self.path

        # The request method
        self.method = soup_message.get_method()
        # The query
        query = soup_message.get_query()
        self.query = decode_query(query)

        # The URI as it was typed by the client
        xfp = soup_message.get_header('X_FORWARDED_PROTO')
        src_scheme = xfp or 'http'
        xff = soup_message.get_header('X-Forwarded-Host')
        if xff:
            xff = xff.split(',', 1)[0].strip()
        hostname = soup_message.get_host()
        src_host = xff or soup_message.get_header('Host') or hostname
        if query:
            uri = '%s://%s%s?%s' % (src_scheme, src_host, path, query)
        else:
            uri = '%s://%s%s' % (src_scheme, src_host, path)
        self.uri = get_reference(uri)

        # Split the path into path and method ("a/b/c/;view")
        path = path if type(path) is Path else Path(path)
        name = path.get_name()
        if name and name[0] == ';':
            self.path = path[:-1]
            self.view_name = name[1:]
        else:
            self.path = path
            self.view_name = None

        # Cookies
        self.cookies = {}

        # Media files (CSS, javascript)
        # Set the list of needed resources. The method we are going to
        # call may need external resources to be rendered properly, for
        # example it could need an style sheet or a javascript file to
        # be included in the html head (which it can not control). This
        # attribute lets the interface to add those resources.
        self.styles = []
        self.scripts = []

        # The authenticated user
        self.authenticate()
        # The Site Root
        self.find_site_root()
        self.site_root.before_traverse(self)  # Hook


    @proto_lazy_property
    def timestamp(self):
        return datetime.utcnow().replace(tzinfo=fixed_offset(0))


    @proto_lazy_property
    def accept_language(self):
        accept_language = self.soup_message.get_header('accept-language')
        if accept_language is None:
            accept_language = ''
        return AcceptLanguageType.decode(accept_language)


    @proto_lazy_property
    def body(self):
        # Case 1: nothing
        body = self.soup_message.get_body()
        if not body:
            return {}
        # Get content type
        content_type, type_parameters = self.get_header('content-type')
        media_type = content_type.split(';')[0]
        if media_type == 'application/x-www-form-urlencoded':
            # Case 1: urlencoded
            return self.get_form_body(body)
        elif media_type == 'application/json':
            # Case 2: json
            return self.get_json_body(body)
        elif media_type == 'application/octet-stream':
            return {'body': body}
        elif media_type.startswith('multipart/'):
            # Case 3: multipart
            return self.get_multipart_body(body)
        # Case 4: Not managed content type
        raise ValueError('Invalid content type "{0}"'.format(content_type))


    def get_form_body(self, body):
        return decode_query(body)


    def get_json_body(self, body):
        data = json.loads(body)
        return fix_json(data)


    def get_multipart_body(self, body):
        content_type, type_parameters = self.get_header('content-type')
        boundary = type_parameters.get('boundary')
        boundary = '--%s' % boundary
        form = {}
        for part in body.split(boundary)[1:-1]:
            # Parse the entity
            entity = Entity(string=part)
            # Find out the parameter name
            header = entity.get_header('Content-Disposition')
            value, header_parameters = header
            name = header_parameters['name']
            # Load the value
            body = entity.get_body()
            if 'filename' in header_parameters:
                filename = header_parameters['filename']
                if filename:
                    # Strip the path (for IE).
                    filename = filename.split('\\')[-1]
                    # Default content-type, see
                    # http://tools.ietf.org/html/rfc2045#section-5.2
                    if entity.has_header('content-type'):
                        mimetype = entity.get_header('content-type')[0]
                    else:
                        mimetype = 'text/plain'
                    form[name] = filename, mimetype, body
                else:
                    form[name] = None
            else:
                if name not in form:
                    form[name] = body
                else:
                    if isinstance(form[name], list):
                        form[name].append(body)
                    else:
                        form[name] = [form[name], body]
        return form


    def add_style(self, *args):
        styles = self.styles
        for style in args:
            if style not in styles:
                styles.append(style)


    def add_script(self, *args):
        scripts = self.scripts
        for script in args:
            if script not in scripts:
                scripts.append(script)


    def get_link(self, resource):
        """Return a link to the given resource, from the given context.
        """
        abspath = deepcopy(resource.abspath)
        abspath.endswith_slash = False
        return str(abspath)


    #######################################################################
    # Request
    #######################################################################
    def get_request_line(self):
        return self.soup_message.get_request_line()

    def get_headers(self):
        return self.soup_message.get_headers()


    def get_header(self, name):
        name = name.lower()
        datatype = get_type(name)
        value = self.soup_message.get_header(name)
        if value is None:
            return datatype.get_default()
        try:
            return datatype.decode(value)
        except ValueError:
            log_warning('malformed header: %s: %s' % (name, value),
                        domain='itools.web')
            return datatype.get_default()


    def set_header(self, name, value):
        datatype = get_type(name)
        value = datatype.encode(value)
        self.soup_message.set_header(name, value)


    def get_referrer(self):
        return self.soup_message.get_header('referer')


    def get_form(self):
        if self.method in ('GET', 'HEAD'):
            return self.uri.query
        # XXX What parameters with the fields defined in the query?
        return self.body


    def set_content_type(self, content_type, **kw):
        if type(content_type) is not str:
            raise TypeError('expected string, got %s' % repr(content_type))

        parameters = [ '; %s=%s' % x for x in kw.items() ]
        parameters = ''.join(parameters)
        self.content_type = content_type + parameters


    def set_content_disposition(self, disposition, filename=None):
        if filename:
            disposition = '%s; filename="%s"' % (disposition, filename)

        self.soup_message.set_header('Content-Disposition', disposition)


    def set_default_response(self, status):
        # Build response
        self.status = status
        self.entity = '{0} {1}'.format(status, reason_phrases[status])
        self.set_content_type('text/plain')
        # Set response
        self.set_response_from_context()


    def set_response_from_context(self):
        # Accept cors
        if self.server.accept_cors:
            self.accept_cors()
        # Set default content type XXX ?
        if self.status == 304:
            # "NotModified" request
            # No status, content-type or other header should be added
            self.soup_message.set_status(self.status)
            return
        if self.content_type is None:
            self.content_type = 'text/plain'
        # Set response body
        if self.entity is None:
            self.status = 204
            self.soup_message.set_status(self.status)
            return
        elif isinstance(self.entity, Reference):
            location = context.uri.resolve(self.entity)
            location = str(location)
            self.status = 302
            self.soup_message.set_status(self.status)
            self.soup_message.set_header('Location', location)
            return
        # Never cache if status != 200
        if self.mtime and self.status != 200:
            self.set_header('Last-Modified', self.mtime)
            self.set_header('Cache-Control', 'max-age=1')
        # Set status response
        self.soup_message.set_status(self.status)
        self.soup_message.set_response(self.content_type, self.entity)


    def accept_cors(self):
        origin = context.get_header('Origin')
        self.set_header('Access-Control-Allow-Credentials', 'true')
        self.set_header('Access-Control-Allow-Origin', origin)
        self.set_header('Access-Control-Allow-Headers', 'Authorization')


    #######################################################################
    # API / Status
    #######################################################################
    def http_not_modified(self):
        self.status = 304
        self.soup_message.set_status(304)


    #######################################################################
    # API / Redirect
    #######################################################################
    def come_back(self, message, goto=None, keep=freeze([]), **kw):
        """This is a handy method that builds a resource URI from some
        parameters.  It exists to make short some common patterns.
        """
        # By default we come back to the referrer
        if goto is None:
            goto = self.soup_message.get_header('referer')
            # Replace goto if no referrer
            if goto is None:
                goto = str(self.uri)
                if '/;' in goto:
                    goto = goto.split('/;')[0]

        if type(goto) is str:
            goto = get_reference(goto)

        # Preserve some form values
        form = {}
        for key, value in self.get_form().items():
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
            text = message.gettext(**kw)
            if is_prototype(message, ERROR):
                return goto.replace(error=text)
            else:
                return goto.replace(info=text)
        return goto


    #######################################################################
    # API / Forms
    #######################################################################
    def get_path_query_value(self, name, type=String, default=None):
        """Returns the value for the given name from the path query.
        """
        form = self.path_query_base
        return get_form_value(form, name, type, default)


    def get_query_value(self, name, type=String, default=None):
        """Returns the value for the given name from the query.  Useful for
        POST requests.
        """
        form = self.uri.query
        return get_form_value(form, name, type, default)


    def get_form_value(self, name, type=String, default=None):
        form = self.get_form()
        return get_form_value(form, name, type, default)


    def get_form_keys(self):
        return self.get_form().keys()


    #######################################################################
    # Cookies
    #######################################################################
    def get_cookie(self, name, datatype=None):
        value = None
        if name in self.cookies:
            # Case 1: the cookie was set in this request
            value = self.cookies[name]
        else:
            # Case 2: read the cookie from the request
            cookies = self.get_header('cookie')
            if cookies:
                cookie = cookies.get(name)
                if cookie:
                    value = cookie.value

        if datatype is None:
            return value

        # Deserialize
        if value is None:
            return datatype.get_default()
        value = datatype.decode(value)
        if not datatype.is_valid(value):
            raise ValueError("Invalid cookie value")
        return value


    def set_cookie(self, name, value, **kw):
        self.cookies[name] = value
        # libsoup
        cookie = Cookie(value, **kw)
        cookie = SetCookieDataType.encode({name: cookie})
        self.soup_message.append_header('Set-Cookie', cookie)


    def del_cookie(self, name):
        self.cookies[name] = None
        # libsoup
        expires = 'Thu, 01-Jan-1970 00:00:01 GMT'
        cookie = Cookie('', expires=expires)
        cookie = SetCookieDataType.encode({name: cookie})
        self.soup_message.append_header('Set-Cookie', cookie)


    #######################################################################
    # API / Utilities
    #######################################################################
    def fix_tzinfo(self, datetime, tz=None):
        if tz is None and self.user:
            tz = self.user.get_timezone()

        # 1. Build the tzinfo object
        tzinfo = timezone(tz) if tz else local_tz

        # 2. Change datetime
        if datetime.tzinfo:
            datetime = datetime.astimezone(tzinfo)
        else:
            datetime = tzinfo.localize(datetime)

        return datetime


    def format_datetime(self, datetime, tz=None):
        datetime = self.fix_tzinfo(datetime, tz)
        # Ok
        return format_datetime(datetime, accept=self.accept_language)


    def format_date(self, date):
        return format_date(date, accept=self.accept_language)


    def format_time(self, time):
        return format_time(time, accept=self.accept_language)


    def format_number(self, number, places=2, curr='', pos=u'', neg=u'-',
            trailneg=u""):
        return format_number(number, places=places, curr=curr, pos=pos,
                neg=neg, trailneg=trailneg, accept=self.accept_language)


    def agent_is_a_robot(self):
        footprints = [
            'Ask Jeeves/Teoma', 'Bot/', 'crawler', 'Crawler',
            'freshmeat.net URI validator', 'Gigabot', 'Google',
            'LinkChecker', 'msnbot', 'Yahoo', 'Wget',
            'Python-urllib', 'Python-httplib2/',
            'CFNetwork/', # iPhone apps
            'Zope External Editor',
            ]

        user_agent = self.get_header('User-Agent')
        if not user_agent:
            return True
        for footprint in footprints:
            if footprint in user_agent:
                return True
        return False


    def get_remote_ip(self):
        remote_ip = self.get_header('X-Forwarded-For')
        return remote_ip.split(',', 1)[0].strip() if remote_ip else None


    def _get_auth_token(self, user_token):
        # We use the header X-User-Agent or User-Agent
        ua = self.get_header('X-User-Agent')
        if not ua:
            ua = self.get_header('User-Agent')
        token = '%s:%s' % (user_token, ua)
        return sha224(token).digest()


    def _set_auth_cookie(self, cookie):
        # Compute expires datetime (FIXME Use the request date)
        session_timeout = self.server.session_timeout
        if session_timeout != timedelta(0):
            expires = self.timestamp + session_timeout
            expires = HTTPDate.encode(expires)
        else:
            expires = None

        # Set cookie
        self.set_cookie('iauth', cookie, path='/', expires=expires)


    def login(self, user):
        user_id = user.get_user_id()
        user_token = user.get_auth_token()

        # Make cookie
        token = self._get_auth_token(user_token)
        cookie = '%s:%s' % (user_id, token)
        cookie = quote(encodestring(cookie))
        self._set_auth_cookie(cookie)

        # Set the user
        self.user = user


    def get_authentication_credentials(self):
        """Try to get credentials from Authorization header or Cookies"""

        # Check for credential in headers
        auth_header = self.get_header('Authorization')
        if auth_header:
            # Parse the header credentials
            auth_type, b64_credentials = auth_header
        else:
            # No Authorization header, get credentials in cookies
            b64_credentials = self.get_cookie('iauth')

        if not b64_credentials:
            # No credentials found
            return None, None

        # Try to return the decoded credentials
        try:
            credentials = decodestring(unquote(b64_credentials))
        except Exception:
            raise ValueError('bad credentials "%s"' % b64_credentials)

        return credentials.split(':', 1)


    def authenticate(self):
        """Checks the authentication credentials and sets the context user if all
        checks are ok.
        """
        self.user = None

        # 1. Get credentials with username and token
        try:
            username, token = self.get_authentication_credentials()
        except ValueError as error:
            msg = "Authentication error : %s " % error.message
            log_warning(msg, domain='itools.web')
            return

        if not username or not token:
            return

        # 2. Get the user
        user = self.root.get_user(username)
        if not user:
            return

        # 3. Check the token
        user_token = user.get_auth_token()
        if token == self._get_auth_token(user_token):
            self.user = user


    def logout(self):
        self.del_cookie('iauth')
        self.user = None


    def is_access_allowed(self, resource, view, user=None):
        """Returns True if the given user is allowed to access the given
        method of the given resource. False otherwise.
        """
        if user is None:
            user = self.user

        # Get the access control definition (default to False)
        if view is None:
            return False
        access = getattr(view, 'access_%s' % self.method, view.access)

        # Private (False) or Public (True)
        if type(access) is bool:
            return access

        # Only booleans and strings are allowed
        if type(access) is not str:
            raise TypeError('unexpected value "%s"' % access)

        # Access Control through a method
        method = getattr(self.root, access, None)
        if method is None:
            raise ValueError('access control "%s" not defined' % access)

        return method(user, resource)


    #######################################################################
    # HTTP methods
    #######################################################################
    def find_site_root(self):
        """This method may be overriden to support virtual hosting.
        """
        self.site_root = self.root


    def handle_request(self, soup_message, path):
        # (1) Attach to the soup message and path
        start_time = time()  # Set start time
        context = self()
        context.soup_message = soup_message
        context.path = path

        # (2) If path is null => 400 Bad Request
        if path is None:
            log_warning('Unexpected HTTP path (null)', domain='itools.web')
            context.set_default_response(400)
            return context

        # (3) Get the method that will handle the request
        method_name = soup_message.get_method()
        # 501 Not Implemented
        if method_name not in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD'):
            log_warning('Unexpected "%s" HTTP method' % method_name,
                        domain='itools.web')
            context.set_default_response(501)
            return context

        # (4) Go
        set_context(None)
        set_context(context)
        try:
            context.init_context()
            RequestMethod.handle_request(context)
        except StandardError:
            log_error('Internal error', domain='itools.web')
            context.set_default_response(500)
        finally:
            # Set request_time to the server to log in access
            request_time = time() - start_time
            self.server.request_time = request_time
            set_context(None)
            return context


    def return_json(self, data, status=None):
        if status:
            context.status = status
        self.entity = json.dumps(data, cls=NewJSONEncoder)
        self.set_content_type('application/json')
        return self.entity


###########################################################################
# Keep the context globally
###########################################################################
context = None


def set_context(ctx):
    global context
    if context and ctx:
        # We cannot set context, if already set
        # else, several databases can be attached
        # to handlers
        raise ValueError('Context already exists')
    context = ctx


def get_context():
    return context


#######################################################################
# Internationalization
#######################################################################
def select_language(languages):
    accept = get_context().accept_language
    return accept.select_language(languages)


#######################################################################
# Get from the form or query
#######################################################################
def _get_form_value(form, name, type=String, default=None):
    field, datatype = get_field_and_datatype(type)
    # Figure out the default value
    if default is None:
        default = datatype.get_default()

    # Errors
    required_msg = field.get_error_message('required')
    invalid_msg = field.get_error_message('invalid')

    # Missing
    is_mandatory = getattr(datatype, 'mandatory', False)
    is_missing = form.get(name) is None
    if is_missing:
        # Mandatory: raise an error
        if is_mandatory and is_missing:
            raise FormError(required_msg, missing=True)
        # Optional: return the default value
        return default

    # Multiple values
    if datatype.multiple:
        value = form.get(name)
        if not isinstance(value, list):
            value = [value]
        try:
            values = [ datatype.decode(x) for x in value ]
        except Exception:
            raise FormError(invalid_msg, invalid=True)
        # Check the values are valid
        for value in values:
            if not datatype.is_valid(value):
                raise FormError(invalid_msg, invalid=True)
        return values

    # Single value
    value = form.get(name)
    if isinstance(value, list):
        value = value[0]
    try:
        value = datatype.decode(value)
    except Exception:
        raise FormError(invalid_msg, invalid=True)

    # We consider that if the type deserializes the value to None, then we
    # must use the default.
    if value is None:
        if is_mandatory:
            raise FormError(required_msg, missing=True)
        return default

    # We consider a blank string to be a missing value (FIXME not reliable).
    is_blank = isinstance(value, (str, unicode)) and not value.strip()
    if is_blank:
        if is_mandatory:
            raise FormError(required_msg, missing=True)
    elif not datatype.is_valid(value):
        raise FormError(invalid_msg, invalid=True)
    return value


def check_form_value(field, value):
    if value in field.empty_values:
        return
    errors = []
    for validator in field.get_validators():
        validator = validator(title=field.title, context=context)
        try:
            validator.check(value)
        except ValidationError, e:
            errors.extend(e.get_messages(field))
    if errors:
        raise FormError(messages=errors, invalid=True)


def get_form_value(form, name, type=String, default=None):
    field, datatype = get_field_and_datatype(type)
    # Not multilingual
    is_multilingual = getattr(type, 'multilingual', False)
    if is_multilingual is False:
        value = _get_form_value(form, name, type, default)
        check_form_value(field, value)
        return value
    # Multilingual
    values = {}
    for key, value in form.iteritems():
        if key.startswith('%s:' % name):
            x, lang = key.split(':', 1)
            value =_get_form_value(form, key, type, default)
            values[lang] = value
    check_form_value(field, values)
    return values



class WebLogger(Logger):

    def get_body(self):
        context = get_context()
        if context is None:
            return Logger.get_body(self)

        # The URI and user
        if context.user:
            lines = ['%s (user: %s)\n\n' % (context.uri, context.user.name)]
        else:
            lines = ['%s\n\n' % context.uri]

        # Request header
        lines.append(context.get_request_line() + '\n')
        headers = context.get_headers()
        for key, value in headers:
            lines.append('%s: %s\n' % (key, value))
        lines.append('\n')

        # Ok
        body = Logger.get_body(self)
        lines.extend(body)
        return lines
