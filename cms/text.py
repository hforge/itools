# -*- coding: UTF-8 -*-
# Copyright (C) 2002-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
import cgi

# Import from itools
from itools.datatypes import FileName
from itools.i18n import get_language_name
from itools.handlers import Text as BaseText, Python as BasePython
from itools.gettext import PO as BasePO
from itools.stl import stl
from itools.rest import Document as RestDocument, checkid
from utils import get_parameters
from file import File
from messages import *
from registry import register_object_class


class Text(File, BaseText):

    class_id = 'text'
    class_title = u'Plain Text'
    class_description = u'Keep your notes with plain text files.'
    class_icon16 = 'images/Text16.png'
    class_icon48 = 'images/Text48.png'
    class_views = [['view', 'view_rest'],
                   ['edit_form', 'externaledit', 'upload_form'],
                   ['edit_metadata_form'],
                   ['state_form'],
                   ['history_form']]


    @classmethod
    def new_instance_form(cls, context, name=''):
        root = context.root

        namespace = {}
        namespace['name'] = name
        # The class id
        namespace['class_id'] = cls.class_id
        # Languages
        languages = []
        website_languages = root.get_property('ikaaro:website_languages')
        default_language = website_languages[0]
        for code in website_languages:
            language_name = get_language_name(code)
            languages.append({'code': code,
                              'name': cls.gettext(language_name),
                              'isdefault': code == default_language})
        namespace['languages'] = languages

        handler = root.get_handler('ui/text/new_instance.xml')
        return stl(handler, namespace)


    @classmethod
    def new_instance(cls, container, context):
        name = context.get_form_value('name')
        title = context.get_form_value('dc:title')
        language = context.get_form_value('dc:language')

        # Check the name
        name = name.strip() or title.strip()
        if not name:
            return context.come_back(MSG_NAME_MISSING)

        name = checkid(name)
        if name is None:
            return context.come_back(MSG_BAD_NAME)

        # Add the language extension to the name
        name = FileName.encode((name, cls.class_extension, language))

        # Check the name is free
        if container.has_handler(name):
            return context.come_back(MSG_NAME_CLASH)

        # Build the object
        handler = cls()
        metadata = handler.build_metadata()
        metadata.set_property('dc:title', title, language=language)
        metadata.set_property('dc:language', language)
        # Add the object
        handler, metadata = container.set_object(name, handler, metadata)

        goto = './%s/;%s' % (name, handler.get_firstview())
        return context.come_back(MSG_NEW_RESOURCE, goto=goto)


    #######################################################################
    # User interface
    #######################################################################

    # Download
    def get_content_type(self):
        return '%s; charset=UTF-8' % File.get_content_type(self)


    #######################################################################
    # View
    view__access__ = 'is_allowed_to_view'
    view__label__ = u'View'
    view__sublabel__ = u'Plain Text'
    def view(self, context):
        namespace = {}
        namespace['text'] = cgi.escape(self.to_str())

        handler = self.get_handler('/ui/text/view.xml')
        return stl(handler, namespace)


    view_rest__access__ = 'is_allowed_to_view'
    view_rest__sublabel__ = u"As reStructuredText"
    def view_rest(self, context):
        namespace = {}

        document = RestDocument(self.uri)
        return document.get_content_as_html()


    view_xml__access__ = 'is_allowed_to_view'
    view_xml__sublabel__ = u"As reStructuredText"
    def view_xml(self, context):
        namespace = {}

        document = RestDocument(self.uri)
        namespace['text'] = document.get_content_as_xml()

        handler = self.get_handler('/ui/text/view.xml')
        return stl(handler, namespace)


    #######################################################################
    # Edit / Inline
    edit_form__access__ = 'is_allowed_to_edit'
    edit_form__label__ = u'Edit'
    edit_form__sublabel__ = u'Inline'
    def edit_form(self, context):
        namespace = {}
        namespace['data'] = self.to_str()

        handler = self.get_handler('/ui/text/edit.xml')
        return stl(handler, namespace)


    edit__access__ = 'is_allowed_to_edit'
    def edit(self, context):
        data = context.get_form_value('data')
        self.load_state_from_string(data)

        return context.come_back(MSG_CHANGES_SAVED)


    #######################################################################
    # Edit / External
    def externaledit(self, context):
        namespace = {}
        # XXX This list should be built from a txt file with all the encodings,
        # or better, from a Python module that tells us which encodings Python
        # supports.
        namespace['encodings'] = [{'value': 'utf-8', 'title': 'UTF-8',
                                   'is_selected': True},
                                  {'value': 'iso-8859-1',
                                   'title': 'ISO-8859-1',
                                   'is_selected': False}]

        handler = self.get_handler('/ui/text/externaledit.xml')
        return stl(handler, namespace)


register_object_class(Text)



class PO(Text, BasePO):

    class_id = 'text/x-po'
    class_title = u'Message Catalog'


    #######################################################################
    # User interface
    #######################################################################


    #######################################################################
    # Edit
    edit_form__access__ = 'is_allowed_to_edit'
    edit_form__label__ = u'Edit'
    edit_form__sublabel__ = u'Inline'
    def edit_form(self, context):
        namespace = {}

        # Get the messages, all but the header
        msgids = [ x for x in self.get_msgids() if x.strip() ]

        # Set total
        total = len(msgids)
        namespace['messages_total'] = str(total)

        # Set the index
        parameters = get_parameters('messages', index='1')
        index = parameters['index']
        namespace['messages_index'] = index
        index = int(index)

        # Set first, last, previous and next
        uri = context.uri
        namespace['messages_first'] = uri.replace(messages_index=1)
        namespace['messages_last'] = uri.replace(messages_index=total)
        previous = max(index - 1, 1)
        namespace['messages_previous'] = uri.replace(messages_index=previous)
        next = min(index + 1, total)
        namespace['messages_next'] = uri.replace(messages_index=next)

        # Set msgid and msgstr
        if msgids:
            msgids.sort()
            msgid = msgids[index-1]
            namespace['msgid'] = cgi.escape(msgid)
            msgstr = self.get_msgstr(msgid)
            msgstr = cgi.escape(msgstr)
            namespace['msgstr'] = msgstr
        else:
            namespace['msgid'] = None

        handler = self.get_handler('/ui/PO_edit.xml')
        return stl(handler, namespace)


    edit__access__ = 'is_allowed_to_edit'
    def edit(self, context):
        msgid = context.get_form_value('msgid')
        msgstr = context.get_form_value('msgstr')
        messages_index = context.get_form_value('messages_index')

        self.set_changed()
        msgid = msgid.replace('\r', '')
        msgstr = msgstr.replace('\r', '')
##        self.set_message(msgid, msgstr)
        self._messages[msgid].msgstr = msgstr

        return context.come_back(MSG_CHANGES_SAVED)


register_object_class(PO)



class CSS(Text):

    class_mimetypes = ['text/css']
    class_extension = 'css'
    class_id = 'text/css'
    class_title = 'CSS'
    class_icon48 = 'images/CSS48.png'


register_object_class(CSS)



class Python(BasePython):

    class_id = 'text/x-python'
    class_icon48 = 'images/Python48.png'


register_object_class(Python)
