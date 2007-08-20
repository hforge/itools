# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Luis Arturo Belmar-Letelier <luis@itaapy.com>
# Copyright (C) 2006-2007 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
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
import mimetypes

# Import from itools
from itools.datatypes import is_datatype
from itools.uri import Path
from itools.stl import stl, set_prefix
from itools.xhtml import Document
from itools.xml import Parser
from itools.handlers import Image
from itools.rest import checkid
from itools.web import get_context

# Import from itools.cms
from itools.cms.registry import get_object_class
from itools.cms.folder import Folder
from itools.cms.html import XHTMLFile
from itools.cms.messages import *



class OrderAware(object):
    orderable_classes = None

    def get_ordered_folder_names(self, mode='mixed'):
        """
        Return current order plus the unordered names at the end.
            mode mixed -> ordered + unordered
            mode ordered -> ordered
            mode all -> (ordered, unordered)
            default mode : mixed
        """
        orderable_classes = self.orderable_classes or self.__class__
        ordered_names = self.get_property('ikaaro:order')
        real_names = [f.name for f in self.search_handlers()
                if isinstance(f, orderable_classes)]

        ordered_folders = [f for f in ordered_names if f in real_names]
        if mode == 'ordered':
            return ordered_folders
        else:
            unordered_folders = [f for f in real_names if f not in ordered_names]
            if mode == 'all':
                return ordered_folders, unordered_folders
            else:
                return ordered_folders + unordered_folders


    def get_ordered_objects(self, objects, mode='mix'):
        "Return a sorted list of child handlers or brains of them."
        ordered_list = []
        if mode is not 'all':
            ordered_names = self.get_ordered_folder_names(mode)
            for object in objects:
                index = ordered_names.index(object.name)
                ordered_list.append((index, object))

            ordered_list.sort()

            return [x[1] for x in ordered_list]
        else:
            ordered_list, unordered_list = [], []
            ordered_names, unordered_names = self.get_ordered_folder_names(mode)
            for data in [(ordered_names, ordered_list),
                         (unordered_names, unordered_list)]:
                names, l = data
                for object in objects:
                    index = names.index(object.name)
                    l.append((index, object))

            ordered_list.sort()
            unordered_list.sort()

            ordered = [x[1] for x in ordered_list]
            unordered = [x[1] for x in unordered_list]
            return (ordered, unordered)


    order_folders_form__access__ = 'is_allowed_to_edit'
    order_folders_form__label__ = u"Order"
    order_folders_form__sublabel__ = u"Order"
    def order_folders_form(self, context):
        namespace = {}

        ordered_folders = []
        unordered_folders = []
        ordered_folders_names, unordered_folders_names = self.get_ordered_folder_names('all')

        for data in [(ordered_folders_names, ordered_folders),
                     (unordered_folders_names, unordered_folders)]:
            names, l = data
            for name in names:
                folder = self.get_handler(name)
                ns = {
                    'name': folder.name,
                    'title': folder.get_property('dc:title')
                }
                l.append(ns)

        namespace['ordered_folders'] = ordered_folders
        namespace['unordered_folders'] = unordered_folders

        handler = self.get_handler('/ui/folder/order_items.xml')
        return stl(handler, namespace)


    order_folders_up__access__ = 'is_allowed_to_edit'
    def order_folders_up(self, context):
        names = context.get_form_values('ordered_names')
        if not names:
            return context.come_back(u"Please select the ordered objects to order up.")

        ordered_names = self.get_ordered_folder_names('ordered')
        
        if ordered_names[0] == names[0]:
            return context.come_back(u"Objects already up.")

        temp = list(ordered_names)
        for name in names:
            idx = temp.index(name)
            temp.remove(name)
            temp.insert(idx - 1, name)

        self.set_property('ikaaro:order', tuple(temp))
        message = u"Objects ordered up."
        return context.come_back(message)
        
        
    order_folders_down__access__ = 'is_allowed_to_edit'
    def order_folders_down(self, context):
        names = context.get_form_values('ordered_names')
        if not names:
            return context.come_back(
                u"Please select the ordered objects to order down.")
        
        ordered_names = self.get_ordered_folder_names('ordered')

        if ordered_names[-1] == names[-1]:
            return context.come_back(u"Objects already down.")
            
        temp = list(ordered_names)
        names.reverse()
        for name in names:
            idx = temp.index(name)
            temp.remove(name)
            temp.insert(idx + 1, name)

        self.set_property('ikaaro:order', tuple(temp))
        message = u"Objects ordered down."
        return context.come_back(message)


    order_folders_top__access__ = 'is_allowed_to_edit'
    def order_folders_top(self, context):
        names = context.get_form_values('ordered_names')
        if not names:
            message = u"Please select the ordered objects to order on top."
            return context.come_back(message)

        ordered_names = self.get_ordered_folder_names('ordered')
        
        if ordered_names[0] == names[0]:
            message = u"Objects already on top."
            return context.come_back(message)

        temp = names + [name for name in ordered_names
                if name not in names]

        self.set_property('ikaaro:order', tuple(temp))
        message = u"Objects ordered on top."
        return context.come_back(message)
        
        
    order_folders_bottom__access__ = 'is_allowed_to_edit'
    def order_folders_bottom(self, context):
        names = context.get_form_values('ordered_names')
        if not names:
            message = u"Please select the ordered objects to order on bottom."
            return context.come_back(message)

        ordered_names = self.get_ordered_folder_names('ordered')
        
        if ordered_names[-1] == names[-1]:
            message = u"Objects already on bottom."
            return context.come_back(message)

        temp = [name for name in ordered_names
                if name not in names] + names

        self.set_property('ikaaro:order', tuple(temp))
        message = u"Objects ordered on bottom."
        return context.come_back(message)


    order_folders_ordered__access__ = 'is_allowed_to_edit'
    def order_folders_ordered(self, context):
        names = context.get_form_values('unordered_names')
        if not names:
            message = u"Please select the unordered objects to move into the ordered category."
            return context.come_back(message)

        ordered_names, unordered_names = self.get_ordered_folder_names('all')
        temp = list(ordered_names) + [name for name in names]

        self.set_property('ikaaro:order', tuple(temp))
        message = u"Objects moved to ordered category."
        return context.come_back(message)


    order_folders_unordered__access__ = 'is_allowed_to_edit'
    def order_folders_unordered(self, context):
        names = context.get_form_values('ordered_names')
        if not names:
            message = u"Please select the ordered objects to move into the unordered category."
            return context.come_back(message)

        ordered_names, unordered_names = self.get_ordered_folder_names('all')

        temp = [name for name in ordered_names
                if name not in names]

        self.set_property('ikaaro:order', tuple(temp))
        message = u"Objects moved to ordered category."
        return context.come_back(message)



class Dressable(Folder):

    class_views = [['edit_document']]
    template = None
    schema = {}


    def new(self, **kw):
        Folder.new(self, **kw)
        cache = self.cache

        for key, data in self.schema.iteritems():
            if isinstance(data, tuple):
                name, cls = data
                if is_datatype(cls, Document):
                    handler = cls()
                    cache[name] = handler
                    cache['%s.metadata' % name] = handler.build_metadata()


    #######################################################################
    # API / Private
    #######################################################################
    def _get_image(self, context, handler):
        here = context.handler
        path = here.get_pathto(handler)
        content = '<img src="%s"/>' % path
        return Parser(content)


    def _get_document(self, context, handler):
        here = context.handler
        stream = handler.get_body().get_content_elements()
        prefix = here.get_pathto(handler)
        return set_prefix(stream, prefix)


    view__label__ = u'View'
    def view(self, context):
        namespace = {}

        for key, data in self.schema.iteritems():
            content = ''
            if isinstance(data, tuple):
                name, kk = data
                if self.has_handler(name):
                    handler = self.get_handler(name)
                    if is_datatype(handler, Image):
                        content = self._get_image(context, handler)
                    elif is_datatype(handler, Document):
                        content = self._get_document(context, handler)
                    else:
                        raise NotImplementedError
            else:
                content = getattr(self, data)(context)
            namespace[key] = content

        handler = self.get_handler(self.template)
        return stl(handler, namespace)


    #######################################################################
    # API
    #######################################################################
    edit_document__access__ = 'is_allowed_to_edit'
    edit_document__label__ = 'edit'
    def edit_document(self, context):
        name = context.get_form_value('dress_name')
        handler = self.get_handler(name)
        return XHTMLFile.edit_form(handler, context)


    edit_image__access__ = 'is_allowed_to_edit'
    def edit_image(self, context):
        name = context.get_form_value('name')
        if self.has_handler(name) is False:
            return context.uri.resolve2('../;add_image_form?name=%s' % name)

        namespace = {}
        name = context.get_form_value('name')
        namespace['name'] = name
        namespace['class_id'] = self.get_class_id_image(name)
        message = self.gettext(MSG_DELETE_OBJECT)
        msg = 'return confirmation("%s");' % message.encode('utf_8')
        namespace['remove_action'] = msg

        # size
        handler = self.get_handler(name)
        width, height = handler.size
        if width > 640:
            coef = 640 / float(width)
            width = 640
            height = height * coef
        elif height > 480:
            coef = 480 / float(height)
            height = 480
            width = width * coef
        namespace['width'] = width
        namespace['height'] = height

        handler = self.get_handler('/ui/dressable/upload_image.xml')
        return stl(handler, namespace)


    def get_class_id_image(self, handler_name):
        """
        Return the class id of a handler
        """
        for key, data in self.schema.iteritems():
            if isinstance(data, tuple):
                name, cls = data
                if name == handler_name:
                    return cls.class_id
        raise AttributeError


    add_image_form__access__ = 'is_allowed_to_edit'
    def add_image_form(self, context):
        namespace = {}
        name = context.get_form_value('name')
        namespace['name'] = name
        namespace['class_id'] = self.get_class_id_image(name)

        handler = self.get_handler('/ui/dressable/Image_new_instance.xml')
        return stl(handler, namespace)


    new_image_resource__access__ = 'is_allowed_to_edit'
    def new_image_resource(self, context):
        class_id = context.get_form_value('class_id')
        image_name = context.get_form_value('name')

        # Check input data
        file = context.get_form_value('file')
        if file is None:
            return context.come_back(MSG_EMPTY_FILENAME)

        # Interpret input data (the mimetype sent by the browser can be
        # minimalistic)
        kk, mimetype, body = file
        guessed, encoding = mimetypes.guess_type(image_name)

        # Check the name
        name = checkid(image_name)
        if name is None:
            return context.come_back(MSG_BAD_NAME)

        # Add the language extension to the name
        if mimetype.startswith('image/') is False:
            return context.come_back(u'The file is not an image')

        # Build the object
        cls = get_object_class(class_id)
        handler = cls(string=body)
        metadata = handler.build_metadata()
        # Add the object
        if self.has_handler(image_name):
            handler = self.get_handler(image_name)
            handler.load_state_from_string(body)
        else:
            handler, metadata = self.set_object(name, handler, metadata)

        goto = './;view'
        return context.come_back(MSG_NEW_RESOURCE, goto=goto)


    remove_image__access__ = 'is_allowed_to_edit'
    def remove_image(self, context):
        name = context.get_form_value('name')
        self.del_object(name)
        goto = './;view'
        return context.come_back(u'Objects removed: %s' % name, goto=goto)


    def get_epoz_document(self):
        name = get_context().get_form_value('dress_name')
        return self.get_handler(name)


    #######################################################################
    # User interface
    #######################################################################
    def get_subviews(self, name):
        if name == 'edit_document':
            subviews = []
            for key, data in self.schema.iteritems():
                if isinstance(data, tuple):
                    name, cls = data
                    if is_datatype(cls, Document):
                        ref = 'edit_document?dress_name=%s' % name
                        subviews.append(ref)
                    elif is_datatype(cls, Image):
                        ref = 'edit_image?name=%s' % name
                        subviews.append(ref)
            return subviews
        return Folder.get_subviews(self, name)


    def edit_document__sublabel__(self, **kw):
        dress_name = kw.get('dress_name')
        handler = self.get_handler(dress_name)
        return handler.get_property('dc:title') or handler.name


    def edit_image__sublabel__(self, **kw):
        name = kw.get('name')
        if self.has_handler(name):
            handler = self.get_handler(name)
            return handler.get_property('dc:title') or handler.name
        return name
