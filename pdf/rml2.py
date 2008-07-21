# -*- coding: UTF-8 -*-

# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008 Fabrice Decroix <fabrice.decroix@gmail.com>
# Copyright (C) 2008 Yannick Martel <yannick.martel@gmail.com>
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
from math import floor
import tempfile

# Import from itools
from itools import get_abspath
from itools.datatypes import Unicode, XMLContent, Integer
from itools.handlers import Image as ItoolsImage
from itools.vfs import vfs
from itools.xml import XMLParser, START_ELEMENT, END_ELEMENT, TEXT
import itools.http

#Import from the reportlab Library
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import(getSampleStyleSheet, ParagraphStyle)
from reportlab.lib.units import inch, cm, mm, pica
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Preformatted,
                                PageBreak, Image, Indenter, Table)
from reportlab.platypus import tableofcontents
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.platypus.flowables import HRFlowable
from reportlab.platypus.frames import Frame
from reportlab.platypus.tableofcontents import TableOfContents

encoding = 'UTF-8'
URI = None
# Mapping HTML -> REPORTLAB
P_FORMAT = {'a': 'a', 'em': 'i', 'b': 'b', 'span': 'font', 'sub': 'sub',
            'i': 'i', 'img': 'img', 'big': 'font', 'tt': 'font', 'p': 'para',
            'u': 'u', 'sup': 'super', 'small': 'font', 'strong': 'b'}
SPECIAL = ('a', 'br', 'img', 'span', 'sub', 'sup')
PHRASE = ('em', 'strong')
FONT_STYLE = ('b', 'big', 'i', 'small', 'tt')
DEPRECATED = ('u',)
INLINE = FONT_STYLE + PHRASE + SPECIAL + DEPRECATED

FONT = {'monospace': 'courier', 'times-new-roman': 'times-roman',
        'arial': 'helvetica', 'serif': 'times',
        'sans-serif': 'helvetica', 'helvetica': 'helvetica',
        'symbol': 'symbol'}

# ALIGNMENT
ALIGNMENTS = {'LEFT': TA_LEFT, 'RIGHT': TA_RIGHT, 'CENTER': TA_CENTER,
              'JUSTIFY': TA_JUSTIFY}

PADDINGS = ('LEFTPADDING', 'RIGHTPADDING', 'BOTTOMPADDING', 'TOPPADDING')

TAG_NOT_SUPPORTED = '%s: line %s tag "%s" is currently not supported.'
WARNING_DTD = '%s: line %s tag "%s" is unapproprieted here.'

HEADING = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')

class Context(object):


    def __init__(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.init_base_style_sheet()
        self.image_not_found_path = get_abspath(globals(), 'not_found.png')
        self.size = {'in': inch, 'cm': cm, 'mm': mm, 'pica': pica, 'px': 1}
        self.toc_place = None
        self.cpt_toc_ref = 0
        self.toc_high_level = 3


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


    def format_size(self, value, default=None):
        """
           Return the reportlab value of value
           only if value is a string
           '2cm' -> 2 * cm
           '2in' -> 2 * inch
           '2in' -> 2 * mm
           '2in' -> 2 * pica
           '2%' -> '2%'
        """

        if value is None:
            return default

        coef = 1
        if not isinstance(value, (str, unicode)):
            return value
        if value == 'None':
            return None
        if value.endswith('%'):
            return value
        for key in self.size.keys():
            lenth_of_key = len(key)
            if value.endswith(key):
                value = value[:-len(key)]
                coef = self.size[key]
                break
        try:
            value = float(value) * coef
        except ValueError:
            value = default
        return value


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


    def __del__(self):
        vfs.remove(self.tmp_dir)



def rml2topdf_test(value, raw=False):
    """
      If raw is False, value is the test file path
      otherwise it is the string representation of a xml document
    """

    if raw is False:
        input = vfs.open(value)
        data = input.read()
        input.close()
    else:
        data = value
    stream = XMLParser(data)
    return document_stream(stream, StringIO(), 'test', True)


def rml2topdf(filename):
    """
      Main function: produces a pdf file from a html-like xml document

      filename: source file
    """

    file = open(filename, 'r')
    stream = XMLParser(file.read())
    iostream = StringIO()
    document_stream(stream, iostream, filename, False)
    return iostream.getvalue()


def makeTocHeaderStyle(level, delta, epsilon, fontName='Times-Roman'):
    "Make a header style for different levels."

    assert level >= 0, "Level must be >= 0."

    PS = ParagraphStyle
    size = 12
    style = PS(name = 'Heading' + str(level),
               fontName = fontName,
               fontSize = size,
               leading = size*1.2,
               spaceBefore = size/4.0,
               spaceAfter = size/8.0,
               firstLineIndent = -epsilon,
               leftIndent = level*delta + epsilon)

    return style


class MyDocTemplate(BaseDocTemplate):
    "The document template used for all PDF documents."

    def __init__(self, filename, **kw):
        BaseDocTemplate.__init__(self, filename, **kw)
        self.toc_index = 0


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
            if level is not None:
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
            if tag_name == 'html':
                if state == 0:
                    state = 1
                else:
                    print WARNING_DTD % ('document', line_number, tag_name)
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
                    print WARNING_DTD % ('document', line_number, tag_name)
                continue
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes))
        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
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
        doc = MyDocTemplate(pdf_stream, pagesize=LETTER)
        frame1 = Frame(doc.leftMargin, doc.bottomMargin, doc.width,
                       doc.height, id='normal')
        template_attrs = {'id': 'now', 'frames': [frame1], 'pagesize': LETTER}
        page_template = PageTemplate(**template_attrs)
        doc.addPageTemplates([page_template])
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
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == _tag_name:
                return informations
            elif tag_name == 'title':
                informations[tag_name] = normalize(' '.join(content))
            elif tag_name == 'meta':
                continue
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag

        #### TEXT ELEMENT ####
        elif event == TEXT:
            content.append(value)


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
    story.append(PageBreak())
    return story


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
            if tag_name in ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                story.append(paragraph_stream(stream, tag_name, attributes,
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
            elif tag_name in ('ol', 'ul'):
                story.extend(list_stream(stream, tag_name, attributes,
                                         context))
            elif tag_name == 'table':
                story.append(table_stream(stream, tag_name, attributes,
                                          context))
            elif tag_name == 'toc':
                context.toc_place = len(story)
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == _tag_name:
                break
            elif tag_name == 'toc':
                continue
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
    return story


def paragraph_stream(stream, elt_tag_name, elt_attributes, context):
    """
        stream : parser stream
    """
    content = compute_paragraph(stream, elt_tag_name, elt_attributes, context)
    return create_paragraph(context, (elt_tag_name, elt_attributes), content)


def pre_stream(stream, tag_name, attributes, context):
    """
        stream : parser stream
    """

    stack = []
    styleN = context.get_style('Normal')
    content = []
    has_content = False
    stack.append((tag_name, attributes))

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break

        #### START ELEMENT ####
        if event == START_ELEMENT:
            print WARNING_DTD % ('document', line_number, tag_name)
            stack.append((tag_name, attributes))

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == 'pre':
                return create_preformatted(context, stack.pop(), content)
            else:
                print WARNING_DTD % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes))

        #### TEXT ELEMENT ####
        elif event == TEXT:
            if stack:
                # we dont strip the string --> preformatted widget
                value = XMLContent.encode(value) # entities
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
            print WARNING_DTD % ('document', line_number, tag_name)
        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == _tag_name:
                return create_hr(_attributes, context)
        #### TEXT ELEMENT ####
        elif event == TEXT:
            pass
        else:
            print WARNING_DTD % ('document', line_number, tag_name)


def img_stream(stream, _tag_name, _attributes, context):
    attrs = build_img_attributes(_attributes, context)
    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            print WARNING_DTD % ('document', line_number, tag_name)
        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == _tag_name:
                return create_img(attrs, context)
        #### TEXT ELEMENT ####
        elif event == TEXT:
            pass
        else:
            print WARNING_DTD % ('document', line_number, tag_name)


def list_stream(stream, _tag_name, attributes, context, id=0):
    """
        stream : parser stream
    """

    stack = []
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
            if tag_name in ('ul', 'ol'):
                if li_state:
                    story.append(create_paragraph(context, stack[0],
                                                  content))
                    content = ["<seqDefault id='%s'/>" % strid]
                    story += list_stream(stream, tag_name, attributes,
                                         context, id+1)
                else:
                    print WARNING_DTD % ('document', line_number, tag_name)
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
                    print TAG_NOT_SUPPORTED % ('document', line_number,
                                               tag_name)
                    stack.append((tag_name, attributes))
            else:
                print WARNING_DTD % ('document', line_number, tag_name)

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
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
                content[-1] += build_end_tag(P_FORMAT.get(tag_name, 'b'))
            elif tag_name == 'br':
                content.append('<br/>')
            elif tag_name in P_FORMAT.keys():
                cpt -= 1
                end_tag = True
                content[-1] += build_end_tag(P_FORMAT.get(tag_name, 'b'))
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
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


def table_stream(stream, _tag_name, attributes, context):
    content = Table_Content(context)
    start = (0, 0)
    stop = (-1, -1)
    if exist_attribute(attributes, ['border']):
        border = get_int_value(attributes.get((URI, 'border')))
        content.add_style(('GRID', start, stop, border, colors.grey))
    if exist_attribute(attributes, ['align']):
        hAlign = attributes.get((URI, 'align')).upper()
        if hAlign in ['LEFT', 'RIGHT', 'CENTER', 'CENTRE']:
            content.add_attributes('hAlign', hAlign)
    if exist_attribute(attributes, ['cellpadding']):
        attr_value = attributes.get((URI, 'cellpadding'), None)
        if attr_value is not None:
            value = int(context.format_size(attr_value))
            for padding in PADDINGS:
                content.add_style((padding, start, stop, value))

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            if tag_name == 'tr':
                content = compute_tr(stream, tag_name, attributes,
                                    content, context)
                content.next_line()
            elif tag_name == 'thead':
                if len(content.content):
                    print 'Warning data are already pushed'
            else:
                print WARNING_DTD % ('document', line_number, tag_name)

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == _tag_name:
                return content.create()
            elif tag_name == 'thead':
                content.thead()
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)


def compute_paragraph(stream, elt_tag_name, elt_attributes, context):
    content = []
    cpt = 0
    has_content = False
    is_table = elt_tag_name in ('td', 'th')
    story = []
    tag_stack = []
    start_tag = True
    end_tag = False

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            if is_table:
                skip = True
                # TODO ? Merge with body_stream?
                if tag_name in ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                    story.append(paragraph_stream(stream, tag_name,
                                                  attributes,
                                                  context))
                elif tag_name == 'pre':
                    story.append(pre_stream(stream, tag_name, attributes,
                                            context))
                elif tag_name == 'hr':
                    story.append(hr_stream(stream, tag_name, attributes,
                                           context))
                elif tag_name == 'img':
                    widget = img_stream(stream, tag_name, attributes, context)
                    if widget:
                        story.append(widget)
                elif tag_name in ('ol', 'ul'):
                    story.extend(list_stream(stream, tag_name, attributes,
                                             context))
                elif tag_name == 'table':
                    story.append(table_stream(stream, tag_name, attributes,
                                              context))
                else:
                    skip = False
                if skip:
                    continue
            if tag_name in INLINE:
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
                    print TAG_NOT_SUPPORTED % ('document', line_number,
                                               tag_name)
                    # unknown tag
            else:
                print WARNING_DTD % ('document', line_number, tag_name)

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if len(content):
                # spaces must be ignore if character before it is '\n'
                tmp = content[-1].rstrip(' \t')
                if len(tmp):
                    if tmp[-1] == '\n':
                        content[-1] = tmp.rstrip('\n')
            if tag_name == elt_tag_name:
                # FIXME
                # if compute_paragraph is called by table_stream
                # then this function return
                #   # either a platypus object list if it exist at least
                #     one platypus object, ignore text out of paragraph
                #   # either a str object in other case
                # else this function is called by paragraph stream which
                #     want a str list to build the platypus object
                if is_table:
                    if len(story) > 0:
                        return story
                    return ' '.join(content)
                return content
            elif tag_name == 'span':
                cpt -= 1
                end_tag = True
                while tag_stack:
                    content[-1] += '</%s>' % tag_stack.pop()
                content[-1] += build_end_tag(P_FORMAT.get(tag_name, 'b'))
            elif tag_name == 'br':
                content.append('<br/>')
            elif tag_name in P_FORMAT.keys():
                cpt -= 1
                end_tag = True
                content[-1] += build_end_tag(P_FORMAT.get(tag_name, 'b'))
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag

        #### TEXT ELEMENT ####
        elif event == TEXT:
            if len(value) > 0:
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


def build_img_attributes(_attributes, context):
    attrs = {}
    itools_img = None
    for key, attr_value in _attributes.iteritems():
        key = key[1]
        if key == 'src':
            file_path, itools_img = check_image(attr_value, context)
            attrs[(URI, 'src')] = file_path
        elif key == 'width':
            attrs[(URI, 'width')] = context.format_size(attr_value)
        elif key == 'height':
            attrs[(URI, 'height')] = context.format_size(attr_value)

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


def compute_tr(stream, _tag_name, attributes, table, context):
    stop = None

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            if tag_name in ('td', 'th'):
                cont = compute_paragraph(stream, tag_name, attributes,
                                         context)
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
                # DEPRECATED
                if exist_attribute(attributes, ['bgcolor']):
                    val = attributes.get((URI,'bgcolor'))
                    color = get_color(val)
                    table.add_style(('BACKGROUND', (table.current_x,
                                                    table.current_y),
                                     stop, color))
                #ALIGNMENT
                for i in ('align', 'valign'):
                    if exist_attribute(attributes, [i]):
                        val = attributes.get((URI, i))
                        table.add_style((i.upper(),
                                        (table.current_x, table.current_y),
                                        stop,
                                        val.upper()))

                table.next_cell()
            else:
                print WARNING_DTD % ('document', line_number, tag_name)

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == _tag_name:
                return table
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)


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
                    if color.startswith('rgb'):
                        attrib[(URI, 'color')] = get_color_hexa(color)
                    else:
                        attrib[(URI, 'color')] = color
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
# Reportlab widget                                                           #
##############################################################################
def create_paragraph(context, element, content):
    """
        Create a reportlab paragraph widget.
    """

    # Now, we strip each value in content before call create_paragraph
    # content = ['Hello', '<i>how are</i>', 'you?']
    # Another choice is to strip the content (1 time) here
    # content = ['  Hello\t\', '\t<i>how are</i>', '\tyou?']

    # DEBUG
    #print 0, content
    content = normalize(' '.join(content))
    if element[0] in HEADING:
        content = context.get_toc_anchor(element[0], content)
    content = '<para>%s</para>' % content
    #print 1, content
    style, bulletText = build_style(context, element)
    return Paragraph(content, style, bulletText)


def build_style(context, element):
    style_attr = {}
    # The default style is Normal
    parent_style_name = 'Normal'
    bulletText = None

    # Overload the attributes values
    for key, attr_value in element[1].iteritems():
        key = key[1] # (None, key)
        if key == 'style':
            # Set the parent style for inheritance
            parent_style_name = attr_value
        elif key == 'bulletText':
            bulletText = attr_value
        else:
            if key == 'align':
                attr_value = ALIGNMENTS.get(attr_value.upper())
            elif key in ['leftIndent', 'rightIndent']:
                attr_value = context.format_size(attr_value)
            style_attr[key] = attr_value
    style_attr['autoLeading'] = 'max'

    if element[0] in HEADING + ('toctitle', ):
        parent_style_name = element[0]
    style_name = parent_style_name
    parent_style = context.get_style(parent_style_name)
    return (ParagraphStyle(style_name, parent=parent_style, **style_attr),
            bulletText)


def create_preformatted(context, element, content):
    """
        Create a reportlab preformatted widget.
    """

    content = ''.join(content)
    style_name = 'Normal'

    for key, attr_value in element[1].iteritems():
        if key[1] == 'style':
            style_name = attr_value
    style = context.get_style(style_name)
    widget = Preformatted(content, style)
    return widget


def create_hr(attributes, context):
    """
        Create a reportlab hr widget
    """

    attrs = {}
    attrs['width'] = '100%'
    for key in ('width', 'thickness', 'spaceBefore', 'spaceAfter'):
        if exist_attribute(attributes, [key]):
            attrs[key] = context.format_size(attributes.get((URI, key)))

    if exist_attribute(attributes, ['lineCap']):
        line_cap = attributes.get((URI, 'lineCap'))
        if line_cap not in ('butt', 'round', 'square'):
            line_cap = 'butt'
        attrs['lineCap'] = line_cap
    if exist_attribute(attributes, ['color']):
        attrs['color'] = get_color(attributes.get((URI, 'color')))
    if exist_attribute(attributes, ['align']):
        h_align = attributes.get((URI, 'align'), '').upper()
        if h_align in ('LEFT', 'RIGHT', 'CENTER', 'CENTRE'):
            attrs['hAlign'] = h_align
    if exist_attribute(attributes, ['vAlign']):
        v_align = attributes.get((URI, 'vAlign'), '').upper()
        if v_align in ('TOP', 'MIDDLE', 'BOTTOM'):
            attrs['vAlign'] = v_align
    return HRFlowable(**attrs)


def create_img(attributes, context, check_dimension=False):
    """
        Create a reportlab image widget.
        If check_dimension is true and the width and the height attributes
        are not set we return None
    """
    filename = attributes.get((URI, 'src'), None)
    width = context.format_size(attributes.get((URI, 'width'), None))
    height = context.format_size(attributes.get((URI, 'height'), None))
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


def check_image(filename, context):
    if vfs.exists(filename) is False:
        print u"/!\ The filename '%s' doesn't exist" % filename
        filename = context.image_not_found_path
    im = None
    if filename.startswith('http://'):
        # Remote file
        # If the image is a remote file, we create a StringIO
        # object contains the image data to avoid reportlab problems ...
        data = vfs.open(filename).read()
        my_file = context.get_tmp_file()
        filename = my_file.name
        my_file.write(data)
        my_file.close()
        im = ItoolsImage(string=data)
    if im is None:
        im = ItoolsImage(filename)

    x, y = im.get_size()
    if not (x or y):
        print u'image not valid : %s' % filename
        filename = context.image_not_found_path
        im = ItoolsImage(filename)
    return filename, im


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
                print u'Table error : too many row at its line: %s' % current_line
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
    def add_attributes(self, name, value):
        self.attrs[name] = value


    def add_style(self, style):
        self.style.append(style)


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
                print u'Table error : too many row at its line: %s' % current_line
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
        platypus_value = self.context.format_size(value)
        if not self.current_y and list_lenth <= self.current_x:
            none_list = [ None for x in xrange(list_lenth, self.current_x+1) ]
            self.colWidths.extend(none_list)
        if self.colWidths[self.current_x] is None\
            or platypus_value > self.colWidths[self.current_x]:
            self.colWidths[self.current_x] = platypus_value


    def add_lineHeight(self, value):
        list_lenth = len(self.rowHeights)
        platypus_value = self.context.format_size(value)
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
# Internal Functions                                                         #
##############################################################################
def stream_next(stream):
    """
        return the next value of the stream
        (event, value, line_number)
        or
        (None, None, None) if StopIteration exception is raised
    """

    try:
        event, value, line_number = stream.next()
        return (event, value, line_number)
    except StopIteration:
        return (None, None, None)


def normalize(data):
    """
        Normalize data

        http://www.w3.org/TR/html401/struct/text.html#h-9.1
        collapse input white space sequences when producing output inter-word
        space.
    """

    # decode the data
    data = Unicode.decode(data, encoding)
    return ' '.join(data.split())


def font_value(str_value, style_size = 12):
    style_size = 12  # TODO : replace default_value by current stylesheet
                     # size
    map_fontsize = {'xx-small': 20, 'x-small': 40, 'smaller': 60, 'small':80,
                    'medium':100, 'large': 120, 'larger': 140, 'x-large': 160,
                    'xx-large': 180}
    if str_value[0].isalpha():
        if str_value in map_fontsize.keys():
            value = map_fontsize[str_value]
        else:
            print u"/!\ 'font-size' bad value"
            value = 100
        if value == 100:
            value = style_size
        else:
            value = value * style_size / 100
    elif str_value.endswith('%'):
        value = (int(str_value.rstrip('%')) * style_size) / 100
    else:
        try:
            value = int(str_value)
        except ValueError:
            value = style_size
    return value


def build_attributes(tag_name, attributes):
    if tag_name == 'a':
        attrs = attributes
    elif tag_name == 'big':
        attrs = {(URI, 'size'): font_value('120%')}
    elif tag_name == 'small':
        attrs = {(URI, 'size'): font_value('80%')}
    elif tag_name == 'tt':
        attrs = {(URI, 'face'): FONT['monospace']}
    else:
        attrs = {}
    return attrs


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
            if tag:
                tag += '<a name="%s"/>' % name
            else:
                tag = '<a name="%s">' % name
        return tag
    else:
        attrs = attributes
    tag = P_FORMAT.get(tag_name, 'b')
    attr_str = ''.join([' %s="%s"' % (key[1], attrs[key])
                            for key in attrs.keys()])
    return '<%s%s>' % (tag, attr_str)


def build_end_tag(tag_name):
    """
        Create the XML end tag from his name.
    """

    return '</%s>' % tag_name


def get_color_hexa(x):
    x = x.lstrip('rgb(').rstrip(')').split(',')
    x = [int(i) for i in x]
    tmp = []
    if len(x) == 3:
        # RGB
        for i in x:
            if i < 256:
                tmp.append('%02x' % i)
            else:
                print 'Warning color error'
                return None
    return '#%s' % ''.join(tmp)


def get_color(value):
    value = value.strip()
    if value:
        if value.startswith('rgb'):
            value = get_color_hexa(value)
        elif value.startswith('#'):
            if len(value) == 4:
                # #aba -> #aabbaa
                r = value[1] * 2
                g = value[2] * 2
                b = value[3] * 2
                value = '#%s%s%s' % (r, g, b)
    color = colors.toColor(value, colors.black)
    return color


def get_int_value(value, default=0):
    """
    Return the interger representation of value is his decoding succeed
    otherwise the default value
    """
    if not value:
        return default
    try:
        return Integer.decode(value)
    except ValueError:
        return default


def round(value):
    return floor(value + 0.5)


def get_bullet(type, indent='-0.4cm'):

    types = {'disc': '\xe2\x80\xa2',
             'square': '\xe2\x80\xa2',
             'circle': '\xe2\x80\xa2'}

    s = '<bullet bulletIndent="%s" font="Symbol">%s</bullet>'
    bullet = s % (indent, types.get(type, types['disc']))
    return bullet


def exist_attribute(attrs, keys, at_least=False):
    """
        if at_least is False
        Return True if all key in keys
        are contained in the dictionnary attrs
    """

    if at_least is False:
        for key in keys:
            if attrs.has_key((URI, key)) is False:
                return False
        return True
    else:
        for key in keys:
            if attrs.has_key((URI, key)) is True:
                return True
        return False
