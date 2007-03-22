# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2005 Luis Belmar-Letelier <luis@itaapy.com>
#               2006 Hervé Cauwelier <herve@itaapy.com>
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

# Import from the Standard Library
from operator import itemgetter
from cgi import escape
from cStringIO import StringIO

# Import from itools
from itools.datatypes import FileName, Unicode
from itools.stl import stl
from itools.web import get_context

# Import from itools.cms
from itools.cms.registry import register_object_class
from itools.cms.Folder import Folder
from itools.cms.text import Text
from itools.cms.utils import checkid


def add_forum_style(context):
    style = context.root.get_handler('ui/forum/forum.css')
    context.styles.append(context.handler.get_pathto(style))



class Message(Text):

    class_id = 'ForumMessage'
    class_title = u"Message"
    class_description = u"Message in a thread"
    class_views = [['edit_form'], ['history_form']]
    

    # Remove from searches
    def to_text(self):
        return u''


    # ACLs
    edit_form__access__ = 'is_admin'


    edit__access__ = 'is_admin'
    def edit(self, context):
        data = context.get_form_value('data')
        data = escape(data.strip())
        self.load_state_from_string(data)

        return context.come_back(u'Document edited.', goto='../;view')



class Thread(Folder):

    class_id = 'ForumThread'
    class_title = u"Thread"
    class_description = u"A thread to discuss"
    class_views = [['view'], ['edit_metadata_form']]

    message_class = Message


    def new(self, body=u''):
        Folder.new(self)
        cache = self.cache
        message = self.message_class(data=body)
        cache['0.txt'] = message
        cache['0.txt.metadata'] = message.build_metadata()


    def to_text(self):
        text = []

        # index messages in order (XXX necessary?)
        for id in ([0] + self.get_replies()):
            name = '%s.txt' % id
            message = self.get_handler(name)
            text.append(message.to_text())

        return u'\n'.join(text)


    def get_document_types(self):
        return [self.message_class]


    def get_replies(self):
        posts = [int(FileName.decode(x)[0]) for x in self.get_handler_names()
                if not x.startswith(u'.') and not x.endswith('.metadata')]
        posts.sort()

        # deduce original post
        return posts[1:]


    def get_last_post(self):
        replies = self.get_replies()
        if replies:
            last = replies[-1]
        else:
            last = 0

        return self.get_handler('%s.txt' % last)


    def get_message_namespace(self, context):
        user = context.user
        username = user and user.name
        namespace = []
        users = self.get_handler('/users')
        ac = self.get_access_control()

        for i, id in enumerate([0] + self.get_replies()):
            name = '%s.txt' % id
            message = self.get_handler(name)
            author_id = message.get_property('owner')
            metadata = users.get_handler('%s.metadata' % author_id)
            namespace.append({
                'author': (metadata.get_property('dc:title') or
                    metadata.get_property('ikaaro:email')),
                'mtime': message.get_mtime().strftime('%F %X'),
                'body': message.to_str().replace('\n', '<br />'),
                'editable': ac.is_admin(user, message),
                'edit_form': '%s/;edit_form' % message.name,
            })

        return namespace


    view__access__ = 'is_allowed_to_view'
    view__label__ = u"View"
    def view(self, context):
        namespace = {}

        namespace['title'] = self.get_title_or_name()
        namespace['description'] = self.get_description()
        namespace['messages'] = self.get_message_namespace(context)

        add_forum_style(context)

        handler = self.get_handler('/ui/forum/Thread_view.xml')
        return stl(handler, namespace)


    new_reply__access__ = 'is_allowed_to_edit'
    def new_reply(self, context):
        replies = self.get_replies()
        if replies:
            last_reply = max(replies)
        else:
            last_reply = 0

        next_reply = str(last_reply + 1)
        name = FileName.encode((next_reply, 'txt', None))

        body = context.get_form_value('body')
        body = escape(body.strip())
        reply = self.message_class()
        reply.load_state_from_string(body)
        self.set_handler(name, reply)

        return context.come_back(u"Reply Posted.", goto='#new_reply')



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


    def get_thread_namespace(self):
        namespace = []
        users = self.get_handler('/users')

        for thread in self.search_handlers(handler_class=self.thread_class):
            first = thread.get_handler('0.txt')
            first_author_id = first.get_property('owner')
            first_metadata = users.get_handler('%s.metadata' % first_author_id)
            last = thread.get_last_post()
            last_author_id = last.get_property('owner')
            last_metadata = users.get_handler('%s.metadata' % last_author_id)
            namespace.append({
                'name': thread.name,
                'title': thread.get_title_or_name(),
                'description': thread.get_description(),
                'author': (first_metadata.get_property('dc:title') or
                    first_metadata.get_property('ikaaro:email')),
                'replies': len(thread.get_replies()),
                'last_date': last.get_mtime().strftime('%F %X'),
                'last_author': (last_metadata.get_property('dc:title') or
                    last_metadata.get_property('ikaaro:email')),
            })

        namespace.sort(key=itemgetter('last_date'), reverse=True)

        return namespace


    view__access__ = 'is_allowed_to_view'
    view__label__ = u"View"
    def view(self, context):
        namespace = {}

        namespace['title'] = self.get_title_or_name()
        namespace['description'] = self.get_description()
        namespace['threads'] = self.get_thread_namespace()

        add_forum_style(context)

        handler = self.get_handler('/ui/forum/Forum_view.xml')
        return stl(handler, namespace)


    new_thread_form__access__ = 'is_allowed_to_edit'
    new_thread_form__label__ = u"New Thread"
    def new_thread_form(self, context):
        add_forum_style(context)

        handler = self.get_handler('/ui/forum/Forum_new_thread.xml')
        return stl(handler)


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

        root = context.root
        website_languages = root.get_property('ikaaro:website_languages')
        default_language = website_languages[0]

        body = context.get_form_value('body', type=Unicode)
        body = escape(body.strip())
        self.set_handler(name, self.thread_class(body=body),
                **{'dc:title': {default_language: title}})

        return context.come_back(u"Thread Created.", goto=name)



register_object_class(Forum)
register_object_class(Thread)
register_object_class(Message)
