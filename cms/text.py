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
import cgi
from difflib import HtmlDiff

# Import from itools
import itools
from itools import gettext
from itools import i18n
from itools.resources import memory
from itools.handlers.rest import RestructuredText as iRestructuredText
from itools.stl import stl
from itools.web import get_context
from itools.web.exceptions import UserError
from itools.xhtml.XHTML import Document

# Import from iKaaro
from utils import get_parameters, comeback
from versioning import VersioningAware
from File import File


class Text(VersioningAware, File, itools.handlers.Text.Text):

    class_id = 'text'
    class_version = '20040625'
    class_title = u'Plain Text'
    class_description = u'Keep your notes with plain text files.'
    class_icon16 = 'images/Text16.png'
    class_icon48 = 'images/Text48.png'


    @classmethod
    def new_instance_form(cls, name=''):
        context = get_context()
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
            language_name = i18n.get_language_name(code)
            languages.append({'code': code,
                              'name': cls.gettext(language_name),
                              'isdefault': code == default_language})
        namespace['languages'] = languages

        handler = root.get_handler('ui/Text_new_instance.xml')
        return stl(handler, namespace)


    #######################################################################
    # API
    #######################################################################
    def before_commit(self):
        File.before_commit(self)
        self.commit_revision()


    def to_text(self):
        return unicode(self.to_str(), 'utf-8')


    #######################################################################
    # User interface
    #######################################################################
    def get_views(self):
        return ['view', 'edit_form', 'edit_metadata_form',
                'history_form']


    def get_subviews(self, name):
        if name in ['edit_form', 'externaledit', 'upload_form']:
            return ['edit_form', 'externaledit', 'upload_form']
        return []


    #######################################################################
    # Download
    def download(self, context):
        # XXX Code duplicated from File.File.download
        metadata = self.get_metadata()
        if metadata is None:
            mimetype = self.get_mimetype()
        else:
            mimetype = self.get_property('format')

        response = context.response
        response.set_header('Content-Type', '%s; charset=UTF-8' % mimetype)
        return self.to_str()


    #######################################################################
    # View
    view__access__ = 'is_allowed_to_view'
    view__label__ = u'View'
    def view(self, context):
        return '<pre>%s</pre>' % cgi.escape(self.to_str())


    #######################################################################
    # Edit / Inline
    edit_form__access__ = 'is_allowed_to_edit'
    edit_form__label__ = u'Edit'
    edit_form__sublabel__ = u'Inline'
    def edit_form(self, context):
        namespace = {}
        namespace['data'] = self.to_str()

        handler = self.get_handler('/ui/Text_edit.xml')
        return stl(handler, namespace)


    edit__access__ = 'is_allowed_to_edit'
    def edit(self, context):
        data = context.get_form_value('data')
        resource = memory.File(data)
        self.load_state(resource)

        message = self.gettext(u'Document edited.')
        comeback(message)


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

        handler = self.get_handler('/ui/Text_externaledit.xml')
        return stl(handler, namespace)


    #######################################################################
    # History
    compare__access__ = 'is_allowed_to_view'
    def compare(self, context):
        from html import XHTMLFile

        names = context.get_form_values('names')
        if len(names) == 0 or len(names) > 2:
            message = u'You must select one or two revisions.'
            raise UserError, self.gettext(message)

        # XXX Hack to get rename working. The current user interface
        # forces the rename_form to be called as a form action, hence
        # with the POST method, but is should be a GET method. Maybe
        # it will be solved after the needed folder browse overhaul.
        if context.request.method == 'POST':
            url = ';compare?%s' % '&'.join([ 'names=%s' % x for x in names ])
            context.redirect(url)

        archives = self.get_root().get_handler('.archive')
        revisions = archives.get_handler(self.get_property('id'))

        r0 = revisions.resource.get_resource(names[0])
        r0_obj = self.__class__(r0)
        if isinstance(r0_obj, XHTMLFile):
            r0 = r0_obj.to_xhtml_body()
        else:
            r0 = r0_obj.to_str()

        if len(names) == 2:
            r1 = revisions.resource.get_resource(names[1])
            r1_obj = self.__class__(r1)
        else:
            r1_obj = self
        if isinstance(r1_obj, XHTMLFile):
            r1 = r1_obj.to_xhtml_body()
        else:
            r1 = r1_obj.to_str()

        htmldiff = HtmlDiff(wrapcolumn=48)
        return htmldiff.make_table(r0.splitlines(), r1.splitlines())


File.register_handler_class(Text)



class PO(Text, gettext.PO.PO):

    class_id = 'text/x-po'
    class_version = '20040625'
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
        request = context.request
        namespace['messages_first'] = request.build_url(messages_index=1)
        namespace['messages_last'] = request.build_url(messages_index=total)
        previous = max(index - 1, 1)
        namespace['messages_previous'] = request.build_url(messages_index=previous)
        next = min(index + 1, total)
        namespace['messages_next'] = request.build_url(messages_index=next)

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

        message = self.gettext(u'Message edited.')
        comeback(message, messages_index=messages_index)


Text.register_handler_class(PO)



class CSS(Text):

    class_mimetypes = ['text/css']
    class_extension = 'css'
    class_id = 'text/css'
    class_version = '20040625'
    class_title = 'CSS'
    class_icon48 = 'images/CSS48.png'


Text.register_handler_class(CSS)



class Python(itools.handlers.python.Python):

    class_id = 'text/x-python'
    class_icon48 = 'images/Python48.png'


Text.register_handler_class(Python)



class RestructuredText(Text, iRestructuredText):

    class_id = 'text/x-restructured-text'
    class_version = '20060522'
    class_title = u"Restructured Text"
    class_description = u"Text files with Restructured Text syntax support."
    class_extension = 'rst'


    #######################################################################
    # View
    def view(self):
        html = self.to_html()
        resource = memory.File(html)
        document = Document(resource)
        body = document.get_body()

        return body.to_str()


Text.register_handler_class(RestructuredText)
