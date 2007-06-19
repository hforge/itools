# -*- coding: UTF-8 -*-
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
import cgi
from datetime import datetime
import logging

# Import from itools
from itools import get_abspath
from itools.uri import Path
from itools.datatypes import QName
from itools import vfs
from itools.catalog import CatalogAware
from itools.handlers import Handler as BaseHandler
from itools.schemas import get_datatype
from itools.stl import stl
from itools.gettext import DomainAware, get_domain
from itools.http import Forbidden
from itools.web import get_context, Node as BaseNode
from handlers import Lock, Metadata
from messages import *
import webdav
from versioning import VersioningAware
from workflow import WorkflowAware
from catalog import schedule_to_reindex


# Initialize logger
logger = logging.getLogger('update')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)



class Node(BaseNode):

    class_views = []

    ########################################################################
    # HTTP
    ########################################################################
    def get_method(self, name):
        try:
            method = getattr(self, name)
        except AttributeError:
            return None
        return method


    GET__access__ = 'is_allowed_to_view'
    def GET(self, context):
        method = self.get_firstview()
        # Check access
        if method is None:
            raise Forbidden

        # Redirect
        return context.uri.resolve2(';%s' % method)


    POST__access__ = 'is_authenticated'
    def POST(self, context):
        for name in context.get_form_keys():
            if name.startswith(';'):
                method_name = name[1:]
                method = self.get_method(method_name)
                if method is None:
                    # XXX When the method is not defined, is it the best
                    # thing to do a Not-Found error?
                    # XXX Send a 404 status code.
                    return context.root.not_found(context)
                # Check security
                user = context.user
                ac = self.get_access_control()
                if not ac.is_access_allowed(user, self, method_name):
                    raise Forbidden
                # Call the method
                return method(context)

        raise Exception, 'the form did not define the action to do'


    ########################################################################
    # Tree
    ########################################################################
    def get_site_root(self):
        from website import WebSite
        handler = self
        while not isinstance(handler, WebSite):
            handler = handler.parent
        return handler


    # XXX See if we can get rid of this code (get_access_control may be used
    # instead)
    def get_workplace(self):
        from users import User
        from website import WebSite

        user = get_context().user
        # Get the "workplace"
        node = self
        while node is not None:
            if isinstance(node, (WebSite, User)):
                return node
            node = node.parent

        # We never should reach here (XXX Raise an exception?)
        return None


    ########################################################################
    # Properties
    ########################################################################
    def get_property(self, name, language=None):
        return get_datatype(name).default


    def get_title_or_name(self):
        return self.name


    def get_mtime(self):
        return self.timestamp

    mtime = property(get_mtime, None, None, "")


    def get_path_to_icon(self, size=16, from_handler=None):
        if hasattr(self, 'icon%s' % size):
            return ';icon%s' % size
        path_to_icon = getattr(self.__class__, 'class_icon%s' % size)
        if from_handler is None:
            from_handler = self
        return '%sui/%s' % (from_handler.get_pathtoroot(), path_to_icon)


    ########################################################################
    # Internationalization
    ########################################################################
    class_domain = 'itools'

    @classmethod
    def select_language(cls, languages):
        accept = get_context().request.accept_language
        return accept.select_language(languages)


    @classmethod
    def gettext(cls, message, language=None):
        gettext = DomainAware.gettext

        if cls.class_domain == 'itools':
            domain_names = ['itools']
        else:
            domain_names = [cls.class_domain, 'itools']

        for domain_name in domain_names:
            if language is None:
                domain = get_domain(domain_name)
                languages = domain.get_languages()
                language = cls.select_language(languages)

            translation = gettext(message, language, domain=domain_name)
            if translation != message:
                return translation

        return message


    ########################################################################
    # User interface
    ########################################################################
    def get_firstview(self):
        """
        Returns the first allowed object view url, or None if there aren't.
        """
        user = get_context().user
        ac = self.get_access_control()
        for view in self.get_views():
            # Check the security
            method_name = view.split('?')[0]
            if ac.is_access_allowed(user, self, method_name):
                return view
        return None


    def get_views(self):
        return [ x[0] for x in self.class_views ]


    def get_subviews(self, name):
        for block in self.class_views:
            if name in block:
                if len(block) == 1:
                    return []
                return block[:]
        return []



class Handler(CatalogAware, Node, DomainAware, BaseHandler):

    def set_changed(self):
        BaseHandler.set_changed(self)
        if self.uri is not None:
            schedule_to_reindex(self)


    @classmethod
    def new_instance(cls, context):
        return cls()


    ########################################################################
    # Indexing
    ########################################################################
    def get_catalog_indexes(self):
        from access import RoleAware
        from file import File
        from users import User

        name = self.name
        abspath = self.get_abspath()
        get_property = self.get_metadata().get_property
        title = self.get_title()

        mtime = self.timestamp
        if mtime is None:
            mtime = datetime.now()

        document = {
            'name': name,
            'abspath': abspath,
            'format': get_property('format'),
            'title': title,
            'owner': get_property('owner'),
            'title_or_name': title or name,
            'mtime': mtime.strftime('%Y%m%d%H%M%S'),
            }

        # Full text
        try:
            text = self.to_text()
        except NotImplementedError:
            pass
        except:
            context = get_context()
            if context is not None:
                context.server.log_error(context)
        else:
            document['text'] = text

        # Parent path
        parent = self.parent
        if parent is not None:
            if parent.parent is None:
                document['parent_path'] = '/'
            else:
                document['parent_path'] = parent.get_abspath()

        # All paths
        abspath = Path(abspath)
        document['paths'] = [ abspath[:x] for x in range(len(abspath) + 1) ]

        # Size
        if isinstance(self, File):
            # FIXME We add an arbitrary size so files will always be bigger
            # than folders. This won't work when there is a folder with more
            # than that size.
            document['size'] = 2**30 + len(self.to_str())
        else:
            names = [ x for x in self.get_handler_names()
                      if (x[0] != '.' and x[-9:] != '.metadata') ]
            document['size'] = len(names)

        # Users
        if isinstance(self, User):
            document['firstname'] = self.get_property('ikaaro:firstname')
            document['lastname'] = self.get_property('ikaaro:lastname')

        # Workflow state
        if isinstance(self, WorkflowAware):
            document['workflow_state'] = self.get_workflow_state()

        # Role Aware
        if isinstance(self, RoleAware):
            document['is_role_aware'] = True
            document['members'] = self.get_members()

        # Versioning
        if isinstance(self, VersioningAware):
            document['is_version_aware'] = True
            # Last Author (used in the Last Changes view)
            history = self.get_property('ikaaro:history')
            if history:
                user_id = history[-1][(None, 'user')]
                user = self.get_handler('/users/%s' % user_id)
                document['last_author'] = user.get_title()

        return document


    ########################################################################
    # Properties
    ########################################################################
    def has_property(self, name, language=None):
        metadata = self.get_metadata()
        if metadata is None:
            return Node.has_property(self, name)
        return metadata.has_property(name, language=language)


    def get_property(self, name, language=None):
        metadata = self.get_metadata()
        if metadata is None:
            return Node.get_property(self, name)
        return metadata.get_property(name, language=language)


    def set_property(self, name, value, language=None):
        schedule_to_reindex(self)
        self.metadata.set_property(name, value, language=language)


    def del_property(self, name, language=None):
        schedule_to_reindex(self)
        self.metadata.del_property(name, language=language)


    ########################################################################
    # Shorthands (XXX remove as many as posible)
    def get_title(self, language=None):
        return self.get_property('dc:title', language=language)

    title = property(get_title, None, None, '')


    def get_title_or_name(self):
        return self.get_title() or self.name

    title_or_name = property(get_title_or_name, None, None, '')


    def get_description(self, language=None):
        desc = self.get_property('dc:description', language=language)
        return desc or ''


    def get_format(self):
        return self.get_property('format')


    def get_owner(self):
        return self.get_property('owner')


    def get_language(self):
        return self.get_property('dc:language')


    def get_parent_path(self):
        parent = self.parent
        if parent is None:
            return ''
        elif parent.parent is None:
            return '/'
        return parent.get_abspath()
    
    parent_path = property(get_parent_path, None, None, '')


    ########################################################################
    # Upgrade
    ########################################################################
    def get_next_versions(self):
        # Set zero version if the object does not have a version
        object_version = self.get_property('version')
        if object_version is None:
            object_version = '00000000'

        # Get all the version numbers
        versions = []
        for name in self.__class__.__dict__.keys():
            if not name.startswith('update_'):
                continue
            kk, version = name.split('_', 1)
            if len(version) != 8:
                continue
            try:
                int(version)
            except ValueError:
                continue
            if version > object_version:
                versions.append(version)

        versions.sort()
        return versions


    def update(self, version):
        # We don't check the version is good
        getattr(self, 'update_%s' % version)()
        self.set_property('version', version)
        logger.info('%s upgraded from %s', self, version)


    ########################################################################
    # Locking
    ########################################################################
    def get_real_handler(self):
        if self.real_handler is None:
            return self

        return self.real_handler


    def lock(self):
        lock = Lock(username=get_context().user.name)

        handler = self.get_real_handler()
        if handler.parent is None:
            handler.set_handler('.lock', lock)
        else:
            parent = handler.parent
            parent.set_handler('%s.lock' % handler.name, lock)

        return lock.key


    def unlock(self):
        handler = self.get_real_handler()
        if handler.parent is None:
            handler.del_handler('.lock')
        else:
            parent = handler.parent
            parent.del_handler('%s.lock' % handler.name)


    def is_locked(self):
        handler = self.get_real_handler()
        if handler.parent is None:
            return handler.has_handler('.lock')
        else:
            parent = handler.parent
            return parent.has_handler('%s.lock' % handler.name)


    def get_lock(self):
        handler = self.get_real_handler()
        if handler.parent is None:
            lock = handler.get_handler('.lock')
        else:
            parent = handler.parent
            lock = parent.get_handler('%s.lock' % handler.name)

        return lock


    ########################################################################
    # HTTP
    ########################################################################
    PUT__access__ = 'is_authenticated'
    def PUT(self, context):
        # Save the data
        body = context.get_form_value('body')
        self.load_state_from_string(body)


    LOCK__access__ = 'is_authenticated'
    def LOCK(self, context):
        if self.is_locked():
            return None
        # Lock the resource
        lock = self.lock()
        # Build response
        response = context.response
        response.set_header('Content-Type', 'text/xml; charset="utf-8"')
        response.set_header('Lock-Token', 'opaquelocktoken:%s' % lock)

        user = context.user
        return webdav.lock_body % {'owner': user.name, 'locktoken': lock}


    UNLOCK__access__ = 'is_authenticated'
    def UNLOCK(self, context):
        # Check wether the resource is locked
        if not self.is_locked():
            # XXX Send some nice response to the client
            raise ValueError, 'resource is not locked'

        # Check wether we have the right key
        request = context.request
        key = request.get_header('Lock-Token')
        key = key[len('opaquelocktoken:'):]

        lock = self.get_lock()
        if lock.key != key:
            # XXX Send some nice response to the client
            raise ValueError, 'can not unlock resource, wrong key'

        # Unlock the resource
        self.unlock()


    ########################################################################
    # User interface
    ########################################################################
    change_content_language__access__ = 'is_allowed_to_view'
    def change_content_language(self, context):
        language = context.get_form_value('dc:language')
        context.set_cookie('content_language', language)

        request = context.request
        return request.referrer


    ########################################################################
    # Metadata
    ########################################################################
    @classmethod
    def build_metadata(cls, owner=None, format=None, **kw):
        """Return a Metadata object with sensible default values."""
        if owner is None:
            owner = ''
            context = get_context()
            if context is not None:
                if context.user is not None:
                    owner = context.user.name

        if format is None:
            format = cls.class_id

        if isinstance(cls, WorkflowAware):
            kw['state'] = cls.workflow.initstate

        return Metadata(handler_class=cls, owner=owner, format=format, **kw)


    def get_metadata(self):
        if self.real_handler is not None:
            return self.real_handler.get_metadata()

        parent = self.parent
        if parent is None:
            return None
        metadata_name = '%s.metadata' % self.name
        if parent.has_handler(metadata_name):
            return parent.get_handler(metadata_name)
        return None

    metadata = property(get_metadata, None, None, "")


    edit_metadata_form__access__ = 'is_allowed_to_edit'
    edit_metadata_form__label__ = u'Metadata'
    edit_metadata_form__sublabel__ = u'Metadata'
    def edit_metadata_form(self, context):
        # Build the namespace
        namespace = {}
        # Language
        site_root = self.get_site_root()
        languages = site_root.get_property('ikaaro:website_languages')
        default_language = languages[0]
        language = context.get_cookie('content_language') or default_language
        namespace['language'] = language
        # Title
        namespace['title'] = self.get_property('dc:title', language=language)
        # Description
        namespace['description'] = self.get_property('dc:description',
                                                     language=language)

        handler = self.get_handler('/ui/Handler_edit_metadata.xml')
        return stl(handler, namespace)


    edit_metadata__access__ = 'is_allowed_to_edit'
    def edit_metadata(self, context):
        title = context.get_form_value('dc:title')
        description = context.get_form_value('dc:description')
        language = context.get_form_value('dc:language')

        if language is None:
            self.set_property('dc:title', title, language=language)
            self.set_property('dc:description', description, language=language)
        else:
            self.set_property('dc:title', title)
            self.set_property('dc:description', description)

        return context.come_back(MSG_CHANGES_SAVED)


    ########################################################################
    # Rich Text Editor
    ########################################################################
    def get_rte(self, name, data):
        js_data = data
        data = cgi.escape(data)
        # Quote newlines and single quotes, so the Epoz-JavaScript won't break.
        # Needs to be a list and no dictionary, cause we need order!!!
        for item in (("\\","\\\\"), ("\n","\\n"), ("\r","\\r"), ("'","\\'")):
            js_data = js_data.replace(item[0], item[1])

        namespace = {}
        namespace['form_name'] = name
        namespace['js_data'] = js_data
        namespace['iframe'] = ';epoz_iframe'

        here = Path(self.get_abspath())
        handler = self.get_handler('/ui/epoz/rte.xml')
        there = Path(handler.get_abspath())
        prefix = here.get_pathto(there)
        return stl(handler, namespace, prefix=prefix)


    epoz_iframe__access__ = 'is_allowed_to_edit'
    def epoz_iframe(self, context):
        namespace = {}
        namespace['data'] = self.get_epoz_data()

        response = context.response
        response.set_header('Content-Type', 'text/html; charset=UTF-8')
        handler = self.get_handler('/ui/epoz/iframe.xml')
        here = Path(self.get_abspath())
        there = Path(handler.get_abspath())
        prefix = here.get_pathto(there)
        return stl(handler, namespace, prefix=prefix)


    #######################################################################
    # Edit / Inline / toolbox: add images
    addimage_form__access__ = 'is_allowed_to_edit'
    def addimage_form(self, context):
        from binary import Image
        from widgets import Breadcrumb

        namespace = {}
        namespace['bc'] = Breadcrumb(filter_type=Image, start=self.parent)

        handler = self.get_handler('/ui/html/addimage.xml')
        return stl(handler, namespace)


    #######################################################################
    # Edit / Inline / toolbox: add links
    addlink_form__access__ = 'is_allowed_to_edit'
    def addlink_form(self, context):
        from file import File
        from widgets import Breadcrumb

        namespace = {}
        namespace['bc'] = Breadcrumb(filter_type=File, start=self.parent)

        handler = self.get_handler('/ui/html/addlink.xml')
        return stl(handler, namespace)


    epoz_color_form__access__ = 'is_allowed_to_edit'
    def epoz_color_form(self, context):
        context.response.set_header('Content-Type', 'text/html; charset=UTF-8')

        handler = self.get_handler('/ui/epoz/script_color.xml')
        return handler.to_str()


    epoz_table_form__access__ = 'is_allowed_to_edit'
    def epoz_table_form(self, context):
        context.response.set_header('Content-Type', 'text/html; charset=UTF-8')

        handler = self.get_handler('/ui/epoz/script_table.xml')
        return handler.to_str()


