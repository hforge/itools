# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Luis Arturo Belmar-Letelier <luis@itaapy.com>
# Copyright (C) 2007 Nicolas Deram <nicolas@itaapy.com>
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
from datetime import datetime
import mimetypes
from operator import itemgetter
from string import Template
from re import sub

# Import from itools
from itools.datatypes import Boolean, DateTime, Integer, String, Unicode, XML
from itools.i18n import format_datetime
from itools.handlers import Config
from itools.csv import IntegerKey, CSV as BaseCSV
from itools.xml import Parser
from itools.stl import stl
from itools.uri import encode_query
from csv import CSV
from file import File
from folder import Folder
from messages import *
from text import Text
from utils import generate_name
from registry import register_object_class, get_object_class
import widgets



# Definition of the fields of the forms to add and edit an issue
issue_fields = [('title', True), ('version', True), ('type', True),
    ('state', True), ('module', False), ('priority', False),
    ('assigned_to', False), ('comment', False), ('file', False)]



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

    __fixed_handlers__ = ['modules.csv', 'versions.csv', 'types.csv',
        'priorities.csv', 'states.csv']


    def new(self, **kw):
        Folder.new(self, **kw)
        cache = self.cache
        # Versions
        csv = Versions()
        csv.add_row([u'1.0', False])
        csv.add_row([u'2.0', False])
        cache['versions.csv'] = csv
        cache['versions.csv.metadata'] = csv.build_metadata()
        # Other Tables
        tables = [
            ('modules.csv', [u'Documentation', u'Unit Tests',
                u'Programming Interface', u'Command Line Interface',
                u'Visual Interface']),
            ('types.csv', [u'Bug', u'New Feature', u'Security Issue',
                u'Stability Issue', u'Data Corruption Issue',
                u'Performance Improvement', u'Technology Upgrade']),
            ('priorities.csv', [u'High', u'Medium', u'Low']),
            ('states.csv', [u'Open', u'Fixed', u'Closed'])]
        for name, values in tables:
            csv = SelectTable()
            cache[name] = csv
            for title in values:
                csv.add_row([title])
            cache['%s.metadata' % name] = csv.build_metadata()
        # Pre-defined stored searches
        open = StoredSearch(state=0)
        not_assigned = StoredSearch(assigned_to='nobody')
        high_priority = StoredSearch(state=0, priority=0)
        i = 0
        for search, title in [(open, u'Open Issues'),
                              (not_assigned, u'Not Assigned'),
                              (high_priority, u'High Priority')]:
            cache['s%s' % i] = search
            kw = {}
            kw['dc:title'] = {'en': title}
            cache['s%s.metadata' % i] = search.build_metadata(**kw)
            i += 1


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


    def get_members_namespace(self, value, not_assigned=False):
        """
        Returns a namespace (list of dictionaries) to be used for the
        selection box of users (the 'assigned to' field).
        """
        users = self.get_handler('/users')
        members = []
        if not_assigned is True:
            members.append({'id': 'nobody', 'title': 'NOT ASSIGNED'})
        for username in self.get_site_root().get_members():
            user = users.get_handler(username)
            members.append({'id': username, 'title': user.get_title()})
        # Select
        for member in members:
            member['is_selected'] = (member['id'] == value)

        return members
        


    #######################################################################
    # User Interface
    #######################################################################
    def get_subviews(self, name):
        if name == 'search_form':
            items = list(self.search_handlers(handler_class=StoredSearch))
            items.sort(lambda x, y: cmp(x.get_property('dc:title'),
                                        y.get_property('dc:title')))
            return ['view?search_name=%s' % x.name for x in items]
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
        # Set Style
        css = self.get_handler('/ui/tracker/tracker.css')
        context.styles.append(str(self.get_pathto(css)))

        # Build the namespace
        namespace = {}
        # Stored Searches
        stored_searches = [
            {'name': x.name, 'title': x.get_title()}
            for x in self.search_handlers(handler_class=StoredSearch) ]
        stored_searches.sort(key=itemgetter('title'))
        namespace['stored_searches'] = stored_searches

        # Search Form
        search_name = context.get_form_value('search_name')
        if search_name:
            search = self.get_handler(search_name)
            namespace['search_name'] = search_name
            namespace['search_title'] = search.get_property('dc:title')
            namespace['text'] = search.get_value('text', type=Unicode)
            namespace['mtime'] = search.get_value('mtime', type=Integer)
            module = search.get_value('module', type=Integer)
            type = search.get_value('type', type=Integer)
            version = search.get_value('version', type=Integer)
            priority = search.get_value('priority', type=Integer)
            assign = search.get_value('assigned_to')
            state = search.get_value('state', type=Integer)
        else:
            namespace['search_name'] = None
            namespace['search_title'] = None
            namespace['text'] = None
            namespace['mtime'] = None
            module = None
            type = None
            version = None
            priority = None
            assign = None
            state = None

        get = self.get_handler
        namespace['modules'] = get('modules.csv').get_options(module)
        namespace['types'] = get('types.csv').get_options(type)
        namespace['versions'] = get('versions.csv').get_options(version)
        namespace['priorities'] = get('priorities.csv').get_options(priority,
            sort=False)
        namespace['states'] = get('states.csv').get_options(state, sort=False)
        namespace['users'] = self.get_members_namespace(assign, True)
        # is_admin 
        ac = self.get_access_control()
        namespace['is_admin'] = ac.is_admin(context.user, self)
        pathto_website = self.get_pathto(self.get_site_root())
        namespace['manage_assigned'] = '%s/;permissions_form' % pathto_website 

        handler = self.get_handler('/ui/tracker/search.xml')
        return stl(handler, namespace)


    search__access__ = 'is_allowed_to_edit'
    def search(self, context):
        search_name = context.get_form_value('search_name')
        search_title = context.get_form_value('search_title').strip()
        search_title = unicode(search_title, 'utf8')

        stored_search = stored_search_title = None
        if search_name:
            # Edit an Stored Search
            try:
                stored_search = self.get_handler(search_name)
                stored_search_title = stored_search.get_property('dc:title')
            except LookupError:
                pass

        if search_title and search_title != stored_search_title:
            # New Stored Search
            search_name = self.get_new_id('s')
            stored_search, kk = self.set_object(search_name, StoredSearch())

        if stored_search is None: 
            # Just Search
            return context.uri.resolve(';view').replace(**context.uri.query)

        # Edit / Title
        context.commit = True
        stored_search.set_property('dc:title', search_title, 'en')
        # Edit / Search Values
        text = context.get_form_value('text').strip().lower()
        mtime = context.get_form_value('mtime', type=Integer)
        module = context.get_form_value('module', type=Integer)
        version = context.get_form_value('version', type=Integer)
        type = context.get_form_value('type', type=Integer)
        priority = context.get_form_value('priority', type=Integer)
        assign = context.get_form_value('assigned_to')
        state = context.get_form_value('state', type=Integer)

        criterias = [('text', text), ('mtime', mtime), ('module', module),
            ('version', version), ('type', type), ('priority', priority),
            ('assigned_to', assign), ('state', state)]
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
        text = getter('text', type=Unicode)
        if text is not None:
            text = text.strip().lower()
        mtime = getter('mtime', type=Integer)
        module = getter('module', type=Integer)
        version = getter('version', type=Integer)
        type = getter('type', type=Integer)
        priority = getter('priority', type=Integer)
        assign = getter('assigned_to', type=String)
        state = getter('state', type=Integer)
        # Build the namespace
        users = self.get_handler('/users')
        namespace = {}
        # Columns
        columns = [('id', u'Id'), ('title', u'Title'), ('version', u'Version'),
            ('module', u'Module'), ('type', u'Type'),
            ('priority', u'Priority'), ('state', u'State'),
            ('assigned_to', u'Assigned To')]
        # Lines
        lines = []
        tables = {'module': self.get_handler('modules.csv'),
                  'version': self.get_handler('versions.csv'),
                  'type': self.get_handler('types.csv'),
                  'priority': self.get_handler('priorities.csv'),
                  'state': self.get_handler('states.csv')}
        now = datetime.now()
        for handler in self.search_handlers(handler_class=Issue):
            if text:
                if not handler.has_text(text):
                    continue
            if mtime is not None:
                if (now - handler.get_mtime()).days >= mtime:
                    continue
            if module is not None:
                if module != handler.get_value('module'):
                    continue
            if version is not None:
                if version != handler.get_value('version'):
                    continue
            if type is not None:
                if type != handler.get_value('type'):
                    continue
            if priority is not None:
                if priority != handler.get_value('priority'):
                    continue
            if assign:
                value = handler.get_value('assigned_to')
                if assign == 'nobody':
                    if value != '':
                        continue
                elif assign != value:
                    continue
            if state is not None:
                if state != handler.get_value('state'):
                    continue
            # Append
            link = '%s/;edit_form' % handler.name
            line = {'id': (handler.name, link),
                    'title': (handler.get_value('title'), link)}
            for name in 'module', 'version', 'type', 'priority', 'state':
                value = handler.get_value(name)
                row = tables[name].get_row_by_id(value)
                line[name] = row and row.get_value('title') or None
            assigned_to = handler.get_value('assigned_to')
            # solid in case the user has been removed
            if assigned_to and users.has_handler(assigned_to):
                    user = users.get_handler(assigned_to)
                    line['assigned_to'] = user.get_title()
            else:
                line['assigned_to'] = ''
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
        # Set Style
        css = self.get_handler('/ui/tracker/tracker.css')
        context.styles.append(str(self.get_pathto(css)))

        # Build the namespace
        namespace = {}
        namespace['title'] = context.get_form_value('title', type=Unicode)
        namespace['comment'] = context.get_form_value('comment', type=Unicode)
        # Others
        get = self.get_handler
        module = context.get_form_value('module', type=Integer)
        namespace['modules'] = get('modules.csv').get_options(module)
        version = context.get_form_value('version', type=Integer)
        namespace['versions'] = get('versions.csv').get_options(version)
        type = context.get_form_value('type', type=Integer)
        namespace['types'] = get('types.csv').get_options(type)
        priority = context.get_form_value('priority', type=Integer)
        namespace['priorities'] = get('priorities.csv').get_options(priority,
            sort=False)
        state = context.get_form_value('state', type=Integer)
        namespace['states'] = get('states.csv').get_options(state, sort=False)

        users = self.get_handler('/users')
        assigned_to = context.get_form_value('assigned_to', type=String)
        namespace['users'] = self.get_members_namespace(assigned_to)

        handler = self.get_handler('/ui/tracker/add_issue.xml')
        return stl(handler, namespace)


    add_issue__access__ = 'is_allowed_to_edit'
    def add_issue(self, context):
        keep = ['title', 'version', 'type', 'state', 'module', 'priority',
            'assigned_to', 'comment']
        # Check input data
        error = context.check_form_input(issue_fields)
        if error is not None:
            return context.come_back(error, keep=keep)

        # Add
        id = self.get_new_id()
        issue, metadata = self.set_object(id, Issue())
        issue._add_row(context)

        goto = context.uri.resolve2('../%s/;edit_form' % issue.name)
        return context.come_back(u'New issue addded.', goto=goto)


    go_to_issue__access__ = 'is_allowed_to_view'
    def go_to_issue(self, context):
        issue_name = context.get_form_value('issue_name')
        if not issue_name in self.get_handler_names():
            return context.come_back(u'Issue not found.')
        issue = self.get_handler(issue_name)
        if not isinstance(issue, Issue):
            return context.come_back(u'Issue not found.')
        return context.uri.resolve2('../%s/;edit_form' % issue_name)

register_object_class(Tracker)


###########################################################################
# Tables
###########################################################################
class SelectTable(CSV):

    class_id = 'tracker_select_table'

    columns = ['id', 'title']
    schema = {'id': IntegerKey, 'title': Unicode}


    def get_options(self, value=None, sort=True):
        options = [ {'id': x[0], 'title': x[1]} for x in self.get_rows() ]
        if sort is True:
            options.sort(key=lambda x: x['title'])
        # Set 'is_selected'
        if value is None:
            for option in options:
                option['is_selected'] = False
        else:
            for option in options:
                option['is_selected'] = (option['id'] == value)

        return options


    def get_row_by_id(self, id):
        for x in self.search(id=id):
            return self.get_row(id)
        return None



register_object_class(SelectTable)



class Versions(SelectTable):
    
    class_id = 'tracker_versions'

    columns = ['id', 'title', 'released']
    schema = {'id': IntegerKey,
              'title': Unicode(title=u'Title'),
              'released': Boolean(title=u'Released')}


    def view(self, context):
        namespace = {}

        # The input parameters
        start = context.get_form_value('batchstart', type=Integer, default=0)
        size = 30

        # The batch
        total = len(self.lines)
        namespace['batch'] = widgets.batch(context.uri, start, size, total,
                                           self.gettext)

        # The table
        actions = []
        if total:
            ac = self.get_access_control()
            if ac.is_allowed_to_edit(context.user, self):
                actions = [('del_row_action', u'Remove', 'button_delete',None)]

        columns = self.get_columns()
        columns.insert(0, ('index', u''))
        columns.append(('issues', u'Issues'))
        rows = []
        index = start
        getter = lambda x, y: x.get_value(y)

        for row in self.lines[start:start+size]:
            rows.append({})
            rows[-1]['id'] = str(index)
            rows[-1]['checkbox'] = True
            # Columns
            rows[-1]['index'] = index, ';edit_row_form?index=%s' % index
            for column, column_title in columns[1:-1]:
                value = getter(row, column)
                datatype = self.get_datatype(column)
                is_enumerate = getattr(datatype, 'is_enumerate', False)
                rows[-1][column] = value
            count = 0
            for handler in self.parent.search_handlers(handler_class=Issue):
                if handler.get_value('version') == index:
                    count += 1
            value = '0'
            if count != 0:
                value = '<a href="../;view?version=%s">%s issues</a>'
                if count == 1:
                    value = '<a href="../;view?version=%s">%s issue</a>'
                value = Parser(value % (index, count))
            rows[-1]['issues'] = value
            index += 1

        # Sorting
        sortby = context.get_form_value('sortby')
        sortorder = context.get_form_value('sortorder', 'up')
        if sortby:
            rows.sort(key=itemgetter(sortby), reverse=(sortorder=='down'))

        namespace['table'] = widgets.table(columns, rows, [sortby], sortorder,
                                           actions)

        handler = self.get_handler('/ui/csv/view.xml')
        return stl(handler, namespace)

register_object_class(Versions)


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
class History(BaseCSV):

    columns = ['datetime', 'username', 'title', 'module', 'version', 'type',
               'priority', 'assigned_to', 'state', 'comment', 'file']
    schema = {'datetime': DateTime,
              'username': String,
              'title': Unicode,
              'module': Integer,
              'version': Integer,
              'type': Integer,
              'priority': Integer,
              'assigned_to': String,
              'state': Integer,
              'comment': Unicode,
              'file': String}



class Issue(Folder):

    class_id = 'issue'
    class_layout = {
        '.history': History}
    class_title = u'Issue'
    class_description = u'Issue'
    class_views = [
        ['edit_form'],
        ['search_form'],
        ['add_form'],
        ['browse_content?mode=list'],
        ['history']]


    def new(self, **kw):
        Folder.new(self, **kw)
        cache = self.cache
        cache['.history'] = History()


    def get_document_types(self):
        return [File]


    #######################################################################
    # API
    #######################################################################
    def get_title(self):
        return self.get_value('title')


    def get_rows(self):
        return self.get_handler('.history').get_rows()


    def _add_row(self, context):
        user = context.user
        root = context.root
        parent = self.parent
        users = root.get_handler('users')

        # Datetime
        row = [datetime.now()]
        # User
        if user is None:
            row.append('')
        else:
            row.append(user.name)
        # Title
        title = context.get_form_value('title', type=Unicode).strip()
        row.append(title)
        # Version, Priority, etc.
        for name in ['module', 'version', 'type', 'priority', 'assigned_to',
                     'state', 'comment']:
            type = History.schema[name]
            value = context.get_form_value(name, type=type)
            if type == Unicode:
                value = value.strip()
            row.append(value)
        # Files
        file = context.get_form_value('file')
        if file is None:
            row.append('')
        else:
            filename, mimetype, body = file
            # Upload
            # The mimetype sent by the browser can be minimalistic
            guessed = mimetypes.guess_type(filename)[0]
            if guessed is not None:
                mimetype = guessed
            # Set the handler
            handler_class = get_object_class(mimetype)
            handler = handler_class()
            handler.load_state_from_string(body)

            # Find a non used name
            filename = generate_name(filename, self.get_handler_names())
            row.append(filename)

            handler, metadata = self.set_object(filename, handler)
            metadata.set_property('format', mimetype)
        # Update
        history = self.get_handler('.history')
        history.add_row(row)

        # Send a Notification Email
        # Notify / From
        if user is None:
            from_addr = ''
            user_title = self.gettext(u'ANONYMOUS')
        else:
            from_addr = user.get_property('ikaaro:email')
            user_title = user.get_title()
        # Notify / To
        to_addrs = set()
        reported_by = self.get_reported_by()
        if reported_by:
            to_addrs.add(reported_by)
        assigned_to = self.get_value('assigned_to')
        if assigned_to:
            to_addrs.add(assigned_to)
        if user.name in to_addrs:
            to_addrs.remove(user.name)
        # Notify / Subject
        subject = '[Tracker Issue #%s] %s' % (self.name, title)
        # Notify / Body
        if context.handler.class_id == Tracker.class_id:
            uri = context.uri.resolve('%s/;history' % self.name)
        else:
            uri = context.uri.resolve(';history')
        body = str(uri) + '\n\n'
        body += self.gettext(u'The user %s did some changes.') % user_title
        body += '\n\n'
        (kk, kk, title, module, version, type, priority, assigned_to, state,
            comment, filename) = row
        if len(history.lines) == 1:
            old_title = old_module = old_version = old_type = old_priority \
                = old_assigned_to = old_state = None
        else:
            (kk, kk, old_title, old_module, old_version, old_type,
                old_priority, old_assigned_to, old_state, kk, kk
                ) = history.lines[-2] 
        if title != old_title:
            body += self.gettext(u'  Title: %s') % title + '\n'
        if version != old_version:
            if version is None:
                version = ''
            else:
                versions = parent.get_handler('versions.csv')
                version = versions.get_row_by_id(version).get_value('title')
            body += self.gettext(u'  Version: %s') % version + '\n'
        if module != old_module:
            if module is None:
                module = ''
            else:
                modules = parent.get_handler('modules.csv')
                module = modules.get_row_by_id(module).get_value('title')
            body += self.gettext(u'  Module: %s') % module + '\n'
        if type != old_type:
            if type is None:
                type = ''
            else:
                types = parent.get_handler('types.csv')
                type = types.get_row_by_id(type).get_value('title')
            body += self.gettext(u'  Type: %s') % type
        if priority != old_priority:
            if priority is None:
                priority = ''
            else:
                priorities = parent.get_handler('priorities.csv')
                priority = priorities.get_row_by_id(priority).get_value('title')
            body += self.gettext(u'  Priority: %s') % priority + '\n'
        if state != old_state:
            if state is None:
                state = ''
            else:
                states = parent.get_handler('states.csv')
                state = states.get_row_by_id(state).get_value('title')
            body += self.gettext(u'  State: %s') % state + '\n'
        if assigned_to != old_assigned_to:
            if assigned_to:
                assigned_to = users.get_handler(assigned_to).get_title()
            else:
                assigned_to = ''
            body += self.gettext(u'  Assigned To: %s') % assigned_to + '\n'
        if file:
            body += self.gettext(u'  New Attachment: %s') % filename + '\n'
        if comment:
            body += self.gettext(u'Comment') + '\n'
            body += self.gettext(u'-------') + '\n\n'
            body += comment
        # Notify / Send
        for to_addr in to_addrs:
            to_addr = users.get_handler(to_addr)
            to_addr = to_addr.get_property('ikaaro:email')
            root.send_email(from_addr, to_addr, subject, body)


    def get_reported_by(self):
        history = self.get_handler('.history')
        return history.get_row(0).get_value('username')


    def get_value(self, name):
        rows = self.get_handler('.history').lines
        if rows:
            return rows[-1].get_value(name)
        return None


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


    def indent(self, text):
        """ Replace spaces at the begining of a line by &nbsp;
            Replace '\n' by <br>\n and URL by HTML links"""
        res = []
        text = text.encode('utf-8')
        text = XML.encode(text)
        for line in text.splitlines():
            sline = line.lstrip()
            indent = len(line) - len(sline)
            if indent:
                line = '&nbsp;' * indent + sline
            line = sub('http://(.\S*)', r'<a href="http://\1">\1</a>', line)
            res.append(line)
        return Parser('<br/>\n'.join(res))


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
        (kk, kk, title, module, version, type, priority, assigned_to, state,
            comment, file) = self.get_handler('.history').lines[-1]

        # Build the namespace
        namespace = {}
        namespace['number'] = self.name
        namespace['title'] = title
        # Reported by
        reported_by = self.get_reported_by()
        reported_by = self.get_handler('/users/%s' % reported_by)
        namespace['reported_by'] = reported_by.get_title()
        # Topics, Version, Priority, etc.
        get = self.parent.get_handler
        namespace['modules'] = get('modules.csv').get_options(module)
        namespace['versions'] = get('versions.csv').get_options(version)
        namespace['types'] = get('types.csv').get_options(type)
        namespace['priorities'] = get('priorities.csv').get_options(priority,
            sort=False)
        namespace['states'] = get('states.csv').get_options(state, sort=False)

        # Assign To
        namespace['users'] = self.parent.get_members_namespace(assigned_to)
        # Comments
        users = self.get_handler('/users')
        comments = []
        i = 0
        for row in self.get_rows():
            comment = row.get_value('comment')
            file = row.get_value('file')
            if not comment and not file:
                continue
            datetime = row.get_value('datetime')
            # solid in case the user has been removed
            username = row.get_value('username')
            user_title = username
            if users.has_handler(username):
                user_title = users.get_handler(username).get_title()
            i += 1
            comments.append({
                'number': i,
                'user': user_title,
                'datetime': format_datetime(datetime),
                'comment': self.indent(comment),
                'file': file})
        comments.reverse()
        namespace['comments'] = comments

        handler = self.get_handler('/ui/tracker/edit_issue.xml')
        return stl(handler, namespace)


    edit__access__ = 'is_allowed_to_edit'
    def edit(self, context):
        # Check input data
        error = context.check_form_input(issue_fields)
        if error is not None:
            return context.come_back(error)
        # Edit
        self._add_row(context)

        return context.come_back(MSG_CHANGES_SAVED)


    #######################################################################
    # User Interface / History
    history__access__ = 'is_allowed_to_view'
    history__label__ = u'History'
    def history(self, context):
        # Set Style
        css = self.get_handler('/ui/tracker/tracker.css')
        context.styles.append(str(self.get_pathto(css)))

        # Local variables
        users = self.get_handler('/users')
        versions = self.get_handler('../versions.csv')
        types = self.get_handler('../types.csv')
        states = self.get_handler('../states.csv')
        modules = self.get_handler('../modules.csv')
        priorities = self.get_handler('../priorities.csv')
        # Initial values
        previous_title = None
        previous_version = None
        previous_type = None
        previous_state = None
        previous_module = None
        previous_priority = None
        previous_assigned_to = None

        # Build the namespace
        namespace = {}
        namespace['number'] = self.name
        rows = []
        i = 0
        for row in self.get_rows():
            (datetime, username, title, module, version, type, priority,
                assigned_to, state, comment, file) = row
            # solid in case the user has been removed
            user_exist = users.has_handler(username) 
            usertitle = (user_exist and 
                         users.get_handler(username).get_title() or username)
            comment = XML.encode(Unicode.encode(comment))
            comment = Parser(comment.replace('\n', '<br />'))
            i += 1
            row_ns = {'number': i,
                      'user': usertitle,
                      'datetime': format_datetime(datetime),
                      'title': None,
                      'version': None,
                      'type': None,
                      'state': None,
                      'module': None,
                      'priority': None,
                      'assigned_to': None,
                      'comment': comment,
                      'file': file}

            if title != previous_title:
                previous_title = title
                row_ns['title'] = title
            if version != previous_version:
                previous_version = version
                if module is None:
                    row_ns['version'] = ' '
                else:
                    version = versions.get_row_by_id(version).get_value('title')
                    row_ns['version'] = version
            if type != previous_type:
                previous_type = type
                if type is None:
                    row_ns['type'] = ' '
                else:
                    type = types.get_row_by_id(type).get_value('title')
                    row_ns['type'] = type
            if state != previous_state:
                previous_state = state
                if state is None:
                    row_ns['state'] = ' '
                else:
                    state = states.get_row_by_id(state).get_value('title')
                    row_ns['state'] = state
            if module != previous_module:
                previous_module = module
                if module is None:
                    row_ns['module'] = ' '
                else:
                    module = modules.get_row_by_id(module).get_value('title')
                    row_ns['module'] = module
            if priority != previous_priority:
                previous_priority = priority
                if priority is None:
                    row_ns['priority'] = ' '
                else:
                    priority = priorities.get_row_by_id(priority).get_value(
                        'title')
                    row_ns['priority'] = priority
            if assigned_to != previous_assigned_to:
                previous_assigned_to = assigned_to
                if assigned_to and users.has_handler(assigned_to):
                    assigned_to_user = users.get_handler(assigned_to)
                    row_ns['assigned_to'] = assigned_to_user.get_title()
                else:
                    row_ns['assigned_to'] = ' '

            rows.append(row_ns)

        rows.reverse()
        namespace['rows'] = rows

        handler = self.get_handler('/ui/tracker/issue_history.xml')
        return stl(handler, namespace)


    add_form__access__ = 'is_allowed_to_edit'
    add_form__label__ = u'Add'
    def add_form(self, context):
        reference = '../;add_form'
        return context.uri.resolve(reference)


    search_form__access__ = 'is_allowed_to_edit'
    search_form__label__ = u'search'
    def search_form(self, context):
        reference = '../;search_form'
        return context.uri.resolve(reference)


    def get_subviews(self, name):
        if name == 'search_form':
            return self.parent.get_subviews(name)
        return Folder.get_subviews(self, name)


    view__access__ = Tracker.view__access__
    view__label__ = Tracker.view__label__
    def view(self, context):
        query = encode_query(context.uri.query)
        reference = '../;view?%s' % query
        return context.uri.resolve(reference)


    def view__sublabel__(self, **kw):
        search_name = kw.get('search_name')
        if search_name is None:
            return u'View'

        search = self.parent.get_handler(search_name)
        return search.get_title()


register_object_class(Issue)
