# -*- coding: UTF-8 -*-

# import from the future
from __future__ import absolute_import

# Import from the Standard Library
import re

# Import from itools.cms
from .. import uri
from ..web import get_context
from ..stl import stl

# Import from itools.cms
from .File import File
from .Folder import Folder
from .text import Text
from .registry import register_object_class
from .utils import checkid

# Import from docutils
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
    class_views = [['view'],
                   ['browse_thumbnails', 'browse_list', 'browse_image'],
                   ['new_resource_form'],
                   ['edit_metadata_form']]

    __fixed_handlers__ = ['FrontPage']


    def new(self, **kw):
        Folder.new(self, **kw)
        cache = self.cache
        page = WikiPage()
        cache['FrontPage'] = page
        cache['FrontPage.metadata'] = self.build_metadata(page,
                **{'dc:title': {'en': u"Front Page"}})


    def new_resource(self, context):
        status = Folder.new_resource(self, context)
        class_id = context.get_form_value('class_id')
        if class_id != 'WikiPage':
            return status

        name = context.get_form_value('name')
        name = checkid(name) or ''
        if not self.has_handler(name):
            return status
        page = self.get_handler(name)

        data = context.get_form_value('data')
        page.load_state_from_string(data)

        return status


    def get_document_types(self):
        return [WikiPage, File]


    #######################################################################
    # User interface
    #######################################################################
    def GET(self, context):
        return uri.get_reference('%s/FrontPage/;view' % self.name)


register_object_class(WikiFolder)



class WikiPage(Text):
    class_id = 'WikiPage'
    class_version = '20061229'
    class_title = u"Wiki Page"
    class_description = u"Wiki contents"
    class_icon16 = 'images/WikiPage16.png'
    class_icon48 = 'images/WikiPage48.png'
    class_extension = None

    _wikiLinkRE = re.compile(r'(<a [^>]* href=")!(.*?)("[^>]*>)(.*?)(</a>)',
                             re.I+re.S)
    link_template = ('%(open_tag)s../%(page)s/;view%(open_tag_end)'
            's%(text)s%(end_tag)s')
    new_link_template = ('<span class="nowiki">%(text)s%(open_tag)s'
            '../;new_resource_form?type=WikiPage&name=%(page)s'
            '%(open_tag_end)s?%(end_tag)s</span>')

    def _exists(self, page):
        parent = self.parent
        name = checkid(page) or ''
        return parent.has_handler(name)


    def _resolve_wiki_link(self, match):
        namespace = {'open_tag': match.group(1),
                     'page': checkid(match.group(2)) or '',
                     'open_tag_end': match.group(3),
                     'text': match.group(4),
                     'end_tag': match.group(5)}
        if self._exists(namespace['page']):
            return self.link_template % namespace
        else:
            return  self.new_link_template % namespace

    def _resolve_wiki_links(self, html):
        return self._wikiLinkRE.sub(self._resolve_wiki_link, ' %s ' % html)


    #######################################################################
    # User interface
    #######################################################################
    def GET(self, context):
        return self.view(context)


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


    def view(self, context):
        css = self.get_handler('/ui/wiki.css')
        context.styles.append(str(self.get_pathto(css)))
        html = publish_string(source=self.to_str(), reader=Reader(),
                              parser_name='restructuredtext',
                              writer_name='html')
        html = html[html.find('<div class="document">'):html.find('</body>')]
        html = self._resolve_wiki_links(html)

        return html


register_object_class(WikiPage)
