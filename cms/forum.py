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
from itools.datatypes import FileName
from itools.stl import stl
from itools.web import get_context
from itools.cms.registry import register_object_class
from itools.cms.Folder import Folder
from itools.cms.text import Text
from itools.cms.utils import checkid


def add_forum_style():
    context = get_context()
    style = context.root.get_handler('ui/forum.css')
    context.styles.append(context.handler.get_pathto(style))



class Message(Text):

    class_id = 'ForumMessage'
    class_title = u"Message"
    class_description = u"Message in a thread"
    class_views = [['edit_form'], ['history_form']]
    

    def is_allowed_to_edit(self, user, object):
        if user is None:
            return False

        if self.is_admin(user):
            return True

        owner = object.get_property('owner')
        return owner == user.name


    # remove from searches
    def get_catalog_indexes(self):
        return None


    def edit(self, context):
        data = context.get_form_value('data')
        data = unicode(data, 'UTF-8')
        data = escape(data)
        self.set_data(data)

        return context.come_back(u'Document edited.', goto='../;view')



class Thread(Folder):

    class_id = 'ForumThread'
    class_title = u"Thread"
    class_description = u"A thread to discuss"
    class_views = [['view'], ['edit_metadata_form']]

    message_class = Message


    def is_allowed_to_post(self, user, object):
        return self.is_allowed_to_view(user, object)


    def to_text(self):
        text = StringIO()

        # index messages in order (XXX necessary?)
        for id in ([0] + self.get_replies()):
            name = '%s.txt' % id
            message = self.get_handler(name)
            text.write(message.to_text())

        return text.getvalue()


    def get_document_types(self):
        return [self.message_class]


    def get_replies(self):
        posts = [int(FileName.decode(x)[0]) for x in self.get_handler_names()
                if not x.startswith(u'.')]
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


    def get_message_namespace(self):
        context = get_context()
        user = context.user
        username = user and user.name
        namespace = []

        for i, id in enumerate([0] + self.get_replies()):
            name = '%s.txt' % id
            message = self.get_handler(name)
            namespace.append({
                'author': message.get_property('owner'),
                'mtime': message.get_mtime().strftime('%F %X'),
                'body': message.to_str().replace('\n', '<br />'),
                'editable': self.is_admin() or (
                    message.get_property('owner') == username),
                'edit_form': '%s/;edit_form' % message.name,
                'class': ((i % 2) and 'forum_odd' or 'forum_even'),
            })

        return namespace


    view__access__ = 'is_allowed_to_view'
    view__label__ = u"View"
    def view(self, context):
        namespace = {}

        namespace['title'] = self.get_title_or_name()
        namespace['description'] = self.get_description()
        namespace['messages'] = self.get_message_namespace()

        add_forum_style()

        handler = self.get_handler('/ui/Thread_view.xml')
        return stl(handler, namespace)


    new_reply__access__ = 'is_allowed_to_edit'
    def new_reply(self, context):
        body = context.get_form_value('body')

        replies = self.get_replies()
        if replies:
            last_reply = max(replies)
        else:
            last_reply = 0

        next_reply = str(last_reply + 1)
        name = FileName.encode((next_reply, 'txt', None))

        body = escape(body)
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
    class_views = [['view'], ['new_thread_form'], ['edit_metadata_form'],
                   ['help']]

    thread_class = Thread


    def get_document_types(self):
        return [self.thread_class]


    def is_allowed_to_post(self, user, object):
        return self.is_allowed_to_view(user, object)


    def get_thread_namespace(self):
        namespace = []

        for thread in self.search_handlers(handler_class=self.thread_class):
            first = thread.get_handler('0.txt')
            last = thread.get_last_post()
            namespace.append({
                'name': thread.name,
                'title': thread.get_title_or_name(),
                'description': thread.get_description(),
                'author': first.get_property('owner'),
                'replies': len(thread.get_replies()),
                'last_date': last.get_mtime().strftime('%F %X'),
                'last_author': last.get_property('owner'),
            })

        namespace.sort(key=itemgetter('last_date'), reverse=True)

        for i, thread in enumerate(namespace):
            thread['class'] = ((i % 2) and 'forum_odd' or 'forum_even')

        return namespace


    view__access__ = 'is_allowed_to_view'
    view__label__ = u"View"
    def view(self, context):
        namespace = {}

        namespace['title'] = self.get_title_or_name()
        namespace['description'] = self.get_description()
        namespace['threads'] = self.get_thread_namespace()

        add_forum_style()

        handler = self.get_handler('/ui/Forum_view.xml')
        return stl(handler, namespace)


    new_thread_form__access__ = 'is_allowed_to_edit'
    new_thread_form__label__ = u"New Thread"
    def new_thread_form(self, context):
        add_forum_style()

        handler = self.get_handler('/ui/Forum_new_thread.xml')
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
            raise context.come_back(u"This thread already exists.")

        context = get_context()
        root = context.root
        website_languages = root.get_property('ikaaro:website_languages')
        default_language = website_languages[0]

        thread = self.thread_class()
        self.set_handler(name, thread,
                **{'dc:title': {default_language: title}})
        thread = self.get_handler(name)

        body = context.get_form_value('body')
        body = escape(body.strip())
        reply = thread.message_class()
        reply.load_state_from_tring(body)
        thread.set_handler('0.txt', reply)

        return context.come_back(u"Thread Created.", goto=name)


    help__label__ = u'Help'
    help__access__ = True
    def help(self, context):
        help = self.gettext(u"Read the doc in README file.")
        return help.encode('utf-8')



register_object_class(Forum)
register_object_class(Thread)
register_object_class(Message)
