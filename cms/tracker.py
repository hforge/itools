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
from itools.datatypes import DateTime, String, Unicode
from itools.i18n.locale_ import format_datetime
from itools.csv.csv import IntegerKey, CSV as BaseCSV
from itools.stl import stl
from itools import vfs
from itools.web import get_context
from csv import CSV
from File import File
from Folder import Folder
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
        ['view'],
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
    # User Interface / View
    view__access__ = 'is_allowed_to_view'
    view__label__ = u'View'
    def view(self, context):
        namespace = {}
        # Columns
        columns = [('id', u'Id'), ('title', u'Title'), ('topic', u'Topic'),
            ('version', u'Version'), ('priority', u'Priority'),
            ('state', u'State')]
        # Lines
        lines = []
        tables = {'topic': self.get_handler('topics.csv'),
                  'version': self.get_handler('versions.csv'),
                  'priority': self.get_handler('priorities.csv'),
                  'state': self.get_handler('states.csv')}
        for handler in self.search_handlers(handler_class=Issue):
            link = '%s/;edit_form' % handler.name
            line = {'id': (handler.name, link),
                    'title': (handler.get_property('dc:title'), link)}
            for name in 'topic', 'version', 'priority', 'state':
                value = handler.get_property('ikaaro:issue_%s' % name)
                row = tables[name].get_row_by_id(value)
                line[name] = row and row.get_value('title') or None
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
        ids = []
        for name in self.get_handler_names():
            if name.endswith('.metadata'):
                continue
            try:
                id = int(name)
            except ValueError:
                continue
            ids.append(id)
        if ids:
            ids.sort()
            id = str(ids[-1] + 1)
        else:
            id = '0'

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
        root.send_email(from_addr, to_addr, subject, body)

        return context.come_back('New issue addded.')


register_object_class(Tracker)



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

    

