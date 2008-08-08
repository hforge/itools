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
import tempfile
import socket

# Import from itools
from itools import get_abspath
from itools.datatypes import XMLContent
from itools.stl import set_prefix
from itools.uri import Path
from itools.uri.uri import get_cwd
from itools.vfs import vfs
from itools.xml import (XMLParser, START_ELEMENT, END_ELEMENT, TEXT,
                        get_start_tag, get_end_tag)
import itools.http

# Internal import
from style import (build_paragraph_style, get_table_style,
                   makeTocHeaderStyle, get_align)
from utils import (FONT, URI, check_image, exist_attribute, font_value,
                   format_size, get_color, get_color_as_hexa, get_int_value,
                   normalize, stream_next)

#Import from the reportlab Library
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import (getSampleStyleSheet, ParagraphStyle)
from reportlab.platypus import (Paragraph, SimpleDocTemplate, XPreformatted,
                                PageBreak, Image, Indenter, Table)
from reportlab.platypus import tableofcontents
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.platypus.flowables import HRFlowable
from reportlab.platypus.frames import Frame
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.units import cm

#import the graphication css parser
import css

# Mapping HTML -> REPORTLAB
P_FORMAT = {'a': 'a', 'em': 'i', 'b': 'b', 'span': 'font', 'sub': 'sub',
            'img': 'img', 'i': 'i', 'big': 'font', 'tt': 'font', 'p': 'para',
            'code': 'font', 'u': 'u', 'sup': 'super', 'small': 'font',
            'strong': 'b'}

SPECIAL = ('a', 'br', 'img', 'span', 'sub', 'sup')
PHRASE = ('code', 'em', 'strong')
FONT_STYLE = ('b', 'big', 'i', 'small', 'tt')
DEPRECATED = ('u',)
INLINE = FONT_STYLE + PHRASE + SPECIAL + DEPRECATED

PADDINGS = ('LEFTPADDING', 'RIGHTPADDING', 'BOTTOMPADDING', 'TOPPADDING')

# ERROR MESSAGES
MSG_TAG_NOT_SUPPORTED = '%s: line %s tag "%s" is currently not supported.'
MSG_WARNING_DTD = '%s: line %s tag "%s" is unapproprieted here.'
MSG_ROW_ERROR = 'Table error : too many row at its line: %s'

HEADING = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')



class Context(object):


    def __init__(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.init_base_style_sheet()
        v_globals = globals()
        self.image_not_found_path = get_abspath(v_globals, 'missing.png')
        self.toc_place = None
        self.cpt_toc_ref = 0
        self.toc_high_level = 3
        self.current_object_path = []
        self.css = None
        css_file = get_abspath(v_globals, 'html.css')
        self.add_css_from_file(css_file)
        self.anchor = []
        socket.setdefaulttimeout(10)


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


    def add_css_from_file(self, filename):
        if vfs.exists(filename):
            data = vfs.open(filename).read()
            self.add_current_style(data)


    def get_css_props(self):
        if self.css is None:
            return {}
        else:
            path = ' '.join(self.current_object_path)
            return self.css.get_properties_str(path)


    def path_on_start_event(self, tag_name, attributes):
        if isinstance(tag_name, str):
            tag_path = tag_name
            o_id = attributes.get((URI, 'id'), None)
            if o_id is not None:
                tag_path += '#%s' % o_id
            o_class = attributes.get((URI, 'class'), None)
            if o_class is not None:
                tag_path += '.%s' % o_class
            self.current_object_path.append(tag_path)


    def path_on_end_event(self):
        self.current_object_path.pop()


    def __del__(self):
        vfs.remove(self.tmp_dir)



def rml2topdf_test(value, raw=False):
    """
      If raw is False, value is the test file path
      otherwise it is the string representation of a xml document
    """

    namespaces = {None: URI}
    if raw is False:
        input = vfs.open(value)
        data = input.read()
        input.close()
    else:
        data = value
    stream = XMLParser(data, namespaces)
    if raw is False:
        here = get_cwd().path
        prefix = here.resolve2(Path(value))
        stream = set_prefix(stream, prefix)
    return document_stream(stream, StringIO(), 'test', True)


def rml2topdf(filename):
    """
      Main function: produces a pdf file from a html-like xml document

      filename: source file
    """

    iostream = StringIO()
    namespaces = {None: URI}
    fd = vfs.open(filename)
    stream = XMLParser(fd.read(), namespaces)
    fd.close()
    here = get_cwd().path
    prefix = here.resolve2(Path(filename))
    stream = set_prefix(stream, prefix)
    document_stream(stream, iostream, filename, False)
    return iostream.getvalue()



class MyDocTemplate(BaseDocTemplate):
    """
        The document template used for all PDF documents.
    """


    def __init__(self, toc_high_level,  filename, **kw):
        BaseDocTemplate.__init__(self, filename, **kw)
        self.toc_index = 0
        frame1 = Frame(self.leftMargin, self.bottomMargin, self.width,
                       self.height, id='normal')
        template_attrs = {'id': 'now', 'frames': [frame1],
                          'pagesize': kw['pagesize']}
        page_template = PageTemplate(**template_attrs)
        self.addPageTemplates([page_template])
        self.toc_high_level = toc_high_level


    def _get_heading_level(self, name):
        if name.startswith('Heading'):
            return int(name[7:])
            # Heading0 -> h1
        elif name[0] == 'h' and len(name) == 2:
            # h1~h6
            return int(name[1:]) - 1
        else:
            return None


    def _allSatisfied(self):
        status = BaseDocTemplate._allSatisfied(self)
        self.toc_index = 0
        return status


    def afterFlowable(self, flowable):
        "Registers TOC entries and makes outline entries."

        if flowable.__class__.__name__ == 'Paragraph':
            style_name = flowable.style.name
            level = self._get_heading_level(style_name)
            if level is not None and level < self.toc_high_level:
                # Register TOC entries.
                text = flowable.getPlainText()
                pageNum = self.page
                # Hook the text content by adding a link
                content = '<para><a href="toc_%s">%s</a></para>'
                content = content % (self.toc_index, text)
                self.toc_index += 1
                self.notify('TOCEntry', (level, content, pageNum))

                # Add PDF outline entries (not really needed/tested here).
                key = str(hash(flowable))
                c = self.canv
                c.bookmarkPage(key)
                c.addOutlineEntry(text, key, level=level, closed=0)



def document_stream(stream, pdf_stream, document_name, is_test=False):
    """
        stream : parser stream
        pdf_stream : reportlab write the pdf into pdf_stream.
        document_name : name of the source file

        Childs : template, stylesheet, story
    """

    stack = []
    story = []
    context = Context()
    state = 0
    informations = {}
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
            elif tag_name == 'body':
                if state == 1:
                    state = 2
                    story += body_stream(stream, tag_name, attributes,
                                         context)
                else:
                    print MSG_WARNING_DTD % ('document', line_number,
                                             tag_name)
                continue
            else:
                print MSG_TAG_NOT_SUPPORTED % ('document', line_number,
                                               tag_name)
                # unknown tag
                stack.append((tag_name, attributes))
        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            context.path_on_end_event()
            if tag_name == 'html':
                break
            if tag_name == 'head':
                continue
            else:
                # unknown tag
                stack.pop()

    #### BUILD PDF ####
    if is_test == True:
        test_data = list(story), context.get_base_style_sheet()

    if context.toc_place is not None:
        # Create platypus toc
        place = context.toc_place
        story = story[:place] + create_toc(context) + story[place:]

        # Create doc template
        doc = MyDocTemplate(context.toc_high_level, pdf_stream,
                            pagesize=LETTER)
    else:
        doc = SimpleDocTemplate(pdf_stream, pagesize=LETTER)

    doc.author = informations.get('author', '')
    doc.title = informations.get('title', '')
    doc.subject = informations.get('subject', '')
    doc.keywords = informations.get('keywords', [])

    if context.toc_place is not None:
        doc.multiBuild(story)
    else:
        doc.build(story)

    if is_test == True:
        return test_data


def head_stream(stream, _tag_name, _attributes, context):
    informations = {}
    names = ('author', 'copyright', 'date', 'keywords', 'subject')
    content = []
    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            content = []
            if tag_name == 'meta':
                if exist_attribute(attributes, ['name']):
                    name = attributes.get((URI, 'name'))
                    if exist_attribute(attributes, ['content']):
                        if name in names:
                            attr_content = attributes.get((URI, 'content'))
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
                    rel = attributes.get((URI, 'rel'))
                    type = attributes.get((URI, 'type'))
                    if rel == 'stylesheet' and type == 'text/css':
                        context.add_css_from_file(attributes[(URI, 'href')])
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
            elif tag_name == 'meta':
                continue
            else:
                print MSG_TAG_NOT_SUPPORTED % ('document', line_number,
                                               tag_name)
                # unknown tag

        #### TEXT ELEMENT ####
        elif event == TEXT:
            content.append(value)


def body_stream(stream, _tag_name, _attributes, context):
    """
        stream : parser stream
    """

    story = []
    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break

        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            context.path_on_start_event(tag_name, attributes)
            if tag_name in ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                story.extend(paragraph_stream(stream, tag_name, attributes,
                                              context))
            elif tag_name == 'pre':
                story.append(pre_stream(stream, tag_name, attributes,
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
                context.anchor.append(build_start_tag(tag_name, attributes))
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
                level = attributes.get((URI, 'level'), None)
                if level is not None:
                    context.toc_high_level = get_int_value(level)
                context.toc_place = len(story)
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
            elif tag_name in ('toc', 'pagebreak'):
                continue
            else:
                print MSG_TAG_NOT_SUPPORTED % ('document', line_number,
                                               tag_name)
                # unknown tag
    return story


def paragraph_stream(stream, elt_tag_name, elt_attributes, context):
    """
        stream : parser stream
    """

    content = []
    cpt = 0
    has_content = False
    is_not_paragraph = (elt_tag_name != 'p')
    story = []
    tag_stack = []
    start_tag = True
    end_tag = False
    style_p = context.get_css_props()
    skip = False
    place = 0

    while context.anchor:
        content.append(context.anchor.pop())
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
                if tag_name in ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                    story.extend(paragraph_stream(stream, tag_name,
                                                  attributes, context))
                elif tag_name == 'pre':
                    story.append(pre_stream(stream, tag_name, attributes,
                                            context))
                elif tag_name == 'hr':
                    story.append(hr_stream(stream, tag_name, attributes,
                                           context))
                elif tag_name == 'img':
                    # allow to put <a><img /></a>
                    skip = False
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
            if not skip:
                if tag_name in INLINE:
                    start_tag = True
                    if tag_name in ('a', 'b', 'big', 'em', 'i', 'small',
                                    'strong', 'sub', 'sup', 'tt', 'u'):
                        # FIXME
                        attrs = build_attributes(tag_name, attributes)
                        if cpt or has_content:
                            content[-1] += build_start_tag(tag_name, attrs)
                        else:
                            content.append(build_start_tag(tag_name, attrs))
                            has_content = True
                        cpt += 1
                    elif tag_name == 'span':
                        attrs, tag_stack = build_span_attributes(attributes)
                        if cpt or has_content:
                            content[-1] += build_start_tag(tag_name, attrs)
                        else:
                            content.append(build_start_tag(tag_name, attrs))
                            has_content = True
                        for i in tag_stack:
                            content[-1] += '<%s>' % i
                        cpt += 1
                    elif tag_name == 'br':
                        continue
                    elif tag_name == 'img':
                        attrs = build_img_attributes(attributes, context)
                        content.append(build_start_tag(tag_name, attrs))
                    else:
                        print MSG_TAG_NOT_SUPPORTED % ('document',
                                                       line_number, tag_name)
                        # unknown tag
                else:
                    print MSG_WARNING_DTD % ('document', line_number,
                                             tag_name)

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            context.path_on_end_event()
            if len(content):
                # spaces must be ignore if character before it is '\n'
                tmp = content[-1].rstrip(' \t')
                if len(tmp):
                    if tmp[-1] == '\n':
                        content[-1] = tmp.rstrip('\n')
            content_lenth = len(content)
            if content_lenth > 0:
                if skip:
                    elt = (elt_tag_name, elt_attributes)
                    para = create_paragraph(context, elt, content, style_p)
                    story.insert(place, para)
                    content = []
                    has_content = False
            if tag_name == elt_tag_name:
                if content_lenth > 0:
                    elt = (elt_tag_name, elt_attributes)
                    para = create_paragraph(context, elt, content, style_p)
                    story.append(para)
                return story
            elif tag_name == 'span':
                cpt -= 1
                end_tag = True
                while tag_stack:
                    content[-1] += '</%s>' % tag_stack.pop()
                content[-1] += get_end_tag(None, P_FORMAT.get(tag_name, 'b'))
            elif tag_name == 'br':
                content.append('<br/>')
            elif tag_name in P_FORMAT.keys():
                cpt -= 1
                end_tag = True
                content[-1] += get_end_tag(None, P_FORMAT.get(tag_name, 'b'))
            else:
                print MSG_TAG_NOT_SUPPORTED % ('document', line_number,
                                               tag_name)
                # unknown tag

        #### TEXT ELEMENT ####
        elif event == TEXT:
            if len(value) > 0:
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
                    elif content[-1].endswith('</span>') or end_tag or cpt:
                        content[-1] += value
                        end_tag = False
                    else:
                        content.append(value)
                else:
                    has_content = True
                    content.append(value)


def pre_stream(stream, tag_name, attributes, context):
    """
        stream : parser stream
    """

    stack = []
    styleN = context.get_style('Normal')
    content = []
    has_content = False

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break

        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attrs = value
            content.append(get_start_tag(tag_uri, tag_name, attrs))

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == 'pre':
                css_style = context.get_css_props()
                context.path_on_end_event()
                return create_paragraph(context, (tag_name, attributes),
                                        content, css_style)
            else:
                content.append(get_end_tag(None, tag_name))

        #### TEXT ELEMENT ####
        elif event == TEXT:
            # we dont strip the string --> preformatted widget
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
            context.path_on_end_event()
            if tag_name == _tag_name:
                return create_hr(_attributes, context)
        #### TEXT ELEMENT ####
        elif event == TEXT:
            pass
        else:
            print MSG_WARNING_DTD % ('document', line_number, tag_name)


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
        #### TEXT ELEMENT ####
        elif event == TEXT:
            pass
        else:
            print MSG_WARNING_DTD % ('document', line_number, tag_name)


def list_stream(stream, _tag_name, attributes, context, id=0):
    """
        stream : parser stream
    """

    stack = []
    # TODO : default value must be in default css
    INDENT_VALUE = 1 * cm
    story = [Indenter(left=INDENT_VALUE)]
    strid = str(id)
    content = ["<seqDefault id='%s'/><seqReset id='%s'/>" % (strid, strid)]
    has_content = False
    stack.append((_tag_name, attributes))
    li_state = 0 # 0 -> outside, 1 -> inside
    attrs = {}
    bullet = None
    cpt = 0
    start_tag = True
    end_tag = False

    if _tag_name == 'ul':
        bullet = get_bullet(attributes.get((URI, 'type'), 'disc'))
    else:
        bullet = "<bullet bulletIndent='-0.4cm'><seq id='%s'>.</bullet>"
        bullet = bullet % strid
        if exist_attribute(attributes, ['type']):
            attrs['type'] = attributes.get((URI, 'type'))
            seq = "<seqFormat id='%s' value='%s'/>" % (strid, attrs['type'])
            content.append(seq)
        else:
            content.append("<seqFormat id='%s' value='1'/>" % strid)

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            context.path_on_start_event(tag_name, attributes)
            if tag_name in ('ul', 'ol'):
                if li_state:
                    story.append(create_paragraph(context, stack[0],
                                                  content))
                    content = ["<seqDefault id='%s'/>" % strid]
                    story += list_stream(stream, tag_name, attributes,
                                         context, id+1)
                else:
                    print MSG_WARNING_DTD % ('document', line_number,
                                             tag_name)
            elif tag_name == 'li':
                li_state = 1
                content.append(bullet)
            elif tag_name in INLINE:
                start_tag = True
                if tag_name in ('a', 'b', 'big', 'em', 'i', 'small', 'strong',
                                'sub', 'sup', 'tt', 'u'):
                    # FIXME
                    attrs = build_attributes(tag_name, attributes)
                    if cpt or has_content:
                        content[-1] += build_start_tag(tag_name, attrs)
                    else:
                        content.append(build_start_tag(tag_name, attrs))
                    cpt += 1
                elif tag_name == 'span':
                    attrs, tag_stack = build_span_attributes(attributes)
                    if cpt or has_content:
                        content[-1] += build_start_tag(tag_name, attrs)
                    else:
                        content.append(build_start_tag(tag_name, attrs))
                    for i in tag_stack:
                        content[-1] += '<%s>' % i
                    cpt += 1
                elif tag_name == 'br':
                    continue
                elif tag_name == 'img':
                    attrs = build_img_attributes(attributes, context)
                    content.append(build_start_tag(tag_name, attrs))
                else:
                    print MSG_TAG_NOT_SUPPORTED % ('document', line_number,
                                               tag_name)
                    stack.append((tag_name, attributes))
            else:
                print MSG_WARNING_DTD % ('document', line_number, tag_name)

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            context.path_on_end_event()
            if tag_name in ('ul', 'ol'):
                story.append(create_paragraph(context, stack.pop(),
                             content))
                story.append(Indenter(left=-INDENT_VALUE))
                return story
            if len(content):
                # spaces must be ignore if character before it is '\n'
                tmp = content[-1].rstrip(' \t')
                if len(tmp):
                    if tmp[-1] == '\n':
                        content[-1] = tmp.rstrip('\n')
            if tag_name == 'li':
                story.append(create_paragraph(context, stack[0],
                                              content))
                content = []
                li_state = 0
            elif tag_name == 'span':
                cpt -= 1
                end_tag = True
                while tag_stack:
                    content[-1] += '</%s>' % tag_stack.pop()
                content[-1] += get_end_tag(None, P_FORMAT.get(tag_name, 'b'))
            elif tag_name == 'br':
                content.append('<br/>')
            elif tag_name in P_FORMAT.keys():
                cpt -= 1
                end_tag = True
                content[-1] += get_end_tag(None, P_FORMAT.get(tag_name, 'b'))
            else:
                print MSG_TAG_NOT_SUPPORTED % ('document', line_number,
                                               tag_name)
                # unknown tag
                stack.append((tag_name, attributes))

        #### TEXT ELEMENT ####
        elif event == TEXT:
            if li_state:
                # alow to write :
                # <para><u><i>foo</i> </u></para>
                value = XMLContent.encode(value) # entities
                # spaces must be ignore after a start tag if the next
                # character is '\n'
                if start_tag:
                    if value[0] == '\n':
                        value = value.lstrip('\n\t ')
                        if not len(value):
                            continue
                    start_tag = False
                if has_content and content[-1].endswith('<br/>'):
                    # <p>
                    #   foo          <br />
                    #     bar   <br />     team
                    # </p>
                    # equal
                    # <p>foo <br />bar <br />team</p>
                    value = value.lstrip()
                    content[-1] += value
                    end_tag = False
                elif has_content and content[-1].endswith('</span>'):
                    content[-1] += value
                    end_tag = False
                elif end_tag or cpt:
                    content[-1] += value
                    end_tag = False
                else:
                    has_content = True
                    content.append(value)


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
            else:
                print MSG_WARNING_DTD % ('document', line_number, tag_name)


def table_stream(stream, _tag_name, attributes, context):
    content = Table_Content(context)
    start = (0, 0)
    stop = (-1, -1)
    content.add_attributes(get_align(attributes))
    content.extend_style(get_table_style(context, attributes, start, stop))

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
                    print 'Warning data are already pushed'
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
            else:
                print MSG_TAG_NOT_SUPPORTED % ('document', line_number,
                                               tag_name)


def tr_stream(stream, _tag_name, attributes, table, context):
    x, y = table.get_current()
    style = get_table_style(context, attributes, (0, y), (-1, y))
    table.extend_style(style)

    stop = None

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            context.path_on_start_event(tag_name, attributes)
            if tag_name in ('td', 'th'):
                cont = paragraph_stream(stream, tag_name, attributes, context)
                table.push_content(cont)
                if exist_attribute(attributes, ['width']):
                    width = attributes.get((URI, 'width'))
                    table.add_colWidth(width)
                if exist_attribute(attributes, ['height']):
                    width = attributes.get((URI, 'height'))
                    table.add_lineHeight(width)
                if exist_attribute(attributes, ['colspan', 'rowspan'],
                                   at_least=True):
                    rowspan = attributes.get((URI, 'rowspan'))
                    colspan = attributes.get((URI, 'colspan'))
                    stop = table.process_span(rowspan, colspan)
                else:
                    stop = table.get_current()
                start = (table.current_x, table.current_y)
                style = get_table_style(context, attributes, start, stop)
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
            else:
                print MSG_TAG_NOT_SUPPORTED % ('document', line_number,
                                               tag_name)


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
    if element[0] == 'pre':
        content = XMLContent.encode(''.join(content))
        widget = XPreformatted(content, style)
    else:
        # DEBUG
        #print 0, content
        content = normalize(' '.join(content))
        if element[0] in HEADING:
            content = context.get_toc_anchor(element[0], content)
        content = '<para>%s</para>' % content
        #print 1, content
        widget = Paragraph(content, style, bulletText)
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


def create_hr(attributes, context):
    """
        Create a reportlab hr widget
    """

    attrs = {}
    attrs['width'] = '100%'
    for key in ('width', 'thickness', 'spaceBefore', 'spaceAfter'):
        if exist_attribute(attributes, [key]):
            attrs[key] = format_size(attributes.get((URI, key)))

    if exist_attribute(attributes, ['lineCap']):
        line_cap = attributes.get((URI, 'lineCap'))
        if line_cap not in ('butt', 'round', 'square'):
            line_cap = 'butt'
        attrs['lineCap'] = line_cap
    if exist_attribute(attributes, ['color']):
        attrs['color'] = get_color(attributes.get((URI, 'color')))
    attrs.update(get_align(attributes))
    return HRFlowable(**attrs)


def create_img(attributes, context, check_dimension=False):
    """
        Create a reportlab image widget.
        If check_dimension is true and the width and the height attributes
        are not set we return None
    """
    filename = attributes.get((URI, 'src'), None)
    width = format_size(attributes.get((URI, 'width'), None))
    height = format_size(attributes.get((URI, 'height'), None))
    if filename is None:
        print u'/!\ Filename is None'
        return None

    if check_dimension and width == None and height == None:
        print u'/!\ Cannot add an image inside a td without predefined size'
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
    file_path, itools_img = check_image(filename, context)
    x, y = itools_img.get_size()
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
        list_lenth = len(self.colWidths)
        platypus_value = format_size(value)
        if not self.current_y and list_lenth <= self.current_x:
            none_list = [ None for x in xrange(list_lenth, self.current_x+1) ]
            self.colWidths.extend(none_list)
        if self.colWidths[self.current_x] is None\
            or platypus_value > self.colWidths[self.current_x]:
            self.colWidths[self.current_x] = platypus_value


    def add_lineHeight(self, value):
        list_lenth = len(self.rowHeights)
        platypus_value = format_size(value)
        if list_lenth <= self.current_y:
            none_list = [ None for y in xrange(list_lenth, self.current_y+1) ]
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
def build_attributes(tag_name, attributes):
    if tag_name == 'a':
        attrs = attributes
    elif tag_name == 'big':
        attrs = {(URI, 'size'): font_value('120%')}
    elif tag_name == 'small':
        attrs = {(URI, 'size'): font_value('80%')}
    elif tag_name in ('code', 'tt'):
        attrs = {(URI, 'face'): FONT['monospace']}
    else:
        attrs = {}
    return attrs


def build_img_attributes(_attributes, context):
    attrs = {}
    itools_img = None
    for key, attr_value in _attributes.iteritems():
        key = key[1]
        if key == 'src':
            file_path, itools_img = check_image(attr_value, context)
            attrs[(URI, 'src')] = file_path
        elif key == 'width':
            attrs[(URI, 'width')] = format_size(attr_value)
        elif key == 'height':
            attrs[(URI, 'height')] = format_size(attr_value)

    exist_width = exist_attribute(attrs, ['width'])
    exist_height = exist_attribute(attrs, ['height'])
    if exist_width or exist_height:
        width, height = itools_img.get_size()
        width = width * 1.0
        height = height * 1.0
        tup_width = (URI, 'width')
        tup_height = (URI, 'height')
        # Calculate sizes to resize
        if exist_width:
            element = attrs[tup_width]
            if isinstance(element, str) and element.endswith('%'):
                value = get_int_value(element[:-1])
                attrs[tup_width] = value * width / 100
            if not exist_height:
                attrs[tup_height] = round(attrs[tup_width] * height / width)
        if exist_height:
            element = attrs[tup_height]
            if isinstance(element, str) and element.endswith('%'):
                value = get_int_value(element[:-1])
                attrs[tup_height] = value * height / 100
            if not exist_width:
                attrs[tup_width] = round(attrs[tup_height] * width / height)
    return attrs


def build_span_attributes(attributes):
    tag_stack = []
    attrs = {}
    attrib = {}
    if exist_attribute(attributes, ['style']):
        style = ''.join(attributes.pop((URI, 'style')).split()).rstrip(';')
        if style:
            stylelist = style.split(';')
            for element in stylelist:
                element_list = element.split(':')
                attrs[element_list[0].lower()] = element_list[1].lower()
            if attrs.has_key('color'):
                color = attrs['color']
                if color is not None:
                    attrib[(URI, 'color')] = get_color_as_hexa(color)
            if attrs.has_key('font-family'):
                family = attrs.pop('font-family')
                attrib[(URI, 'face')] = FONT.get(family, 'helvetica')
            if attrs.has_key('font-size'):
                size = attrs.pop('font-size')
                attrib[(URI, 'size')] = font_value(size)
            if attrs.has_key('font-style'):
                style = attrs.pop('font-style')
                if style in ('italic', 'oblique'):
                    tag_stack.append('i')
                elif style != 'normal':
                    print 'Warning font-style not valid'
    return attrib, tag_stack


##############################################################################
# Internal Functions                                                         #
##############################################################################
def build_start_tag(tag_name, attributes={}):
    """
        Create the XML start tag from his name and his attributes
        span => font (map)
    """
    if tag_name == 'a':
        tag = None
        attrs = {}
        if exist_attribute(attributes, ['href']):
            attrs['href'] = attributes.get((URI, 'href'))
            # Reencode the entities because the a tags
            # are decoded again by the reportlab para parser.
            href = XMLContent.encode(attrs['href'])
            tag = '<a href="%s">' % href
        if exist_attribute(attributes, ['id', 'name'], at_least=True):
            name = attributes.get((URI, 'id'), attributes.get((URI, 'name')))
            if name:
                if tag:
                    tag += '<a name="%s"/>' % name
                else:
                    tag = '<a name="%s"/>' % name
            else:
                tag = ''
        return tag
    else:
        attrs = attributes
    tag = P_FORMAT.get(tag_name, 'b')
    attr_str = ''.join([' %s="%s"' % (key[1], attrs[key])
                            for key in attrs.keys()])
    return '<%s%s>' % (tag, attr_str)


def get_bullet(type, indent='-0.4cm'):

    types = {'disc': '\xe2\x80\xa2',
             'square': '\xe2\x80\xa2',
             'circle': '\xe2\x80\xa2'}

    s = '<bullet bulletIndent="%s" font="Symbol">%s</bullet>'
    bullet = s % (indent, types.get(type, types['disc']))
    return bullet
