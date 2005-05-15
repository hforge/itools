# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA

# Import from the Standard Library
import mimetypes
import textwrap

# Import from itools
from itools.resources import get_resource
from itools.handlers.Text import Text
from itools.handlers import get_handler
import itools.xml


mimetypes.add_type('text/x-task-tracker', '.tt')


class Task(object):
    def __init__(self, title, description, state='open'):
        self.title = title
        self.description = description
        self.state = state
    


class TaskTracker(Text):

    class_mimetypes = ['text/x-task-tracker']


    #########################################################################
    # Load & Save
    #########################################################################
    def _load_state(self, resource=None):
        # Load the resource as a unicode string
        Text._load_state(self, resource)
        # Split the raw data in lines.
        lines = self._data.splitlines()
        # Append None to signal the end of the data.
        lines.append(None)
        # Free the un-needed data structure, 'self._data'
        del self._data

        # Initialize the internal data structure
        self.tasks = []
        # Parse and load the tasks
        fields = {}
        for line in lines:
            if line is None or line.strip() == '':
                if fields:
                    task = Task(fields['title'],
                                fields['description'],
                                fields['state'])
                    self.tasks.append(task)
                    fields = {}
            else:
                if line.startswith(' '):
                    fields[field_name] += line
                else:
                    field_name, field_value = line.split(':', 1)
                    fields[field_name] = field_value


    def to_unicode(self, encoding=None):
        lines = []
        for task in self.tasks:
            lines.append(u'title:%s' % task.title)
            description = u'description:%s' % task.description
            description = textwrap.wrap(description)
            lines.append(description[0])
            for line in description[1:]:
                lines.append(u' %s' % line)
            lines.append(u'state:%s' % task.state)
            lines.append('')
        return u'\n'.join(lines)


    #########################################################################
    # The Skeleton
    #########################################################################
    def get_skeleton(self):
        return 'title:Read the docs!\n' \
               'description:Read the itools documentation, it is\n' \
               ' so gooood.\n' \
               'state:open\n'


    #########################################################################
    # The API
    #########################################################################
    def add_task(self, title, description):
        task = Task(title, description)
        self.tasks.append(task)


    def show_open_tasks(self):
        for id, task in enumerate(self.tasks):
            if task.state == 'open':
                print 'Task #%d: %s' % (id, task.title)
                print
                print textwrap.fill(task.description)
                print
                print


    def close_task(self, id):
        task = self.tasks[id]
        task.state = u'closed'


    #########################################################################
    # Web Interface
    #########################################################################
    def view(self):
        # Load the STL template
        handler = get_handler('TaskTracker_view.xml')

        # Build the namespace
        namespace = {}
        namespace['tasks'] = []
        for i, task in enumerate(self.tasks):
            namespace['tasks'].append({'id': i,
                                       'title': task.title,
                                       'description': task.description,
                                       'state': task.state,
                                       'is_open': task.state == 'open'})

        # Process the template and return the output
        return handler.stl(namespace)


Text.register_handler_class(TaskTracker)



if __name__ == '__main__':
    task_tracker = get_handler('itools.tt')
    print task_tracker.view()
