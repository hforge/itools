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
from base64 import decodestring
from types import GeneratorType
from urllib import unquote

# Import from itools
from itools.core import freeze
from itools.datatypes import String
from itools.gettext import MSG
from itools.html import stream_to_str_as_html, xhtml_doctype
from itools.http import HTTPContext, ClientError, get_context
from itools.i18n import AcceptLanguageType
from itools.log import Logger, log_warning
from itools.uri import Path, Reference, get_reference
from itools.xml import XMLParser
from exceptions import FormError
from messages import ERROR


DO_NOT_CHANGE = 'do not change'


class WebContext(HTTPContext):

    status = None

    def __init__(self, soup_message, path):
        HTTPContext.__init__(self, soup_message, path)

        # Query
        self.query_schema = {}

        # Split the path so '/a/b/c/;view' becomes ('/a/b/c', 'view')
        path = self.path
        name = path.get_name()
        if name and name[0] == ';':
            self.resource_path = path[:-1]
            self.view_name = name[1:]
        else:
            self.resource_path = path
            self.view_name = None


    def get_link(self, resource):
        """Return a link to the given resource, from the given context.
        """
        # FIXME This method should give an error if the given resource is
        # not within the site root.
        host = self.host
        return '/%s' % host.get_pathto(resource)


    #######################################################################
    # Lazy load
    #######################################################################
    def load_accept_language(self):
        accept_language = self.get_header('Accept-Language') or ''
        return AcceptLanguageType.decode(accept_language)


    def get_host(self, hostname):
        return None


    def load_host(self):
        return self.get_host(self.hostname)


    def get_resource(self, path, soft=False):
        raise NotImplementedError


    def load_resource(self):
        resource = self.get_resource(self.resource_path, soft=True)
        if resource is None:
            raise ClientError(404)
        return resource


    def load_view(self):
        return self.resource.get_view(self.view_name, self.query)


    def get_credentials(self):
        # Credentials
        cookie = self.get_cookie('__ac')
        if cookie is None:
            return None

        try:
            cookie = unquote(cookie)
            cookie = decodestring(cookie)
            username, password = cookie.split(':', 1)
        except Exception:
            log_warning('bad authentication cookie "%s"' % cookie)
            return None

        if username is None or password is None:
            return None

        return username, password


    def get_user(self, credentials):
        return None


    def load_user(self):
        credentials = self.get_credentials()
        if credentials is None:
            return None
        return self.get_user(credentials)


    def load_access(self):
        resource = self.resource
        ac = resource.get_access_control()
        if ac.is_access_allowed(self, resource, self.view):
            return True

        # XXX Special case, we raise an error instead of returning 'False'
        self.access = False
        if self.user:
            raise ClientError(403)
        raise ClientError(401)


    #######################################################################
    # Return conditions
    #######################################################################
    def ok(self, content_type, body, wrap=True):
        # Wrap
        if wrap:
            if type(body) is str:
                body = XMLParser(body, doctype=xhtml_doctype)

            skin = self.host.skin
            body = skin.render(body, self)
        else:
            is_xml = isinstance(body, (list, GeneratorType, XMLParser))
            if is_xml:
                body = stream_to_str_as_html(body)

        # Ok
        self.status = 200
        self.set_body(content_type, body)


    def no_content(self):
        self.status = 204


    def see_other(self, location):
        if type(location) is Reference:
            location = str(location)

        self.status = 303
        self.set_header('Location', location)


    def redirect(self, resource=DO_NOT_CHANGE, view=DO_NOT_CHANGE):
        self.method = 'GET'

        if resource is not DO_NOT_CHANGE:
            self.resource_path = resource
            self.del_attribute('resource')
            self.del_attribute('uri')

        if view is not DO_NOT_CHANGE:
            self.view_name = view
            self.del_attribute('view')
            self.del_attribute('uri')

        if self.view_name:
            path = '%s/;%s' % (self.resource_path, self.view_name)
        else:
            path = self.resource_path
        self.path = Path(path)

        # Redirect
        self.repeat = True


    #######################################################################
    # API / Redirect
    #######################################################################
    def come_back(self, message, goto=None, keep=freeze([]), **kw):
        """This is a handy method that builds a resource URI from some
        parameters.  It exists to make short some common patterns.
        """
        # By default we come back to the referrer
        if goto is None:
            goto = self.get_referrer()
            # Replace goto if no referrer
            if goto is None:
                uri = str(self.uri)
                if '/;' in uri:
                    goto = uri.split('/;')[0]

        if type(goto) is str:
            goto = get_reference(goto)

        # Preserve some form values
        form = {}
        for key, value in self.form.items():
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
            if isinstance(message, ERROR):
                return goto.replace(error=text)
            else:
                return goto.replace(info=text)
        return goto


    #######################################################################
    # API / Forms
    #######################################################################
    def add_query_schema(self, schema):
        self.query_schema.update(schema)


    def get_query_value(self, name, type=None, default=None):
        """Returns the value for the given name from the query.  Useful for
        POST requests.
        """
        if type is None:
            type = self.query_schema.get(name, String)

        return get_form_value(self.query, name, type, default)


    def get_form_value(self, name, type=String, default=None):
        return get_form_value(self.form, name, type, default)


    def get_form_keys(self):
        return self.form.keys()


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
    # API / Utilities
    #######################################################################
    def agent_is_a_robot(self):
        footprints = [
            'Ask Jeeves/Teoma', 'Bot/', 'crawler', 'Crawler',
            'freshmeat.net URI validator', 'Gigabot', 'Google',
            'LinkChecker', 'msnbot', 'Python-urllib', 'Yahoo', 'Wget',
            'Zope External Editor']

        user_agent = self.get_header('User-Agent')
        for footprint in footprints:
            if footprint in user_agent:
                return True
        return False


#######################################################################
# Get from the form or query
#######################################################################
def get_form_value(form, name, type=String, default=None):
    # Figure out the default value
    if default is None:
        default = type.get_default()

    # Missing
    is_mandatory = getattr(type, 'mandatory', False)
    is_missing = form.get(name) is None
    if is_missing:
        # Mandatory: raise an error
        if is_mandatory and is_missing:
            raise FormError(missing=[name])
        # Optional: return the default value
        return default

    # Multiple values
    if type.multiple:
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



class WebLogger(Logger):

    def get_body(self):
        context = get_context()
        if context is None:
            return Logger.get_body(self)

        # The URI and user
        if context.user:
            lines = ['%s (user: %s)\n' % (context.uri, context.user.name)]
        else:
            lines = ['%s\n' % context.uri]

        # TODO
        # Request headers
#       request = context.request
#       details = (
#           request.request_line_to_str()
#           + request.headers_to_str()
#           + '\n')

        # Ok
        body = Logger.get_body(self)
        lines.extend(body)
        return lines

