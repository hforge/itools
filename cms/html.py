# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2002-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
import os
import re

# Import from itools
from itools.resources import memory
from itools.xml import XML
from itools.stl import stl
from itools.xhtml import XHTML
from itools.html import HTML
from itools.web import get_context
from itools.web.exceptions import UserError

# Import from ikaaro
from Handler import Handler
from File import File
from images import Image
from text import Text
from utils import comeback
from widgets import Breadcrumb


class XMLFile(Text, XML.Document):

    class_id = 'text/xml'


Text.register_handler_class(XMLFile)
Text.register_handler_class(XMLFile, format='application/xml')



class XHTMLFile(Text, XHTML.Document):

    class_id = 'application/xhtml+xml'
    class_version = '20040625'
    class_title = u'Web Page'
    class_description = u'Publish your own web pages.'
    class_icon16 = 'images/HTML16.png'
    class_icon48 = 'images/HTML48.png'


    #######################################################################
    # API
    #######################################################################
    def to_xhtml_body(self):
        body = self.get_body()
        if body is None:
            return None
        return body.get_content()


    def to_html(self):
        stdin, stdout, stderr = os.popen3('tidy -i -utf8 -ashtml')
        stdin.write(self.to_str())
        stdin.close()
        return unicode(stdout.read(), 'utf-8')


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
            elif isinstance(node, XML.Element):
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
    view__access__ = Handler.is_allowed_to_view
    view__label__ = u'View'
    def view(self):
        return self.to_xhtml_body()


    #######################################################################
    # Edit / Inline
    def get_epoz_data(self):
        return self.get_body().get_content_as_html()


    edit_form__access__ = Handler.is_allowed_to_edit
    edit_form__label__ = u'Edit'
    edit_form__sublabel__ = u'Inline'
    def edit_form(self):
        """WYSIWYG editor for HTML documents."""
        # If the document has not a body (e.g. a frameset), edit as plain text
        body = self.get_body()
        if body is None:
            return Text.edit_form(self)

        # Edit with a rich text editor
        namespace = {}
        # Epoz expects HTML
        data = body.get_content_as_html()
        namespace['rte'] = self.get_rte('data', data)

        handler = self.get_handler('/ui/HTML_edit.xml')
        return stl(handler, namespace)


    edit__access__ = Handler.is_allowed_to_edit
    def edit(self, **kw):
        # XXX This code is ugly. We must: (1) write our own XML parser, with
        # support for fragments, and (2) use the commented code.
##        body = self.get_body()
##        body.set_content(data)

        new_body = kw['data']
        # Epoz returns HTML, coerce to XHTML (by tidy)
        stdin, stdout, stderr = os.popen3('tidy -i -utf8 -asxhtml')
        stdin.write(new_body)
        stdin.close()
        new_body = stdout.read()
        if not new_body:
            raise UserError, \
                  u'ERROR: the document could not be changed, the input' \
                  ' data was not proper HTML code.'

        # Get only the body
        expr = re.compile('<body>(.*)</body>', re.I + re.S)
        match = expr.search(new_body)
        new_body = match.group()
        # Replace by the new body
        data = self.to_str()
        data = expr.sub(new_body, data)

        resource = memory.File(data)
        self.load_state(resource)

        message = self.gettext(u'Document changed.')
        comeback(message)


    #######################################################################
    # Edit / Inline / toolbox: add images
    addimage_form__access__ = Handler.is_allowed_to_edit
    def addimage_form(self):
        namespace = {}
        namespace['bc'] = Breadcrumb(filter_type=Image, start=self.parent)

        handler = self.get_handler('/ui/HTML_addimage.xml')
        return stl(handler, namespace)


    #######################################################################
    # Edit / Inline / toolbox: add links
    addlink_form__access__ = Handler.is_allowed_to_edit
    def addlink_form(self):
        namespace = {}
        namespace['bc'] = Breadcrumb(filter_type=File, start=self.parent)

        handler = self.get_handler('/ui/HTML_addlink.xml')
        return stl(handler, namespace)


Text.register_handler_class(XHTMLFile)



class HTMLFile(HTML.Document, XHTMLFile):

    class_id = 'text/html'


    def to_html(self):
        return self.to_str()


    edit__access__ = Handler.is_allowed_to_edit
    def edit(self, **kw):
        # XXX This is copy and paste from XHTMLFile.edit (except for the
        # tidy part)
        new_body = kw['data']
        new_body = '<body>%s</body>' % new_body
        # Replace by the new body
        expr = re.compile('<body>(.*)</body>', re.I + re.S)
        data = self.to_str()
        data = expr.sub(new_body, data)

        resource = memory.File(data)
        self.load_state(resource)

        message = self.gettext(u'Version edited.')
        comeback(message)


XHTMLFile.register_handler_class(HTMLFile)
