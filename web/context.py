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
from urllib import unquote

# Import from itools
from itools.core import freeze, lazy
from itools.datatypes import String
from itools.html import xhtml_doctype
from itools.http import HTTPContext, ClientError, ServerError, get_context
from itools.i18n import AcceptLanguageType
from itools.log import Logger, log_warning, log_error
from itools.uri import Path, Reference, get_reference
from itools.xml import XMLParser
from exceptions import FormError
from messages import ERROR


DO_NOT_CHANGE = 'do not change'

status2name = {
    401: 'http_unauthorized',
    403: 'http_forbidden',
    404: 'http_not_found',
    405: 'http_method_not_allowed',
    409: 'http_conflict',
    500: 'http_internal_server_error'}



class WebContext(HTTPContext):

    status = None

    def __init__(self, soup_message, path):
        HTTPContext.__init__(self, soup_message, path)

        # Resource path and view
        self.split_path()


    def split_path(self):
        # Split the path so '/a/b/c/;view' becomes ('/a/b/c', 'view')
        path = self.path
        name = path.get_name()
        if name and name[0] == ';':
            self.resource_path = path[:-1]
            self.view_name = name[1:]
        else:
            self.resource_path = path
            self.view_name = None


    def get_physical_path(self, logical_path):
        """Returns the physical path from the given logical path.
        """
        if self.host is None:
            return logical_path
        path = '/%s%s' % (self.host, logical_path)
        return Path(path)


    def get_logical_path(self, physical_path):
        """Returns the logical path from the given physical path.
        """
        if self.host is None:
            return physical_path
        if physical_path[0] != self.host:
            return None
        return physical_path[1:]


    #######################################################################
    # Lazy load
    #######################################################################
    @lazy
    def accept_language(self):
        accept_language = self.get_header('Accept-Language') or ''
        return AcceptLanguageType.decode(accept_language)


    def get_host(self, hostname):
        return None


    @lazy
    def host(self):
        return self.get_host(self.hostname)


    def get_resource(self, path, soft=False):
        raise NotImplementedError


    @lazy
    def resource(self):
        resource = self.get_resource(self.resource_path, soft=True)
        if resource is None:
            raise ClientError(404)
        return resource


    @lazy
    def view(self):
        resource = self.resource
        view = resource.get_view(self.view_name, self.query)
        if view is None:
            raise ClientError(404)
        return view(resource=resource, context=self)


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
            log_warning('bad authentication cookie "%s"' % cookie,
                        domain='itools.web')
            return None

        if username is None or password is None:
            return None

        return username, password


    def get_user(self, credentials):
        return None


    @lazy
    def user(self):
        credentials = self.get_credentials()
        if credentials is None:
            return None
        return self.get_user(credentials)


    @lazy
    def access(self):
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
    # Handle requests
    #######################################################################
    def handle_request(self):
        try:
            self.access
            method = self.known_methods[self.method]
            method = getattr(self, method)
            method()
        except (ClientError, ServerError), error:
            status = error.status
            self.status = status
            self.resource = self.get_resource('/')
            self.del_attribute('view')
            self.view_name = status2name[status]
            self.access = True
            self.handle_request()
        except Exception:
            log_error('Internal Server Error', domain='itools.web')
            self.status = 500
            self.method = 'GET'
            self.resource = self.get_resource('/')
            self.del_attribute('view')
            self.view_name = 'http_internal_server_error'
            self.access = True
            self.handle_request()
        else:
            if self.status is None:
                self.status = 200
            self.set_status(self.status)


    known_methods = freeze({
        'OPTIONS': 'http_options',
        'GET': 'http_get',
        'HEAD': 'http_get',
        'POST': 'http_post'})


    def get_allowed_methods(self):
        obj = self.view or self.resource
        methods = [
            x for x in self.known_methods
            if getattr(obj, self.known_methods[x], None) ]
        methods = set(methods)
        methods.add('OPTIONS')
        return methods


    def http_options(self):
        methods = self.get_allowed_methods()
        self.set_status(200)
        self.set_header('Allow', ','.join(methods))


    def http_get(self):
        resource = self.resource
        view = self.view
        try:
            view.cook('get')
        except FormError, error:
            # FIXME
            raise
        else:
            self.commit = False
            view.http_get()


    def http_post(self):
        resource = self.resource
        view = self.view
        try:
            view.cook('post')
        except FormError, error:
            self.message = error.get_message()
            self.commit = False
            view.http_get()
        else:
            self.commit = True
            view.http_post()


    def close_transaction(self):
        if self.commit is True:
            try:
                self.save_changes()
            finally:
                self.abort_changes()
        else:
            self.abort_changes()


    def abort_changes(self):
        raise NotImplementedError


    def save_changes(self):
        raise NotImplementedError


    #######################################################################
    # Return conditions
    #######################################################################
    def ok(self, content_type, body):
        self.close_transaction()
        self.status = 200
        self.set_body(content_type, body)


    def ok_wrap(self, content_type, body):
        self.close_transaction()
        self.status = 200

        # Wrap
        if type(body) is str:
            body = XMLParser(body, doctype=xhtml_doctype)

        root = self.get_resource('/')
        skin = root.get_skin()
        skin = skin(resource=root, context=self, body=body)
        skin.cook('get')
        body = skin.render()
        self.set_body(content_type, body)


    def created(self, location):
        self.close_transaction()
        self.status = 201
        self.method = 'GET'
        self.set_header('Location', location)
        self.del_attribute('uri')
        self.del_attribute('resource')
        self.del_attribute('view')
        self.path = Path(location)
        self.split_path()
        self.handle_request()


    def no_content(self):
        self.close_transaction()
        self.status = 204


    def see_other(self, location):
        self.close_transaction()
        if type(location) is Reference:
            location = str(location)

        self.status = 303
        self.set_header('Location', location)


    def redirect(self, resource=DO_NOT_CHANGE, view=DO_NOT_CHANGE):
        self.close_transaction()
        self.method = 'GET'

        if resource is not DO_NOT_CHANGE:
            path = resource if type(resource) is Path else Path(resource)
            # FIXME Check the path is absolute
            self.resource_path = path
            self.del_attribute('resource')
            self.del_attribute('uri')

        if view is not DO_NOT_CHANGE:
            self.view_name = view
            self.del_attribute('view')
            self.del_attribute('uri')

        if self.view_name:
            self.path = self.resource_path.resolve2(self.view_name)
        else:
            self.path = self.resource_path

        # Redirect
        self.handle_request()


    #######################################################################
    # API
    #######################################################################
    # TODO For backwards compatibility, to be removed
    def get_query_value(self, name, datatype=String, default=None):
        value = self.query.get(name)
        if value is None:
            if default is None:
                return datatype.get_default()
            return default

        return datatype.decode(value)


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



class WebLogger(Logger):

    def get_body(self):
        context = get_context()
        if context is None:
            return Logger.get_body(self)

        # The URI and user
        if context.user:
            username = context.user.get_name()
            lines = ['%s (user: %s)\n' % (context.uri, username)]
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

