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
import cgi
import logging

# Import from itools
import itools
from itools import get_abspath
from itools import uri
from itools.datatypes import QName
from itools import vfs
from itools.handlers.Handler import Node as iNode
from itools.handlers.transactions import get_transaction
from itools import schemas
from itools.stl import stl
from itools.xhtml import XHTML
from itools.gettext import domains
from itools.http.exceptions import Forbidden
from itools.web import get_context

# Import from itools.cms
from access import AccessControl
from catalog import CatalogAware
from LocaleAware import LocaleAware
import webdav


# Initialize logger
logger = logging.getLogger('update')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)



class Node(iNode):

    class_views = []

    ########################################################################
    # HTTP
    ########################################################################
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
        user = context.user
        for name in context.get_form_keys():
            if name.startswith(';'):
                ac = self.get_access_control()
                # Get the method
                method_name = name[1:]
                method = self.get_method(user, self, method_name)
                # Check security
                if method is None:
                    method = self.forbidden_form
                # Call the method
                return method(context)

        raise Exception, 'the form did not define the action to do'


    ########################################################################
    # Tree
    ########################################################################
    def get_site_root(self):
        from WebSite import WebSite
        handler = self
        while not isinstance(handler, WebSite):
            handler = handler.parent
        return handler


    # XXX See if we can get rid of this code (get_access_control may be used
    # instead)
    def get_workplace(self):
        from users import User
        from WebSite import WebSite

        user = get_context().user
        # Get the "workplace"
        node = self
        while node is not None:
            if isinstance(node, (WebSite, User)):
                return node
            node = node.parent

        # We never should reach here (XXX Raise an exception?)
        return None


    def get_access_control(self):
        from itools.web.access import AccessControl

        node = self
        while node is not None:
            if isinstance(node, AccessControl):
                return node
            node = node.parent

        # We never should reach here (XXX Raise an exception?)
        return None


    ########################################################################
    # Properties
    ########################################################################
    def get_property(self, name, language=None):
        return schemas.get_datatype(name).default


    def get_title_or_name(self):
        return self.name


    def get_mtime(self):
        # XXX Should use the handler timestamp instead?
        return vfs.get_mtime(self.handler.uri)

    mtime = property(get_mtime, None, None, "")


    def get_path_to_icon(self, size=16, from_handler=None):
        if hasattr(self, 'icon%s' % size):
            return ';icon%s' % size
        path_to_icon = getattr(self.__class__, 'class_icon%s' % size)
        if from_handler is None:
            from_handler = self
        return '%sui/%s' % (from_handler.get_pathtoroot(), path_to_icon)


    def get_human_size(self):
        uri = self.handler.uri
        if vfs.is_file(uri):
            bytes = resource.get_size()
            kbytes = bytes / 1024.0
            if kbytes >= 1024:
                mbytes = kbytes / 1024.0
                size = self.gettext(u'%.01f MB') % mbytes
            else:
                size = self.gettext(u'%.01f KB') % kbytes
        else:
            size = len([ x for x in resource.get_names()
                         if not x.startswith('.') ])
            size = self.gettext(u'%d obs') % size

        return size


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
        gettext = domains.DomainAware.gettext

        if cls.class_domain == 'itools':
            domain_names = ['itools']
        else:
            domain_names = [cls.class_domain, 'itools']

        for domain_name in domain_names:
            if language is None:
                domain = domains.domains[domain_name]
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
        for name in self.get_views():
            if ac.is_access_allowed(user, self, name):
                return name
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



class Handler(itools.handlers.Handler.Handler, Node, domains.DomainAware,
              CatalogAware):

    def before_commit(self):
        from root import Root

        root = self.get_root()
        if isinstance(root, Root):
            root.reindex_handler(self)


    @classmethod
    def new_instance(cls):
        return cls()


    ########################################################################
    # Properties
    ########################################################################
    def get_property(self, name, language=None):
        metadata = self.metadata
        if metadata is None:
            return Node.get_property(self, name)
        return metadata.get_property(name, language=language)


    def set_property(self, name, value, language=None):
        self.metadata.set_property(name, value, language=language)


    def del_property(self, name, language=None):
        self.metadata.del_property(name, language=language)


    ########################################################################
    # Shorthands (XXX remove as many as posible)
    def get_title(self, language=None):
        return self.get_property('dc:title', language=language)

    title = property(get_title, None, None, '')


    def get_title_or_name(self):
        return self.get_property('dc:title') or self.name

    title_or_name = property(get_title_or_name, None, None, '')


    def get_description(self, language=None):
        desc = self.get_property('dc:description', language=language)
        return desc or ''


    def get_format(self):
        return self.metadata.get_property('format')


    def get_owner(self):
        return self.metadata.get_property('owner')


    def get_language(self):
        return self.metadata.get_property('dc:language')


    def get_parent_path(self):
        parent = self.parent
        if parent is None:
            return ''
        elif parent.parent is None:
            return '/'
        return parent.get_abspath()
    
    parent_path = property(get_parent_path, None, None, '')


    ########################################################################
    # Catalog
    ########################################################################
    def to_text(self):
        return u''


    ########################################################################
    # Upgrade
    ########################################################################
    def is_uptodate(self):
        object_version = self.metadata.get_property('version')
        class_version = self.class_version
        if object_version is None:
            object_version = class_version

        return class_version == object_version


    def update(self, version=None, *args, **kw):
        # Set zero version if the object does not have a version
        object_version = self.metadata.get_property('version')
        if object_version is None:
            object_version = '00000000'

        # Default version to the current class version
        if version is None:
            version = self.class_version

        # Get all the version numbers
        versions = [ x.split('_')[-1]
                     for x in self.__class__.__dict__.keys()
                     if x.startswith('update_') ]

        # Sort the version numbers
        versions.sort()

        # Filter the versions previous to the current object version
        versions = [ x for x in versions if x > object_version ]

        # Filter the versions next to the given version
        versions = [ x for x in versions if x <= version ]

        # Upgrade
        if versions:
            for version in versions:
                getattr(self, 'update_%s' % version)(*args, **kw)
                logger.info('%s upgraded from %s to %s', self,
                            self.class_version, version)
                self.set_property('version', version)
            get_transaction().commit()


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
            parent.set_handler('.%s.lock' % handler.name, lock)

        return lock.key


    def unlock(self):
        handler = self.get_real_handler()
        if handler.parent is None:
            handler.del_handler('.lock')
        else:
            parent = handler.parent
            parent.del_handler('.%s.lock' % handler.name)


    def is_locked(self):
        handler = self.get_real_handler()
        if handler.parent is None:
            return handler.has_handler('.lock')
        else:
            parent = handler.parent
            return parent.has_handler('.%s.lock' % handler.name)


    def get_lock(self):
        handler = self.get_real_handler()
        if handler.parent is None:
            lock = handler.get_handler('.lock')
        else:
            parent = handler.parent
            lock = parent.get_handler('.%s.lock' % handler.name)

        return lock


    ########################################################################
    # HTTP
    ########################################################################
    PUT__access__ = 'is_authenticated'
    def PUT(self, context):
        # Save the data
        resource = context.get_form_value('body')
        self.load_state_from(resource)
        # Build the response
        context.response.set_status(204)


    LOCK__access__ = 'is_authenticated'
    def LOCK(self, context):
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

        context.response.set_status(204)


    ########################################################################
    # User interface
    ########################################################################
    change_content_language__access__ = 'is_allowed_to_view'
    def change_content_language(self, context):
        language = context.get_form_value('dc:language')
        context.set_cookie('content_language', language)

        request = context.request
        return request.referrer

##        handler = self.get_version_handler(language=kw['dc:language'])
##        print kw['dc:language'], handler.abspath
##        method_name = request.referrer.path[-1].param
##
##        goto = '%s/;%s' % (self.get_pathto(handler), method_name)
##        return uri.get_reference(goto)



    ########################################################################
    # Metadata
    ########################################################################
    def get_metadata(self):
        if self.real_handler is not None:
            return self.real_handler.get_metadata()

        parent = self.parent
        if parent is None:
            return None
        metadata_name = '.%s.metadata' % self.name
        if parent.has_handler(metadata_name):
            return parent.get_handler(metadata_name)
        return None

    metadata = property(get_metadata, None, None, "")


    edit_metadata_form__access__ = 'is_allowed_to_edit'
    edit_metadata_form__label__ = u'Metadata'
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

        if isinstance(self, LocaleAware):
            self.set_property('dc:title', title)
            self.set_property('dc:description', description)
        else:
            self.set_property('dc:title', title, language=language)
            self.set_property('dc:description', description, language=language)

        # Reindex
        root = context.root
        root.reindex_handler(self)

        return context.come_back(u'Metadata changed.')


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
        namespace['widget_id'] = 'epoz_widget_%s' % name
        namespace['toolbar_id'] = 'ToolBar_%s' % name
        namespace['frame_id'] = 'Iframe_%s' % name
        namespace['textarea_id'] = name
        namespace['switch_id'] = 'CB_%s' % name
        namespace['js_data'] = js_data
        namespace['iframe'] = ';epoz_iframe'
        js_code = """<!--
        document.getElementById('%(widget_id)s').style.display = 'inline';
        document.getElementById('%(textarea_id)s').disabled = 0;
        -->"""
        namespace['js_code'] = js_code % namespace
        namespace['SetTextColor_call'] = "SetTextColor(';epoz_color_form')"
        namespace['SetBackColor_call'] = "SetBackColor(';epoz_color_form')"
        namespace['SetTable_call'] = "SetTable(';epoz_table_form')"

        here = uri.Path(self.get_abspath())
        handler = self.get_handler('/ui/epoz.xml')
        there = uri.Path(handler.get_abspath())
        prefix = here.get_pathto(there)
        handler = XHTML.set_template_prefix(handler, prefix)
        return stl(handler, namespace)


    epoz_iframe__access__ = 'is_allowed_to_edit'
    def epoz_iframe(self, context):
        namespace = {}
        namespace['data'] = self.get_epoz_data()

        response = context.response
        response.set_header('Content-Type', 'text/html; charset=UTF-8')
        handler = self.get_handler('/ui/epoz_iframe.xml')
        here = uri.generic.Path(self.get_abspath())
        there = uri.generic.Path(handler.get_abspath())
        handler = XHTML.set_template_prefix(handler, here.get_pathto(there))
        return stl(handler, namespace)
