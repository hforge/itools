# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from the Standard Library
import smtplib
from time import time
import traceback

# Import from itools
from itools.datatypes import FileName
from itools import vfs
from itools.handlers.Folder import Folder as FolderHandler
from itools.handlers.transactions import get_transaction
from itools.stl import stl
from itools.catalog.catalog import Catalog
from itools.web import get_context

# Import from itools.cms
from text import PO
from users import UserFolder
from WebSite import WebSite
from handlers import ListOfUsers, Metadata
from registry import register_object_class
from Folder import Folder
from catalog import CatalogAware



class Root(WebSite):

    class_id = 'iKaaro'
    class_title = u'iKaaro'
    class_version = '20061203'
    class_icon16 = 'images/Root16.png'
    class_icon48 = 'images/Root48.png'
    class_views = [['browse_thumbnails', 'browse_list'],
                   ['new_resource_form'],
                   ['edit_metadata_form'],
                   ['languages_form'],
                   ['permissions_form', 'anonymous_form'],
                   ['catalog_form', 'check_groups'],
                   ['about', 'license']]

    __fixed_handlers__ = ['users', 'ui']


    __roles__ = [
        {'name': 'admins', 'title': u'Admins', 'unit': u'Admin'}]


    ########################################################################
    # Override itools.web.root.Root
    ########################################################################
    def init(self, context):
        # Set the list of needed resources. The method we are going to
        # call may need external resources to be rendered properly, for
        # example it could need an style sheet or a javascript file to
        # be included in the html head (which it can not control). This
        # attribute lets the interface to add those resources.
        context.styles = []
        context.scripts = []
        # Reload the root handler if needed
        if self.is_outdated():
            self.load_state()


    def get_user(self, name):
        users = self.get_handler('users')
        if users.has_handler(name):
            return users.get_handler(name)
        return None


    def before_traverse(self, context):
        # Language negotiation
        user = context.user
        if user is not None:
            language = user.get_property('ikaaro:user_language')
            context.request.accept_language.set(language, 2.0)


    def after_traverse(self, context, body):
        # If there is not content type and the body is not None,
        # wrap it in the skin template
        if context.response.has_header('Content-Type'):
            return body
        return self.get_skin().template(body)


    ########################################################################
    # Skeleton
    ########################################################################
    _catalog_fields = [('text', 'text', True, False),
                       ('title', 'text', True, True),
                       ('owner', 'keyword', True, True),
                       ('is_role_aware', 'bool', True, False),
                       ('format', 'keyword', True, True),
                       ('workflow_state', 'keyword', True, True),
                       ('abspath', 'keyword', True, True),
                       ('members', 'keyword', True, False),
                       # Users
                       ('email', 'keyword', True, False),
                       ('username', 'keyword', True, False),
                       # Folder's view
                       ('parent_path', 'keyword', True, False),
                       ('paths', 'keyword', True, False),
                       ('name', 'keyword', True, True),
                       ('title_or_name', 'keyword', True, True),
                       ('mtime', 'keyword', False, True),
                       ]


    def new(self, username=None, password=None):
        # Call the parent
        WebSite.new(self)

        # Create sub-handlers
        cache = self.cache
        cache['.metadata'] = self.build_metadata(self)
        cache['.catalog'] = Catalog(fields=self._catalog_fields)
        # Users
        users = UserFolder()
        cache['users'] = users
        metadata = self.build_metadata(users, owner=None,
                                       **{'dc:title': {'en': u'Users'}})
        cache['users.metadata'] = metadata

        # Add user
        user = users.set_user(username, password)
        self.set_role('admins', user.name)


    def get_catalog_metadata_fields(self):
        return [field[0] for field in self._catalog_fields if field[3]]


    ########################################################################
    # Publish
    ########################################################################
    def unauthorized(self, context):
        return self.login_form(context)


    def forbidden(self, context):
        message = (u'Access forbidden, you are not authorized to access'
                   u' this resource.')
        return self.gettext(message).encode('utf-8')


    def internal_server_error(self, context):
        namespace = {'traceback': traceback.format_exc()}

        handler = self.get_handler('/ui/Root_internal_server_error.xml')
        return stl(handler, namespace)


    def not_found(self, context):
        namespace = {'uri': str(context.uri)}

        # Don't show the skin if it is not going to work
        request = context.request
        if request.has_header('x-base-path'):
            try:
                self.get_handler('%s/ui' % request.get_header('x-base-path'))
            except LookupError:
                response = context.response
                response.set_header('content-type', 'text/html; charset=UTF-8')

        handler = self.get_handler('/ui/Root_not_found.xml')
        return stl(handler, namespace)


    ########################################################################
    # Traverse
    ########################################################################
    def _get_handler_names(self):
        return WebSite._get_handler_names(self) + ['ui']


    def _get_handler(self, segment, uri):
        name = segment.name

        if name == '.catalog':
            return Catalog(uri)
        elif name == '.archive':
            return FolderHandler(uri)
        return WebSite._get_handler(self, segment, uri)


    ########################################################################
    # API
    ########################################################################
    def get_metadata(self):
        return self.get_handler('.metadata')

    metadata = property(get_metadata, None, None, "")


    def get_usernames(self):
        return self.get_handler('users').get_usernames()


##  def get_document_types(self):
##      return WebSite.get_document_types(self) + [WebSite]


    ########################################################################
    # Index & Search
    def index_handler(self, handler):
        catalog = self.get_handler('.catalog')
        document = handler.get_catalog_indexes()
        n = catalog.index_document(document)


    def unindex_handler(self, handler):
        catalog = self.get_handler('.catalog')

        abspath = handler.get_abspath()
        for document in catalog.search(abspath=abspath).get_documents():
            catalog.unindex_document(document.__number__)


    def reindex_handler(self, handler):
        if handler.real_handler is not None:
            handler = handler.real_handler
        self.unindex_handler(handler)
        self.index_handler(handler)


    def search(self, **kw):
        catalog = self.get_handler('.catalog')
        return catalog.search(**kw)


    ########################################################################
    # Skins and themes (themes are a sub-set of the skins)
    def get_themes(self):
        return ['aruni']


    def get_skin(self):
        context = get_context()


        # Default
        themes = self.get_themes()
        theme = themes[0]

        return self.get_handler('ui/%s' % theme)


    ########################################################################
    # Settings
    def get_available_languages(self):
        return ['en', 'es', 'fr', 'zh', 'it']


    def get_default_language(self):
        return 'en'


    ########################################################################
    # Email
    def send_email(self, from_addr, to_addr, subject, body, **kw):
        context = get_context()
        response = context.response

        # Hard coded encoding, to UTF-8
        encoding = 'UTF-8'
        # Build the message
        message_pattern = (
            u'To: %(to_addr)s\n'
            u'From: %(from_addr)s\n'
            u'Subject: %(subject)s\n'
            u'Content-Transfer-Encoding: 8bit\n'
            u'Content-Type: text/plain; charset="%(encoding)s"\n'
            u'\n'
            u'%(body)s\n')
        message = message_pattern % {'to_addr': to_addr,
                                     'from_addr': from_addr,
                                     'subject': subject,
                                     'body': body,
                                     'encoding': encoding}
        message = message.encode(encoding)
        # Send email
        smtp_host = context.server.smtp_host
        # XXX Fallback for backwards compatibility, introduced in 0.14.2
        if smtp_host is None:
            smtp_host = self.smtp_host
        smtp = smtplib.SMTP(smtp_host)
        smtp.sendmail(from_addr, to_addr, message)
        smtp.quit()


    ########################################################################
    # Back Office
    ########################################################################

    ########################################################################
    # About
    about__access__ = True
    about__label__ = u'About'
    about__sublabel__ = u'iKaaro'
    def about(self, context):
        handler = self.get_handler('/ui/Root_about.xml')
        return stl(handler)


    ########################################################################
    # License
    license__access__ = True
    license__label__ = u'About'
    license__sublabel__ = u'License'
    def license(self, context):
        handler = self.get_handler('/ui/Root_license.xml')
        return stl(handler)


    ########################################################################
    # Maintenance
    ########################################################################

    ########################################################################
    # Catalog
    catalog_form__access__ = 'is_admin'
    catalog_form__label__ = u'Maintenance'
    catalog_form__sublabel__ = u'Update Catalog'
    def catalog_form(self, context):
        handler = self.get_handler('/ui/Root_catalog.xml')
        return stl(handler)


    def _update_catalog(self):
        t0 = time()
        # Start fresh
        self.del_handler('.catalog')
        self.set_handler('.catalog', Catalog(fields=self._catalog_fields))
        catalog = self.get_handler('.catalog')

        # Go
        n = 0
        for handler, ctx in self.traverse2(caching=False):
            # Skip virtual handlers
            if handler.real_handler is not None:
                ctx.skip = True
                continue
            # Skip non catalog aware handlers
            if not isinstance(handler, CatalogAware):
                ctx.skip = True
                continue
            # Index the document
            print n, handler.get_abspath()
            catalog.index_document(handler.get_catalog_indexes())
            n += 1

        # It is done
        t = time() - t0
        print 'Updating catalog, total:', t


    update_catalog__access__ = 'is_admin'
    def update_catalog(self, context):
        self._update_catalog()

        message = u'$n handlers have been indexed in $time seconds.'
        return context.come_back(message, n=n, time=('%.02f' % t))


    #######################################################################
    # Check groups
    def get_groups(self):
        """
        Returns a list with all the subgroups, including the subgroups of
        the subgroups, etc..
        """
        results = self.search(is_role_aware=True)
        return [ x.abspath for x in results.get_documents() ]


    check_groups__access__ = 'is_admin'
    check_groups__label__ = u'Maintenance'
    check_groups__sublabel__ = u'Check Groups'
    def check_groups(self, context):
        namespace = {}

        groups = []
        root_users = self.get_handler('users').get_usernames()
        for path in self.get_groups():
            group = self.get_handler(path)
            members = group.get_members()
            if not members.issubset(root_users):
                missing = list(members - root_users)
                missing.sort()
                missing = ' '.join(missing)
                groups.append({'path': path, 'users': missing})
        namespace['groups'] = groups

        handler = self.get_handler('/ui/Root_check_groups.xml')
        return stl(handler, namespace)


    fix_groups__access__ = 'is_admin'
    def fix_groups(self, context):
        root_users = self.get_handler('users').get_usernames()
        for path in self.get_groups():
            group = self.get_handler(path)
            members = group.get_members()
            for username in members - root_users:
                group.del_roles(username)

        return context.come_back(u'Groups fixed.')


    #######################################################################
    # Update
    #######################################################################
    def update_20061203(self):
        users = self.get_handler('users')
        i = 0
        for name in users.get_handler_names():
            if name.endswith('.metadata'):
                continue
            user = users.get_handler(name) 
            # Update roles
            user_id = str(i)
            for role_aware_object_path in user.get_groups():
                role_aware_object = self.get_handler(role_aware_object_path)
                for role_name in role_aware_object.get_role_names():
                    role = role_aware_object.get_role(role_name)
                    if name in role.get_usernames():
                        role.add(user_id)
            # Rename user
            users.set_handler(user_id, user, move=True)
            users.del_handler(name)
            user = users.get_handler(user_id)
            # Keep the username
            user.set_property('ikaaro:username', name)
            i += 1
        # Update catalog
        self._update_catalog()


register_object_class(Root)
