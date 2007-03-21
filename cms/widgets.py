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
from itools.uri import Path
from itools.handlers.Folder import Folder
from itools.xhtml import XHTML
from itools.stl import stl
from itools.web import get_context

# Import from itools.cms
from utils import get_parameters
from Handler import Handler



###########################################################################
# Table
###########################################################################

def batch(uri, start, size, total, gettext=Handler.gettext):
    """
    Outputs an HTML snippet with navigation links to move through a set
    of objects.

    Input data:
        
        uri -- The base URI to use to build the navigation links.

        start -- The start of the batch (from 0).

        size -- The size of the batch.

        total -- The total number of objects.
    """
    # Plural forms (XXX do it the gettext way)
    if total == 1:
        msg1 = gettext(u"There is 1 object.")
    else:
        msg1 = gettext(u"There are ${n} objects.")
        msg1 = Template(msg1).substitute(n=total)

    # Calculate end
    end = min(start + size, total)

    # Previous
    previous = None
    if start > 0:
        previous = max(start - size, 0)
        previous = str(previous)
        previous = uri.replace(batchstart=previous)
        previous = '<a href="%s" title="%s">&lt;&lt;</a>' \
                   % (previous, gettext(u'Previous'))
    # Next
    next = None
    if end < total:
        next = str(end)
        next = uri.replace(batchstart=next)
        next = '<a href="%s" title="%s">&gt;&gt;</a>' \
               % (next, gettext(u'Next'))

    # Output
    if previous is None and next is None:
        msg = msg1
    else:
        # View more
        if previous is None:
            link = next
        elif next is None:
            link = previous
        else:
            link = '%s %s' % (previous, next)

        msg2 = gettext(u"View from ${start} to ${end} (${link}):")
        msg2 = Template(msg2)
        msg2 = msg2.substitute(start=(start+1), end=end, link=link)

        msg = '%s %s' % (msg1, msg2)

    # Wrap around a paragraph
    return '<p class="batchcontrol">%s</p>' % msg



def table_sortcontrol(column, sortby, sortorder):
    """
    Returns an html snippet with a link that lets to order a column
    in a table.
    """
    # Process column
    if isinstance(column, (str, unicode)):
        column = [column]

    # Calculate the href
    data = {}
    data['sortby'] = column

    if sortby == column:
        value = sortorder
        if sortorder == 'up':
            data['sortorder'] = 'down'
        else:
            data['sortorder'] = 'up'
    else:
        value = 'none'
        data['sortorder'] = 'up'

    href = get_context().uri.replace(**data)
    return href, value


def table_head(columns, sortby, sortorder, gettext=lambda x: x):
    # Build the namespace
    columns_ = []
    for name, title in columns:
        if title is None:
            column = None
        else:
            column = {'title': gettext(title)}
            href, sort = table_sortcontrol(name, sortby, sortorder)
            column['href'] = href
            column['order'] = sort
        columns_.append(column)
    # Go
    return columns_


table_template_string = """
<stl:block xmlns="http://www.w3.org/1999/xhtml"
  xmlns:stl="http://xml.itools.org/namespaces/stl">

  <!-- Content -->
  <form action="." method="post">
    <table xmlns="http://www.w3.org/1999/xhtml"
      xmlns:stl="http://xml.itools.org/namespaces/stl">
      <thead stl:if="columns">
        <tr>
          <th stl:if="column_checkbox"></th>
          <th stl:if="column_image"></th>
          <th stl:repeat="column columns" valign="bottom">
            <a stl:if="column" href="${column/href}"
              class="sort_${column/order}">${column/title}</a>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr stl:repeat="row rows" class="${repeat/row/even} ${row/class}">
          <td stl:if="column_checkbox">
            <input class="checkbox" type="checkbox" name="ids" stl:if="row/id"
              value="${row/id}" />
          </td>
          <td stl:if="column_image">
            <img border="0" src="${row/img}" stl:if="row/img" />
          </td>
          <td stl:repeat="column row/columns">
            <a stl:if="column/href" href="${column/href}">${column/value}</a>
            <stl:block if="not column/href">${column/value}</stl:block>
          </td>
        </tr>
      </tbody>
    </table> 
    <p stl:if="actions">
      <stl:block repeat="action actions">
        <input type="submit" name=";${action/name}" value="${action/value}"
          class="${action/class}" onclick="${action/onclick}" />
      </stl:block>
    </p>
  </form>
</stl:block>
"""

table_template = XHTML.Document()
table_template.load_state_from_string(table_template_string)


def table(columns, rows, sortby, sortorder, actions=[], gettext=lambda x: x):
    """
    The parameters are:

      columns --
        [(name, title), (name, title), ...]

      rows --
        [{'checkbox': , 'img': }, ...]

      sortby --
        The column to sort.

      sortorder --
        The order the column must be sorted by.

      actions --
        [{'name': , 'value': , 'class': , 'onclick': }, ...]

      gettext --
        The translation function.
    """
    namespace = {}
    namespace['column_checkbox'] = False
    namespace['column_image'] = False
    # The columns
    namespace['columns'] = table_head(columns, sortby, sortorder, gettext)
    # The rows
    aux = []
    for row in rows:
        x = {}
        # The checkbox column
        x['id'] = None
        if actions and row['checkbox'] is True:
            x['id'] = row['id']
            namespace['column_checkbox'] = True
        # The image column
        x['img'] = row.get('img')
        if x['img'] is not None:
            namespace['column_image'] = True
        # A CSS class on the TR
        x['class'] = row.get('class')
        # Other columns
        x['columns'] = []
        for column, kk in columns:
            value = row.get(column)
            if isinstance(value, tuple):
                value, href = value
            else:
                href = None
            x['columns'].append({'value': value, 'href': href})
        aux.append(x)

    namespace['rows'] = aux
    # The actions
    namespace['actions'] = [
        {'name': name, 'value': value, 'class': cls, 'onclick': onclick}
        for name, value, cls, onclick in actions ]

    return stl(table_template, namespace)



###########################################################################
# Breadcrumb
###########################################################################
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
                path_to_handler = Path(str(path) + '/')
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



###########################################################################
# Menu
###########################################################################
def build_menu(options):
    """
    The input (options) is a tree:

      [{'href': ...,
        'class': ...,
        'src': ...,
        'title': ...,
        'items': [....]}
       ...
       ]
       
    """
    output = '<dl>\n'

    for option in options:
        cls = option['class']
        href = option['href']
        src = option['src']
        # The option
        output += '<dt class="%s">' % cls
        # The image
        if option['src'] is not None:
            output += '<img src="%s" alt="" width="16" height="16" /> ' % src
        # The link
        if option['href'] is None:
            output += option['title']
        else:
            output += '<a href="%s">' % href
            output += option['title']
            output += '</a>'
        output += '</dt>\n'

        # Sub-options
        output += '<dd>'
        if option['items']:
            output += build_menu(option['items'])
        output += '</dd>'

    output += '</dl>\n'
    return output



def _tree(node, root, depth, active_node, filter, user):
    # Build the namespace
    namespace = {}
    namespace['src'] = node.get_path_to_icon(size=16, from_handler=active_node)
    namespace['title'] = node.get_title_or_name()

    # The href
    firstview = node.get_firstview()
    if firstview is None:
        namespace['href'] = None
    else:
        path = active_node.get_pathto(node)
        namespace['href'] = '%s/;%s' % (path, firstview)

    # The CSS style
    namespace['class'] = ''
    if node is active_node:
        namespace['class'] = 'nav_active'

    # Expand only if in path
    aux = active_node
    while True:
        # Match
        if aux is node:
            break
        # Reach the root, do not expand
        if aux is root:
            namespace['items'] = []
            return namespace
        # Next
        aux = aux.parent

    # Expand till a given depth
    if depth <= 0:
        namespace['items'] = []
        return namespace

    # Expand the children
    depth = depth - 1

    # Filter the handlers by the given class (don't filter by default)
    if filter is None:
        search = node.search_handlers()
    else:
        search = node.search_handlers(handler_class=filter)

    children = []
    for child in search:
        ac = child.get_access_control()
        if ac.is_allowed_to_view(user, child):
            aux = _tree(child, root, depth, active_node, filter, user)
            children.append(aux)
    namespace['items'] = children
 
    return namespace



def tree(root, depth=6, active_node=None, filter=None, user=None):
    options = [_tree(root, root, depth, active_node, filter, user)]
    return build_menu(options)

