# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from datetime import datetime
from string import Template

# Import from itools
from itools.datatypes import DateTime, Integer, String, Unicode
from itools.i18n.locale_ import format_datetime
from itools.handlers.config import Config
from itools.csv.csv import IntegerKey, CSV as BaseCSV
from itools.stl import stl
from itools import vfs
from itools.web import get_context
from csv import CSV
from File import File
from Folder import Folder
from text import Text
from registry import register_object_class
import widgets



class SelectTable(CSV):

    class_id = 'topics'

    columns = ['id', 'title']
    schema = {'id': IntegerKey, 'title': Unicode}


    def get_namespace(self, value=None):
        namespace = []
        for id, title in self.get_rows():
            namespace.append(
                {'id': id, 'title': title, 'is_selected': id == value})
        namespace.sort(key=lambda x: x['title'])
        return namespace


    def get_row_by_id(self, id):
        for x in self.search(id=id):
            return self.get_row(id)
        return None



register_object_class(SelectTable)



class Tracker(Folder):
    
    class_id = 'tracker'
    class_title = u'Issue Tracker'
    class_description = u'To manage bugs and tasks'
    class_icon16 = 'images/tracker16.png'
    class_icon48 = 'images/tracker48.png'
    class_views = [
        ['search_form'],
        ['add_form'],
        ['browse_content?mode=list'],
        ['edit_metadata_form']]

    __fixed_handlers__ = ['topics.csv', 'priorities.csv', 'versions.csv',
        'states.csv']


    def new(self, **kw):
        Folder.new(self, **kw)
        cache = self.cache
        # Tables
        tables = [
            ('topics.csv', [u'User Interface', u'Programming Interface']),
            ('priorities.csv', [u'High', u'Medium', u'Low']),
            ('versions.csv', [u'Stable', u'Development']),
            ('states.csv', [u'Open', u'Closed'])]
            
        for name, values in tables:
            csv = SelectTable()
            cache[name] = csv
            for row in enumerate(values):
                csv.add_row(row)
            cache['%s.metadata' % name] = self.build_metadata(csv)


    def get_document_types(self):
        return []

    #######################################################################
    # API
    #######################################################################
    def get_new_id(self, prefix=''):
        ids = []
        for name in self.get_handler_names():
            if name.endswith('.metadata'):
                continue
            if prefix:
                if not name.startswith(prefix):
                    continue
                name = name[len(prefix):]
            try:
                id = int(name)
            except ValueError:
                continue
            ids.append(id)

        if ids:
            ids.sort()
            return prefix + str(ids[-1] + 1)
        
        return prefix + '0'


    #######################################################################
    # User Interface
    #######################################################################
    def get_subviews(self, name):
        if name == 'search_form':
            return [
                'view?search_name=%s' % x.name
                for x in self.search_handlers(handler_class=StoredSearch) ]
        return Folder.get_subviews(self, name)


    def view__sublabel__(self , **kw):
        search_name = kw.get('search_name')
        if search_name is None:
            return u'View'

        search = self.get_handler(search_name)
        return search.get_title()


    #######################################################################
    # User Interface / View
    search_form__access__ = 'is_allowed_to_view'
    search_form__label__ = u'Search'
    def search_form(self, context):
        namespace = {}

        # Stored Searches
        namespace['stored_searches'] = [
            {'name': x.name, 'title': x.get_title()}
            for x in self.search_handlers(handler_class=StoredSearch) ]
        
        # Search Form
        search_name = context.get_form_value('search_name')
        if search_name:
            search = self.get_handler(search_name)
            namespace['search_name'] = search_name
            namespace['search_title'] = search.get_property('dc:title')
            namespace['text'] = search.get_value('text', type=Unicode)
            topic = search.get_value('topic', type=Integer)
            version = search.get_value('version', type=Integer)
            priority = search.get_value('priority', type=Integer)
            assign = search.get_value('assigned_to')
            state = search.get_value('state', type=Integer)
        else:
            namespace['search_name'] = None
            namespace['search_title'] = None
            namespace['text'] = None
            topic = None
            version = None
            priority = None
            assign = None
            state = None

        for name, value in [('topics', topic), ('versions', version),
                            ('priorities', priority), ('states', state)]:
            table = self.get_handler('%s.csv' % name)
            namespace[name] = table.get_namespace(value)

        users = self.get_handler('/users')
        namespace['users'] = [
            {'id': x, 'title': users.get_handler(x).get_title(),
             'is_selected': x == assign}
            for x in self.get_site_root().get_members() ]

        handler = self.get_handler('/ui/tracker/search.xml')
        return stl(handler, namespace)


    search__access__ = 'is_allowed_to_edit'
    def search(self, context):
        search_name = context.get_form_value('search_name')
        search_title = context.get_form_value('search_title').strip()
        if search_name:
            # Edit an Stored Search
            try:
                stored_search = self.get_handler(search_name)
            except LookupError:
                pass
        elif search_title:
            # New Stored Search
            search_name = self.get_new_id('s')
            stored_search = self.set_handler(search_name, StoredSearch())
        else:
            # Just Search
            return context.uri.resolve(';view').replace(**context.uri.query)

        # Edit / Title
        context.commit = True
        stored_search.set_property('dc:title', search_title, 'en')
        # Edit / Search Values
        text = context.get_form_value('text').strip().lower()
        topic = context.get_form_value('ikaaro:issue_topic')
        version = context.get_form_value('ikaaro:issue_version')
        priority = context.get_form_value('ikaaro:issue_priority')
        assign = context.get_form_value('ikaaro:issue_assigned_to')
        state = context.get_form_value('ikaaro:issue_state')

        criterias = [('text', text), ('topic', topic), ('version', version),
            ('priority', priority), ('assigned_to', assign), ('state', state)]
        for name, value in criterias:
            stored_search.set_value(name, value)
 
        return context.uri.resolve(';view?search_name=%s' % search_name)


    view__access__ = 'is_allowed_to_view'
    view__label__ = u'View'
    def view(self, context):
        # Stored Search
        search_name = context.get_form_value('search_name')
        if search_name:
            search = self.get_handler(search_name)
            text = search.get_value('text', type=Unicode)
            topic = search.get_value('topic', type=Integer)
            version = search.get_value('version', type=Integer)
            priority = search.get_value('priority', type=Integer)
            assign = search.get_value('assigned_to')
            state = search.get_value('state', type=Integer)
        else:
            text = context.get_form_value('text').strip().lower()
            topic = context.get_form_value('ikaaro:issue_topic')
            version = context.get_form_value('ikaaro:issue_version')
            priority = context.get_form_value('ikaaro:issue_priority')
            assign = context.get_form_value('ikaaro:issue_assigned_to')
            state = context.get_form_value('ikaaro:issue_state')
        # Build the namespace
        users = self.get_handler('/users')
        namespace = {}
        # Columns
        columns = [('id', u'Id'), ('title', u'Title'), ('topic', u'Topic'),
            ('version', u'Version'), ('priority', u'Priority'),
            ('assigned_to', u'Assigned To'), ('state', u'State')]
        # Lines
        lines = []
        tables = {'topic': self.get_handler('topics.csv'),
                  'version': self.get_handler('versions.csv'),
                  'priority': self.get_handler('priorities.csv'),
                  'state': self.get_handler('states.csv')}
        for handler in self.search_handlers(handler_class=Issue):
            if text:
                if not handler.has_text(text):
                    continue
            if topic is not None:
                if topic != handler.get_property('ikaaro:issue_topic'):
                    continue
            if version is not None:
                if version != handler.get_property('ikaaro:issue_version'):
                    continue
            if priority is not None:
                if priority != handler.get_property('ikaaro:issue_priority'):
                    continue
            if assign:
                if assign != handler.get_property('ikaaro:issue_assigned_to'):
                    continue
            if state is not None:
                if state != handler.get_property('ikaaro:issue_state'):
                    continue
            # Append
            link = '%s/;edit_form' % handler.name
            line = {'id': (handler.name, link),
                    'title': (handler.get_property('dc:title'), link)}
            for name in 'topic', 'version', 'priority', 'state':
                value = handler.get_property('ikaaro:issue_%s' % name)
                row = tables[name].get_row_by_id(value)
                line[name] = row and row.get_value('title') or None
            assigned_to = handler.get_property('ikaaro:issue_assigned_to')
            if assigned_to is None:
                line['assigned_to'] = ''
            else:
                user = users.get_handler(assigned_to)
                line['assigned_to'] = user.get_title()
            lines.append(line)
        # Sort
        sortby = context.get_form_value('sortby', default='id')
        sortorder = context.get_form_value('sortorder', default='up')
        lines.sort(key=lambda x: x[sortby])
        if sortorder == 'down':
            lines.reverse()
        # Table
        namespace['table'] = widgets.table(columns, lines, [sortby], sortorder)

        handler = self.get_handler('/ui/tracker/view_tracker.xml')
        return stl(handler, namespace)


    #######################################################################
    # User Interface / Add Issue
    add_form__access__ = 'is_allowed_to_edit'
    add_form__label__ = u'Add'
    def add_form(self, context):
        namespace = {}
        for name in 'topics', 'versions', 'priorities':
            namespace[name] = self.get_handler('%s.csv' % name).get_namespace()

        users = self.get_handler('/users')
        namespace['users'] = [
            {'id': x, 'title': users.get_handler(x).get_title()}
            for x in self.get_site_root().get_members() ]

        handler = self.get_handler('/ui/tracker/add_issue.xml')
        return stl(handler, namespace)


    add_issue__access__ = 'is_allowed_to_edit'
    def add_issue(self, context):
        # The id
        id = self.get_new_id()
        # Add
        issue = self.set_handler(id, Issue())
        user = context.user
        if user is not None:
            issue.set_property('ikaaro:issue_reported_by', user.name)

        # Metadata properties
        fields = ['dc:title', 'ikaaro:issue_topic', 'ikaaro:issue_version',
            'ikaaro:issue_priority', 'ikaaro:issue_assigned_to']
        for name in fields:
            value = context.get_form_value(name)
            issue.set_property(name, value)
        # Comment
        comment = context.get_form_value('comment', type=Unicode)
        issue.add_comment(comment)

        # Notify / From
        if user is None:
            from_addr = ''
        else:
            from_addr = user.get_property('ikaaro:email')
        # Notify / To
        assigned_to = context.get_form_value('ikaaro:issue_assigned_to')
        assigned_to = self.get_handler('/users/%s' % assigned_to)
        to_addr = assigned_to.get_property('ikaaro:email')
        # Notify / Subject
        title = context.get_form_value('dc:title')
        subject = '[Tracker Issue #%s] %s' % (issue.name, title)
        # Notify / Body
        body = Template(u'${description}\n'
                        u'\n'
                        u'    ${uri}\n')

        uri = context.uri.resolve2('../%s/;edit_form' % issue.name)
        body = body.substitute({'description': comment, 'uri': uri})
        # Notify / Send
        root = context.root
        ##root.send_email(from_addr, to_addr, subject, body)

        goto = context.uri.resolve2('../%s/;edit_form' % issue.name)
        return context.come_back(u'New issue addded.', goto=goto)


register_object_class(Tracker)


###########################################################################
# Stored Searches
###########################################################################
class StoredSearch(Text, Config):

    class_id = 'stored_search'
    class_title = u'Stored Search'
 

register_object_class(StoredSearch)



###########################################################################
# Issues
###########################################################################
class Issue(Folder):
    
    class_id = 'issue'
    class_title = u'Issue'
    class_description = u'Issue'
    class_views = [
        ['edit_form'],
        ['browse_content?mode=list'],
        ['new_resource_form?type=file']]


    def new(self, **kw):
        Folder.new(self, **kw)
        cache = self.cache
        cache['.comments'] = Comments()


    def _get_handler(self, segment, uri):
        name = segment.name
        if name == '.comments':
            return Comments(uri)
        return Folder._get_handler(self, segment, uri)


    def get_document_types(self):
        return [File]


    #######################################################################
    # API
    #######################################################################
    def add_comment(self, comment):
        context = get_context()
        user = context.user
        date = datetime.now()

        user = (user is not None and user.name) or ''

        comments = self.get_handler('.comments')
        comments.add_row([date, user, comment])


    def has_text(self, text):
        if text in self.get_property('dc:title').lower():
            return True
        comments = self.get_handler('.comments')
        for comment in comments.get_rows():
            comment = comment.get_value('comment').lower()
            if text in comment:
                return True
        return False


    #######################################################################
    # User Interface
    #######################################################################
    edit_form__access__ = 'is_allowed_to_edit'
    edit_form__label__ = u'Edit'
    def edit_form(self, context):
        # Set Style
        css = self.get_handler('/ui/tracker/tracker.css')
        context.styles.append(str(self.get_pathto(css)))

        # Local variables
        users = self.get_handler('/users')

        # Build the namespace
        namespace = {}
        namespace['number'] = self.name
        namespace['title'] = self.get_property('dc:title')
        # Reported by
        reported_by = self.get_property('ikaaro:issue_reported_by')
        if reported_by is None:
            reported_by = None
        else:
            reported_by = users.get_handler(reported_by).get_title()
        namespace['reported_by'] = reported_by
        # Topic, Priority, etc.
        parent = self.parent
        tables = [('topic', 'topics'), ('version', 'versions'),
            ('priority', 'priorities'), ('state', 'states')]
        for name, table_name in tables:
            table = parent.get_handler('%s.csv' % table_name)
            value = self.get_property('ikaaro:issue_%s' % name)
            namespace[table_name] = table.get_namespace(value)
        # Assign To
        selected = self.get_property('ikaaro:issue_assigned_to')
        namespace['users'] = [
            {'id': x, 'title': users.get_handler(x).get_title(),
             'is_selected': x == selected}
            for x in self.get_site_root().get_members() ]
        # Attachements
        namespace['files'] = [
            {'name': x.name, 'type': x.get_property('format'),
             'datetime': format_datetime(vfs.get_mtime(x.uri))}
            for x in self.search_handlers() ]
        # Comments
        users = self.get_handler('/users')
        comments = []
        for comment in self.get_handler('.comments').get_rows():
            username = comment.get_value('username')
            datetime = comment.get_value('datetime')
            user = users.get_handler(username)
            comments.append({
                'user': user.get_title(),
                'datetime': format_datetime(datetime),
                'comment': comment.get_value('comment')})
        comments.reverse()
 
        namespace['comments'] = comments

        handler = self.get_handler('/ui/tracker/edit_issue.xml')
        return stl(handler, namespace)


    edit__access__ = 'is_allowed_to_edit'
    def edit(self, context):
        for name in ('dc:title', 'ikaaro:issue_topic', 'ikaaro:issue_version',
            'ikaaro:issue_priority', 'ikaaro:issue_state',
            'ikaaro:issue_assigned_to'):
            value = context.get_form_value(name)
            self.set_property(name, value)
        # Add Comment
        comment = context.get_form_value('comment')
        self.add_comment(comment)

        return context.come_back('Changes saved.')


register_object_class(Issue)



class Comments(BaseCSV):

    columns = ['datetime', 'username', 'comment']
    schema = {'datetime': DateTime,
              'username': String,
              'comment': Unicode}

    

