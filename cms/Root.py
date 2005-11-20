# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from itools.xml.stl import stl
from itools.catalog.Catalog import Catalog
from itools.web import get_context

# Import from itools.cms
from Group import Group
from Handler import Handler
from Metadata import Metadata, Record
from text import PO
from skins import ui
from User import User
from UserFolder import UserFolder
from utils import comeback
from WebSite import WebSite

# Initialize the local logger for error_page
error_page_logger = logging.getLogger('error_page')
error_page_logger.setLevel(logging.ERROR)
error_page_logger_buffer = cStringIO.StringIO()
error_page_logger_handler = logging.StreamHandler(error_page_logger_buffer)
error_page_logger.addHandler(error_page_logger_handler)



class Root(Group, WebSite):

    class_id = 'iKaaro'
    class_title = u'iKaaro'
    class_version = '20051025'
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
    # Zope registry metatype (replaces bootstrap)
    ########################################################################
    @classmethod
    def get_dummy_user(cls, username, password):
        return User(password=password)


    @classmethod
    def manage_addForm(cls, container):
        # Load the template
        path = get_abspath(globals(), 'zmi/add.xml')
        template = get_handler(path)
        # Build the namespace
        namespace = {}
        namespace['title'] = cls.class_title
        namespace['message'] = get_context().request.form.get('message')
        # Process the template
        return stl(template, namespace)


    @classmethod
    def manage_add(cls, container):
        from itools.resources import zope2
        from versioning import VersioningAware

        context = get_context()
        request = context.request
        zope_response = container.REQUEST.RESPONSE

        # Pre-process input parameters
        form = request.form
        name = form['name'].strip()
        title = form['title']
        username = form['username'].strip()
        password = form['password']
        password2 = form['password2']
        # Check the input data
        error_message = None
        if not name:
            error_message = 'You must enter the name'
        elif not username:
            error_message = 'You must enter the username'
        elif not password:
            error_message = 'You must enter the password'
        elif not password2:
            error_message = 'You must enter the password twice'
        elif password != password2:
            error_message = 'The passwords differ'

        if error_message is not None:
            referrer = request.referrer
            zope_response.redirect('%s?message=%s' % (referrer.path,
                                                      error_message))
            return None, None

        # Create new handler
        root_handler = cls(username=username, password=password)

        # Build the user handler, and set it in the request
        user = cls.get_dummy_user(username, password)
        context.user = user

        # Index and archive where appropriate
        catalog = root_handler.get_handler('.catalog')
        for handler, context in root_handler.traverse2():
            abspath = handler.get_abspath()
            if handler.name.startswith('.'):
                context.skip = True
            elif abspath == '/ui':
                context.skip = True
            elif isinstance(handler, Handler):
                print handler.get_abspath()
                catalog.index_document(handler)
                if isinstance(handler, VersioningAware):
                    handler.add_to_archive()

        transaction = transactions.get_transaction()
        transaction.commit()

        # Copy the handler tree from memory the Zope 2 database
        container_path = '/'.join(container.getPhysicalPath()) or '/'
        container_resource = zope2.get_resource(container_path)
        container_resource.set_resource(name, root_handler.resource)

        # Come back
        zope_response.redirect('manage_main')


    metatypes_registry = {}


    @classmethod
    def register_in_zope(cls, context):
        cls.metatypes_registry[cls.class_id] = cls

        def manage_addForm(container, cls=cls):
            """ """
            return cls.manage_addForm(container)

        def manage_add(container, cls=cls):
            """ """
            cls.manage_add(container)

        context.registerClass(cls, meta_type=cls.class_id,
                              constructors=(manage_addForm, manage_add))


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
        self.unindex_handler(handler)
        self.index_handler(handler)


    ########################################################################
    # Skins and themes (themes are a sub-set of the skins)
    def get_themes(self):
        return ['classic', 'surf']


    def get_skin(self):
        context = get_context()

        # Check the request
        form = context.request.form
        if form.has_key('skin_path'):
            return self.get_handler(form['skin_path'])

        # Check the user preferences
        user = context.user
        if user is None:
            return self.get_handler('ui/surf')

        theme = user.get_property('ikaaro:user_theme')
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
        handler_path = context.handler.get_abspath()
        method = context.method
        
        # Build the message
        message_pattern = u'To: %(to_addr)s\n' \
                          u'From: %(from_addr)s\n' \
                          u'Subject: %(subject)s\n' \
                          u'\n' \
                          u'%(body)s\n'
        message = message_pattern % {'to_addr': to_addr,
                                     'from_addr': from_addr,
                                     'subject': subject,
                                     'body': body}
        message = message.encode('UTF-8')
        # Send email
        now = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        uri = "%s/;%s" % (handler_path , method)

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
                 ['about', 'license']]
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
    # Catalog
    ########################################################################
    catalog_form__access__ = 'is_admin'
    catalog_form__label__ = u'Catalog'
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


##    export_catalog__access__ = True
##    def export_catalog(self):
##        from itools.handlers import get_handler
##        tmp = get_handler('/tmp')
##        catalog = self.get_handler('.catalog')
##        tmp.set_handler('catalog', catalog)
##        tmp.save_state()

##        return 'ok'


    #######################################################################
    # Update
    #######################################################################
    def update_20050509(self):
        # Move settings to metadata
        settings = self.get_handler('.settings')
        if settings.state.join is True:
            self.set_property('ikaaro:website_is_open', True)
        self.set_property('ikaaro:website_languages',
                          tuple(settings.state.languages))
        self.metadata.save_state()

        self.resource.del_resource('.settings')


    def update_20050728(self):
        resource = self.resource
        object = resource._get_object().aq_base
        delattr(object, '__before_publishing_traverse__')
        delattr(object, '__browser_default__')
        resource.get_transaction().commit()


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
