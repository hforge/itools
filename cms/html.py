# -*- coding: UTF-8 -*-
# Copyright (C) 2002-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006-2007 Hervé Cauwelier <herve@itaapy.com>
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

# Import from itools
from itools.xml import Document as XMLDocument, TEXT, START_ELEMENT
from itools.stl import stl
from itools.xhtml import Document as XHTMLDocument
from itools.html import Document as HTMLDocument, Parser as HTMLParser

# Import from ikaaro
from messages import *
from text import Text
from registry import register_object_class


class XMLFile(Text, XMLDocument):

    class_id = 'text/xml'



class XHTMLFile(Text, XHTMLDocument):

    class_id = 'application/xhtml+xml'
    class_title = u'Web Document'
    class_description = u'Create and publish a Web Document.'
    class_icon16 = 'images/HTML16.png'
    class_icon48 = 'images/HTML48.png'
    class_views = [['view'],
                   ['edit_form', 'externaledit', 'upload_form'],
                   ['edit_metadata_form'],
                   ['state_form'],
                   ['history_form']]


    def GET(self, context):
        method = self.get_firstview()
        # Check access
        if method is None:
            raise Forbidden
        # Redirect
        return context.uri.resolve2(';%s' % method)


    #######################################################################
    # API
    #######################################################################
    def is_empty(self):
        """Test if XML doc is empty"""
        body = self.get_body()
        if body is None:
            return True
        for type, value, line in body.events:
            if type == TEXT:
                if value.replace('&nbsp;', '').strip():
                    return False
            elif type == START_ELEMENT:
                tag_uri, tag_name, attributes = value
                if tag_name == 'img':
                    return False
        return True


    #######################################################################
    # User interface
    #######################################################################

    #######################################################################
    # View
    view__access__ = 'is_allowed_to_view'
    view__label__ = u'View'
    def view(self, context):
        namespace = {}
        body = self.get_body()
        if body is None:
            namespace['text'] = None
        else:
            namespace['text'] = body.get_content_elements()

        handler = self.get_handler('/ui/html/view.xml')
        return stl(handler, namespace)


    #######################################################################
    # Edit / Inline
    def get_epoz_data(self):
        body = self.get_body()
        return body.get_content_elements()


    edit_form__access__ = 'is_allowed_to_edit'
    edit_form__label__ = u'Edit'
    edit_form__sublabel__ = u'Inline'
    def edit_form(self, context):
        """WYSIWYG editor for HTML documents."""
        # If the document has not a body (e.g. a frameset), edit as plain text
        body = self.get_body()
        if body is None:
            return Text.edit_form(self, context)

        # Edit with a rich text editor
        namespace = {}
        # Epoz expects HTML
        data = body.get_content_elements()
        namespace['rte'] = self.get_rte(context, 'data', data)

        handler = self.get_handler('/ui/html/edit.xml')
        return stl(handler, namespace)


    edit__access__ = 'is_allowed_to_edit'
    def edit(self, context):
        new_body = context.get_form_value('data')
        new_body = HTMLParser(new_body)
        # Save the changes
        old_body = self.get_body()
        self.set_changed()
        self.events = (self.events[:old_body.start+1]
                       + new_body
                       + self.events[old_body.end:])

        return context.come_back(MSG_CHANGES_SAVED)



class HTMLFile(HTMLDocument, XHTMLFile):

    class_id = 'text/html'


    def GET(self, context):
        return Text.GET(self, context)



# Register the objects
register_object_class(XMLFile)
register_object_class(XMLFile, format='application/xml')
register_object_class(XHTMLFile)
register_object_class(HTMLFile)
