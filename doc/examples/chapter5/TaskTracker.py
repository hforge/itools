
# Import from itools
from itools.handlers.Text import Text



class Task(object):
    def __init__(self, id, title, description, state):
        self.id = id
        self.title = title
        self.description = description
        self.state = state
    


class TaskTracker(Text):

    def _load(self, resource=None):
        # Call the parent handler to load the resource as a unicode string
        Text._load(self, resource)
        # Parse the file and load the tasks
        self.tasks = []
        fields = {}
        for line in self._data.splitlines():
            if line.strip() == '':
                id = int(fields['id'])
                task = Task(id, fields['title'], fields['description'],
                            fields['state'])
                self.tasks.append(task)
            else:
                if line.startswith(' '):
                    fields[field_name] += line
                else:
                    field_name, field_value = line.split(':', 1)
                    fields[field_name] = field_value
        # Free un-needed data structure
        del self._data
