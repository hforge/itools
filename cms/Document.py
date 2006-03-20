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

# Import from itools
from itools.resources import memory
from itools.gettext import PO
from itools.xml import XML
from itools.stl import stl
from itools.web import get_context
from itools.web.exceptions import Forbidden

# Import from ikaaro
from utils import get_parameters, comeback
from Handler import Handler
import html
from LocaleAware import LocaleAware
from workflow import WorkflowAware



class HTML(WorkflowAware, LocaleAware, html.XHTMLFile):

    def GET(self):
        method = self.get_firstview()
        # Check access
        if method is None:
            raise Forbidden
        # Redirect
        context = get_context()
        goto = context.uri.resolve2(';%s' % method)
        context.redirect(goto)


    def get_content(self, language=None):
        if language is None:
            master = self.get_master_handler()
            master_language = master.metadata.get_property('dc:language')
            # Build the mapping: {language: handler}
            versions = getattr(master.metadata.state.properties, 'hasVersion', {})
            versions = versions.copy()
            for key, value in versions.items():
                handler = master.parent.get_handler(value)
                versions[key] = handler
            versions[master_language] = master
            # Filter non-public handlers
            for key, handler in versions.items():
                state = handler.metadata.get_property('state')
                if state != 'public':
                    del versions[key]
            # Build the mapping: {language: property value} (don't include
            # empty properties)
            for key, handler in versions.items():
                if handler.is_empty():
                    del versions[key]
                else:
                    body = handler.get_body()
                    versions[key] = body.get_content()
            # Language negotiation
            accept = get_context().request.accept_language
            language = accept.select_language(versions.keys())
            if language is None:
                language = master_language
            # Done
            if language in versions:
                return versions[language]
            else:
                body = handler.get_body()
                if body is None:
                    return u''
                return body.get_content()
        elif language == self.metadata.get_property('dc:language'):
            return handler.get_body().get_content()
        else:
            master = self.get_master_handler()
            versions = getattr(master.metadata.properties, 'hasVersion', {})
            if language in versions:
                handler = master.parent.get_handler(versions[language])
                return handler.get_body().get_content()
            else:
                return handler.get_body().get_content()


    #######################################################################
    # User interface
    #######################################################################
    def get_views(self):
        if self.is_master():
            return ['view', 'edit_form', 'edit_metadata_form', 'state_form',
                    'history_form']
        return ['view', 'translate_form', 'edit_form', 'edit_metadata_form',
                'state_form', 'history_form']


    #######################################################################
    # Edit form
##    def edit_form(self):
##        """WYSIWYG editor for HTML documents."""
##        namespace = {}
##        master = self.get_master_handler()
##        if self.is_empty():
##            body = master.get_body()
##        else:
##            body = self.get_body()
##        if body is None:
##            # XXX For example, a frameset
##            return html.XHTMLFile.edit_form(self)
##        else:
##            data = body.get_content()

##        toolbox = self.get_handler('/ui/HTML_toolbox.js')
##        epoz = Epoz(self, 'data', data, lang='en', path='/misc_/Epoz/',
##                    widget=self.get_pathto(toolbox),
##                    style='width: 100%; height: 350px', charset='utf-8',
##                    pageurl=str(get_context().uri))
##        namespace['rte'] = epoz

##        handler = self.get_handler('/ui/HTML_edit.xml')
##        return stl(handler, namespace)


    #######################################################################
    # Translate form
    def get_catalog(self):
        return self.acquire('en.po')
        

    translate_form__access__ = Handler.is_allowed_to_edit
    translate_form__label__ = u'Translate'
    def translate_form(self):
        context = get_context()
        request = context.request

        namespace = {}
        # Translate from the master
        master = self.get_master_handler()
        catalog = self.get_catalog()
        data = master.translate(catalog)
        namespace['text'] = data

        # Translation form
        msgids = master.get_messages()
        msgids = list(msgids)

        # Set total
        total = len(msgids)
        namespace['messages_total'] = str(total)

        # Set the index
        parameters = get_parameters('messages', index='1')
        index = parameters['index']
        namespace['messages_index'] = index
        index = int(index)

        # Set first, last, previous and next
        request = get_context().request
        namespace['messages_first'] = request.build_url(messages_index=1)
        namespace['messages_last'] = request.build_url(messages_index=total)
        previous = max(index - 1, 1)
        namespace['messages_previous'] = request.build_url(messages_index=previous)
        next = min(index + 1, total)
        namespace['messages_next'] = request.build_url(messages_index=next)

        # Set msgid and msgstr
        if msgids:
            # Acquire catalog
            catalog = self.get_catalog()

            msgid = msgids[index-1]
            namespace['msgid'] = cgi.escape(PO.unescape(msgid))
            msgstr = catalog.get_msgstr(msgid) or ''
            msgstr = cgi.escape(PO.unescape(msgstr))
            namespace['msgstr'] = msgstr
        else:
            namespace['msgid'] = None

        handler = self.get_handler('/ui/Document_translate.xml')
        return stl(handler, namespace)


    save_translation__access__ = Handler.is_allowed_to_edit
    def save_translation(self):
        # Translate from the master
        master = self.get_master_handler()
        catalog = self.get_catalog()
        data = master.translate(catalog)

        resource = memory.File(data)
        self.load_state(resource)

        message = self.gettext(u'Translation saved.')
        comeback(message)


    translate_message__access__ = Handler.is_allowed_to_edit
    def translate_message(self, msgid, msgstr, messages_index=None, **kw):
        msgid = PO.escape(msgid.replace('\r', ''))
        msgstr = PO.escape(msgstr.replace('\r', ''))

        catalog = self.get_catalog()
        catalog.set_message(msgid, msgstr)

        message = self.gettext(u'Message edited.')
        comeback(message, messages_index=messages_index)


html.XHTMLFile.register_handler_class(HTML)
