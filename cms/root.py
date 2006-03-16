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
from itools.handlers import transactions
from itools.xml import namespaces
from itools.stl import stl
from itools.catalog.Catalog import Catalog
from itools.web import get_context

# Import from itools.cms
from Group import Group
from Handler import Handler
from metadata import Metadata, Password
from text import PO
from skins import ui
from users import User, UserFolder
from utils import comeback
from WebSite import WebSite



class Root(Group, WebSite):

    class_id = 'iKaaro'
    class_title = u'iKaaro'
    class_version = '20060205'
    class_icon16 = 'images/Root16.png'
    class_icon48 = 'images/Root48.png'

    __fixed_handlers__ = ['users', 'admins', 'reviewers', 'ui']


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
                       ('mtime_microsecond', 'keyword', False, True),
                       ]


    def get_skeleton(self, username=None, password=None):
        skeleton = {}
        # The catalog must be added first, so everything else is indexed
        # (<index name>, <type>, <indexed>, <stored>)
        catalog = Catalog(fields=self._catalog_fields)
        skeleton['.catalog'] = catalog
        # The archive is used for versioning
        skeleton['.archive'] = handlers.Folder.Folder()
        # Now call the parents get_skeleton
        users = [username]
        skeleton.update(Group.get_skeleton(self, users=users))
        # Reviewers
        reviewers = Group(users=users)
        skeleton['reviewers'] = reviewers
        metadata = self.build_metadata(reviewers, owner=username,
                                       **{'dc:title': {'en': u'Reviewers'}})
        skeleton['.reviewers.metadata'] = metadata
        # Admins
        admins = Group(users=users)
        skeleton['admins'] = admins
        metadata = self.build_metadata(admins, owner=username,
                                       **{'dc:title': {'en': u'Admins'}})
        skeleton['.admins.metadata'] = metadata
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


    def forbidden(self):
        message = (u'Access forbidden, you are not authorized to access'
                   u' this resource.')
        return self.gettext(message)


    def internal_server_error(self):
        namespace = {}
        namespace['traceback'] = traceback.format_exc()

        handler = self.get_handler('/ui/Root_internal_server_error.xml')
        return stl(handler, namespace)


    def not_found(self):
        message = u'The requested resource has not been found.'
        return self.gettext(message)


    ########################################################################
    # Traverse
    ########################################################################
    def _get_handler_names(self):
        return Group._get_handler_names(self) + ['ui']


    def _get_handler(self, segment, resource):
        name = segment.name

        if name == '.catalog':
            return Catalog(resource)
        elif name == '.archive':
            return handlers.Folder.Folder(resource)
        return Group._get_handler(self, segment, resource)


    def _get_virtual_handler(self, segment):
        name = segment.name
        if name == 'ui':
            return ui
        return Group._get_virtual_handler(self, segment)


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
        return Group.get_document_types(self) ##+ [WebSite]


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
            return ['about', 'login_form', 'join_form']
        return ['browse_thumbnails', 'new_resource_form',
                'edit_metadata_form', 'general_form', 'catalog_form', 'about']


    def get_subviews(self, name):
        views = [['browse_thumbnails', 'browse_list'],
                 ['general_form', 'languages_form'],
                 ['about', 'license'],
                 ['catalog_form', 'check_groups']]
        for subviews in views:
            if name in subviews:
                return subviews
        return Group.get_subviews(self, name)


    browse_thumbnails__label__ = u'View'


    ########################################################################
    # About
    about__access__ = True
    about__label__ = u'About'
    about__sublabel__ = u'iKaaro'
    def about(self):
        handler = self.get_handler('/ui/Root_about.xml')
        return stl(handler)


    ########################################################################
    # License
    license__access__ = True
    license__label__ = u'About'
    license__sublabel__ = u'License'
    def license(self):
        handler = self.get_handler('/ui/Root_license.xml')
        return stl(handler)


    ########################################################################
    # Join
    def is_allowed_to_join(self):
        context = get_context()
        website_is_open = context.root.get_property('ikaaro:website_is_open')
        return website_is_open


    join_form__access__ = 'is_allowed_to_join'
    join_form__label__ = u'Join'
    def join_form(self):
        handler = self.get_handler('/ui/Root_join.xml')
        return stl(handler)


    join__access__ = 'is_allowed_to_join'
    def join(self, username, password, password2, **kw):
        users = self.get_handler('users')
        error = users.new_user(username, password, password2)

        message = self.gettext(u'Thanks for joining us, please log in')
        get_context().redirect(';login_form?username=%s&message=%s'
                               % (username, quote(message.encode('utf8'))))


    ########################################################################
    # Maintenance
    ########################################################################

    ########################################################################
    # Catalog
    catalog_form__access__ = 'is_admin'
    catalog_form__label__ = u'Maintenance'
    catalog_form__sublabel__ = u'Update Catalog'
    def catalog_form(self):
        handler = self.get_handler('/ui/Root_catalog.xml')
        return stl(handler)


    update_catalog__access__ = 'is_admin'
    def update_catalog(self):
        # Initialize a new empty catalog
        t0 = time()
        tmp_path = tempfile.mkdtemp()
        tmp_folder = get_handler(tmp_path)
        tmp_folder.set_handler('catalog', Catalog(fields=self._catalog_fields))
        tmp_folder.save_state()
        catalog_resource = tmp_folder.resource.get_resource('catalog')
        catalog = Catalog(catalog_resource)
        # Remove old catalog
        self.del_handler('.catalog')
        t1 = time()
        print 'Updating catalog, initialization:', t1 - t0

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
                if n % 500 == 0:
                    catalog.save_state()
        catalog.save_state()

        t2 = time()
        print 'Updating catalog, indexing:', t2 - t1
        # Set new catalog
        self.set_handler('.catalog', catalog)
        t3 = time()
        print 'Updating catalog, saving:', t3 - t2
        path = tmp_path.split('/')
        path, name = '/'.join(path[:-1]), path[-1]
        get_resource(path).del_resource(name)
        t4 = time()
        print 'Updating catalog, removing temporary files:', t4 - t3
        print 'Updating catalog, total:', t4 - t0

        message = self.gettext(u'%s handlers have been re-indexed.') % n
        comeback(message)


    #######################################################################
    # Check groups
    check_groups__access__ = 'is_admin'
    check_groups__label__ = u'Maintenance'
    check_groups__sublabel__ = u'Check Groups'
    def check_groups(self):
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
    def fix_groups(self):
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
    ximport__access__ = 'is_admin'
    def ximport(self, path):
        from itools.handlers import get_handler
        for resource_name in self.resource.get_resource_names():
            self.resource.del_resource(resource_name)
        source = get_resource(path)
        for resource_name in source.get_resource_names():
            resource = source.get_resource(resource_name)
            self.resource.set_resource(resource_name, resource)
        print 'importing, done'


Group.register_handler_class(Root)
