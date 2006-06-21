# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2002-2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
from operator import attrgetter

# Import from itools
from itools import uri
from itools.handlers.Folder import Folder
from itools.web import get_context

# Import from itools.cms
from utils import get_parameters
from Handler import Handler


class Table(object):
    """
    Returns the ordered subset of objects that matches the given parameters.
    Paremeters:

      - objects: list of objects to be shown in the table;

      - sortby: ..

      - sortorder: ..

      - batchstart: ..

      - batchsize: ..
    """

    def __init__(self, root, name, objects, sortby=None, sortorder='up',
                 batchstart='0', batchsize='0'):
        # Get the parameters
        total = len(objects)
        parameters = get_parameters(name, sortby=sortby, sortorder=sortorder,
                                    batchstart=batchstart, batchsize=batchsize)

        sortby = parameters['sortby']
        sortorder = parameters['sortorder']
        batchstart = int(parameters['batchstart'])
        batchsize = int(parameters['batchsize'])

        # Calculate subtotal and batchend
        subtotal = len(objects)

        batchend = batchstart + batchsize
        if batchend > subtotal:
            batchend = subtotal

        # Order
        if sortby is not None:
            # Process sortby, it must be a list like:
            #   [<criteria>, ...]
            # where criteria is a list:
            #   [<key>, ...]
            if isinstance(sortby, (str, unicode)):
                sortby = [sortby]
            sortby = [ x.split('.') for x in sortby ]

            aux = []
            for object in objects:
                criterias = []
                for criteria in sortby:
                    value = object
                    for key in criteria:
                        if hasattr(value, key):
                            value = getattr(value, key)
                        else:
                            value = value[key]
                    if callable(value):
                        value = value()
                    criterias.append(value)
                criterias.append(object)
                aux.append(tuple(criterias))
            aux.sort()
            objects = [ x[-1] for x in aux ]

            if sortorder == 'down':
                objects.reverse()

            # Previous and next
        previous = batchstart - batchsize
        if previous < 0:
            previous = 0
        if previous == batchstart:
            previous = None

        next = batchend
        if next >= subtotal:
            next = None

        # Get the subset
        if batchsize:
            objects = objects[batchstart:batchend]

        self.root = root # XXX Needed by sortcontrol, remove..
        self.name = name
        self.objects = objects
        self.total = total # objects here are not original objects list
        if sortby is None:
            self.sortby = None
        else:
            self.sortby = [ '.'.join(x) for x in sortby ]
        self.sortorder = sortorder
        self.batchstart = batchstart + 1
        self.batchend = batchend
        self.subtotal = subtotal
        self.previous = previous
        self.next = next


    def sortcontrol(self, column):
        """
        Returns an html snippet with a link that lets to order a column
        in a table.
        """
        context = get_context()

        # Process column
        if isinstance(column, (str, unicode)):
            column = [column]
        # The html snippet, variables: href and src
        pattern = '<a href="%(href)s"><img src="%(src)s"></a>'

        # Calculate the href
        data = {}
        data['%s_sortby' % self.name] = column

        if self.sortby == column:
            if self.sortorder == 'up':
                value = 'down'
            else:
                value = 'up'
        else:
            value = 'up'
        data['%s_sortorder' % self.name] = value

        href = context.uri.replace(**data)
        # Calculate the src
        if self.sortby == column:
            value = self.sortorder
        else:
            value = 'none'
        src = context.path.get_pathto('/ui/images/order-%s.png' % value)

        return pattern % {'href': href, 'src': src}


    def batch_control(self):
        """Return a dict. as {'total', 'previous', 'next',  'control'}"""
        context = get_context()
        request = context.request

        batch = {}
        batch['total'] = self.total

        # Batch control
        batch['previous'] = None
        if self.previous is not None:
            data = {'%s_batchstart' % self.name: str(self.previous)}
            batch['previous'] = context.uri.replace(**data)

        batch['next'] = None
        if self.next is not None:
            data = {'%s_batchstart' % self.name: str(self.next)}
            batch['next'] = context.uri.replace(**data)

        # Batch summary
        control = Handler.gettext(u'%(start)s-%(end)s of %(total)s') \
                  % {'start': self.batchstart, 'end': self.batchend,
                     'total': self.total}
        batch['control'] = control
        return batch



class Breadcrumb(object):
    """
    Instances of this class will be used as namespaces for STL templates.
    The built namespace contains the breadcrumb, that is to say, the path
    from the tree root to another tree node, and the content of that node.
    """

    def __init__(self, filter_type=Handler, root=None, start=None):
        """
        The 'start' must be a handler, 'filter_type' must be a handler class.
        """
        context = get_context()
        request, response = context.request, context.response

        if root is None:
            root = context.root
        if start is None:
            start = root

        here = context.handler

        # Get the query parameters
        parameters = get_parameters('bc', id=None, target=None)
        id = parameters['id']
        # Get the target folder
        target_path = parameters['target']
        if target_path is None:
            if isinstance(start, Folder):
                target = start
            else:
                target = start.parent
        else:
            target = root.get_handler(target_path)

        # XXX Obsolete code
        self.style = 'style'
##        self.style = '../' * len(start.get_abspath().split('/')) + 'style'

        # Object to link
        object = request.form.get('object')
        if object == '':
            object = '.'
        self.object = object

        # The breadcrumb
        breadcrumb = []
        node = target
        while node is not root.parent:
            url = context.uri.replace(bc_target=str(root.get_pathto(node)))
            breadcrumb.insert(0, {'name': node.name, 'url': url})
            node = node.parent
        self.path = breadcrumb

        # Content
        objects = []
        self.is_submit = False
        for name in target.resource.get_names():
            if name.startswith('.'):
                continue

            handler = target.get_handler(name)
            if handler.is_allowed_to_view():
                path = here.get_pathto(handler)
                bc_target = str(root.get_pathto(handler))
                url = context.uri.replace(bc_target=bc_target)

                is_folder = isinstance(handler, Folder)
                is_selectable = False
                if is_folder or isinstance(handler, filter_type):
                    is_selectable = True
                    self.is_submit = True
                    # Calculate path
                    path_to_icon = handler.get_path_to_icon(16)
                    if path:
                        path_to_handler = uri.Path(str(path) + '/')
                        path_to_icon = path_to_handler.resolve(path_to_icon)
                    objects.append({'name': name,
                                    'is_folder': is_folder,
                                    'is_selectable': is_selectable,
                                    'path': path,
                                    'url': url,
                                    'icon': path_to_icon,
                                    'object_type': handler.get_mimetype()})

        self.objects = objects

        # Avoid general template
        response.set_header('Content-Type', 'text/html; charset=UTF-8')



class Node(object):

    def __init__(self, handler, depth=None, count=None):
        from Folder import Folder as DatabaseFolder

        if depth is None:
            raise ValueError, 'calling Node without a maximum depth'
        # 'count' is an internal value, don't touch!
        if count is None:
            count = 0

        here = get_context().handler
        here_abspath = here.abspath
        handler_abspath = handler.abspath

        self.title = handler.get_title_or_name()
        self.icon = handler.get_path_to_icon(size=16, from_handler=here)
        self.path = '%s/;%s' % (here.get_pathto(handler), here.get_firstview())
        self.active = (here_abspath == handler_abspath)

        self.is_last = False
        self.in_path = False
        self.children = []

        if count == depth:
            self.is_last = True
            self.in_path = True
            return

        # continue for possible children
        #
        here_path = uri.Path(here_abspath)

        if count == 0:
            # always recurse root
            self.in_path = True
        elif here_path.get_prefix(handler_abspath) == '.':
            # no common part, so not in path
            pass
        elif here_abspath.startswith(handler_abspath):
            # on the way
            self.in_path = True
        else:
            pass

        # recurse children in our way
        if self.in_path:
            self.children = [self.__class__(h, depth=depth, count=count + 1)
                for h in handler.search_handlers(handler_class=DatabaseFolder)]

        # sort lexicographically by title
        self.children.sort(key=attrgetter('title'))


    def children_as_html(self):
        output = []

        output.append('<dd>')
        output.append('<dl>')
        for child in self.children:
            output.extend(child.node_as_html())
        output.append('</dl>')
        output.append('</dd>')

        return output


    def node_as_html(self):
        output = []

        output.append('<dt>')
        output.append('<img src="%s" width="16" height="16" alt="" />' % self.icon)
        css_classes = []
        if self.active:
            css_classes.append('nav_active')
        if self.in_path:
            css_classes.append('nav_in_path')
        if self.is_last:
            css_classes.append('nav_is_last')
        css_classes = ' '.join(css_classes)
        output.append('<a href="%s" class="%s">%s</a>'  % (self.path,
            css_classes, self.title))
        output.append('</dt>')
        if self.children:
            output.extend(self.children_as_html())

        return output


    def tree_as_html(self):
        output = []

        output.append('<dl>')
        output.extend(self.node_as_html())
        output.append('</dl>')

        return '\n'.join(output)
