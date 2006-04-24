# -*- coding: ISO-8859-1 -*-
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
from copy import copy
import cStringIO
import datetime
import logging
import smtplib
import tempfile
from time import time
import traceback
from urllib import quote

# Import from itools
from itools import get_abspath
from itools.resources import get_resource
from itools import handlers
from itools.handlers import get_handler
from itools.handlers.transactions import get_transaction
from itools.xml import namespaces
from itools.stl import stl
from itools.catalog.Catalog import Catalog
from itools.web import get_context

# Import from itools.cms
from Group import RoleAware
from text import PO
from users import User, UserFolder
from utils import comeback
from WebSite import WebSite



class Root(RoleAware, WebSite):

    class_id = 'iKaaro'
    class_title = u'iKaaro'
    class_version = '20060205'
    class_icon16 = 'images/Root16.png'
    class_icon48 = 'images/Root48.png'

    __fixed_handlers__ = ['users', 'ui']


    __roles__ = [
        {'name': 'reviewers', 'title': u'Reviewers', 'unit': u'Reviewer'},
        {'name': 'admins', 'title': u'Admins', 'unit': u'Admin'}]


    ########################################################################
    # Skeleton
    ########################################################################
    _catalog_fields = [('text', 'text', True, False),
                       ('title', 'text', True, True),
                       ('owner', 'keyword', True, True),
                       ('is_group', 'bool', True, False),
                       ('format', 'keyword', True, True),
                       ('workflow_state', 'keyword', True, True),
                       ('abspath', 'keyword', True, True),
                       ('usernames', 'keyword', True, False),
                       # Folder's view
                       ('parent_path', 'keyword', True, True),
                       ('name', 'keyword', True, True),
                       ('title_or_name', 'keyword', True, True),
                       ('mtime', 'keyword', False, True),
                       ]


    def get_skeleton(self, username=None, password=None):
        # First call the parent's get_skeleton
        users = [username]
        skeleton = RoleAware.get_skeleton(self, admins=users)
        # The catalog, index and search
        skeleton['.catalog'] = Catalog(fields=self._catalog_fields)
        # The archive is used for versioning
        skeleton['.archive'] = handlers.Folder.Folder()
        # Metadata
        skeleton['.metadata'] = self.build_metadata(self)
        # Users
        users = UserFolder(users=[(username, password)])
        skeleton['users'] = users
        metadata = self.build_metadata(users, owner=username,
                                       **{'dc:title': {'en': u'Users'}})
        skeleton['.users.metadata'] = metadata
        # Message catalog
        en_po = PO()
        skeleton['en.po'] = en_po
        skeleton['.en.po.metadata'] = self.build_metadata(en_po)
        # That's all
        return skeleton


    def get_catalog_metadata_fields(self):
        return [field[0] for field in self._catalog_fields if field[3]]


    ########################################################################
    # Publish
    ########################################################################
    def before_traverse(self):
        context = get_context()
        # Language negotiation
        user = context.user
        if user is not None:
            language = user.get_property('ikaaro:user_language')
            context.request.accept_language.set(language, 2.0)


    def after_traverse(self):
        context = get_context()
        request, response = context.request, context.response

        # If there is not content type and the body is not None,
        # wrap it in the skin template
        response_body = response.state.body
        if request.method == 'GET' and response_body is not None:
            if not response.has_header('Content-Type'):
                skin = self.get_skin()
                response_body = skin.template(response_body)
                response.set_body(response_body)


    def forbidden(self, context):
        message = (u'Access forbidden, you are not authorized to access'
                   u' this resource.')
        return self.gettext(message)


    def internal_server_error(self, context):
        namespace = {}
        namespace['traceback'] = traceback.format_exc()

        handler = self.get_handler('/ui/Root_internal_server_error.xml')
        return stl(handler, namespace)


    def not_found(self, context):
        message = u'The requested resource has not been found.'
        return self.gettext(message)


    ########################################################################
    # Traverse
    ########################################################################
    def _get_handler_names(self):
        return WebSite._get_handler_names(self) + ['ui']


    def _get_handler(self, segment, resource):
        name = segment.name

        if name == '.catalog':
            return Catalog(resource)
        elif name == '.archive':
            return handlers.Folder.Folder(resource)
        return WebSite._get_handler(self, segment, resource)


    ########################################################################
    # API
    ########################################################################
    def get_metadata(self):
        return self.get_handler('.metadata')

    metadata = property(get_metadata, None, None, "")


    def get_user(self, name):
        return self.get_handler('users/%s' % name)


    def get_usernames(self):
        return self.get_handler('users').get_usernames()


    def get_groups(self):
        """
        Returns a list with all the subgroups, including the subgroups of
        the subgroups, etc..
        """
        groups = self.search(is_group=True)
        groups = [ x.abspath for x in groups if x.abspath != '/' ]
        return groups


    def get_document_types(self):
        return WebSite.get_document_types(self) ##+ [WebSite]


    ########################################################################
    # Index & Search
    def index_handler(self, handler):
        catalog = self.get_handler('.catalog')
        document = handler.get_catalog_indexes()
        n = catalog.index_document(document)


    def unindex_handler(self, handler):
        catalog = self.get_handler('.catalog')

        abspath = handler.get_abspath()
        for document in catalog.search(abspath=abspath):
            catalog.unindex_document(document.__number__)


    def reindex_handler(self, handler):
        if handler.real_handler is not None:
            handler = handler.real_handler
        self.unindex_handler(handler)
        self.index_handler(handler)


    ########################################################################
    # Skins and themes (themes are a sub-set of the skins)
    def get_themes(self):
        return ['aruni']


    def get_skin(self):
        context = get_context()

        # Check the request (designed to be used from Apache)
        form = context.request.form
        if form.has_key('skin_path'):
            return self.get_handler(form['skin_path'])

        # Default
        themes = self.get_themes()
        theme = themes[0]

        # Check the user preferences
        user = context.user
        if user is not None:
            theme = user.get_property('ikaaro:user_theme')
            if theme not in themes:
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
        smtp_host = self.smtp_host
        smtp = smtplib.SMTP(smtp_host)
        smtp.sendmail(from_addr, to_addr, message)
        smtp.quit()


    ########################################################################
    # Back Office
    ########################################################################
    def get_views(self):
        user = get_context().user
        if user is None:
            return ['about', 'login_form', 'register_form']
        return ['browse_thumbnails', 'new_resource_form', 'edit_metadata_form',
                'general_form', 'permissions_form', 'catalog_form', 'about']


    def get_subviews(self, name):
        views = [['browse_thumbnails', 'browse_list'],
                 ['general_form', 'languages_form'],
                 ['about', 'license'],
                 ['catalog_form', 'check_groups']]
        for subviews in views:
            if name in subviews:
                return subviews
        return WebSite.get_subviews(self, name)


    browse_thumbnails__label__ = u'Contents'


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


    update_catalog__access__ = 'is_admin'
    def update_catalog(self, context):
        # Initialize a new empty catalog
        t0 = time()
        transaction = get_transaction()
        # Init transaction (because we use sub-transactions)
        server = get_context().server
        server.start_commit()

        try:
            # Start fresh
            self.del_handler('.catalog')
            self.set_handler('.catalog', Catalog(fields=self._catalog_fields))
            transaction.commit()

            # Initialize a new empty catalog
            catalog = self.get_handler('.catalog')
            t1 = time()
            print 'Updating catalog, init:', t1 - t0

            n = 0
            for handler, context in self.traverse2():
                name = handler.name
                abspath = handler.get_abspath()

                if name.startswith('.'):
                    context.skip = True
                elif abspath == '/ui':
                    context.skip = True
                elif handler.real_handler is not None and not abspath == '/ui':
                    context.skip = True
                elif not name.startswith('.'):
                    print n, abspath
                    catalog.index_document(handler.get_catalog_indexes())
                    n += 1
                    # Avoid too much memory usage but saving changes
                    if n % 1000 == 0:
                        transaction.commit()
            transaction.commit()
            t2 = time()
            print 'Updating catalog, indexing:', t2 - t1
        except:
            server.end_commit_on_error()
            raise
        else:
            server.end_commit_on_success()
            t3 = time()
            print 'Updating catalog, sync:', t3 - t2

        print 'Updating catalog, total:', t3 - t0

        message = self.gettext(u'%s handlers have been re-indexed.') % n
        comeback(message)


    #######################################################################
    # Check groups
    check_groups__access__ = 'is_admin'
    check_groups__label__ = u'Maintenance'
    check_groups__sublabel__ = u'Check Groups'
    def check_groups(self, context):
        namespace = {}

        groups = []
        root_users = self.get_handler('users').get_usernames()
        for path in self.get_groups():
            group = self.get_handler(path)
            group_users = group.get_usernames()
            if not group_users.issubset(root_users):
                missing = list(group_users - root_users)
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
            group_users = group.get_usernames()
            for username in group_users - root_users:
                group.remove_user(username)

        message = u'Groups fixed.'
        comeback(self.gettext(message))


    #######################################################################
    # Update
    #######################################################################
    def update_20051025(self):
        """Folders now wear the 'folder' format in their metadata."""
        from Folder import Folder

        reindex_handler = self.reindex_handler
        for handler, context in self.traverse2():
            name = handler.name
            abspath = handler.abspath
            if name.startswith('.'):
                context.skip = True
            elif abspath == '/ui':
                context.skip = True
            elif handler is self:
                pass
            elif isinstance(handler, Folder):
                format = handler.get_property('format')
                if format == '':
                    print abspath
                    handler.set_property('format', Folder.class_id)
                    reindex_handler(handler)


    def update_20060205(self):
        users = self.get_handler('users')
        for user in users.search_handlers(handler_class=User):
            data = user.get_handler('.data')
            # Move email and password to the metadata
            user.set_property('ikaaro:email', data.state.email)
            password = Password.decode(data.state.password)
            user.set_property('ikaaro:password', password)
            # Remove obsolete resource
            user.resource.del_resource('.data')


    #######################################################################
    # Import
    #######################################################################
##    ximport__access__ = 'is_admin'
##    def ximport(self, path):
##        from itools.handlers import get_handler
##        for resource_name in self.resource.get_resource_names():
##            self.resource.del_resource(resource_name)
##        source = get_resource(path)
##        for resource_name in source.get_resource_names():
##            resource = source.get_resource(resource_name)
##            self.resource.set_resource(resource_name, resource)
##        print 'importing, done'


WebSite.register_handler_class(Root)
