# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006-2007 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
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
from datetime import datetime

# Import from itools
from itools.uri import Path, get_reference
from itools import vfs
from itools.catalog import CatalogAware
from itools.handlers import Handler as BaseHandler
from itools.i18n import get_language_name
from itools.schemas import get_datatype
from itools.stl import stl
from itools.gettext import DomainAware, get_domain
from itools.http import Forbidden
from itools.web import get_context, Node as BaseNode
from itools.datatypes import FileName
from itools.rest import checkid

# Import from itools.cms
from catalog import schedule_to_reindex, schedule_to_index
from handlers import Lock, Metadata
from messages import *
from registry import get_object_class
from versioning import VersioningAware
import webdav
from workflow import WorkflowAware



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


    ########################################################################
    # Properties
    ########################################################################
    def get_property_and_language(self, name, language=None):
        return get_datatype(name).default, None


    def get_property(self, name, language=None):
        return self.get_property_and_language(name, language=language)[0]


    def get_title(self):
        return self.name


    def get_mtime(self):
        if self.uri is None:
            return None

        if self.timestamp is not None:
            return self.timestamp
        elif vfs.exists(self.uri):
            return vfs.get_mtime(self.uri)

        return None


    # XXX TODO remove "from_handler" in 0.17
    def get_path_to_icon(self, size=16, from_handler=None):
        if hasattr(self, 'icon%s' % size):
            return ';icon%s' % size
        path_to_icon = getattr(self.__class__, 'class_icon%s' % size)
        return '/ui/' + path_to_icon


    ########################################################################
    # Internationalization
    ########################################################################
    class_domain = 'itools'

    @classmethod
    def select_language(cls, languages):
        accept = get_context().get_accept_language()
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
        """Returns the first allowed object view url, or None if there
        aren't.
        """
        for view in self.get_views():
            return view
        return None


    def get_views(self):
        user = get_context().user
        ac = self.get_access_control()
        for view in self.class_views:
            view = view[0]
            name = view.split('?')[0]
            if ac.is_access_allowed(user, self, name):
                yield view


    def get_subviews(self, name):
        for block in self.class_views:
            if name in block:
                if len(block) == 1:
                    return []
                return block[:]
        return []



class DBObject(CatalogAware, Node, DomainAware):

    def __init__(self, metadata):
        self.metadata = metadata
        self._handler = None
        # The tree
        self.name = ''
        self.parent = None



    @classmethod
    def make_object(cls, container, name, *args, **kw):
        from folder import Folder

        cls._make_object(container.handler, name, *args, **kw)
        object = container.get_object(name)

        # Versioning
        if isinstance(object, VersioningAware):
            object.commit_revision()
        # Schedule to index
        if isinstance(object, Folder):
            for x in object.traverse_objects():
                schedule_to_index(x)
        else:
            schedule_to_index(object)

        return object


    @classmethod
    def _make_object(cls, folder, name):
        metadata = cls.build_metadata()
        folder.set_handler('%s.metadata' % name, metadata)


    def get_handler(self):
        if self._handler is None:
            cls = self.class_handler
            database = self.metadata.database
            if self.parent is None:
                uri = self.metadata.uri.resolve('.')
            else:
                uri = self.metadata.uri.resolve(self.name)
            if database.has_handler(uri):
                self._handler = database.get_handler(uri, cls=cls)
            else:
                handler = cls()
                handler.database = database
                handler.uri = uri
                handler.timestamp = None
                handler.dirty = False
                database.cache[uri] = handler
                self._handler = handler
        return self._handler

    handler = property(get_handler, None, None, '')


#   def set_changed(self):
#       Metadata.set_changed(self)
#       if self.uri is not None:
#           schedule_to_reindex(self)


    ########################################################################
    # Indexing
    ########################################################################
    def to_text(self):
        raise NotImplementedError


    def get_catalog_indexes(self):
        from access import RoleAware
        from file import File
        from users import User

        name = self.name
        abspath = self.get_canonical_path()
        get_property = self.get_property
        title = self.get_title()

        mtime = self.get_mtime()
        if mtime is None:
            mtime = datetime.now()

        document = {
            'name': name,
            'abspath': abspath,
            'format': get_property('format'),
            'title': title,
            'owner': get_property('owner'),
            'mtime': mtime.strftime('%Y%m%d%H%M%S')}

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
        if abspath != '/':
            parent_path = Path(abspath).resolve2('..')
            document['parent_path'] = str(parent_path)

        # All paths
        abspath = Path(abspath)
        document['paths'] = [ abspath[:x] for x in range(len(abspath) + 1) ]

        # Size
        if isinstance(self, File):
            # FIXME We add an arbitrary size so files will always be bigger
            # than folders. This won't work when there is a folder with more
            # than that size.
            document['size'] = 2**30 + len(self.handler.to_str())
        else:
            names = self.get_names()
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
                users = self.get_object('/users')
                try:
                    user = users.get_object(user_id)
                except LookupError:
                    document['last_author'] = u'Unavailable'
                else:
                    document['last_author'] = user.get_title()

        return document


    ########################################################################
    # Properties
    ########################################################################
    def has_property(self, name, language=None):
        return self.metadata.has_property(name, language=language)


    def get_property_and_language(self, name, language=None):
        return self.metadata.get_property_and_language(name, language=language)


    def set_property(self, name, value, language=None):
        schedule_to_reindex(self)
        self.metadata.set_property(name, value, language=language)


    def del_property(self, name, language=None):
        schedule_to_reindex(self)
        self.metadata.del_property(self, name, language=language)


    def get_mtime(self):
        metadata = self.metadata
        if metadata.timestamp is not None:
            metadata_mtime = metadata.timestamp
        elif vfs.exists(metadata.uri):
            metadata_mtime = vfs.get_mtime(metadata.uri)
        else:
            metadata_mtime = None

        handler = self.handler
        if handler is None:
            return metadata_mtime
        elif handler.timestamp is not None:
            handler_mtime = handler.timestamp
        elif vfs.exists(handler.uri):
            handler_mtime = vfs.get_mtime(handler.uri)
        else:
            return metadata_mtime

        if metadata_mtime is None:
            return handler_mtime

        return max(handler_mtime, metadata_mtime)


    ########################################################################
    # Upgrade
    ########################################################################
    def get_next_versions(self):
        class_version = self.class_version
        object_version = self.get_property('version')
        # Set zero version if the object does not have a version
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
            if version > object_version and version <= class_version:
                versions.append(version)

        versions.sort()
        return versions


    def update(self, version):
        # We don't check the version is good
        getattr(self, 'update_%s' % version)()
        self.set_property('version', version)


    ########################################################################
    # Locking
    ########################################################################
    def lock(self):
        lock = Lock(username=get_context().user.name)

        self = self.get_real_object()
        if self.parent is None:
            self.set_handler('.lock', lock)
        else:
            self.parent.set_handler('%s.lock' % self.name, lock)

        return lock.key


    def unlock(self):
        self = self.get_real_object()
        if self.parent is None:
            self.del_handler('.lock')
        else:
            self.parent.del_handler('%s.lock' % self.name)


    def is_locked(self):
        self = self.get_real_object()
        if self.parent is None:
            return self.has_handler('.lock')
        return self.parent.has_handler('%s.lock' % self.name)


    def get_lock(self):
        self = self.get_real_object()
        if self.parent is None:
            return self.get_handler('.lock')
        return self.parent.get_handler('%s.lock' % self.name)


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
    @classmethod
    def new_instance_form(cls, context):
        root = context.root
        # Build the namespace
        namespace = {}
        namespace['title'] = context.get_form_value('dc:title')
        namespace['name'] = context.get_form_value('name', '')
        # The class id and title
        namespace['class_id'] = cls.class_id
        namespace['class_title'] = cls.gettext(cls.class_title)

        handler = root.get_object('ui/base/new_instance.xml')
        return stl(handler, namespace)


    @classmethod
    def new_instance(cls, container, context):
        name = context.get_form_value('name')
        title = context.get_form_value('dc:title')

        # Check the name
        name = name.strip() or title.strip()
        if not name:
            return context.come_back(MSG_NAME_MISSING)

        name = checkid(name)
        if name is None:
            return context.come_back(MSG_BAD_NAME)

        # Add the language extension to the name
        extension = cls.class_handler.class_extension
        name = FileName.encode((name, extension, None))

        # Check the name is free
        if container.has_object(name):
            return context.come_back(MSG_NAME_CLASH)

        object = cls.make_object(container, name)
        # The metadata
        metadata = object.metadata
        language = container.get_content_language(context)
        metadata.set_property('dc:title', title, language=language)

        goto = './%s/;%s' % (name, object.get_firstview())
        return context.come_back(MSG_NEW_RESOURCE, goto=goto)


    def get_title(self, language=None):
        return self.get_property('dc:title', language=language) or self.name


    change_content_language__access__ = 'is_allowed_to_view'
    def change_content_language(self, context):
        language = context.get_form_value('dc:language')
        context.set_cookie('content_language', language)

        request = context.request
        return request.referrer


    def get_content_language(self, context):
        site_root = self.get_site_root()
        languages = site_root.get_property('ikaaro:website_languages')
        # Check cookie
        language = context.get_cookie('content_language')
        if language in languages:
            return language
        # Default
        return languages[0]


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


    edit_metadata_form__access__ = 'is_allowed_to_edit'
    edit_metadata_form__label__ = u'Metadata'
    edit_metadata_form__sublabel__ = u'Metadata'
    def edit_metadata_form(self, context):
        # Build the namespace
        namespace = {}
        # Language
        language = self.get_content_language(context)
        language_name = get_language_name(language)
        namespace['language_name'] = self.gettext(language_name)
        # Title, Description, Subject
        for name in 'dc:title', 'dc:description', 'dc:subject':
            namespace[name] = self.get_property(name, language=language)

        handler = self.get_object('/ui/base/edit_metadata.xml')
        return stl(handler, namespace)


    edit_metadata__access__ = 'is_allowed_to_edit'
    def edit_metadata(self, context):
        title = context.get_form_value('dc:title')
        description = context.get_form_value('dc:description')
        subject = context.get_form_value('dc:subject')
        language = self.get_content_language(context)
        self.set_property('dc:title', title, language=language)
        self.set_property('dc:description', description, language=language)
        self.set_property('dc:subject', subject, language=language)

        return context.come_back(MSG_CHANGES_SAVED)


    ########################################################################
    # Rich Text Editor
    ########################################################################
    @classmethod
    def get_rte(cls, context, name, data):
        # XXX Not needed anymore I believe
##        js_data = data
##        data = cgi.escape(data)
##        # Quote newlines and single quotes, so the Epoz-JavaScript won't
##        # break. Needs to be a list and no dictionary, cause we need order!!
##        for item in (("\\","\\\\"), ("\n","\\n"), ("\r","\\r"), ("'","\\'")):
##            js_data = js_data.replace(item[0], item[1])

        namespace = {}
        namespace['form_name'] = name
        namespace['js_data'] = data
        namespace['iframe'] = ';epoz_iframe'
        dress_name = context.get_form_value('dress_name')
        if dress_name:
            namespace['iframe'] = ';epoz_iframe?dress_name=%s' % dress_name
        else:
            namespace['iframe'] = ';epoz_iframe'
        namespace['dress_name'] = dress_name

        here = Path(context.handler.get_abspath())
        there = '/ui/epoz/rte.xml'
        prefix = here.get_pathto(there)

        handler = context.root.get_object(there)
        return stl(handler, namespace, prefix=prefix)


    epoz_iframe__access__ = 'is_allowed_to_edit'
    def epoz_iframe(self, context):
        namespace = {}
        namespace['data'] = self.get_epoz_data()

        response = context.response
        response.set_header('Content-Type', 'text/html; charset=UTF-8')

        here = Path(self.get_abspath())
        there = '/ui/epoz/iframe.xml'
        prefix = here.get_pathto(there)

        handler = self.get_object(there)
        return stl(handler, namespace, prefix=prefix)


    #######################################################################
    # Edit / Inline / toolbox: add images
    addimage_form__access__ = 'is_allowed_to_edit'
    def addimage_form(self, context):
        from file import File
        from binary import Image
        from widgets import Breadcrumb
        # Build the bc
        if isinstance(self, File):
            start = self.parent
        else:
            start = self
        # Construct namespace
        namespace = {}
        namespace['bc'] = Breadcrumb(filter_type=Image, start=start)
        namespace['message'] = context.get_form_value('message')

        prefix = Path(self.abspath).get_pathto('/ui/html/addimage.xml')
        handler = self.get_object('/ui/html/addimage.xml')
        return stl(handler, namespace, prefix=prefix)


    addimage__access__ = 'is_allowed_to_edit'
    def addimage(self, context):
        """
        Allow to upload and add an image to epoz
        """
        from binary import Image
        root = context.root
        # Get the container
        container = root.get_object(context.get_form_value('target_path'))
        # Add the image to the handler
        uri = Image.new_instance(container, context)
        if ';addimage_form' not in uri.path:
            handler = container.get_handler(uri.path[0])
            return """
            <script type="text/javascript">
                window.opener.CreateImage('%s');
                window.close();
            </script>
                    """ % handler.abspath

        return context.come_back(message=uri.query['message'])


    #######################################################################
    # Edit / Inline / toolbox: add links
    addlink_form__access__ = 'is_allowed_to_edit'
    def addlink_form(self, context):
        from file import File
        from widgets import Breadcrumb

        # Build the bc
        if isinstance(self, File):
            start = self.parent
        else:
            start = self
        # Construct namespace
        namespace = {}
        namespace['language'] = self.get_property('dc:language') or 'en'
        namespace['bc'] = Breadcrumb(filter_type=File, start=start)
        namespace['message'] = context.get_form_value('message')

        prefix = Path(self.abspath).get_pathto('/ui/html/addimage.xml')
        handler = self.get_object('/ui/html/addlink.xml')
        return stl(handler, namespace, prefix=prefix)


    addlink__access__ = 'is_allowed_to_edit'
    def addlink(self, context):
        """
        Allow to upload a file and link it to epoz
        """
        # Get the container
        root = context.root
        container = root.get_handler(context.get_form_value('target_path'))
        # Add the image to the handler
        class_id = context.get_form_value('type')
        cls = get_object_class(class_id)
        uri = cls.new_instance(container, context)
        if ';addlink_form' not in uri.path:
            handler = container.get_handler(uri.path[0])
            return """
            <script type="text/javascript">
                window.opener.CreateLink('%s');
                window.close();
            </script>
                    """ % handler.abspath

        return context.come_back(message=uri.query['message'])


    epoz_color_form__access__ = 'is_allowed_to_edit'
    def epoz_color_form(self, context):
        context.response.set_header('Content-Type', 'text/html; charset=UTF-8')

        handler = self.get_object('/ui/epoz/script_color.xml')
        return handler.to_str()


    epoz_table_form__access__ = 'is_allowed_to_edit'
    def epoz_table_form(self, context):
        context.response.set_header('Content-Type', 'text/html; charset=UTF-8')

        handler = self.get_object('/ui/epoz/script_table.xml')
        return handler.to_str()

