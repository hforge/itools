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
from itools.resources import base, memory
from itools.handlers.Handler import Node as iNode
from itools.handlers.transactions import get_transaction
from itools import schemas
from itools.xml.stl import stl
from itools.xhtml import XHTML
from itools.gettext import domains
from itools.web import get_context
from itools.web.exceptions import Forbidden

# Import from itools.cms
from access import AccessControl
from catalog import CatalogAware
from utils import comeback
from LocaleAware import LocaleAware
import webdav


# Initialize logger
logger = logging.getLogger('update')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)



class Node(AccessControl, iNode):

    ########################################################################
    # HTTP
    ########################################################################
    GET__access__ = 'is_allowed_to_view'
    def GET(self):
        method = self.get_firstview()
        # Check access
        if method is None:
            raise Forbidden
        # Redirect
        context = get_context()
        goto = context.uri.resolve2(';%s' % method)
        context.redirect(goto)


    POST__access__ = 'is_authenticated'
    def POST(self, **kw):
        for name in kw:
            if name.startswith(';'):
                # Get the method
                method_name = name[1:]
                method = self.get_method(method_name)
                # Check security
                if method is None:
                    method = self.forbidden_form
                # Call the method
                if method.im_func.func_code.co_flags & 8:
                    return method(**kw)
                else:
                    return method()

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


    ########################################################################
    # Properties
    ########################################################################
    def get_property(self, name, language=None):
        return schemas.get_datatype(name).default


    def get_title_or_name(self):
        return self.name


    def get_mtime(self):
        # XXX Should use the handler timestamp instead?
        return self.resource.get_mtime()

    mtime = property(get_mtime, None, None, "")


    def get_path_to_icon(self, size=16, from_handler=None):
        if hasattr(self, 'icon%s' % size):
            return ';icon%s' % size
        path_to_icon = getattr(self.__class__, 'class_icon%s' % size)
        if from_handler is None:
            from_handler = self
        return '%sui/%s' % (from_handler.get_pathtoroot(), path_to_icon)


    def get_human_size(self):
        resource = self.resource
        if isinstance(resource, base.File):
            bytes = resource.get_size()
            kbytes = bytes / 1024.0
            if kbytes >= 1024:
                mbytes = kbytes / 1024.0
                size = self.gettext(u'%.01f MB') % mbytes
            else:
                size = self.gettext(u'%.01f KB') % kbytes
        else:
            size = len([ x for x in resource.get_resource_names()
                         if not x.startswith('.') ])
            size = self.gettext(u'%d obs') % size

        return size


    ########################################################################
    # Internationalization
    ########################################################################
    class_domain = 'ikaaro'

    @classmethod
    def select_language(cls, languages):
        accept = get_context().request.accept_language
        return accept.select_language(languages)


    @classmethod
    def gettext(cls, message, language=None):
        gettext = domains.DomainAware.gettext

        if cls.class_domain == 'ikaaro':
            domain_names = ['ikaaro']
        else:
            domain_names = [cls.class_domain, 'ikaaro']

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
        for name in self.get_views():
            method = self.get_method(name)
            if method is not None:
                return name
        return None


    def get_views(self):
        return []


    def get_subviews(self, name):
        return []



class Handler(itools.handlers.Handler.Handler, Node, domains.DomainAware,
              CatalogAware):

    # Needed by the classic skin
    is_image = False


    def before_commit(self):
        from Root import Root

        root = self.get_root()
        if isinstance(root, Root):
            root.reindex_handler(self)


    ########################################################################
    # The Factory
    ########################################################################
    handler_class_registry = {}

    @classmethod
    def register_handler_class(cls, handler_class, format=None):
        if format is None:
            format = handler_class.class_id
        cls.handler_class_registry[format] = handler_class


    @classmethod
    def build_handler(cls, resource, format=None):
        from File import File
        from Folder import Folder

        registry = cls.handler_class_registry
        if format in registry:
            handler_class = registry[format]
        else:
            format = format.split('/')
            if format[0] in registry:
                handler_class = registry[format[0]]
            else:
                # XXX Show a warning message here
                if isinstance(resource, base.File):
                    handler_class = registry[File.class_id]
                elif isinstance(resource, base.Folder):
                    handler_class = registry[Folder.class_id]
                else:
                    raise ValueError, \
                          'Unknown resource type "%s"' % repr(resource)
##        # Check wether the resource is a file and the handler class is a
##        # folder, or viceversa.
##        if isinstance(resource, base.File):
##            if not issubclass(handler_class, File):
##                handler_class = File
##        elif isinstance(resource, base.Folder):
##            if not issubclass(handler_class, Folder):
##                handler_class = Folder

        return handler_class(resource)


    def get_handler_class(self, class_id):
        return self.handler_class_registry[class_id]


    @classmethod
    def new_instance(cls, **kw):
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
    # HTTP
    ########################################################################
    PUT__access__ = 'is_authenticated'
    def PUT(self):
        context = get_context()
        request, response = context.request, context.response

        # Save the data
        resource = request.get_parameter('body')
        self.load_state(resource)
        # Build the response
        response.set_status(204)


    LOCK__access__ = 'is_authenticated'
    def LOCK(self):
        # XXX This action is not persitent, the lock is not stored in the
        # database.
        context = get_context()
        request, response = context.request, context.response

        # Lock the resource
        resource = self.resource
        lock = resource.lock()
        # Build response        
        response.set_header('Content-Type', 'text/xml; charset="utf-8"')
        response.set_header('Lock-Token', 'opaquelocktoken:%s' % lock)

        user = context.user
        return webdav.lock_body % {'owner': user.name, 'locktoken': lock}


    UNLOCK__access__ = 'is_authenticated'
    def UNLOCK(self):
        # XXX This action is not persitent, the lock is not stored in the
        # database.
        context = get_context()
        request, response = context.request, context.response

        # Unlock the resource
        key = request.get_header('Lock-Token')
        key = key[len('opaquelocktoken:'):]
        self.resource.unlock(key)

        response.set_status(204)


    ########################################################################
    # User interface
    ########################################################################
    change_content_language__access__ = 'is_allowed_to_view'
    def change_content_language(self, **kw):
        context = get_context()
        request = context.request

        context.set_cookie('content_language', kw['dc:language'])
        context.redirect(request.referrer)

##        handler = self.get_version_handler(language=kw['dc:language'])
##        print kw['dc:language'], handler.abspath
##        method_name = request.referrer.path[-1].param

##        context.redirect('%s/;%s' % (self.get_pathto(handler), method_name))


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
    def edit_metadata_form(self):
        context = get_context()
        request = context.request

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
    def edit_metadata(self, **kw):
        context = get_context()
        root = context.root

        language = kw['dc:language']
        if isinstance(self, LocaleAware):
            self.set_property('dc:title', kw['dc:title'])
            self.set_property('dc:description', kw['dc:description'])
        else:
            self.set_property('dc:title', kw['dc:title'], language=language)
            self.set_property('dc:description', kw['dc:description'],
                              language=language)

        # Reindex
        root.reindex_handler(self)

        message = self.gettext(u'Metadata changed.')
        comeback(message)


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

        handler = self.get_handler('/ui/epoz.xml')
        here = uri.generic.Path(self.get_abspath())
        there = uri.generic.Path(handler.get_abspath())
        handler = XHTML.set_template_prefix(handler, here.get_pathto(there))
        return stl(handler, namespace)


    epoz_iframe__access__ = 'is_allowed_to_edit'
    def epoz_iframe(self):
        context = get_context()
        response = context.response

        namespace = {}
        namespace['data'] = self.get_epoz_data()

        response.set_header('Content-Type', 'text/html; charset=UTF-8')
        handler = self.get_handler('/ui/epoz_iframe.xml')
        here = uri.generic.Path(self.get_abspath())
        there = uri.generic.Path(handler.get_abspath())
        handler = XHTML.set_template_prefix(handler, here.get_pathto(there))
        return stl(handler, namespace)
