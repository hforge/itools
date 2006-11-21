# -*- coding: UTF-8 -*-
# Copyright (C) 2002-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from operator import attrgetter
from string import Template

# Import from itools
from itools import uri
from itools.handlers.Folder import Folder
from itools.web import get_context

# Import from itools.cms
from utils import get_parameters
from Handler import Handler



def sort(objects, sortby, sortorder='up', getter=None):
    """
    Returns the same objects sorted by the given criteria ("sortby"),
    in the given sense ("sortorder").

    The parameter "sortby" must be a list with the different criterias
    to use to sort the objects.

    The parameter "getter" if given must be a function that defines the
    way to get values from every object.
    """

    # The default getter tries first getattr, and if it fails tries
    # mapping access.
    if getter is None:
        def getter(object, key):
            try:
                return getattr(object, key)
            except AttributeError:
                return object[key]

    # Process sortby, it must be a list like:
    #   [<criteria>, ...]
    # where criteria is a list:
    #   [<key>, ...]
    # XXX Do we really need this "feature"?
    sortby = [ x.split('.') for x in sortby ]

    # Define the sort function
    def sort_key(x, sortby=sortby, getter=getter):
        criterias = []
        for criteria in sortby:
            for key in criteria:
                x = getter(x, key)
            if callable(x):
                x = x()
            criterias.append(x)
        return tuple(criterias)

    # Reverse?
    reverse = (sortorder == 'down')

    return sorted(objects, key=sort_key, reverse=reverse)



def batch(objects, start=0, size=0):
    # Calculate subtotal and batchend
    total = len(objects)

    end = start + size
    if end > total:
        end = total

    # Previous and next
    previous = start - size
    if previous < 0:
        previous = 0
    if previous == start:
        previous = None

    next = end
    if next >= total:
        next = None

    # Get the subset
    if size:
        objects = objects[start:end]
        subtotal = end - start
    else:
        subtotal = total

    return objects, total, subtotal, end, previous, next





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

    def __init__(self, objects, sortby=None, sortorder='up', batchstart=0,
                 batchsize=0, getter=None, name='table'):
        context = get_context()
        # Get the parameters
        if context.has_form_value('%s_sortby' % name):
            sortby = context.get_form_values('%s_sortby' % name)
        elif isinstance(sortby, (str, unicode)):
            sortby = [sortby]
        sortorder = context.get_form_value('%s_sortorder' % name, sortorder)
        start = context.get_form_value('%s_batchstart' % name, batchstart)
        start = int(start)
        size = context.get_form_value('%s_batchsize' % name, batchsize)
        size = int(batchsize)

        # Sort
        if sortby is not None:
            objects = sort(objects, sortby, sortorder, getter)

        # Batch
        objects, total, subtotal, end, prev, next = batch(objects, start, size)


        self.name = name
        self.objects = objects
        self.total = total # objects here are not original objects list
        self.sortby = sortby
        self.sortorder = sortorder
        self.batchstart = start + 1
        self.batchend = end
        self.subtotal = subtotal
        self.previous = prev
        self.next = next

        # Return a dict. as {'total', 'previous', 'next',  'control'}
        context = get_context()
        # Previous
        self.batch_previous = None
        if self.previous is not None:
            data = {'%s_batchstart' % self.name: str(self.previous)}
            self.batch_previous = context.uri.replace(**data)
        # Next 
        self.batch_next = None
        if self.next is not None:
            data = {'%s_batchstart' % self.name: str(self.next)}
            self.batch_next = context.uri.replace(**data)
        # Summary
        message = Handler.gettext(u'$start-$end of $total')
        self.batch_control = Template(message).substitute(
            {'start': self.batchstart, 'end': end, 'total': total})


    def _sortcontrol(self, column):
        """
        Returns an html snippet with a link that lets to order a column
        in a table.
        """
        # Process column
        if isinstance(column, (str, unicode)):
            column = [column]

        # Calculate the href
        data = {}
        data['%s_sortby' % self.name] = column

        if self.sortby == column:
            value = self.sortorder
            if self.sortorder == 'up':
                data['%s_sortorder' % self.name] = 'down'
            else:
                data['%s_sortorder' % self.name] = 'up'
        else:
            value = 'none'
            data['%s_sortorder' % self.name] = 'up'

        href = get_context().uri.replace(**data)
        return href, value



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
        user = context.user
        filter = (Folder, filter_type)
        for handler in target.search_handlers(handler_class=filter):
            ac = handler.get_access_control()
            if not ac.is_allowed_to_view(user, handler):
                continue

            path = here.get_pathto(handler)
            bc_target = str(root.get_pathto(handler))
            url = context.uri.replace(bc_target=bc_target)

            self.is_submit = True
            # Calculate path
            path_to_icon = handler.get_path_to_icon(16)
            if path:
                path_to_handler = uri.Path(str(path) + '/')
                path_to_icon = path_to_handler.resolve(path_to_icon)
            objects.append({'name': handler.name,
                            'is_folder': isinstance(handler, Folder),
                            'is_selectable': True,
                            'path': path,
                            'url': url,
                            'icon': path_to_icon,
                            'object_type': handler.get_mimetype()})

        self.objects = objects

        # Avoid general template
        response.set_header('Content-Type', 'text/html; charset=UTF-8')



class Node(object):

    def __init__(self, handler, depth=None, count=None):
        from Folder import Folder

        if depth is None:
            raise ValueError, 'calling Node without a maximum depth'
        # 'count' is an internal value, don't touch!
        if count is None:
            count = 0

        context = get_context()
        here = context.path
        handler_abspath = uri.Path(handler.abspath)

        self.title = handler.get_title_or_name()
        self.icon = handler.get_path_to_icon(size=16,
                                             from_handler=context.handler)
        self.path = '%s/;%s' % (here.get_pathto(handler_abspath),
                                handler.get_firstview())
        self.active = (here == handler_abspath)

        self.is_last = False
        self.in_path = False
        self.children = []

        if count == depth:
            self.is_last = True
            self.in_path = True
            return

        # continue for possible children
        #
        if count == 0:
            # always recurse root
            self.in_path = True
        else:
            prefix = here.get_prefix(handler_abspath)
            if prefix != '.':
                # on the way
                self.in_path = True

        # recurse children in our way
        if self.in_path:
            user = context.user
            self.children = []
            for h in handler.search_handlers(handler_class=Folder):
                ac = h.get_access_control()
                if ac.is_allowed_to_view(user, h):
                    node = self.__class__(h, depth=depth, count=count + 1)
                    self.children.append(node)

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
