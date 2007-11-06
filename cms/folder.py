# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2005 Alexandre Fernandez <alex@itaapy.com>
# Copyright (C) 2006-2007 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2006-2007 Nicolas Deram <nicolas@itaapy.com>
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
from marshal import dumps, loads
from string import Template
from urllib import quote, quote_plus, unquote
from zlib import compress, decompress

# Import from itools
from itools.i18n import format_datetime
from itools.uri import Path, get_reference
from itools.catalog import CatalogAware, EqQuery, AndQuery, PhraseQuery
from itools.datatypes import Boolean, DataType, FileName, Integer, Unicode
from itools import vfs
from itools.handlers import Folder as BaseFolder, get_handler_class
from itools.rest import checkid
from itools.stl import stl
from itools.web import get_context
from itools.xml import Parser

# Import from itools.cms
from base import Handler
from binary import Image
from handlers import Lock, Metadata
from ical import CalendarAware
from messages import MSG_DELETE_SELECTION, MSG_BAD_NAME, MSG_EXISTANT_FILENAME
from versioning import VersioningAware
from workflow import WorkflowAware
from utils import generate_name, reduce_string
import widgets
from registry import register_object_class, get_object_class
from catalog import schedule_to_index, schedule_to_unindex



class CopyCookie(DataType):

    default = None, []

    @staticmethod
    def encode(value):
        return quote(compress(dumps(value), 9))


    @staticmethod
    def decode(str):
        return loads(decompress(unquote(str)))



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
        ['browse_content?mode=list',
         'browse_content?mode=thumbnails',
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


    #######################################################################
    # Traverse
    #######################################################################
    GET__access__ = True
    def GET(self, context):
        # Try index
        try:
            self.get_handler('index')
        except LookupError:
            return Handler.GET(self, context)

        return context.uri.resolve2('index')


    #######################################################################
    # API
    #######################################################################
    def _has_object(self, name):
        return self.has_handler('%s.metadata' % name)


    def _get_names(self):
        return [ x[:-9] for x in self.get_handler_names()
                 if x[-9:] == '.metadata' ]


    def _get_object(self, name):
        database = self.database
        uri = self.uri.resolve2(name)
        timestamp = None
        dirty = False
        # The metadata
        metadata = self.get_handler('%s.metadata' % name)
        format = metadata.get_property('format')
        # The object
        cls = get_object_class(format)
        try:
            handler = self.get_handler(name, cls=cls)
        except LookupError:
            handler = cls()
            database.cache[uri] = handler
            # Attach
            handler.database = database
            handler.uri = uri
            handler.timestamp = timestamp
            handler.dirty = dirty
        return handler


    def set_object(self, name, handler, metadata=None):
        """
        Adds the given handler (and metadata). The handler may be not an
        instance but a class, then the handler will not be added, only
        the metadata.
        """
        if metadata is None:
            metadata = handler.build_metadata()

        # The metadata
        self.set_handler('%s.metadata' % name, metadata)
        metadata.parent = self
        metadata.name = '%s.metadata' % name

        # The handler
        if type(handler) is type:
            # Class
            handler = handler()
            handler.database = self.database
            handler.uri = self.uri.resolve2(name)
        else:
            # Instance
            self.set_handler(name, handler)
        handler.parent = self
        handler.name = name

        # Versioning
        if isinstance(handler, VersioningAware):
            handler.commit_revision()

        # Schedule to index
        if isinstance(handler, Folder):
            for x in handler.traverse_objects():
                schedule_to_index(x)
        else:
            schedule_to_index(handler)

        return handler, metadata


    def del_object(self, name):
        # Schedule to unindex
        handler = self.get_object(name)
        if isinstance(handler, Folder):
            for x in handler.traverse_objects():
                schedule_to_unindex(x)
        else:
            schedule_to_unindex(handler)

        # Remove
        self.del_handler('%s.metadata' % name)
        if self.has_handler(name):
            self.del_handler(name)


    def copy_object(self, source, target):
        # Copy
        source = self.get_object(source).uri
        self.copy_handler(source, target)
        self.copy_handler('%s.metadata' % source, '%s.metadata' % target)

        # Index
        handler = self.get_object(target)
        if isinstance(handler, Folder):
            for x in handler.traverse_objects():
                schedule_to_index(x)
        else:
            schedule_to_index(handler)


    def move_object(self, source, target):
        # Unindex
        handler = self.get_object(source)
        if isinstance(handler, Folder):
            for x in handler.traverse_objects():
                schedule_to_unindex(x)
        else:
            schedule_to_unindex(handler)

        # Move
        source = self.get_object(source).uri
        self.move_handler(source, target)
        self.move_handler('%s.metadata' % source, '%s.metadata' % target)

        # Index
        handler = self.get_object(target)
        if isinstance(handler, Folder):
            for x in handler.traverse_objects():
                schedule_to_index(x)
        else:
            schedule_to_index(handler)


    def traverse_objects(self):
        yield self
        for name in self._get_names():
            handler = self.get_object(name)
            if isinstance(handler, Folder):
                for x in handler.traverse_objects():
                    yield x
            else:
                yield handler


    def search_handlers(self, path='.', format=None, state=None,
                        handler_class=None):
        container = self.get_object(path)
        for handler in container.get_objects():
            if handler_class is not None:
                if not isinstance(handler, handler_class):
                    continue

            get_property = handler.get_metadata().get_property
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
                ref = 'new_resource_form?type=%s' % quote_plus(id)
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
        names = self.get_names()
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


    def browse_namespace(self, icon_size, sortby=['title'], sortorder='up',
                         batchstart=0, batchsize=20, query=None,
                         results=None):
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
            handler = root.get_object(document.abspath)
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

        handler = self.get_object('/ui/folder/browse_thumbnails.xml')
        return stl(handler, namespace)


    def browse_list(self, context, sortby=['title'], sortorder='up'):
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
        abspath = self.abspath
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
        message = self.gettext(MSG_DELETE_SELECTION)
        if namespace['total']:
            actions = [
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

        handler = self.get_object('/ui/folder/browse_list.xml')
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
        css = self.get_object('/ui/gallery.css')
        context.styles.append(str(self.get_pathto(css)))

        handler = self.get_object('/ui/folder/browse_image.xml')
        return stl(handler, namespace)


    remove__access__ = 'is_allowed_to_remove'
    def remove(self, context):
        # Check input
        ids = context.get_form_values('ids')
        if not ids:
            return context.come_back(u'No objects selected.')

        # Clean the copy cookie if needed
        cut, paths = context.get_cookie('ikaaro_cp', type=CopyCookie)

        # Remove objects
        removed = []
        not_allowed = []
        user = context.user
        abspath = self.abspath
        for name in ids:
            handler = self.get_object(name)
            ac = handler.get_access_control()
            if ac.is_allowed_to_remove(user, handler):
                # Remove handler
                self.del_object(name)
                removed.append(name)
                # Clean cookie
                if (abspath + '/' + name) in paths:
                    context.del_cookie('ikaaro_cp')
                    paths = []
            else:
                not_allowed.append(name)

        message = u'Objects removed: $objects.'
        return context.come_back(message, objects=', '.join(removed))


    rename_form__access__ = 'is_allowed_to_move'
    def rename_form(self, context):
        # Filter names which the authenticated user is not allowed to move
        ac = self.get_access_control()
        names = [
            x for x in context.get_form_values('ids')
            if ac.is_allowed_to_move(context.user, self.get_object(x)) ]

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
            handler = self.get_object(real_name)
            if handler.class_extension is None:
                name = real_name
            else:
                name, extension, language = FileName.decode(real_name)
            namespace['objects'].append({'real_name': real_name, 'name': name})

        # Process the template
        handler = self.get_object('/ui/folder/rename.xml')
        return stl(handler, namespace)


    rename__access__ = 'is_allowed_to_move'
    def rename(self, context):
        names = context.get_form_values('names')
        new_names = context.get_form_values('new_names')
        used_names = self.get_names()
        # Clean the copy cookie if needed
        cut, paths = context.get_cookie('ikaaro_cp', type=CopyCookie)

        # Process input data
        abspath = self.abspath
        for i, old_name in enumerate(names):
            new_name = new_names[i]
            handler = self.get_object(old_name)
            if handler.class_extension is not None:
                xxx, extension, language = FileName.decode(old_name)
                new_name = FileName.encode((new_name, extension, language))
            new_name = checkid(new_name)
            if new_name is None:
                # Invalid name
                return context.come_back(MSG_BAD_NAME)
            # Rename
            if new_name != old_name:
                if new_name in used_names:
                    # Name already exists
                    return context.come_back(MSG_EXISTANT_FILENAME)
                # Clean cookie (FIXME Do not clean the cookie, update it)
                if (abspath + '/' + old_name) in paths:
                    context.del_cookie('ikaaro_cp')
                    paths = []
                self.move_object(old_name, new_name)

        message = u'Objects renamed.'
        return context.come_back(message, goto=';browse_content')


    copy__access__ = 'is_allowed_to_copy'
    def copy(self, context):
        # Filter names which the authenticated user is not allowed to copy
        ac = self.get_access_control()
        names = [
            x for x in context.get_form_values('ids')
            if ac.is_allowed_to_copy(context.user, self.get_object(x)) ]

        # Check input data
        if not names:
            return context.come_back(u'No objects selected.')

        abspath = Path(self.abspath)
        cp = (False, [ str(abspath.resolve2(x)) for x in names ])
        cp = CopyCookie.encode(cp)
        context.set_cookie('ikaaro_cp', cp, path='/')

        return context.come_back(u'Objects copied.')


    cut__access__ = 'is_allowed_to_move'
    def cut(self, context):
        # Filter names which the authenticated user is not allowed to move
        ac = self.get_access_control()
        names = [
            x for x in context.get_form_values('ids')
            if ac.is_allowed_to_move(context.user, self.get_object(x)) ]

        # Check input data
        if not names:
            return context.come_back(u'No objects selected.')

        abspath = Path(self.abspath)
        cp = (True, [ str(abspath.resolve2(x)) for x in names ])
        cp = CopyCookie.encode(cp)
        context.set_cookie('ikaaro_cp', cp, path='/')

        return context.come_back(u'Objects cut.')


    paste__access__ = 'is_allowed_to_add'
    def paste(self, context):
        cut, paths = context.get_cookie('ikaaro_cp', type=CopyCookie)
        if len(paths) == 0:
            return context.come_back(u'Nothing to paste.')

        root = context.root
        allowed_types = tuple(self.get_document_types())
        for path in paths:
            try:
                handler = root.get_object(path)
            except LookupError:
                continue
            if not isinstance(handler, allowed_types):
                continue

            container = handler.parent
            # Cut&Paste in the same place (do nothing)
            if cut and self is container:
                continue

            name = generate_name(handler.name, self.get_names(), '_copy_')
            if cut is True:
                # Cut&Paste
                self.move_object(path, name)
            else:
                # Copy&Paste
                self.copy_object(path, name)
                # Fix metadata properties
                handler = self.get_object(name)
                metadata = handler.get_metadata()
                # Fix state
                if isinstance(handler, WorkflowAware):
                    metadata.set_property('state', handler.workflow.initstate)
                # Fix owner
                metadata.set_property('owner', context.user.name)
        # Cut, clean cookie
        if cut is True:
            context.del_cookie('ikaaro_cp')

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

        base = Path(self.abspath).get_pathto('/ui/')
        for cls in self.get_document_types():
            namespace['types'].append({
                'icon': base.resolve2(cls.class_icon48),
                'title': cls.gettext(cls.class_title),
                'description': cls.gettext(cls.class_description),
                'url': ';new_resource_form?type=%s' % quote(cls.class_id)})

        handler = self.get_object('/ui/folder/new_resource.xml')
        return stl(handler, namespace)


    new_resource__access__ = 'is_allowed_to_add'
    def new_resource(self, context):
        class_id = context.get_form_value('class_id')
        cls = get_object_class(class_id)
        return cls.new_instance(self, context)


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
        users = root.get_object('users')
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
            handler = root.get_object(document.abspath)
            ac = handler.get_access_control()
            if not ac.is_allowed_to_view(user, handler):
                continue
            line = self._browse_namespace(handler, 16)
            revisions = handler.get_revisions(context)
            if revisions:
                last_rev = revisions[0]
                username = last_rev['username']
                try:
                    user = users.get_object(username)
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

        handler = self.get_object('/ui/folder/browse_list.xml')
        return stl(handler, namespace)


register_object_class(Folder)
register_object_class(Folder, format="application/x-not-regular-file")
