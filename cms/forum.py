# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from operator import itemgetter

# Import from itools
from itools.datatypes import FileName
from itools.i18n import format_datetime
from itools.stl import stl
from itools.xml import Parser
from itools.xhtml import sanitize_stream, xhtml_uri
from itools.html import Parser as HTMLParser
from itools.rest import checkid

# Import from itools.cms
from folder import Folder
from messages import MSG_EDIT_CONFLICT, MSG_CHANGES_SAVED
from registry import register_object_class
from html import XHTMLFile
from text import Text



class Message(XHTMLFile):

    class_id = 'ForumMessage'
    class_title = u"Message"
    class_description = u"Message in a thread"
    class_views = [['edit_form'], ['history_form']]


    def new(self, data):
        XHTMLFile.new(self)
        new_body = HTMLParser(data)
        new_body = sanitize_stream(new_body)
        old_body = self.get_body()
        self.events = (self.events[:old_body.start+1]
                       + new_body
                       + self.events[old_body.end:])


    def _load_state_from_file(self, file):
        data = file.read()
        stream = Parser(data, {None: xhtml_uri})
        self.events = list(stream)


    # Was already indexed at the thread level
    def to_text(self):
        return u''


    edit__access__ = 'is_admin'
    def edit(self, context):
        XHTMLFile.edit(self, context, sanitize=True)

        return context.come_back(MSG_CHANGES_SAVED, goto='../;view')




class Thread(Folder):

    class_id = 'ForumThread'
    class_title = u"Thread"
    class_description = u"A thread to discuss"
    class_views = [['view'], ['edit_metadata_form']]

    message_class = Message


    def new(self, data=u''):
        Folder.new(self)
        cache = self.cache
        message = self.message_class(data=data)
        cache['0.xhtml'] = message
        cache['0.xhtml.metadata'] = message.build_metadata()


    def to_text(self):
        # Index the thread by the content of all its posts
        text = [ x.to_text()
                 for x in self.search_handlers(handler_class=Message) ]

        return u'\n'.join(text)


    def get_document_types(self):
        return [self.message_class]


    def get_posts(self):
        posts = [ (int(FileName.decode(x.name)[0]), x)
                  for x in self.search_handlers(handler_class=Message) ]
        posts.sort()
        return [ x[1] for x in posts ]


    def get_last_post_id(self):
        posts = self.search_handlers(handler_class=Message)
        ids = [ int(FileName.decode(x.name)[0]) for x in posts ]
        return max(ids)


    view__access__ = 'is_allowed_to_view'
    view__label__ = u"View"
    def view(self, context):
        context.styles.append('/ui/forum/forum.css')

        user = context.user
        users = self.get_object('/users')
        ac = self.get_access_control()
        accept_language = context.get_accept_language()
        # The namespace
        namespace = {}
        namespace['title'] = self.get_title()
        namespace['description'] = self.get_property('dc:description')
        namespace['messages'] = []
        for message in self.get_posts():
            author_id = message.get_property('owner')
            namespace['messages'].append({
                'name': message.name,
                'author': users.get_object(author_id).get_title(),
                'mtime': format_datetime(message.get_mtime(), accept_language),
                'body': message.events,
                'editable': ac.is_admin(user, message),
            })
        namespace['rte'] = self.get_rte(context, 'data', None)

        handler = self.get_object('/ui/forum/Thread_view.xml')
        return stl(handler, namespace)


    new_reply__access__ = 'is_allowed_to_edit'
    def new_reply(self, context):
        # Find out the name for the new post
        id = self.get_last_post_id()
        name = '%s.xhtml' % (id + 1)

        # Post
        data = context.get_form_value('data')
        reply = self.message_class(data=data)
        self.set_object(name, reply)

        return context.come_back(u"Reply Posted.", goto='#new_reply')


    # Used by "get_rte" above
    def get_epoz_data(self):
        # Default document for new message form
        return None



class Forum(Folder):

    class_id = 'Forum'
    class_title = u'Forum'
    class_description = u'An iKaaro forum'
    class_icon48 = 'images/Forum48.png'
    class_icon16 = 'images/Forum16.png'
    class_views = [['view'], ['new_thread_form'], ['edit_metadata_form']]

    thread_class = Thread


    def get_document_types(self):
        return [self.thread_class]


    view__access__ = 'is_allowed_to_view'
    view__label__ = u"View"
    def view(self, context):
        context.styles.append('/ui/forum/forum.css')
        # Namespace
        namespace = {}
        namespace['title'] = self.get_title()
        namespace['description'] = self.get_property('dc:description')
        # Namespace / Threads
        accept_language = context.get_accept_language()
        users = self.get_object('/users')
        namespace['threads'] = []
        for thread in self.search_handlers(handler_class=Thread):
            message = thread.get_object('0.xhtml')
            author = users.get_object(thread.get_property('owner'))
            posts = thread.search_handlers(handler_class=Message)
            posts = list(posts)
            namespace['threads'].append({
                'name': thread.name,
                'title': thread.get_title(),
                'author': author.get_title(),
                'date': format_datetime(message.get_mtime(), accept_language),
                'comments': len(posts) - 1,
##                'description': thread.get_property('dc:description'),
            })
        namespace['threads'].sort(key=itemgetter('date'), reverse=True)

        handler = self.get_object('/ui/forum/Forum_view.xml')
        return stl(handler, namespace)


    new_thread_form__access__ = 'is_allowed_to_edit'
    new_thread_form__label__ = u"New Thread"
    def new_thread_form(self, context):
        context.styles.append('/ui/forum/forum.css')

        namespace = {}
        namespace['rte'] =  self.get_rte(context, 'data', None)

        handler = self.get_object('/ui/forum/Forum_new_thread.xml')
        return stl(handler, namespace)


    new_thread__access__ = 'is_allowed_to_edit'
    def new_thread(self, context):
        title = context.get_form_value('dc:title').strip()
        if not title:
            return context.come_back(u"No title given.")

        name = checkid(title)
        if name is None:
            return context.come_back(u"Invalid title.")

        if self.has_handler(name):
            return context.come_back(u"This thread already exists.")

        default_language = context.site_root.get_default_language()

        data = context.get_form_value('data')
        thread = self.thread_class(data=data)
        thread, metadata = self.set_object(name, thread)
        thread.set_property('dc:title', title, language=default_language)

        return context.come_back(u"Thread Created.", goto=name)


    # Used by "get_rte" above
    def get_epoz_data(self):
        # Default document for new thread form
        return None


register_object_class(Forum)
register_object_class(Thread)
register_object_class(Message)
