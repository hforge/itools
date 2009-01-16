# -*- coding: UTF-8 -*-

# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008 Fabrice Decroix <fabrice.decroix@gmail.com>
# Copyright (C) 2008 Yannick Martel <yannick.martel@gmail.com>
# Copyright (C) 2008 Dumont Sébastien <sebastien.dumont@itaapy.com>
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
from cStringIO import StringIO
from types import FileType
import copy
import socket
import tempfile

# Import from itools
from itools.core import freeze, get_abspath
from itools.datatypes import XMLContent
import itools.http
from itools.stl import set_prefix, stl
from itools.uri import Path
from itools.uri.uri import get_cwd
from itools.vfs import vfs
from itools.xml import XMLParser, START_ELEMENT, END_ELEMENT, TEXT
from itools.xml import get_end_tag, XMLFile
# Internal import
from doctemplate import MySimpleDocTemplate, MyDocTemplate
from style import build_paragraph_style, get_table_style, makeTocHeaderStyle
from style import get_align, build_inline_style, build_frame_style
from style import get_hr_style, get_font_name
from utils import check_image, exist_attribute, font_value
from utils import format_size, get_int_value, normalize
from utils import Paragraph, pc_float, stream_next, join_content, Div

# Import from reportlab
import reportlab
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
# CJK
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (XPreformatted, PageBreak, Image, Indenter,
                                Table, tableofcontents)
from reportlab.platypus.flowables import HRFlowable
from reportlab.platypus.tableofcontents import TableOfContents

# Import the graphication css parser
import css


######################################################################
# Initialization
######################################################################

# URI of a PML tags, for the moment, it's xhtml
pml_uri = 'http://www.hforge.org/xml-namespaces/pml'

# CJK font registration
# register font for simplified Chinese
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
# register font for Japanese
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
# register font for Korean
pdfmetrics.registerFont(UnicodeCIDFont('HYSMyeongJo-Medium'))

# Mapping HTML -> REPORTLAB
P_FORMAT = {'a': 'a', 'em': 'i', 'b': 'b', 'br': 'br', 'span': 'font',
            'sub': 'sub', 'img': 'img', 'i': 'i', 'big': 'font',
            'tt': 'font', 'p': 'para', 'code': 'font', 'u': 'u',
            'sup': 'super', 'small': 'font', 'strong': 'b'}

SPECIAL = ('a', 'br', 'img', 'span', 'sub', 'sup')
PHRASE = ('code', 'em', 'strong')
FONT_STYLE = ('b', 'big', 'i', 'small', 'tt')
DEPRECATED = ('u',)
INLINE = FONT_STYLE + PHRASE + SPECIAL + DEPRECATED

# ERROR MESSAGES
MSG_TAG_NOT_SUPPORTED = '(WW) %s: line %s tag "%s" is currently not supported.'
MSG_WARNING_DTD = '(WW) %s: line %s tag "%s" is unapproprieted here.'
MSG_ROW_ERROR = '(EE) Table : too many row at its line: %s'

HEADING = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')

EMPTY_TAGS = ('br', 'img', 'toc', 'pagebreak', 'pagenumber')



######################################################################
# Public API
######################################################################
def pmltopdf(document, path=None):
    """
    document: string buffer or open file descriptor
    path: the path of the document
    """

    # Input
    if isinstance(document, str):
        data = document
    else:
        # Try to get the path from the file
        if path is None and isinstance(document, FileType):
            path = document.name
        data = document.read()

    events = XMLParser(data, {None: pml_uri})

    if path:
        here = get_cwd().path
        prefix = here.resolve2(Path(path))
        stream = set_prefix(events, prefix, ns_uri=pml_uri)

    return make_pdf(events)


def stl_pmltopdf(document, namespace=freeze({}), path=None, mode='pdf'):
    """
    document: XMLFile, events, XMLParser, generator
    path: the path of the document
    """

    if isinstance(document, XMLFile):
        events = document.events
        # Try to get the path from the file
        if path is None and document.uri:
            path = str(document.uri.path)
    else:
        events = document

    if namespace:
        events = stl(events=events, namespace=namespace)

    if path:
        here = get_cwd().path
        prefix = here.resolve2(Path(path))
        events = set_prefix(events, prefix, ns_uri=pml_uri)

    if mode == 'events':
        return events
    elif mode == 'pdf':
        return make_pdf(events)
    raise ValueError, 'unexpected mode "%s"' % mode



######################################################################
# Public test API
######################################################################
def pmltopdf_test(document, path=None):
    """
    document: string buffer or open file descriptor
    path: the path of the document
    """

    # Input
    if isinstance(document, str):
        data = document
    else:
        # Try to get the path from the file
        if path is None and isinstance(document, FileType):
            path = document.name
        data = document.read()
        # Should we close the file descriptor ?
        document.close()

    events = XMLParser(data, {None: pml_uri})

    if path:
        here = get_cwd().path
        prefix = here.resolve2(Path(path))
        events = set_prefix(events, prefix, ns_uri=pml_uri)

    return document_stream(events, StringIO(), True)


def stl_pmltopdf_test(document, namespace=freeze({}), path=None):
    """
    document: XMLFile, events, XMLParser, generator
    path: the path of the document
    """

    if isinstance(document, XMLFile):
        events = document.events
        # Try to get the path from the file
        if path is None:
            path = str(document.uri.path)
    else:
        events = document

    if namespace:
        events = stl(events=events, namespace=namespace)

    if path:
        here = get_cwd().path
        prefix = here.resolve2(Path(path))
        events = set_prefix(events, prefix, ns_uri=pml_uri)

    return document_stream(events, StringIO(), True)


######################################################################
# Private API
######################################################################
def make_pdf(stream, is_test=False):
    """Make the PDF"""
    iostream = StringIO()
    document_stream(stream, iostream, is_test)

    return iostream.getvalue()


class Context(object):


    def __init__(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.init_base_style_sheet()
        self.image_not_found_path = get_abspath('missing.png')
        self.toc_place = None
        self.cpt_toc_ref = 0
        self.toc_high_level = 3
        self.current_object_path = []
        self.css = None
        css_file = get_abspath('html.css')
        self.add_css_from_file(css_file)
        self.anchor = []
        socket.setdefaulttimeout(10)
        self.list_anchor = []
        self.tag_stack = []
        self.style_tag_stack = []
        self.num_id = 0
        self.header = None
        # True if the header as been encapsulated inside a table
        self.header_as_table = False
        self.footer = None
        # True if the footer as been encapsulated inside a table
        self.footer_as_table = False
        self.current_page = 0
        self.number_of_pages = 0
        # set tag substution
        self.pagenumber = XMLContent.encode('#pagenumber/>')
        self.pagetotal = XMLContent.encode('#pagetotal/>')
        self.multibuild = False
        self.doc_attr = {'pagesize': A4} # FIXME Should be customizable


    def init_base_style_sheet(self):
        self.stylesheet = getSampleStyleSheet()
        # Add heading level 4, 5 and 6 like in html
        self.stylesheet.add(ParagraphStyle(name='Heading4',
                                           parent=self.stylesheet['h3'],
                                           fontSize=11),
                            alias='h4')
        self.stylesheet.add(ParagraphStyle(name='Heading5',
                                           parent=self.stylesheet['h4'],
                                           fontSize=10),
                            alias='h5')
        self.stylesheet.add(ParagraphStyle(name='Heading6',
                                           parent=self.stylesheet['h5'],
                                           fontSize=9),
                            alias='h6')
        self.stylesheet.add(ParagraphStyle(name='toctitle',
                                           parent=self.stylesheet['Normal'],
                                           fontSize=40))


    def get_base_style_sheet(self):
        return self.stylesheet


    def get_style(self, name):
        """
           Return the style corresponding to name or the style normal if it
           does not exist.
        """

        if self.stylesheet.has_key(name):
            return self.stylesheet[name]
        return self.stylesheet['Normal']


    def get_tmp_file(self):
        fd, filename = tempfile.mkstemp(dir=self.tmp_dir)
        return vfs.open(filename, 'w')


    def get_toc_anchor(self, tag_name, content):
        if not self.toc_high_level > tag_name[1]:
            ref = 'toc_' + str(self.cpt_toc_ref)
            self.cpt_toc_ref += 1
            content = '<a name="' + ref + '" />' + content
        return content


    def add_current_style(self, stylesheet_text):
        if self.css is None:
            self.css = css.CssStylesheet.from_css(stylesheet_text)
        else:
            tmp = css.CssStylesheet.from_css(stylesheet_text)
            self.css = self.css.merge(tmp)


    def add_style_attribute(self, data):
        if self.current_object_path[-1].find('#') < 0:
            str_id = '_attr_style_id_' + str(self.num_id)
            self.num_id += 1
            self.current_object_path[-1] += "#%s" % str_id
        data = '%s {%s}' % (self.current_object_path[-1], data)
        self.add_current_style(data)


    def add_css_from_file(self, filename):
        if vfs.exists(filename):
            data = vfs.open(filename).read()
            self.add_current_style(data)
        else:
            print u'(WW) CSS filename "%s" does not exist' % filename


    def get_css_props(self):
        if self.css is None:
            return {}
        else:
            path = ' '.join(self.current_object_path)
            return self.css.get_properties_str(path)


    def path_on_start_event(self, tag_name, attributes):
        if isinstance(tag_name, str):
            tag_path = tag_name
            o_id = attributes.get((None, 'id'), None)
            if o_id is not None:
                tag_path += '#%s' % o_id
            o_class = attributes.get((None, 'class'), None)
            if o_class is not None:
                tag_path += '.%s' % o_class
            self.current_object_path.append(tag_path)


    def path_on_end_event(self):
        self.current_object_path.pop()


    def check_image(self, path):
        if path in self.check_img_cache:
            return self.check_img_cache[path]
        data = check_image(path, self)
        self.check_img_cache[path] = data
        return data


    def has_header(self):
        return self.header != None


    def get_header(self):
        if self.header_as_table is False:
            self.header = [Table([[self.header]])]
            self.header_as_table = True
        return self.header


    def get_header_copy(self):
        return copy.deepcopy(self.header)


    def has_footer(self):
        return self.footer != None


    def get_footer(self):
        if self.footer_as_table is False:
            self.footer = [Table([[self.footer]])]
            self.footer_as_table = True
        return self.footer


    def get_footer_copy(self):
        return copy.deepcopy(self.footer)


    def del_tmp_dir(self):
        if vfs.exists(self.tmp_dir):
            vfs.remove(self.tmp_dir)



def document_stream(stream, pdf_stream, is_test=False):
    """
        stream : parser stream
        pdf_stream : reportlab write the pdf into pdf_stream.

        Childs : template, stylesheet, story
    """

    # Reportlab, HACK to prevent too many open files error with inline images
    previous_imageReaderFlags = None
    if hasattr(reportlab.rl_config, 'imageReaderFlags'):
        previous_imageReaderFlags = reportlab.rl_config.imageReaderFlags
        reportlab.rl_config.imageReaderFlags = -1

    story = []
    context = Context()
    informations = {}

    state = 0
    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            context.path_on_start_event(tag_name, attributes)
            if tag_name == 'html':
                if state == 0:
                    state = 1
                else:
                    print MSG_WARNING_DTD % ('document', line_number,
                                             tag_name)
                continue
            elif tag_name == 'head':
                informations = head_stream(stream, tag_name, attributes,
                                           context)
            elif tag_name == 'header':
                # the story is pushed in a table (1x1) in order to know its
                # size
                context.header = paragraph_stream(stream, tag_name,
                                                  attributes, context)
            elif tag_name == 'body':
                if state == 1:
                    state = 2
                    story += body_stream(stream, tag_name, attributes,
                                         context)
                else:
                    print MSG_WARNING_DTD % ('document', line_number,
                                             tag_name)
                continue
            elif tag_name == 'footer':
                # the story is pushed in a table (1x1) in order to know its
                # size
                context.footer = paragraph_stream(stream, tag_name,
                                                  attributes, context)
            else:
                print MSG_TAG_NOT_SUPPORTED % ('document', line_number,
                                               tag_name)
                # unknown tag
        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            context.path_on_end_event()
            if tag_name == 'html':
                break

    #### BUILD PDF ####
    if is_test == True:
        test_data = list(story), context.get_base_style_sheet()
    if context.multibuild:
        if context.toc_place is not None:
            # Create platypus toc
            place = context.toc_place
            story = story[:place] + create_toc(context) + story[place:]

        # Create doc template
        doc = MyDocTemplate(pdf_stream, context, **context.doc_attr)
    else:
        doc = MySimpleDocTemplate(pdf_stream, context, **context.doc_attr)

    # Record PDF informations
    doc.author = informations.get('author', '')
    doc.title = informations.get('title', '')
    doc.subject = informations.get('subject', '')
    doc.keywords = informations.get('keywords', [])

    if context.multibuild:
        doc.multiBuild(story)
    else:
        doc.build(story)

    # Reportlab, HACK to prevent too many open files error with inline images
    if previous_imageReaderFlags:
        reportlab.rl_config.imageReaderFlags = previous_imageReaderFlags

    # Remove temporary directory
    context.del_tmp_dir()

    if is_test == True:
        return test_data


def head_stream(stream, _tag_name, _attributes, context):
    informations = {}
    names = ('author', 'copyright', 'date', 'keywords', 'subject')
    content = []
    while True:
        event, value, line_number = stream_next(stream)
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            content = []
            if tag_name == 'meta':
                if exist_attribute(attributes, ['name']):
                    name = attributes.get((None, 'name'))
                    if exist_attribute(attributes, ['content']):
                        if name in names:
                            attr_content = attributes.get((None, 'content'))
                            if name == 'keywords':
                                attr_content = attr_content.split(',')
                                keywords = ''.join(attr_content).split(' ')
                                informations[name] = keywords
                            else:
                                informations[name] = normalize(attr_content)
            elif tag_name == 'title':
                continue
            elif tag_name == 'link':
                if exist_attribute(attributes, ['rel', 'type', 'href']):
                    rel = attributes.get((None, 'rel'))
                    type = attributes.get((None, 'type'))
                    if rel == 'stylesheet' and type == 'text/css':
                        context.add_css_from_file(attributes[(None, 'href')])
            elif tag_name == 'style':
                continue
            else:
                print MSG_TAG_NOT_SUPPORTED % ('document', line_number,
                                               tag_name)

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == _tag_name:
                context.path_on_end_event()
                return informations
            elif tag_name == 'style':
                context.add_current_style(' '.join(content))
            elif tag_name == 'title':
                informations[tag_name] = normalize(' '.join(content))

        #### TEXT ELEMENT ####
        elif event == TEXT:
            content.append(value)


def body_stream(stream, _tag_name, _attributes, context):
    """
        stream : parser stream
    """

    body_style = context.get_css_props()
    context.doc_attr.update(build_frame_style(context, body_style))
    temp_story = None
    story = []
    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break

        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            context.path_on_start_event(tag_name, attributes)
            if tag_name in ('p', 'pre', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                story.extend(paragraph_stream(stream, tag_name, attributes,
                                              context))
            elif tag_name == 'hr':
                story.append(hr_stream(stream, tag_name, attributes, context))
            elif tag_name == 'img':
                widget = img_stream(stream, tag_name, attributes, context)
                if widget:
                    story.append(widget)
            elif tag_name == 'a':
                # FIXME anchor are stored in stack and it pop in the nextest
                # paragraph
                attrs = build_attributes(tag_name, attributes, context)
                context.anchor.append(build_start_tag(tag_name, attrs))
            elif tag_name in ('ol', 'ul'):
                story.extend(list_stream(stream, tag_name, attributes,
                                         context))
            elif tag_name == 'dl':
                story.extend(def_list_stream(stream, tag_name, attributes,
                                             context))
            elif tag_name == 'pagebreak':
                story.append(PageBreak())
            elif tag_name == 'table':
                story.append(table_stream(stream, tag_name, attributes,
                                          context))
            elif tag_name == 'toc':
                level = attributes.get((None, 'level'), None)
                if level is not None:
                    context.toc_high_level = get_int_value(level)
                context.toc_place = len(story)
                context.multibuild = True
            elif tag_name == 'nobreak':
                temp_story = story
                story = []
            elif tag_name == 'div':
                style = context.get_css_props()
                div_attrs = build_frame_style(context, style, attributes)
                story.append(Div(body_stream(stream, tag_name, attributes,
                                             context), frame_attrs=div_attrs))
            elif tag_name in PHRASE:
                story.extend(paragraph_stream(stream, tag_name, attributes,
                                              context))
            else:
                print MSG_TAG_NOT_SUPPORTED % ('document', line_number,
                                               tag_name)
                # unknown tag

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            context.path_on_end_event()
            if tag_name == _tag_name:
                break
            elif tag_name == 'nobreak':
                # raise LayoutError if too big
                if temp_story:
                    temp_story.append(Table([[story]]))
                story = temp_story
                temp_story = None
    return story


def paragraph_stream(stream, elt_tag_name, elt_attributes, context,
                     prefix=None):
    """
        stream : parser stream
    """

    content = []
    cpt = 0
    has_content = False
    is_not_paragraph = (elt_tag_name != 'p')
    is_not_pre = (elt_tag_name != 'pre')
    is_footer = (elt_tag_name == 'footer')

    story = []
    start_tag = True
    end_tag = False
    style_p = context.get_css_props()

    style_attr_value = elt_attributes.get((None, 'style'))
    skip = False
    place = 0
    if prefix is not None:
        content.append(prefix)

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            context.path_on_start_event(tag_name, attributes)
            if is_not_paragraph:
                skip = True
                place = len(story)
                # TODO ? Merge with body_stream?
                if tag_name in ('p', 'pre', 'h1', 'h2', 'h3', 'h4', 'h5',
                                'h6'):
                    story.extend(paragraph_stream(stream, tag_name,
                                                  attributes, context))
                elif tag_name == 'hr':
                    story.append(hr_stream(stream, tag_name, attributes,
                                           context))
                elif tag_name in ('ol', 'ul'):
                    story.extend(list_stream(stream, tag_name, attributes,
                                             context))
                elif tag_name == 'dl':
                    story.extend(def_list_stream(stream, tag_name, attributes,
                                                 context))
                elif tag_name == 'table':
                    story.append(table_stream(stream, tag_name, attributes,
                                              context))
                else:
                    skip = False
            if skip:
                if content:
                    elt = (elt_tag_name, elt_attributes)
                    para = create_paragraph(context, elt, content, style_p)
                    story.insert(place, para)
                    content = []
                    has_content = False
            else:
                while context.anchor:
                    content.append(context.anchor.pop())

                if tag_name in INLINE:
                    if tag_name in P_FORMAT.keys():
                        start_tag = True
                        attrs = build_attributes(tag_name, attributes,
                                                 context)
                        if cpt or has_content:
                            content[-1] += build_start_tag(tag_name, attrs)
                        else:
                            content.append(build_start_tag(tag_name, attrs))
                            has_content = True
                        for tag, attrs in context.tag_stack[-1]:
                            content[-1] += build_start_tag(tag, attrs)
                        cpt += 1
                    else:
                        print MSG_TAG_NOT_SUPPORTED % ('document',
                                                       line_number, tag_name)
                        # unknown tag
                elif tag_name == 'pagenumber':
                    content.append(context.pagenumber)
                elif tag_name == 'pagetotal':
                    context.multibuild = True
                    content.append(context.pagetotal)
                else:
                    print MSG_WARNING_DTD % ('document', line_number,
                                             tag_name)

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            context.path_on_end_event()
            if is_not_pre:
                if content:
                    # spaces must be ignore if character before it is '\n'
                    tmp = content[-1].rstrip(' \t')
                    if len(tmp):
                        if tmp[-1] == '\n':
                            content[-1] = tmp.rstrip('\n')
            if tag_name == elt_tag_name:
                if content and content != ['']: # Avoid empty paragraph
                    elt = (elt_tag_name, elt_attributes)
                    para = create_paragraph(context, elt, content, style_p)
                    story.append(para)
                return story
            elif tag_name in P_FORMAT.keys():
                if tag_name in EMPTY_TAGS:
                    has_content = False
                cpt -= 1
                end_tag = True
                while context.tag_stack[-1]:
                    tag, attrib = context.tag_stack[-1].pop()
                    content[-1] += get_end_tag(None, P_FORMAT.get(tag, 'b'))
                context.tag_stack.pop()
                content[-1] += get_end_tag(None, P_FORMAT.get(tag_name, 'b'))

        #### TEXT ELEMENT ####
        elif event == TEXT:
            if len(value) > 0:
                value = XMLContent.encode(value)
                if is_not_pre:
                    # alow to write :
                    # <para><u><i>foo</i> </u></para>
                    # spaces must be ignore after a start tag if the next
                    # character is '\n'
                    if start_tag:
                        if value[0] == '\n':
                            value = value.lstrip('\n\t ')
                            if not len(value):
                                continue
                        start_tag = False
                if has_content:
                    if content[-1].endswith('<br/>'):
                        # <p>
                        #   foo          <br />
                        #     bar   <br />     team
                        # </p>
                        # equal
                        # <p>foo <br />bar <br />team</p>
                        value = value.lstrip()
                        content[-1] += value
                        end_tag = False
                    elif  end_tag or cpt:
                        content[-1] += value
                        end_tag = False
                    else:
                        content.append(value)
                else:
                    has_content = True
                    content.append(value)


def hr_stream(stream, _tag_name, _attributes, context):
    """
        Create a hr widget.

        stream : parser stream
    """

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            print MSG_WARNING_DTD % ('document', line_number, tag_name)
        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            css_attributes = context.get_css_props()
            context.path_on_end_event()
            if tag_name == _tag_name:
                return create_hr(_attributes, css_attributes, context)


def img_stream(stream, _tag_name, _attributes, context):
    attrs = build_img_attributes(_attributes, context)
    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            print MSG_WARNING_DTD % ('document', line_number, tag_name)
        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            context.path_on_end_event()
            if tag_name == _tag_name:
                return create_img(attrs, context)


def list_stream(stream, _tag_name, attributes, context, id=0):
    """
        stream : parser stream
    """

    # TODO : default value must be in default css
    INDENT_VALUE = 1 * cm
    story = [Indenter(left=INDENT_VALUE)]
    strid = str(id)
    prefix = ["<seqDefault id='%s'/><seqReset id='%s'/>" % (strid, strid)]
    has_content = False
    li_state = 0 # 0 -> outside, 1 -> inside
    attrs = {}
    bullet = None
    cpt = 0
    start_tag = True
    end_tag = False

    if _tag_name == 'ul':
        bullet = get_bullet(attributes.get((None, 'type'), 'disc'))
    else:
        bullet = "<bullet bulletIndent='-0.4cm'><seq id='%s'>.</bullet>"
        bullet = bullet % strid
        if exist_attribute(attributes, ['type']):
            attrs['type'] = attributes.get((None, 'type'))
            seq = "<seqFormat id='%s' value='%s'/>" % (strid, attrs['type'])
            prefix.append(seq)
        else:
            prefix.append("<seqFormat id='%s' value='1'/>" % strid)
    pref = "<seqDefault id='%s'/>"

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            context.path_on_start_event(tag_name, attributes)
            if tag_name in ('ul', 'ol'):
                prefix = [pref % strid]
                story += list_stream(stream, tag_name, attributes,
                                     context, id+1)
            elif tag_name == 'li':
                prefix.append(bullet)
                para = paragraph_stream(stream, tag_name, attributes,
                                        context, ''.join(prefix))
                story.extend(para)
                prefix = []
            else:
                print MSG_WARNING_DTD % ('document', line_number, tag_name)

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            context.path_on_end_event()
            if tag_name in ('ul', 'ol'):
                story.append(Indenter(left=-INDENT_VALUE))
                return story


def def_list_stream(stream, _tag_name, attributes, context):
    """
        stream : parser stream
    """

    INDENT_VALUE = 1 * cm
    story = []
    has_content = False

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            context.path_on_start_event(tag_name, attributes)
            if tag_name == 'dt':
                para = paragraph_stream(stream, tag_name, attributes, context)
                story.extend(para)
            elif tag_name == 'dd':
                story.append(Indenter(left=INDENT_VALUE))
                para = paragraph_stream(stream, tag_name, attributes, context)
                story.extend(para)
                story.append(Indenter(left=-INDENT_VALUE))
            else:
                print MSG_WARNING_DTD % ('document', line_number, tag_name)

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            context.path_on_end_event()
            if tag_name == _tag_name:
                return story


def table_stream(stream, _tag_name, attributes, context):
    content = Table_Content(context)
    start = (0, 0)
    stop = (-1, -1)
    content.add_attributes(get_align(attributes))

    # Get the CSS style
    style_css = context.get_css_props()
    content.extend_style(get_table_style(style_css, attributes, start, stop))

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            context.path_on_start_event(tag_name, attributes)
            if tag_name == 'tr':
                content = tr_stream(stream, tag_name, attributes,
                                    content, context)
                content.next_line()
            elif tag_name == 'thead':
                if len(content.content):
                    print '(WW) Data are already pushed'
            else:
                print MSG_WARNING_DTD % ('document', line_number, tag_name)

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            context.path_on_end_event()
            if tag_name == _tag_name:
                return content.create()
            elif tag_name == 'thead':
                content.thead()


def tr_stream(stream, _tag_name, attributes, table, context):
    x, y = table.get_current()
    style_css = context.get_css_props()
    style = get_table_style(style_css, attributes, (0, y), (-1, y))
    table.extend_style(style)

    stop = None

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            if tag_name in ('td', 'th'):
                context.path_on_start_event(tag_name, attributes)
                style_css = context.get_css_props()
                cont = paragraph_stream(stream, tag_name, attributes, context)
                table.push_content(cont)
                if exist_attribute(attributes, ['width']):
                    width = attributes.get((None, 'width'))
                    table.add_colWidth(width)
                if exist_attribute(attributes, ['height']):
                    width = attributes.get((None, 'height'))
                    table.add_lineHeight(width)
                if exist_attribute(attributes, ['colspan', 'rowspan'],
                                   at_least=True):
                    rowspan = attributes.get((None, 'rowspan'))
                    colspan = attributes.get((None, 'colspan'))
                    stop = table.process_span(rowspan, colspan)
                else:
                    stop = table.get_current()
                start = (table.current_x, table.current_y)
                style = get_table_style(style_css, attributes, start, stop)
                table.extend_style(style)
                table.next_cell()
            else:
                print MSG_WARNING_DTD % ('document', line_number, tag_name)

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            context.path_on_end_event()
            tag_uri, tag_name = value
            if tag_name == _tag_name:
                return table


##############################################################################
# Reportlab widget                                                           #
##############################################################################
def create_paragraph(context, element, content, style_css = {}):
    """
        Create a reportlab paragraph widget.
    """

    # Now, we strip each value in content before call create_paragraph
    # content = ['Hello', '<i>how are</i>', 'you?']
    # Another choice is to strip the content (1 time) here
    # content = ['  Hello\t\', '\t<i>how are</i>', '\tyou?']

    style, bulletText = build_paragraph_style(context, element, style_css)
    start_tags = end_tags = ''
    if context.style_tag_stack:
        for tag in context.style_tag_stack:
            start_tags += '<%s>' % tag
        while context.style_tag_stack:
            end_tags += get_end_tag(None, context.style_tag_stack.pop())
    if element[0] == 'pre':
        content = join_content(content)
        content = start_tags + content + end_tags
        widget = XPreformatted(content, style)
    else:
        # DEBUG
        #print 0, content
        content = normalize(' '.join(content))
        if element[0] in HEADING:
            content = context.get_toc_anchor(element[0], content)
        content = start_tags + content + end_tags
        content = '<para>%s</para>' % content
        #print 1, content
        widget = Paragraph(content, style, context, bulletText)
    return widget


def create_toc(context):
    text_title = ['Contents']
    title = create_paragraph(context, ('toctitle', {}), text_title)
    story = [title,]
    # Create styles to be used for TOC entry lines
    # for headers on differnet levels.
    tocLevelStyles = []
    d, e = tableofcontents.delta, tableofcontents.epsilon
    for i in range(context.toc_high_level):
        tocLevelStyles.append(makeTocHeaderStyle(i, d, e))
    toc = TableOfContents()
    toc.levelStyles = tocLevelStyles
    story.append(toc)
    return story


def create_hr(attributes, css_attributes, context):
    """
        Create a reportlab hr widget
    """
    attrs = get_hr_style(css_attributes, attributes)

    return HRFlowable(**attrs)


def create_img(attributes, context, check_dimension=False):
    """
        Create a reportlab image widget.
        If check_dimension is true and the width and the height attributes
        are not set we return None
    """
    filename = attributes.get((None, 'src'), None)
    width = format_size(attributes.get((None, 'width'), None))
    height = format_size(attributes.get((None, 'height'), None))
    if filename is None:
        print u'(WW) Filename is None'
        return None

    if check_dimension and width == None and height == None:
        print u'(WW) Cannot add an image inside a td without predefined size'
        return None

    try:
        I = build_image(filename, width, height, context)
        return I
    except IOError, msg:
        print msg
        filename = context.image_not_found_path
        I = build_image(filename, width, height, context)
        return I
    except Exception, msg:
        print msg
        return None


def build_image(filename, width, height, context):
    # determines behavior of both arguments(width, height)
    kind = 'direct'
    file_path, size = check_image(filename, context)
    x, y = size
    #FIXME not like html
    if height or width:
        if isinstance(width, str) and width.endswith('%'):
            width = get_int_value(width[:-1])
            if not height:
                height = width
            kind = '%'
        if isinstance(height, str) and height.endswith('%'):
            height = get_int_value(height[:-1])
            if not width:
                width = height
            kind = '%'
        if not (height and width):
            if height:
                width = height * x / y
            elif width:
                height = width * y / x
    return Image(file_path, width, height, kind)



class Table_Content(object):
    """
        Allow to add, to manipulate table content and to create platypus
        widget
    """


    def __init__(self, context, parent_style=None):
        self.content = []
        """
        [['foo'], ['bar']] => size[1,2]
        [['foo', 'bar']] => size[2,1]
        """
        self.size = [0, 0]
        self.attrs = {}
        # Cell vertical alignment
        self.style = [('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]
        # Span in first line are stocked in stack
        self.span_stack = []
        # current cell
        self.current_x = 0
        self.current_y = 0
        self.colWidths = []
        self.rowHeights = []
        self.context = context
        self.split = 0


    # Create platypus object
    def create(self):
        l = len(self.rowHeights)
        if l:
            none_list = [ None for x in xrange(l, self.current_y) ]
            self.rowHeights.extend(none_list)
        else:
            self.rowHeights = None
        return Table(self.content, style=self.style, colWidths=self.colWidths,
                     rowHeights=self.rowHeights, repeatRows=self.split,
                     **self.attrs)


    # Get current position in table
    def get_current(self):
        return (self.current_x, self.current_y)


    def next_line(self):
        # Add span if first line
        if not self.current_y:
            while self.span_stack:
                start, stop = self.span_stack.pop()
                self.add_span(start, stop)
            l = len(self.colWidths)
            none_list = [ None for x in xrange(l, self.current_x) ]
            self.colWidths.extend(none_list)
        # Next line
        self.current_x = 0
        self.current_y += 1


    def next_cell(self):
        self.current_x += 1


    def push_content(self, value, x=None, y=None):
        # if x or y is undefineted, x and y are set to default value
        if x == None or y == None:
            x = self.current_x
            y = self.current_y
        if y:
            if x >= self.size[0]:
                current_line = self.current_y + 1
                print MSG_ROW_ERROR % current_line
                return
            elif y >= self.size[1]:
                self.create_table_line()
            if self.content[y][x] == None:
                self.next_cell()
                self.push_content(value, x+1, y)
                return
            self.content[y][x] = value
        else:
            if self.size[0]:
                if x < self.size[0] and self.content[y][x] == None:
                    x += 1
                    self.push_content(value, x, y)
                    return
            else:
                self.content.append([])
                # increment the line number
                self.size[1] += 1
            self.content[0].append(value)
            self.size[0] += 1


    def thead(self):
        self.split = self.current_y


    # Attributes
    def add_attributes(self, attributes):
        self.attrs.update(attributes)


    def extend_style(self, style):
        self.style.extend(style)


    def process_span(self, rowspan, colspan):
        rtmp = get_int_value(rowspan) - 1
        ctmp = get_int_value(colspan) - 1
        col = self.current_x
        row = self.current_y
        stop = None
        if rtmp > 0:
            row += rtmp
        if ctmp > 0:
            col += ctmp
            if self.current_y and col >= self.size[0]:
                current_line = self.current_y + 1
                print MSG_ROW_ERROR % current_line
                col = self.size[0] - 1
        if not self.current_y:
            if ctmp > 0:
                self.span_stack.append(((self.current_x, self.current_y),
                                        (col, row)))
                self.content[0].extend([ None for x in xrange(ctmp) ])
                self.size[0] += ctmp
                self.current_x += ctmp - 1
                return (col, row)
            if rtmp > 0:
                self.span_stack.append(((self.current_x, self.current_y),
                                        (col, row)))
                return (col, row)
        self.add_span((self.current_x, self.current_y), (col, row))
        return (col, row)


    # Set colomn and line size
    def add_colWidth(self, value):
        list_length = len(self.colWidths)
        platypus_value = format_size(value)
        if not self.current_y and list_length <= self.current_x:
            none_list = [ None for x in xrange(list_length, self.current_x+1) ]
            self.colWidths.extend(none_list)

        # Colspan one the first cell
        # FIXME To improve
        if list_length <= self.current_x:
            self.colWidths.extend([None])

        if self.colWidths[self.current_x] is None\
            or platypus_value > self.colWidths[self.current_x]:
            self.colWidths[self.current_x] = platypus_value


    def add_lineHeight(self, value):
        list_length = len(self.rowHeights)
        platypus_value = format_size(value)
        if list_length <= self.current_y:
            none_list = [ None for y in xrange(list_length, self.current_y+1) ]
            self.rowHeights.extend(none_list)
        if self.rowHeights[self.current_y] is None\
            or platypus_value > self.rowHeights[self.current_y]:
            self.rowHeights[self.current_y] = platypus_value


    # Internal
    def create_table_line(self):
        line = []
        line.extend([ 0 for x in xrange(self.size[0]) ])
        self.content.append(line)
        self.size[1] += 1


    def add_span(self, start, stop):
        self.style.append(('SPAN', start, stop))
        st = start[1]
        if not st:
            if st >= start[1]:
                st += 1
            else:
                return
        for y in xrange(st, stop[1] + 1):
            for x in xrange(start[0], stop[0] + 1):
                if x != start[0] or y != start[1]:
                    self.push_content(None, x, y)



##############################################################################
# tag attributes
##############################################################################
def build_attributes(tag_name, attributes, context):
    context.tag_stack.append([])
    style_attr_value = attributes.get((None, 'style'))
    if style_attr_value:
        context.add_style_attribute(style_attr_value)
    style_css = context.get_css_props()
    build_inline_style(context, tag_name, style_css)

    if tag_name == 'a':
        attrs = build_anchor_attributes(attributes, context)
    elif tag_name == 'big':
        attrs = {(None, 'size'): font_value('120%')}
    elif tag_name == 'img':
        attrs = build_img_attributes(attributes, context)
    elif tag_name == 'small':
        attrs = {(None, 'size'): font_value('80%')}
    elif tag_name in ('code', 'tt'):
        attrs = {(None, 'face'): get_font_name('monospace')}
    else:
        attrs = {}
    return attrs


def build_anchor_attributes(attributes, context):
    flag = False
    attrs = {}
    if exist_attribute(attributes, ['href']):
        flag = True
        href = XMLContent.encode(attributes.get((None, 'href')))
        # Reencode the entities because the a tags
        # are decoded again by the reportlab para parser.
        if href.startswith('#'):
            ref = href[1:]
            if ref not in context.list_anchor:
                attrs2 = {(None, 'name'): ref}
                context.tag_stack[-1].append(('a',  attrs2))
        attrs[(None, 'href')] = href
    if exist_attribute(attributes, ['id', 'name'], at_least=True):
        name = attributes.get((None, 'id'), attributes.get((None, 'name')))
        if name:
            if flag:
                attrs2 = {(None, 'name'): name}
                context.tag_stack[-1].append(('a',  attrs2))
            else:
                flag = True
                attrs[(None, 'name')] = name
            context.list_anchor.append(name)
    if not flag:
        attrs[(None, 'name')] = '_invalid_syntax_:('
    return attrs


def build_img_attributes(attributes, context):
    attrs = {}
    for key, attr_value in attributes.iteritems():
        key = key[1]
        if key == 'src':
            file_path, size = check_image(attr_value, context)
            attrs[(None, 'src')] = file_path
        elif key == 'width':
            attrs[(None, 'width')] = format_size(attr_value)
        elif key == 'height':
            attrs[(None, 'height')] = format_size(attr_value)

    exist_width = exist_attribute(attrs, ['width'])
    exist_height = exist_attribute(attrs, ['height'])
    if exist_width or exist_height:
        width, height = size
        width = width * 1.0
        height = height * 1.0
        tup_width = (None, 'width')
        tup_height = (None, 'height')
        # Calculate sizes to resize
        if exist_width:
            element = attrs[tup_width]
            if isinstance(element, str) and element.endswith('%'):
                value = get_int_value(element[:-1])
                attrs[tup_width] = pc_float(value, width)
            if not exist_height:
                attrs[tup_height] = round(attrs[tup_width] * height / width)
        if exist_height:
            element = attrs[tup_height]
            if isinstance(element, str) and element.endswith('%'):
                value = get_int_value(element[:-1])
                attrs[tup_height] = pc_float(value, height)
            if not exist_width:
                attrs[tup_width] = round(attrs[tup_height] * width / height)
    return attrs


##############################################################################
# Internal Functions                                                         #
##############################################################################
def build_start_tag(tag_name, attrs=freeze({})):
    """
        Create the XML start tag from his name and his attributes
        span => font (map)
    """
    tag = P_FORMAT.get(tag_name, 'b')
    attr_str = ''.join([' %s="%s"' % (key[1], attrs[key])
                            for key in attrs.keys()])
    a_is_empty = tag_name == 'a' and exist_attribute(attrs, ['name'])
    if tag_name in EMPTY_TAGS or a_is_empty:
        return '<%s%s/>' % (tag, attr_str)
    else:
        return '<%s%s>' % (tag, attr_str)


def get_bullet(type, indent='-0.4cm'):

    types = {'disc': '\xe2\x80\xa2',
             'square': '\xe2\x80\xa2',
             'circle': '\xe2\x80\xa2'}

    s = '<bullet bulletIndent="%s" font="Symbol">%s</bullet>'
    bullet = s % (indent, types.get(type, types['disc']))
    return bullet
