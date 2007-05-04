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
import mimetypes
from string import Template

# Import from itools
from itools.datatypes import DateTime, Integer, String, Tokens, Unicode
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
from registry import register_object_class, get_object_class
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
        topic = context.get_form_value('topic', type=Integer)
        version = context.get_form_value('version', type=Integer)
        priority = context.get_form_value('priority', type=Integer)
        assign = context.get_form_value('assigned_to')
        state = context.get_form_value('state', type=Integer)

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
            getter = search.get_value
        else:
            getter = context.get_form_value
        text = getter('text', type=Unicode).strip().lower()
        topic = getter('topic', type=Integer)
        version = getter('version', type=Integer)
        priority = getter('priority', type=Integer)
        assign = getter('assigned_to', type=String)
        state = getter('state', type=Integer)
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
                if topic != handler.get_value('topic'):
                    continue
            if version is not None:
                if version != handler.get_value('version'):
                    continue
            if priority is not None:
                if priority != handler.get_value('priority'):
                    continue
            if assign:
                if assign != handler.get_value('assigned_to'):
                    continue
            if state is not None:
                if state != handler.get_value('state'):
                    continue
            # Append
            link = '%s/;edit_form' % handler.name
            line = {'id': (handler.name, link),
                    'title': (handler.get_value('title'), link)}
            for name in 'topic', 'version', 'priority', 'state':
                value = handler.get_value(name)
                row = tables[name].get_row_by_id(value)
                line[name] = row and row.get_value('title') or None
            assigned_to = handler.get_value('assigned_to')
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
        # Add
        id = self.get_new_id()
        issue = self.set_handler(id, Issue())
        # Datetime
        row = [datetime.now()]
        # Reported By
        user = context.user
        if user is None:
            row.append(None)
        else:
            row.append(user.name)
        # Title
        for name in 'title', 'topic', 'version', 'priority', 'assigned_to':
            type = History.schema[name]
            value = context.get_form_value(name, type=type)
            row.append(value)
        # State
        row.append('')
        # Comment
        comment = context.get_form_value('comment', type=Unicode)
        row.append(comment)
        # Files
        file = context.get_form_value('file')
        if file is None:
            row.append(())
        else:
            filename, mimetype, body = file
            row.append((filename,))
            # Upload
            # The mimetype sent by the browser can be minimalistic
            guessed = mimetypes.guess_type(filename)[0]
            if guessed is not None:
                mimetype = guessed
            # Set the handler
            handler_class = get_object_class(mimetype)
            handler = handler_class()
            handler.load_state_from_string(body)
            issue.set_handler(filename, handler, format=mimetype)
        # First row
        issue.add_row(row)

        # Notify / From
        if user is None:
            from_addr = ''
        else:
            from_addr = user.get_property('ikaaro:email')
        # Notify / To
        assigned_to = context.get_form_value('assigned_to')
        assigned_to = self.get_handler('/users/%s' % assigned_to)
        to_addr = assigned_to.get_property('ikaaro:email')
        # Notify / Subject
        title = context.get_form_value('title', type=Unicode)
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
        ['history'],
        ['browse_content?mode=list'],
        ['new_resource_form?type=file']]


    def new(self, **kw):
        Folder.new(self, **kw)
        cache = self.cache
        cache['.history'] = History()


    def _get_handler(self, segment, uri):
        name = segment.name
        if name == '.history':
            return History(uri)
        return Folder._get_handler(self, segment, uri)


    def get_document_types(self):
        return [File]


    #######################################################################
    # API
    #######################################################################
    def get_rows(self):
        return self.get_handler('.history').get_rows()


    def add_row(self, row):
        self.get_handler('.history').add_row(row)


    def get_reported_by(self):
        history = self.get_handler('.history')
        username = history.get_row(0).get_value('username')
        return self.get_handler('/users/%s' % username).get_title()


    def get_value(self, name):
        return self.get_handler('.history').lines[-1].get_value(name)


    def get_comment(self):
        rows = self.get_handler('.history').lines
        i = len(rows) - 1
        while i >= 0:
            row = rows[i]
            comment = row.get_value('comment')
            if comment:
                return comment
            i -= 1
        return ''


    def has_text(self, text):
        if text in self.get_value('title').lower():
            return True
        return text in self.get_comment().lower()


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
        namespace['title'] = self.get_value('title')
        # Reported by
        namespace['reported_by'] = self.get_reported_by()
        # Topic, Priority, etc.
        parent = self.parent
        tables = [('topic', 'topics'), ('version', 'versions'),
            ('priority', 'priorities'), ('state', 'states')]
        for name, table_name in tables:
            table = parent.get_handler('%s.csv' % table_name)
            value = self.get_value(name)
            namespace[table_name] = table.get_namespace(value)
        # Assign To
        selected = self.get_value('assigned_to')
        namespace['users'] = [
            {'id': x, 'title': users.get_handler(x).get_title(),
             'is_selected': x == selected}
            for x in self.get_site_root().get_members() ]
        # Attachements
        files = []
        for filename in self.get_value('files'):
            file = self.get_handler(filename)
            files.append({'name': filename,
                'type': file.get_property('format'),
                'datetime': format_datetime(vfs.get_mtime(file.uri))})
        namespace['files'] = files
        # Comments
        users = self.get_handler('/users')
        comments = []
        for row in self.get_rows():
            comment = row.get_value('comment')
            if not comment:
                continue
            username = row.get_value('username')
            datetime = row.get_value('datetime')
            user = users.get_handler(username)
            comments.append({
                'user': user.get_title(),
                'datetime': format_datetime(datetime),
                'comment': comment})
        comments.reverse()
 
        namespace['comments'] = comments

        handler = self.get_handler('/ui/tracker/edit_issue.xml')
        return stl(handler, namespace)


    edit__access__ = 'is_allowed_to_edit'
    def edit(self, context):
        user = context.user
        # Date and Username
        username = (user is not None and user.name) or ''
        row = [datetime.now(), username]
        # Other values
        for name in ('title', 'topic', 'version', 'priority', 'assigned_to',
            'state', 'comment'):
            type = History.schema[name]
            value = context.get_form_value(name, type=type)
            if type == Unicode:
                value = value.strip()
            row.append(value)
        # Attachements
        files = self.get_value('files')
        row.append(files)
        # Append
        self.add_row(row)

        return context.come_back('Changes saved.')


    #######################################################################
    # User Interface / History
    history__access__ = 'is_allowed_to_view'
    history__label__ = u'History'
    def history(self, context):
        namespace = {}
        namespace['number'] = self.name

        users = self.get_handler('/users')
        rows = []
        for row in self.get_rows():
            username = row.get_value('username')
            user = users.get_handler(username)
            rows.append({'datetime': row.get_value('datetime'),
                         'user': user.get_title()})
        namespace['rows'] = rows

        handler = self.get_handler('/ui/tracker/issue_history.xml')
        return stl(handler, namespace)


register_object_class(Issue)


class History(BaseCSV):
    
    columns = ['datetime', 'username', 'title', 'topic', 'version', 'priority',
               'assigned_to', 'state', 'comment', 'files']
    schema = {'datetime': DateTime,
              'username': String,
              'title': Unicode,
              'topic': Integer,
              'version': Integer,
              'priority': Integer,
              'assigned_to': String,
              'state': Integer,
              'comment': Unicode,
              'files': Tokens}

