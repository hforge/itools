# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Hervé Cauwelier <herve@itaapy.com>
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

# Import from the future
from __future__ import absolute_import

# Import from the Standard Library
import re
from operator import itemgetter

# Import from itools.cms
from ..web import get_context
from ..stl import stl

# Import from itools.cms
from .File import File
from .Folder import Folder
from .text import Text
from .registry import register_object_class
from .utils import checkid
from .widgets import table

# Import from docutils
try:
    import docutils
except ImportError:
    print "docutils is not installed, wiki deactivated."
    raise
from docutils.core import publish_string
from docutils.nodes import SparseNodeVisitor
from docutils.readers.standalone import Reader as StandaloneReader
from docutils.transforms import Transform


########################################
# reST-specific stuff
#
# Inspired from http://docutils.sourceforge.net/sandbox/ianb/wiki/Wiki.py
#
########################################

class WikiLinkResolver(SparseNodeVisitor):

    def visit_reference(self, node):
        if node.resolved:
            node['classes'].append('external_reference')
            return
        if not node.hasattr('refname'):
            return
        refname = node['name']
        node.resolved = 1
        node['classes'].append('wiki')
        # Wiki links marked with a '!' for further resolution
        node['refuri'] = '!' + refname
        del node['refname']



class WikiLink(Transform):

    default_priority = 800

    def apply(self):
        visitor = WikiLinkResolver(self.document)
        self.document.walk(visitor)



class Reader(StandaloneReader):

    supported = StandaloneReader.supported + ('wiki',)

    def get_transforms(self):
        return StandaloneReader.get_transforms(self) + [WikiLink]



class WikiFolder(Folder):
    class_id = 'WikiFolder'
    class_version = '20061229'
    class_title = u"Wiki Folder"
    class_description = u"Container for a wiki"
    class_icon16 = 'images/WikiFolder16.png'
    class_icon48 = 'images/WikiFolder48.png'
    class_views = [
        ['view'],
        ['browse_content?mode=thumbnails',
         'browse_content?mode=list',
         'browse_content?mode=image'],
        ['new_resource_form'],
        ['edit_metadata_form'],
        ['last_changes']]

    __fixed_handlers__ = ['FrontPage']


    def new(self, **kw):
        Folder.new(self, **kw)
        cache = self.cache
        page = WikiPage()
        cache['FrontPage'] = page
        cache['FrontPage.metadata'] = self.build_metadata(page,
                **{'dc:title': {'en': u"Front Page"}})


    def get_document_types(self):
        return [WikiPage, File]


    #######################################################################
    # User interface
    #######################################################################
    def GET(self, context):
        if context.has_form_value('message'):
            message = context.get_form_value('message')
            return context.come_back(message, 'FrontPage')
        return context.uri.resolve2('FrontPage')


    view__access__ = 'is_allowed_to_view'
    view__label__ = u"View"
    def view(self, context):
        if context.has_form_value('message'):
            message = context.get_form_value('message')
            return context.come_back(message, 'FrontPage')
        return context.uri.resolve('FrontPage')



    last_changes__access__ = 'is_allowed_to_view'
    last_changes__label__ = u"Last Changes"
    def last_changes(self, context, sortby=['mtime'], sortorder='down'):
        users = self.get_handler('/users')
        namespace = {}
        pages = []

        namespace['search_fields'] = None
        namespace['batch'] = ''

        for page in self.search_handlers(handler_class=WikiPage):
            revisions = page.get_revisions(context)
            if revisions:
                last_rev = revisions[0]
                username = last_rev['username']
                try:
                    user = users.get_handler(username)
                    user_title = user.get_title()
                    if not user_title.strip():
                        user_title = user.get_property('ikaaro:email')
                except LookupError:
                    user_title = username
            else:
                user_title = '?'
            pages.append({'name': (page.name, page.name),
                          'title': page.get_title_or_name(),
                          'mtime': page.get_mtime(),
                          'last_author': user_title})

        sortby = context.get_form_values('sortby', sortby)
        sortorder = context.get_form_value('sortorder', sortorder)
        pages.sort(key=itemgetter(sortby[0]), reverse=(sortorder == 'down'))
        namespace['pages'] = pages

        columns = [
            ('name', u'Name'), ('title', u'Title'), ('mtime', u'Last Modified'),
            ('last_author', u'Last Author')]
        namespace['table'] = table(columns, pages, sortby, sortorder, [],
                self.gettext)

        handler = self.get_handler('/ui/Folder_browse_list.xml')
        return stl(handler, namespace)


register_object_class(WikiFolder)



class WikiPage(Text):
    class_id = 'WikiPage'
    class_version = '20061229'
    class_title = u"Wiki Page"
    class_description = u"Wiki contents"
    class_icon16 = 'images/WikiPage16.png'
    class_icon48 = 'images/WikiPage48.png'
    class_views = Text.class_views + [
            ['browse_content'],
            ['last_changes']]
    class_extension = None

    _wikiLinkRE = re.compile(r'(<a [^>]* href=")!(.*?)("[^>]*>)(.*?)(</a>)',
                             re.I+re.S)
    link_template = ('%(open_tag)s../%(page)s%(open_tag_end)'
            's%(text)s%(end_tag)s')
    new_link_template = ('<span class="nowiki">%(text)s%(open_tag)s'
            '../;new_resource_form?type=WikiPage&name=%(page)s'
            '%(open_tag_end)s?%(end_tag)s</span>')


    def _resolve_wiki_link(self, match):
        namespace = {'open_tag': match.group(1),
                     'page': checkid(match.group(2)) or '',
                     'open_tag_end': match.group(3),
                     'text': match.group(4),
                     'end_tag': match.group(5)}
        parent = self.parent
        name = checkid(namespace['page']) or ''
        if parent.has_handler(name):
            return self.link_template % namespace
        else:
            return  self.new_link_template % namespace


    def _resolve_wiki_links(self, html):
        return self._wikiLinkRE.sub(self._resolve_wiki_link, ' %s ' % html)


    #######################################################################
    # User interface
    #######################################################################
    def GET(self, context):
        return context.uri.resolve2(';view')


    @classmethod
    def new_instance_form(cls, name=''):
        context = get_context()
        root = context.root
        namespace = {}

        # Page name
        name = context.get_form_value('name', '')
        name = unicode(name, 'utf_8')
        namespace['name'] = checkid(name) or False

        # Class id
        namespace['class_id'] = cls.class_id

        handler = root.get_handler('ui/WikiPage_new_instance.xml')
        return stl(handler, namespace)


    def to_html(self):
        html = publish_string(source=self.to_str(), reader=Reader(),
                              parser_name='restructuredtext',
                              writer_name='html')
        html = html[html.find('<div class="document"'):html.find('</body>')]
        return self._resolve_wiki_links(html)


    def view(self, context):
        css = self.get_handler('/ui/wiki.css')
        context.styles.append(str(self.get_pathto(css)))

        return self.to_html()


    def edit_form(self, context):
        css = self.get_handler('/ui/wiki.css')
        context.styles.append(str(self.get_pathto(css)))

        namespace = {}
        namespace['data'] = self.to_str()

        handler = self.get_handler('/ui/WikiPage_edit.xml')
        return stl(handler, namespace)


    def edit(self, context):
        goto = Text.edit(self, context)
        # Avoid full source in the return query
        goto = goto.replace(data=None)

        message = goto.query['message']
        if 'class="system-message"' in self.to_html():
            message = u"Syntax error, please check the view for details."

        if context.has_form_value('view'):
            goto = ';view'
        else:
            goto.fragment = 'bottom'
        return context.come_back(message, goto)


    browse_content__access__ = WikiFolder.browse_content__access__
    browse_content__label__ = WikiFolder.browse_content__label__
    def browse_content(self, context):
        return context.uri.resolve('../;browse_content')


    last_changes__access__ = WikiFolder.last_changes__access__
    last_changes__label__ = WikiFolder.last_changes__label__
    def last_changes(self, context):
        return context.uri.resolve('../;last_changes')


register_object_class(WikiPage)
