# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#                    2005 Alexandre Fernandez <alex@itaapy.com>
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
import marshal
from string import Template
import urllib
import zlib
import mimetypes

# Import from itools
from itools.i18n import format_datetime, guess_language, has_language
from itools.uri import Path, get_reference, Reference
from itools.catalog import CatalogAware, EqQuery, AndQuery, PhraseQuery
from itools.datatypes import Boolean, FileName, Integer, Unicode
from itools import vfs
from itools.handlers import Folder as BaseFolder, Text, get_handler_class
from itools.rest import checkid
from itools.stl import stl
from itools.web import get_context
from itools.xml import Parser

# Import from itools.cms
from file import File
from base import Handler
from binary import Image
from handlers import Lock, Metadata, ListOfUsers
from ical import CalendarAware, Calendar
from messages import *
from versioning import VersioningAware
from workflow import WorkflowAware
from utils import reduce_string
import widgets
from registry import register_object_class, get_object_class
from catalog import schedule_to_index, schedule_to_unindex



class Folder(Handler, BaseFolder, CalendarAware):

    #########################################################################
    # Class metadata
    #########################################################################
    class_id = 'folder'
    class_version = '20040625'
    class_layout = {}
    class_title = u'Folder'
    class_description = u'Organize your files and documents with folders.'
    class_icon16 = 'images/Folder16.png'
    class_icon48 = 'images/Folder48.png'
    class_views = [
        ['browse_content?mode=thumbnails',
         'browse_content?mode=list',
         'browse_content?mode=image'],
        ['new_resource_form'],
        ['edit_metadata_form']]


    search_criteria =  [
        {'id': 'title', 'title': u"Title"},
        {'id': 'text', 'title': u"Text"},
        {'id': 'name', 'title': u"Name"},
    ]


    #########################################################################
    # Aggregation relationship (what a generic folder can contain)
    class_document_types = []

    __fixed_handlers__ = []


    @classmethod
    def register_document_type(cls, handler_class):
        cls.class_document_types.append(handler_class)


    def get_document_types(self):
        return self.class_document_types


    @classmethod
    def new_instance_form(cls, context):
        namespace = {'class_id': cls.class_id,
                     'class_title': cls.gettext(cls.class_title)}

        handler = context.root.get_handler('ui/folder/new_instance.xml')
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

        # Check the name is free
        if container.has_handler(name):
            return context.come_back(MSG_NAME_CLASH)

        # Build the object
        handler = cls()
        metadata = handler.build_metadata()
        language = container.get_site_root().get_default_language()
        metadata.set_property('dc:title', title, language=language)
        # Add the object
        handler, metadata = container.set_object(name, handler, metadata)

        goto = './%s/;%s' % (name, handler.get_firstview())
        return context.come_back(MSG_NEW_RESOURCE, goto=goto)


    #######################################################################
    # Traverse
    #######################################################################
    GET__access__ = True
    def GET(self, context):
        # Try index
        for name in ['index.xhtml', 'index.html']:
            try:
                self.get_handler(name)
            except LookupError:
                pass
            else:
                return context.uri.resolve2(name)

        return Handler.GET(self, context)


    def _get_handler(self, name, uri):
        # Check the layout first
        cls = self.class_layout.get(name)
        if cls is not None:
            return cls(uri)

        # Metadata
        if name.endswith('.metadata'):
            return Metadata(uri)
        # Locks
        if name.endswith('.lock'):
            return Lock(uri)
        # XXX ListOfUsers (to be removed in 0.16)
        if name.startswith('.') and name.endswith('.users'):
            return ListOfUsers(uri)

        # cms objects
        if self.has_handler('%s.metadata' % name):
            metadata = self.get_handler('%s.metadata' % name)
            format = metadata.get_property('format')
            cls = get_object_class(format)
            return cls(uri)

        # XXX For now UI objects are like cms objects
        from skins import UI
        x = self
        while x:
            if isinstance(x, UI):
                format = vfs.get_mimetype(uri)
                cls = get_object_class(format)
                return cls(uri)
            x = x.parent

        # Anything else is a bare handler
        cls = get_handler_class(uri)
        return cls(uri)


    def _get_handler_names(self):
        names = BaseFolder._get_handler_names(self)
        for name in names:
            if not name.startswith('.'):
                name, type, language = FileName.decode(name)
                if language is not None:
                    name = FileName.encode((name, type, None))
                    names.append(name)

        return names


    def _get_virtual_handler(self, name):
        languages = [ x.split('.')[-1] for x in self.cache
                      if x.startswith(name) ]
        languages = [ x for x in languages if has_language(x) ]

        if languages:
            # Get the best variant
            context = get_context()
            if context is None:
                language = None
            else:
                accept = context.get_accept_language()
                language = accept.select_language(languages)

            # By default use whatever variant
            # (XXX we need a way to define the default)
            if language is None:
                language = languages[0]
            return self.get_handler('%s.%s' % (name, language))

        return BaseFolder._get_virtual_handler(self, name)


    # FIXME Rename this method to "traverse_objects"
    def _traverse_catalog_aware_objects(self):
        for handler, ctx in self.traverse2(caching=False):
            # Skip virtual handlers
            if handler.real_handler is not None:
                ctx.skip = True
                continue
            # Skip non catalog aware handlers
            if not isinstance(handler, CatalogAware):
                ctx.skip = True
                continue
            yield handler


    #######################################################################
    # API
    #######################################################################
    def set_object(self, name, handler, metadata=None):
        if metadata is None:
            metadata = handler.build_metadata()

        # Add
        handler = self.set_handler(name, handler)
        metadata = self.set_handler('%s.metadata' % name, metadata)

        # Versioning
        if isinstance(handler, VersioningAware):
            handler.commit_revision()

        # Schedule to index
        if isinstance(handler, Folder):
            for x in handler._traverse_catalog_aware_objects():
                schedule_to_index(x)
        else:
            schedule_to_index(handler)

        return handler, metadata


    def del_object(self, name):
        # Schedule to unindex
        handler = self.get_handler(name)
        if isinstance(handler, Folder):
            for x in handler._traverse_catalog_aware_objects():
                schedule_to_unindex(x)
        else:
            schedule_to_unindex(handler)

        # Remove
        self.del_handler(name)
        self.del_handler('%s.metadata' % name)


    def get_object(self, name):
        handler = self.get_handler(name)
        metadata = handler.get_metadata()
        return handler, metadata


    def search_handlers(self, path='.', format=None, state=None,
                        handler_class=None):
        container = self.get_handler(path)

        for name in container.get_handler_names():
            # Skip hidden handlers
            if name.startswith('.'):
                continue
            if name.endswith('.metadata'):
                continue

            filename, type, language = FileName.decode(name)
            if language is not None:
                continue

            handler = container.get_handler(name)
            if handler_class is not None:
                if not isinstance(handler, handler_class):
                    continue

            get_property = getattr(handler, 'get_property', lambda x: None)
            if format is None or get_property('format') == format:
                if state is None:
                    yield handler
                else:
                    handler_state = get_property('state')
                    if handler_state == state:
                        yield handler


    #######################################################################
    # User interface
    #######################################################################
    def get_subviews(self, name):
        if name == 'new_resource_form':
            subviews = []
            for cls in self.get_document_types():
                id = cls.class_id
                ref = 'new_resource_form?type=%s' % urllib.quote_plus(id)
                subviews.append(ref)
            return subviews
        return Handler.get_subviews(self, name)


    def new_resource_form__sublabel__(self, **kw):
        type = kw.get('type')
        for cls in self.get_document_types():
            if cls.class_id == type:
                return cls.class_title
        return u'New Resource'


    #######################################################################
    # Browse
    def get_human_size(self):
        names = self.get_handler_names()
        names = [ x for x in names if (x[0] != '.' and x[-9:] != '.metadata') ]
        size = len(names)

        str = self.gettext('$n obs')
        return Template(str).substitute(n=size)


    def _browse_namespace(self, object, icon_size):
        line = {}
        id = str(self.get_pathto(object))
        line['id'] = id
        title = object.get_title()
        line['title_or_name'] = title
        firstview = object.get_firstview()
        if firstview is None:
            href = None
        else:
            href = '%s/;%s' % (id, firstview)
        line['name'] = (id, href)
        line['format'] = self.gettext(object.class_title)
        line['title'] = object.get_property('dc:title')
        # Titles
        line['short_title'] = reduce_string(title, 12, 40)
        # The size
        line['size'] = object.get_human_size()
        # The url
        line['href'] = href
        # The icon
        path_to_icon = object.get_path_to_icon(icon_size, from_handler=self)
        if path_to_icon.startswith(';'):
            path_to_icon = Path('%s/' % object.name).resolve(path_to_icon)
        line['img'] = path_to_icon
        # The modification time
        accept = get_context().get_accept_language()
        line['mtime'] = format_datetime(object.get_mtime(), accept=accept)
        # The workflow state
        line['workflow_state'] = ''
        if isinstance(object, WorkflowAware):
            statename = object.get_statename()
            state = object.get_state()
            msg = self.gettext(state['title']).encode('utf-8')
            state = ('<a href="%s/;state_form" class="workflow">'
                     '<strong class="wf_%s">%s</strong>'
                     '</a>') % (object.name, statename, msg)
            line['workflow_state'] = Parser(state)
        # Objects that should not be removed/renamed/etc
        line['checkbox'] = object.name not in self.__fixed_handlers__

        return line


    def browse_namespace(self, icon_size, sortby=['title_or_name'],
                         sortorder='up', batchstart=0, batchsize=20,
                         query=None, results=None):
        context = get_context()
        # Load variables from the request
        start = context.get_form_value('batchstart', type=Integer,
                                       default=batchstart)
        size = context.get_form_value('batchsize', type=Integer,
                                      default=batchsize)

        # Search
        root = context.root
        if results is None:
            results = root.search(query)

        reverse = (sortorder == 'down')
        documents = results.get_documents(sort_by=sortby, reverse=reverse,
                                          start=start, size=batchsize)

        # Get the handlers, check security
        user = context.user
        handlers = []
        for document in documents:
            handler = root.get_handler(document.abspath)
            ac = handler.get_access_control()
            if ac.is_allowed_to_view(user, handler):
                handlers.append(handler)

        # Get the handler for the visible documents and extracts values
        objects = []
        for handler in handlers:
            line = self._browse_namespace(handler, icon_size)
            objects.append(line)

        # Build namespace
        namespace = {}
        total = results.get_n_documents()
        namespace['total'] = total
        namespace['objects'] = objects

        # The batch
        namespace['batch'] = widgets.batch(context.uri, start, size, total)

        return namespace


    def browse_thumbnails(self, context):
        context.set_cookie('browse', 'thumb')

        query = EqQuery('parent_path', self.get_abspath())
        namespace = self.browse_namespace(48, query=query)

        handler = self.get_handler('/ui/folder/browse_thumbnails.xml')
        return stl(handler, namespace)


    # Allow displaying the "Select All/None" Javascript buttons
    select__access__ = True

    def browse_list(self, context, sortby=['title_or_name'], sortorder='up'):
        context.set_cookie('browse', 'list')

        # Get the form values
        get_form_value = context.get_form_value
        term = get_form_value('search_term', type=Unicode)
        term = term.strip()
        field = get_form_value('search_field')
        search_subfolders = get_form_value('search_subfolders', type=Boolean,
                                           default=False)

        sortby = context.get_form_values('sortby', default=sortby)
        sortorder = context.get_form_value('sortorder', sortorder)

        # Build the query
        abspath = self.get_abspath()
        if term:
            if search_subfolders is True:
                query = EqQuery('paths', abspath)
            else:
                query = EqQuery('parent_path', abspath)
            query = AndQuery(query, PhraseQuery(field, term))
        else:
            query = EqQuery('parent_path', abspath)

        # Build the namespace
        namespace = self.browse_namespace(16, query=query, sortby=sortby,
                                          sortorder=sortorder)
        namespace['search_term'] = term
        namespace['search_subfolders'] = search_subfolders
        namespace['search_fields'] = [
            {'id': x['id'], 'title': self.gettext(x['title']),
             'selected': x['id'] == field or None}
            for x in self.get_search_criteria() ]

        # The column headers
        columns = [
            ('name', u'Name'), ('title', u'Title'), ('format', u'Type'),
            ('mtime', u'Date'), ('size', u'Size'),
            ('workflow_state', u'State')]

        # Actions
        user = context.user
        ac = self.get_access_control()
        actions = []
        message = self.gettext(u"Delete this objet, are you sure?")
        if namespace['total']:
            actions = [
                ('select', u'Select All', 'button_select_all',
                 "return select_checkboxes('browse_list', true);"),
                ('select', u'Select None', 'button_select_none',
                 "return select_checkboxes('browse_list', false);"),
                ('remove', u'Remove', 'button_delete',
                 'return confirmation("%s");' % message.encode('utf_8')),
                ('rename_form', u'Rename', 'button_rename', None),
                ('copy', u'Copy', 'button_copy', None),
                ('cut', u'Cut', 'button_cut', None)]
            actions = [(x[0], self.gettext(x[1]), x[2], x[3])
                    for x in actions if ac.is_access_allowed(user, self, x[0])]
        if context.has_cookie('ikaaro_cp'):
            if ac.is_access_allowed(user, self, 'paste'):
                actions.append(('paste', self.gettext(u'Paste'),
                                'button_paste', None))

        # Go!
        namespace['table'] = widgets.table(
            columns, namespace['objects'], sortby, sortorder, actions,
            self.gettext)

        handler = self.get_handler('/ui/folder/browse_list.xml')
        return stl(handler, namespace)


    def browse_image(self, context):
        selected_image = context.get_form_value('selected_image')
        selected_index = None

        # check selected image
        if selected_image is not None:
            path = Path(selected_image)
            selected_image = path[-1]
            if not selected_image in self.get_handler_names():
                selected_image = None

        # look up available images
        query = EqQuery('parent_path', self.get_abspath())
        namespace = self.browse_namespace(48, query=query, batchsize=0)
        objects = []
        offset = 0
        for index, object in enumerate(namespace['objects']):
            name = object['name']
            if isinstance(name, tuple):
                name = name[0]
            handler = self.get_handler(name)
            if not isinstance(handler, Image):
                offset = offset + 1
                continue
            if selected_image is None:
                selected_image = name
            if selected_image == name:
                selected_index = index - offset
            object['name'] = name
            objects.append(object)

        namespace['objects'] = objects

        # selected image namespace
        if selected_image is None:
            namespace['selected'] = None
        else:
            image = self.get_handler(selected_image)
            selected = {}
            selected['title_or_name'] = image.get_title()
            selected['description'] = image.get_property('dc:description')
            selected['url'] = '%s/;%s' % (image.name, image.get_firstview())
            selected['preview'] = '%s/;icon48?height=320&width=320' \
                                  % image.name
            size = image.get_size()
            if size is None:
                # PIL not installed
                width, height = 0, 0
            else:
                width, height = size
            selected['width'] = width
            selected['height'] = height
            selected['format'] = image.get_property('format')
            if selected_index == 0:
                selected['previous'] = None
            else:
                previous = objects[selected_index - 1]['name']
                selected['previous'] = ';%s?selected_image=%s' % (
                        context.method, previous)
            if selected_index == (len(objects) - 1):
                selected['next'] = None
            else:
                next = objects[selected_index + 1]['name']
                selected['next'] = ';%s?selected_image=%s' % (context.method,
                        next)
            namespace['selected'] = selected

        # Append gallery style
        css = self.get_handler('/ui/gallery.css')
        context.styles.append(str(self.get_pathto(css)))

        handler = self.get_handler('/ui/folder/browse_image.xml')
        return stl(handler, namespace)


    remove__access__ = 'is_allowed_to_remove'
    def remove(self, context):
        ids = context.get_form_values('ids')
        if not ids:
            return context.come_back(u'No objects selected.')

        removed = []
        not_allowed = []

        user = context.user
        for name in ids:
            handler = self.get_handler(name)
            ac = handler.get_access_control()
            if ac.is_allowed_to_remove(user, handler):
                # Remove handler
                self.del_object(name)
                removed.append(name)
            else:
                not_allowed.append(name)

        return context.come_back(
            u'Objects removed: $objects.', objects=', '.join(removed))


    rename_form__access__ = 'is_allowed_to_move'
    def rename_form(self, context):
        ids = context.get_form_values('ids')
        # Filter names which the authenticated user is not allowed to move
        handlers = [ self.get_handler(x) for x in ids ]
        ac = self.get_access_control()
        names = [ x.name for x in handlers
                  if ac.is_allowed_to_move(context.user, x) ]

        # Check input data
        if not names:
            return context.come_back(u'No objects selected.')

        # XXX Hack to get rename working. The current user interface
        # forces the rename_form to be called as a form action, hence
        # with the POST method, but it should be a GET method. Maybe
        # it will be solved after the needed folder browse overhaul.
        if context.request.method == 'POST':
            ids_list = '&'.join([ 'ids=%s' % x for x in names ])
            return get_reference(';rename_form?%s' % ids_list)

        # Build the namespace
        namespace = {}
        namespace['objects'] = []
        for real_name in names:
            name, extension, language = FileName.decode(real_name)
            namespace['objects'].append({'real_name': real_name, 'name': name})

        # Process the template
        handler = self.get_handler('/ui/folder/rename.xml')
        return stl(handler, namespace)


    rename__access__ = 'is_allowed_to_move'
    def rename(self, context):
        names = context.get_form_values('names')
        new_names = context.get_form_values('new_names')
        # Process input data
        for i, old_name in enumerate(names):
            xxx, extension, language = FileName.decode(old_name)
            new_name = FileName.encode((new_names[i], extension, language))
            new_name = checkid(new_name)
            if new_name is None:
                # Invalid name
                return context.come_back(MSG_BAD_NAME)
            # Rename
            if new_name != old_name:
                # XXX itools should provide an API to copy and move handlers
                handler = self.get_handler(old_name)
                handler_metadata = handler.get_metadata()
                self.set_object(new_name, handler, handler_metadata)
                self.del_object(old_name)


        message = u'Objects renamed.'
        return context.come_back(message, goto=';browse_content')


    copy__access__ = 'is_allowed_to_copy'
    def copy(self, context):
        ids = context.get_form_values('ids')
        # Filter names which the authenticated user is not allowed to copy
        handlers = [ self.get_handler(x) for x in ids ]
        ac = self.get_access_control()
        names = [ x.name for x in handlers
                  if ac.is_allowed_to_copy(context.user, x) ]

        if not names:
            return context.come_back(u'No objects selected.')

        path = self.get_abspath()
        cp = (False, [ '%s/%s' % (path, x) for x in names ])
        cp = urllib.quote(zlib.compress(marshal.dumps(cp), 9))
        context.set_cookie('ikaaro_cp', cp, path='/')

        return context.come_back(u'Objects copied.')


    cut__access__ = 'is_allowed_to_move'
    def cut(self, context):
        ids = context.get_form_values('ids')
        # Filter names which the authenticated user is not allowed to move
        handlers = [ self.get_handler(x) for x in ids ]
        ac = self.get_access_control()
        names = [ x.name for x in handlers
                  if ac.is_allowed_to_move(context.user, x) ]

        if not names:
            return context.come_back(u'No objects selected.')

        path = self.get_abspath()
        cp = (True, [ '%s/%s' % (path, x) for x in names ])
        cp = urllib.quote(zlib.compress(marshal.dumps(cp), 9))
        context.set_cookie('ikaaro_cp', cp, path='/')

        return context.come_back(u'Objects cut.')


    paste__access__ = 'is_allowed_to_add'
    def paste(self, context):
        cp = context.get_cookie('ikaaro_cp')
        if cp is None:
            return context.come_back(u'Nothing to paste.')

        root = context.root
        allowed_types = tuple(self.get_document_types())
        cut, paths = marshal.loads(zlib.decompress(urllib.unquote(cp)))
        for path in paths:
            handler = root.get_handler(path)
            if not isinstance(handler, allowed_types):
                continue

            name = handler.name
            # Find a non used name
            # XXX ROBLES To be tested carefully and optimized
            while self.has_handler(name):
                name = name.split('.')
                id = name[0].split('_')
                index = id[-1]
                try:   # tests if id ends with a number
                    index = int(index)
                except ValueError:
                    id.append('copy_1')
                else:
                    try:  # tests if the pattern is '_copy_x'
                       if id[-2] == 'copy':
                          index = str(index + 1) # increment index
                          id[-1] = index
                       else:
                          id.append('copy_1')
                    except IndexError:
                       id.append('copy_1')
                    else:
                       pass
                id = '_'.join(id)
                name[0] = id
                name = '.'.join(name)
            # Unicode is not a valid Zope id
            name = str(name)
            # Add it here
            metadata = handler.metadata
            self.set_object(name, handler, metadata)
            if cut is True:
                # Cut&Paste (remove original)
                container = handler.parent
                container.del_object(name)
            else:
                # Copy&Paste (fix metadata properties)
                handler = self.get_handler(name)
                metadata = handler.metadata
                # Fix state
                if isinstance(handler, WorkflowAware):
                    metadata.set_property('state', handler.workflow.initstate)
                # Fix owner
                metadata.set_property('owner', context.user.name)

        return context.come_back(u'Objects pasted.')


    browse_content__access__ = 'is_allowed_to_view'
    browse_content__label__ = u'Contents'

    def browse_content__sublabel__(self, **kw):
        mode = kw.get('mode', 'thumbnails')
        return {'thumbnails': u'As Icons',
                'list': u'As List',
                'image': u'As Image Gallery'}[mode]

    def browse_content(self, context):
        mode = context.get_form_value('mode')
        if mode is None:
            mode = context.get_cookie('browse_mode')
            # Default
            if mode is None:
                mode = 'thumbnails'
        else:
            context.set_cookie('browse_mode', mode)

        method = getattr(self, 'browse_%s' % mode)
        return method(context)


    #######################################################################
    # Add / New Resource
    new_resource_form__access__ = 'is_allowed_to_add'
    new_resource_form__label__ = u'Add'
    def new_resource_form(self, context):
        type = context.get_form_value('type')
        # Type choosen
        if type is not None:
            cls = get_object_class(type)
            return cls.new_instance_form(context)

        # Choose a type
        namespace = {}
        namespace['types'] = []

        for handler_class in self.get_document_types():
            type_ns = {}
            gettext = handler_class.gettext
            format = urllib.quote(handler_class.class_id)
            type_ns['format'] = format
            icon = handler_class.class_icon48
            type_ns['icon'] = self.get_pathtoroot() + 'ui/' + icon
            title = handler_class.class_title
            type_ns['title'] = gettext(title)
            description = handler_class.class_description
            type_ns['description'] = gettext(description)
            type_ns['url'] = ';new_resource_form?type=' + format
            namespace['types'].append(type_ns)

        handler = self.get_handler('/ui/folder/new_resource.xml')
        return stl(handler, namespace)


    new_resource__access__ = 'is_allowed_to_add'
    def new_resource(self, context):
        class_id = context.get_form_value('class_id')
        cls = get_object_class(class_id)
        return cls.new_instance(self, context)


    browse_dir__access__ = 'is_authenticated'
    def browse_dir(self, context):
        namespace = {}
        namespace['bc'] = widgets.Breadcrumb(filter_type=File, start=self)

        # Avoid general template
        response = context.response
        response.set_header('Content-Type', 'text/html; charset=UTF-8')

        handler = self.get_handler('/ui/folder/browsedir.xml')
        return stl(handler, namespace)


    #######################################################################
    # Search
    def get_search_criteria(self):
        """Return the criteria as a list of dictionnary
        like [{'id': criteria_id, 'title' : criteria_title},...]
        """
        return self.search_criteria


    #######################################################################
    # Last Changes
    last_changes__access__ = 'is_allowed_to_view'
    last_changes__label__ = u"Last Changes"
    def last_changes(self, context, sortby=['mtime'], sortorder='down',
                     batchstart=0, batchsize=20):
        root = context.root
        user = context.user
        users = root.get_handler('users')
        namespace = {}

        start = context.get_form_value('batchstart', type=Integer,
                                       default=batchstart)
        sortby = context.get_form_values('sortby', sortby)
        sortorder = context.get_form_value('sortorder', sortorder)

        results = root.search(is_version_aware=True,
                              paths=self.get_abspath())
        documents = results.get_documents(sortby, (sortorder == 'down'), start,
                                          batchsize)

        lines = []
        for document in documents:
            handler = root.get_handler(document.abspath)
            ac = handler.get_access_control()
            if not ac.is_allowed_to_view(user, handler):
                continue
            line = self._browse_namespace(handler, 16)
            revisions = handler.get_revisions(context)
            if revisions:
                last_rev = revisions[0]
                username = last_rev['username']
                try:
                    user = users.get_handler(username)
                    user_title = user.get_title()
                except LookupError:
                    user_title = username
            else:
                user_title = Parser('<em>Unavailable</em>')
            line['last_author'] = user_title
            lines.append(line)

        # The filter (none)
        namespace['search_fields'] = None

        # The batch
        total = results.get_n_documents()
        namespace['batch'] = widgets.batch(context.uri, start, batchsize,
                                           total)

        # The table
        columns = [('name', u'Name'), ('title', u'Title'),
                   ('mtime', u'Last Modified'),
                   ('last_author', u'Last Author'),
                   ('workflow_state', u'State')]
        namespace['table'] = widgets.table(columns, lines, sortby, sortorder,
                                           gettext=self.gettext)

        handler = self.get_handler('/ui/folder/browse_list.xml')
        return stl(handler, namespace)


    # Get list of calendars
    def get_calendars(self):
        return list(self.search_handlers(handler_class=Calendar))


register_object_class(Folder)
register_object_class(Folder, format="application/x-not-regular-file")
