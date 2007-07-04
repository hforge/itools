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
from __future__ import with_statement

# Import from the Standard Library
from tempfile import mkdtemp
from subprocess import call
import urllib

# Import from itools
from ..uri import get_reference
from .. import vfs
from ..stl import stl
from ..datatypes import Unicode, FileName
from ..rest import checkid

# Import from itools.cms
from .file import File
from .folder import Folder
from itools.cms.messages import *
from .text import Text
from .registry import register_object_class
from .binary import Image

# Import from docutils
try:
    import docutils
except ImportError:
    print "docutils is not installed, wiki deactivated."
    raise
from docutils import core
from docutils import io
from docutils import readers
from docutils import nodes


class WikiFolder(Folder):
    class_id = 'WikiFolder'
    class_version = '20061229'
    class_title = u"Wiki Folder"
    class_description = u"Container for a wiki"
    class_icon16 = 'images/WikiFolder16.png'
    class_icon48 = 'images/WikiFolder48.png'
    class_views = [['view'],
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
        cache['FrontPage.metadata'] = page.build_metadata(
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
            message = context.get_form_value('message', type=Unicode)
            return context.come_back(message, 'FrontPage')
        return context.uri.resolve('FrontPage')


register_object_class(WikiFolder)



class WikiPage(Text):
    class_id = 'WikiPage'
    class_version = '20061229'
    class_title = u"Wiki Page"
    class_description = u"Wiki contents"
    class_icon16 = 'images/WikiPage16.png'
    class_icon48 = 'images/WikiPage48.png'
    class_views = [['view'],
                   ['edit_form', 'externaledit', 'upload_form'],
                   ['state_form', 'edit_metadata_form'],
                   ['browse_content?mode=thumbnails',
                    'browse_content?mode=list',
                    'browse_content?mode=image'],
                   ['new_resource_form'],
                   ['last_changes'],
                   ['to_pdf'],
                   ['help']]
    class_extension = None

    overrides = {
        # Security
        'file_insertion_enabled': 0,
        'raw_enabled': 0,
        # Encodings
        'input_encoding': 'utf-8',
        'output_encoding': 'utf-8',
    }

    #######################################################################
    # User interface
    #######################################################################
    def get_subviews(self, name):
        if name == 'new_resource_form':
            subviews = []
            for cls in self.parent.get_document_types():
                id = cls.class_id
                ref = 'new_resource_form?type=%s' % urllib.quote_plus(id)
                subviews.append(ref)
            return subviews
        return Text.get_subviews(self, name)


    @classmethod
    def new_instance_form(cls, context, name=''):
        root = context.root
        namespace = {}

        # Page name
        name = context.get_form_value('name', default=u'', type=Unicode)
        namespace['name'] = checkid(name) or False

        # Class id
        namespace['class_id'] = cls.class_id

        handler = root.get_handler('ui/wiki/WikiPage_new_instance.xml')
        return stl(handler, namespace)


    @classmethod
    def new_instance(cls, container, context):
        name = context.get_form_value('name')
        data = context.get_form_value('data', default='')

        # Check the name
        name = name.strip() or title.strip()
        if not name:
            return context.come_back(MSG_NAME_MISSING)

        name = checkid(name)
        if name is None:
            return context.come_back(MSG_BAD_NAME)

        # Check the name is free
        if container.has_handler(name):
            return context.come_back(MSG_NAME_CLASH)

        # Build the object
        handler = cls(string=data)
        metadata = handler.build_metadata()
        # Add the object
        handler, metadata = container.set_object(name, handler, metadata)

        goto = './%s/;%s' % (name, handler.get_firstview())
        return context.come_back(MSG_NEW_RESOURCE, goto=goto)


    def GET(self, context):
        return context.uri.resolve2(';view')


    def to_html(self):
        parent = self.parent

        # Override dandling links handling
        StandaloneReader = readers.get_reader_class('standalone')
        class WikiReader(StandaloneReader):
            supported = ('wiki',)

            def wiki_reference_resolver(target):
                refname = target['name']
                name = checkid(refname)
                target['wiki_name'] = name
                if parent.has_handler(name):
                    target['wiki_refname'] = refname
                else:
                    target['wiki_refname'] = False
                return True

            wiki_reference_resolver.priority = 851
            unknown_reference_resolvers = [wiki_reference_resolver]

        # Manipulate publisher directly (from publish_doctree)
        reader = WikiReader(parser_name='restructuredtext')
        pub = core.Publisher(reader=reader, source_class=io.StringInput,
                destination_class=io.NullOutput)
        pub.set_components(None, 'restructuredtext', 'null')
        pub.process_programmatic_settings(None, self.overrides, None)
        pub.set_source(self.to_str(), None)
        pub.set_destination(None, None)

        # Publish!
        pub.publish(enable_exit_status=None)
        document = pub.document

        # Fix the wiki links
        for node in document.traverse(condition=nodes.reference):
            refname = node.get('wiki_refname')
            if refname is None:
                if node.get('refid'):
                    node['classes'].append('internal')
                elif node.get('refuri'):
                    node['classes'].append('external')
            else:
                name = node['wiki_name']
                if refname is False:
                    refuri = ";new_resource_form?type=%s&name=%s"
                    refuri = refuri % (self.__class__.__name__, name)
                    css_class = 'nowiki'
                else:
                    refuri = name
                    css_class = 'wiki'
                node['refuri'] = '../' + refuri
                node['classes'].append(css_class)

        # Allow to reference images by name
        for node in document.traverse(condition=nodes.image):
            node_uri = node['uri']
            if not self.has_handler(node_uri):
                if parent.has_handler(node_uri):
                    node['uri'] = '../' + node_uri

        # Manipulate publisher directly (from publish_from_doctree)
        reader = readers.doctree.Reader(parser_name='null')
        pub = core.Publisher(reader, None, None,
                source=io.DocTreeInput(document),
                destination_class=io.StringOutput)
        pub.set_writer('html')
        pub.process_programmatic_settings(None, self.overrides, None)
        pub.set_destination(None, None)
        pub.publish(enable_exit_status=None)
        parts = pub.writer.parts
        body = parts['html_body']

        return body.encode('utf_8')


    to_pdf__access__ = 'is_allowed_to_view'
    to_pdf__label__ = u"To PDF"
    def to_pdf(self, context):
        parent = self.parent
        pages = [self.name]
        images = []

        # Override dandling links handling
        StandaloneReader = readers.get_reader_class('standalone')
        class WikiReader(StandaloneReader):
            supported = ('wiki',)

            def wiki_reference_resolver(target):
                refname = target['name']
                name = checkid(refname)
                if refname not in pages:
                    pages.append(refname)
                target['wiki_refname'] = refname
                target['wiki_name'] = name
                return True

            wiki_reference_resolver.priority = 851
            unknown_reference_resolvers = [wiki_reference_resolver]

        reader = WikiReader(parser_name='restructuredtext')
        document = core.publish_doctree(self.to_str(), reader=reader,
                settings_overrides=self.overrides)

        # Fix the wiki links
        for node in document.traverse(condition=nodes.reference):
            refname = node.get('wiki_refname')
            if refname is None:
                continue
            name = node['name'].lower()
            document.nameids[name] = refname

        # Append referenced pages
        for refname in pages[1:]:
            references = document.refnames[refname.lower()]
            reference = references[0]
            reference.parent.remove(reference)
            name = reference['wiki_name']
            if not parent.has_handler(name):
                continue
            title = reference.astext()
            page = parent.get_handler(name)
            if isinstance(page, Image):
                # Link to image?
                images.append(('../%s' % name, name))
                continue
            elif not isinstance(page, WikiPage):
                # Link to file
                continue
            source = page.to_str()
            subdoc = core.publish_doctree(source,
                    settings_overrides=self.overrides)
            if isinstance(subdoc[0], nodes.section):
                for node in subdoc.children:
                    if isinstance(node, nodes.section):
                        document.append(node)
            else:
                subtitle = subdoc.get('title', u'')
                section = nodes.section(*subdoc.children, **subdoc.attributes)
                section.insert(0, nodes.title(text=subtitle))
                document.append(section)

        # Find the list of images to append
        for node in document.traverse(condition=nodes.image):
            node_uri = node['uri']
            if not self.has_handler(node_uri):
                if parent.has_handler(node_uri):
                    node_uri = '../' + node_uri
                else:
                    continue
            reference = get_reference(node_uri)
            path = reference.path
            filename = str(path[-1])
            name, ext, lang = FileName.decode(filename)
            if ext == 'jpeg':
                # pdflatex does not support this extension
                ext = 'jpg'
            filename = FileName.encode((name, ext, lang))
            # Remove all path so the image is found in tempdir
            node['uri'] = filename
            images.append((node_uri, filename))

        overrides = dict(self.overrides)
        overrides['stylesheet'] = 'style.tex'
        output = core.publish_from_doctree(document, writer_name='latex',
                settings_overrides=overrides)

        dirname = mkdtemp('wiki', 'itools')
        tempdir = vfs.open(dirname)

        # Save the document...
        with tempdir.make_file(self.name) as file:
            file.write(output)
        # The stylesheet...
        stylesheet = self.get_handler('/ui/wiki/style.tex')
        with tempdir.make_file('style.tex') as file:
            stylesheet.save_state_to_file(file)
        # The 'powered' image...
        image = self.get_handler('/ui/images/ikaaro_powered.png')
        with tempdir.make_file('ikaaro.png') as file:
            image.save_state_to_file(file)
        # And referenced images
        for node_uri, filename in images:
            if tempdir.exists(filename):
                continue
            image = self.get_handler(node_uri)
            with tempdir.make_file(filename) as file:
                image.save_state_to_file(file)

        call(['pdflatex', '-8bit', '-no-file-line-error', '-interaction=batchmode', self.name], cwd=dirname)
        # Twice for correct page numbering
        call(['pdflatex', '-8bit', '-no-file-line-error', '-interaction=batchmode', self.name], cwd=dirname)

        pdfname = '%s.pdf' % self.name
        try:
            with tempdir.open(pdfname) as file:
                data = file.read()
        except LookupError:
            data = None
        vfs.remove(dirname)

        if data is None:
            return context.come_back(u"PDF generation failed.")

        response = context.response
        response.set_header('Content-Type', 'application/pdf')
        response.set_header('Content-Disposition',
                'attachment; filename=%s' % pdfname)

        return data


    def view(self, context):
        css = self.get_handler('/ui/wiki/wiki.css')
        context.styles.append(str(self.get_pathto(css)))

        return self.to_html()


    def edit_form(self, context):
        css = self.get_handler('/ui/wiki/wiki.css')
        context.styles.append(str(self.get_pathto(css)))

        namespace = {}
        namespace['data'] = self.to_str()

        handler = self.get_handler('/ui/wiki/WikiPage_edit.xml')
        return stl(handler, namespace)


    def edit(self, context):
        data = context.get_form_value('data', type=Unicode)
        # Ensure source is encoded to UTF-8
        data = data.encode('utf_8')
        self.load_state_from_string(data)

        if 'class="system-message"' in self.to_html():
            message = u"Syntax error, please check the view for details."
        else:
            message = MSG_CHANGES_SAVED

        goto = context.come_back(message)
        if context.has_form_value('view'):
            query = goto.query
            goto = goto.resolve(';view')
            goto.query = query
        else:
            goto.fragment = 'bottom'
        return goto


    browse_content__access__ = WikiFolder.browse_content__access__
    browse_content__label__ = WikiFolder.browse_content__label__

    def browse_content__sublabel__(self, **kw):
        mode = kw.get('mode', 'thumbnails')
        return {'thumbnails': u'As Icons',
                'list': u'As List',
                'image': u'As Image Gallery'}[mode]

    def browse_content(self, context):
        mode = context.get_form_value('mode')
        if mode is None:
            mode = context.get_cookie('browse_mode') or 'thumbnails'
        return context.uri.resolve('../;browse_content?mode=%s' % mode)


    new_resource_form__access__ = WikiFolder.new_resource_form__access__
    new_resource_form__label__ = WikiFolder.new_resource_form__label__

    def new_resource_form__sublabel__(self, **kw):
        type = kw.get('type')
        for cls in self.parent.get_document_types():
            if cls.class_id == type:
                return cls.class_title
        return u'New Resource'

    def new_resource_form(self, context):
        type = context.get_form_value('type')
        if type:
            reference = '../;new_resource_form?type=%s' % type
        else:
            reference = '../;new_resource_form'
        return context.uri.resolve(reference)


    last_changes__access__ = WikiFolder.last_changes__access__
    last_changes__label__ = WikiFolder.last_changes__label__
    def last_changes(self, context):
        return context.uri.resolve('../;last_changes')


    help__access__ = 'is_allowed_to_view'
    help__label__ = u"Help"
    def help(self, context):
        namespace = {}
        css = self.get_handler('/ui/wiki/wiki.css')
        context.styles.append(str(self.get_pathto(css)))

        source = self.get_handler('/ui/wiki/help.txt')
        source = source.to_str()
        html = core.publish_string(source, writer_name='html',
                settings_overrides=self.overrides)

        namespace['help_source'] = source.replace('&', '&amp;').replace('<', '&lt;')
        namespace['help_html'] = html

        handler = self.get_handler('/ui/wiki/WikiPage_help.xml')
        return stl(handler, namespace)


register_object_class(WikiPage)
