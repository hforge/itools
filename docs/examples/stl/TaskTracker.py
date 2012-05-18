# -*- coding: UTF-8 -*-
# Copyright (C) 2005, 2010 J. David Ibáñez <jdavid.ibp@gmail.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
from textwrap import wrap, fill

# Import from itools
from itools.core import add_type
from itools.handlers import register_handler_class, ro_database, TextFile
from itools.stl import stl


add_type('text/x-task-tracker', '.tt')


class Task(object):

    def __init__(self, title, description, state='open'):
        self.title = title
        self.description = description
        self.state = state



class TaskTracker(TextFile):

    class_mimetypes = ['text/x-task-tracker']


    #########################################################################
    # Load & Save
    #########################################################################
    def _load_state_from_file(self, file):
        # Split the raw data in lines.
        lines = file.readlines()
        # Append None to signal the end of the data.
        lines.append(None)

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
                    fields[field_name] += line.rstrip()
                else:
                    field_name, field_value = line.split(':', 1)
                    fields[field_name] = field_value.rstrip()


    def to_str(self, encoding='utf-8'):
        lines = []
        for task in self.tasks:
            lines.append('title:%s' % task.title)
            description = 'description:%s' % task.description
            description = wrap(description)
            lines.append(description[0])
            for line in description[1:]:
                lines.append(' %s' % line)
            lines.append('state:%s' % task.state)
            lines.append('')
        return '\n'.join(lines)


    #########################################################################
    # The Skeleton
    #########################################################################
    def new(self):
        self.tasks = []
        task = Task('Read the docs!',
                    'Read the itools documentation, it is so gooood.',
                    'open')
        self.tasks.append(task)


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
                print fill(task.description)
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
        handler = ro_database.get_handler('TaskTracker_view.xml')

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
        return stl(handler, namespace, mode='xhtml')


register_handler_class(TaskTracker)



if __name__ == '__main__':
    task_tracker = ro_database.get_handler('itools.tt')
    print task_tracker.view()
