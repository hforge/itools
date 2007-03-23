# -*- coding: UTF-8 -*-
# Copyright (C) 2002-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import other libraries
try:
    import tidy
except ImportError:
    print 'uTidylib is not installed, download from http://utidylib.berlios.de/'

# Import from itools
from itools.xml import Document as XMLDocument, Element as XMLElement
from itools.stl import stl
from itools.xhtml import XHTML
from itools.html import Document as HTMLDocument

# Import from ikaaro
from text import Text
from registry import register_object_class


class XMLFile(Text, XMLDocument):

    class_id = 'text/xml'



class XHTMLFile(Text, XHTML.Document):

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
    def to_xhtml_body(self):
        body = self.get_body()
        if body is None:
            return None
        return body.get_content()


    def to_html(self):
        doc = tidy.parseString(self.to_str(), indent=1, char_encoding='utf8',
                               output_html=1)
        return unicode(str(doc), 'utf-8')


    def to_text(self):
        return XHTML.Document.to_text(self)


    def is_empty(self):
        """Test if XML doc is empty"""
        body = self.get_body()
        if body is None:
            return True
        is_empty = False
        for node in body.traverse():
            if isinstance(node, unicode):
                if node.replace('&nbsp;', '').strip():
                    break
            elif isinstance(node, XMLElement):
                if node.name == 'img':
                    break
        else:
            is_empty = True
        return is_empty


    #######################################################################
    # User interface
    #######################################################################

    #######################################################################
    # View
    view__access__ = 'is_allowed_to_view'
    view__label__ = u'View'
    def view(self, context):
        namespace = {}
        namespace['text'] = self.to_xhtml_body()

        handler = self.get_handler('/ui/HTML_view.xml')
        return stl(handler, namespace)


    #######################################################################
    # Edit / Inline
    def get_epoz_data(self):
        return self.get_body().get_content_as_html()


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
        data = body.get_content_as_html()
        namespace['rte'] = self.get_rte('data', data)

        handler = self.get_handler('/ui/HTML_edit.xml')
        return stl(handler, namespace)


    edit__access__ = 'is_allowed_to_edit'
    def edit(self, context):
        # XXX This code is ugly. We must: (1) write our own XML parser, with
        # support for fragments, and (2) use the commented code.
##        body = self.get_body()
##        body.set_content(data)

        new_body = context.get_form_value('data')
        # Epoz returns HTML, coerce to XHTML (by tidy)
        new_body = tidy.parseString(new_body, indent=1, char_encoding='utf8',
                                    output_xhtml=1)
        new_body = str(new_body)
        if not new_body:
            return context.come_back(
                u'ERROR: the document could not be changed, the input'
                u' data was not proper HTML code.')

        # Parse the new data
        doc = XHTML.Document()
        doc.load_state_from_string(new_body)
        children = doc.get_body().children
        # Save the changes
        body = self.get_body()
        self.set_changed()
        body.children = children

        return context.come_back(u'Document changed.')



class HTMLFile(HTMLDocument, XHTMLFile):

    class_id = 'text/html'


    def GET(self, context):
        return Text.GET(self, context)


    def to_html(self):
        return self.to_str()


    edit__access__ = 'is_allowed_to_edit'
    def edit(self, context):
        # XXX This is copy and paste from XHTMLFile.edit (except for the
        # tidy part)
        new_body = context.get_form_value('data')
        # Parse the new data
        doc = HTMLDocument()
        doc.load_state_from_string(new_body)
        children = doc.get_root_element().children
        # Save the changes
        body = self.get_body()
        self.set_changed()
        body.children = children

        return context.come_back(u'Version edited.')


# Register the objects
register_object_class(XMLFile)
register_object_class(XMLFile, format='application/xml')
register_object_class(XHTMLFile)
register_object_class(HTMLFile)
