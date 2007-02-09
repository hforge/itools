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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
from __future__ import with_statement
import smtplib
from sys import stdout
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
from handlers import Metadata
from registry import register_object_class
from Folder import Folder
from catalog import CatalogAware



class Root(WebSite):

    class_id = 'iKaaro'
    class_title = u'iKaaro'
    class_version = '20061216'
    class_icon16 = 'images/Root16.png'
    class_icon48 = 'images/Root48.png'
    class_views = [
        ['browse_content?mode=thumbnails',
         'browse_content?mode=list'],
        ['new_resource_form'],
        ['edit_metadata_form'],
        ['languages_form', 'anonymous_form', 'contact_options_form'],
        ['permissions_form', 'new_user_form'],
        ['catalog_form', 'check_groups']]

    __fixed_handlers__ = ['users', 'ui']


    __roles__ = [
        {'name': 'ikaaro:members', 'title': u'Members', 'unit': u'Member'},
        {'name': 'ikaaro:admins', 'title': u'Admins', 'unit': u'Admin'}]


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
    # Override RoleAware
    ########################################################################
    def get_role_unit(self, name):
        if name == 'ikaaro:members':
            return self.gettext(u'Member')
        return WebSite.get_role_unit(self, name)


    def get_user_role(self, user_id):
        user_role = WebSite.get_user_role(self, user_id)
        if user_role is not None:
            return user_role
        users = self.get_handler('users')
        if users.has_handler(user_id):
            return 'ikaaro:members'
        return None


    def has_user_role(self, user_id, *roles):
        user_role = self.get_user_role(user_id)
        return user_role in roles


    def set_user_role(self, user_ids, role):
        if role == 'ikaaro:members':
            role = None
        WebSite.set_user_role(self, user_ids, role)


    def get_members(self):
        users = self.get_handler('users')
        return [ x for x in users.get_handler_names()
                 if not x.endswith('.metadata') ]


    def get_members_classified_by_role(self):
        roles = WebSite.get_members_classified_by_role(self)
        members = self.get_handler_names('users')
        members = set(members)
        for role in roles:
            members = members - roles[role]
        roles['ikaaro:members'] = members
        return roles

 
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
                       ('email', 'keyword', True, True),
                       ('lastname', 'keyword', True, True),
                       ('firstname', 'keyword', True, True),
                       ('username', 'keyword', True, False),
                       # Folder's view
                       ('parent_path', 'keyword', True, False),
                       ('paths', 'keyword', True, False),
                       ('name', 'keyword', True, True),
                       ('title_or_name', 'keyword', True, True),
                       ('mtime', 'keyword', False, True),
                       ('size', 'keyword', False, True),
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
        cache['users.metadata'] = self.build_metadata(users, owner=None,
                                        **{'dc:title': {'en': u'Users'}})

        # Add user
        user = users.set_user(username, password)
        self.set_user_role(user.name, 'ikaaro:admins')


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
    # Skins
    def get_skin(self):
        return self.get_handler('ui/aruni')


    ########################################################################
    # Settings
    def get_available_languages(self):
        return ['en', 'es', 'fr', 'zh', 'it']


    def get_default_language(self):
        return 'en'


    ########################################################################
    # Email
    def send_email(self, from_addr, to_addr, subject, body, **kw):
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
        context = get_context()
        smtp_host = context.server.smtp_host
        if smtp_host is None:
            msg = ('the configuration variable "smtp-host" is not defined,'
                   ' check the "config.conf" file')
            raise RuntimeError, msg

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
    about__sublabel__ = u'About'
    def about(self, context):
        handler = self.get_handler('/ui/Root_about.xml')
        return stl(handler)


    ########################################################################
    # Credits
    credits__access__ = True
    credits__label__ = u'About'
    credits__sublabel__ = u'Credits'
    def credits(self, context):
        context.styles.append('/ui/credits.css')

        handler = self.get_handler('/ui/Root_credits.xml')
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


    def _update_catalog(self, quiet=False):
        if quiet is False:
            print 'Updating the catalog:'
        # Start fresh
        self.del_handler('.catalog')
        self.set_handler('.catalog', Catalog(fields=self._catalog_fields))
        catalog = self.get_handler('.catalog')

        # Go
        if quiet is False:
            stdout.write('0')
            stdout.flush()
            str_len = 1
            max_len = 1

        doc_n = 0
        for handler, ctx in self.traverse2(caching=False):
            # Skip virtual handlers
            if handler.real_handler is not None:
                ctx.skip = True
                continue
            # Skip non catalog aware handlers
            if not isinstance(handler, CatalogAware):
                ctx.skip = True
                continue

            doc_n += 1
            # Print progress message 
            if quiet is False:
                stdout.write('\b' * max_len)
                str = '%d %s' % (doc_n, handler.get_abspath())
                str_len = len(str)
                if str_len > max_len:
                    max_len = str_len
                stdout.write(str)
                stdout.write(' ' * (max_len - str_len))
                stdout.flush()
            # Index the document
            catalog.index_document(handler.get_catalog_indexes())

        # It is done
        return doc_n


    update_catalog__access__ = 'is_admin'
    def update_catalog(self, context):
        t0 = time()
        n = self._update_catalog()
        t = time() - t0
        print
        print 'Done. Time taken: %.02f seconds' % t

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
            members = set(members)
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
            group.set_user_role(members - root_users, None)

        return context.come_back(u'Groups fixed.')


    #######################################################################
    # Update
    #######################################################################
    def update_20061216(self):
        # Update roles
        for path in self.get_groups():
            handler = self.get_handler(path)
            for role in handler.get_role_names():
                # Get the users
                filename = '.%s.users' % role.split(':')[1]
                try:
                    users = handler.get_handler(filename)
                except LookupError:
                    pass
                else:
                    users = tuple(users.usernames)
                    # Add to the metadata
                    handler.set_property(role, users)
                    # Remove the old ".users" file
                    handler.del_handler(filename)

        # Update users
        users = self.get_handler('users')
        i = 0
        for name in users.get_handler_names():
            if name.endswith('.metadata'):
                continue
            user = users.get_handler(name) 
            # Update roles
            user_id = str(i)
            for path in user.get_groups():
                group = self.get_handler(path)
                user_role = group.get_user_role(name)
                if user_role is not None:
                    group.set_user_role(user_id, user_role)
            # Rename user
            users.set_handler(user_id, user, move=True)
            users.del_handler(name)
            user = users.get_handler(user_id)
            # Keep the username
            user.set_property('ikaaro:username', name)
            i += 1

        # Save
        get_transaction().commit()

        # Update 'members' index
        self._update_catalog()


register_object_class(Root)
