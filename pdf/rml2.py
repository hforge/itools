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

# Import from itools
from itools.xml import XMLParser, START_ELEMENT, END_ELEMENT, TEXT, CDATA
from itools.datatypes import Unicode, XML

#Import from the reportlab Library
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch, cm, mm, pica
from reportlab.lib.pagesizes import (letter, legal, elevenSeventeen, A0, A1,
    A2, A3, A4, A5, A6, B0, B1, B2, B3, B4, B5, B6, landscape, portrait)
from reportlab.lib.styles import getSampleStyleSheet as getBaseSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Preformatted)
from reportlab.platypus.flowables import Flowable, HRFlowable


# Mapping HTML -> REPORTLAB
p_format_map = {'i': 'i', 'em': 'i', 'b': 'b', 'strong': 'b', 'u': 'u',
                'sup': 'super', 'sub': 'sub'}

__tab_para_alignment = {'LEFT': TA_LEFT, 'RIGHT': TA_RIGHT,
                        'CENTER': TA_CENTER, 'JUSTIFY': TA_JUSTIFY}
TAG_NOT_SUPPORTED = '%s: line %s tag "%s" is currently not supported.'
WARNING_DTD = '%s: line %s tag "%s" is unapproprieted here.'
encoding = 'UTF-8'


def getSampleStyleSheet():
    stylesheet = getBaseSampleStyleSheet()

    # Add heading level 4, 5 and 6 like in html
    stylesheet.add(ParagraphStyle(name='Heading4',
                                  parent=stylesheet['h3'],
                                  fontSize=11),
                   alias='h4')
    stylesheet.add(ParagraphStyle(name='Heading5',
                                  parent=stylesheet['h4'],
                                  fontSize=10),
                   alias='h5')
    stylesheet.add(ParagraphStyle(name='Heading6',
                                  parent=stylesheet['h5'],
                                  fontSize=9),
                   alias='h6')

    return stylesheet


def rml2topdf_test(data):
    """
      Main function: produces a pdf file from a html-like xml
      document represented by a string
    """

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


def document_stream(stream, pdf_stream, document_name, is_test=False):
    """
        stream : parser stream
        pdf_stream : reportlab write the pdf into pdf_stream.
        document_name : name of the source file

        Childs : template, stylesheet, story
    """

    alias_style = {}
    stack = []
    story = []
    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            if tag_name == 'html':
                a = 1
            elif tag_name == 'head':
                a = 2
            elif tag_name == 'body':
                story += body_stream(stream, tag_name, attributes, alias_style)
            else :
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes, None))
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
        _story = list(story)


    doc = SimpleDocTemplate(pdf_stream, pagesize = letter)
    doc.build(story)

    if is_test == True:
        return _story


def body_stream(stream, _tag_name, _attributes, alias_style):
    """
        stream : parser stream
    """

    stack = []
    pdf_stylesheet = getSampleStyleSheet()
    story = []
    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break

        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            if tag_name == 'p':
                story.append(p_stream(stream, tag_name, attributes, pdf_stylesheet))
            elif tag_name == 'pre':
                story.append(pre_stream(stream, tag_name, attributes, pdf_stylesheet))
            elif tag_name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                story.append(heading_stream(stream, tag_name,
                             attributes, pdf_stylesheet, alias_style))
            elif tag_name == 'hr':
                story.append(hr_stream(stream, tag_name, attributes))
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes, None))

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == 'body':
                break
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes, None))
    return story


def p_stream(stream , tag_name, attributes, pdf_stylesheet):
    """
        stream : parser stream
    """

    stack = []
    story = []
    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    content = []
    has_content = False
    stack.append((tag_name, attributes, None))

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            if tag_name == 'p':
                print WARNING_DTD % ('document', line_number, tag_name)
            elif tag_name in ('i', 'em', 'b', 'strong', 'u', 'sup', 'sub'):
                content.append(build_start_tag(p_format_map.get(tag_name, 'b')))
            elif tag_name == 'br':
                continue
            elif tag_name == 'ol':
                content += ol_stream(stream, tag_name, attributes)
            elif tag_name == 'ul':
                content += ul_stream(stream, tag_name, attributes)
            elif tag_name == 'a':
                content += link_stream(stream, tag_name, attributes)
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes, None))

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == 'p':
                return create_paragraph(pdf_stylesheet, {}, stack.pop(), content)
            elif tag_name in ('i', 'em', 'b', 'strong', 'u', 'sup', 'sub'):
                content.append(build_end_tag(p_format_map.get(tag_name, 'b')))
            elif tag_name == 'br':
                content.append("<br/>")
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes, None))

        #### TEXT ELEMENT ####
        elif event == TEXT:
            value = normalize(value)
            if len(value) > 0:
                # alow to write :
                # <para><u><i>foo</i> </u></para>
                value = XML.encode(value) # entities
                # FIXME
                if has_content and content[-1] == '</br>':
                    value = value.lstrip()
                content.append(value)
                has_content = True


def pre_stream(stream , tag_name, attributes, pdf_stylesheet):
    """
        stream : parser stream
    """

    stack = []
    story = []
    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    content = []
    has_content = False
    stack.append((tag_name, attributes, None))

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            print WARNING_DTD % ('document', line_number, tag_name)
            stack.append((tag_name, attributes, None))

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == 'pre':
                return create_preformatted(pdf_stylesheet, {}, stack.pop(), content)
            else:
                print WARNING_DTD % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes, None))

        #### TEXT ELEMENT ####
        elif event == TEXT:
            if stack:
                # we dont strip the string --> preformatted widget
                value = XML.encode(value) # entities
                content.append(value)


def heading_stream(stream,  _tag_name, _attributes, pdf_stylesheet,
                   alias_style):
    """
        Create a heading widget.

        stream : parser stream
    """


    content = []
    stack = []
    stack.append((_tag_name, _attributes, None))
    style = get_style(pdf_stylesheet, alias_style,  _tag_name)

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            if tag_name in ('i', 'em', 'b', 'strong', 'u', 'sup', 'sub'):
                content.append(build_start_tag(p_format_map.get(tag_name, 'b')))
            elif tag_name == 'a':
                content += link_stream(stream, tag_name, attributes)
                print content
            else:
                print WARNING_DTD % ('document', line_number, tag_name)
                stack.append((tag_name, attributes, None))
        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == _tag_name:
                content = ''.join(content)
                widget = Paragraph(content, style)
                return widget
            if tag_name in ('i', 'em', 'b', 'strong', 'u', 'sup', 'sub'):
                content.append(build_end_tag(p_format_map.get(tag_name, 'b')))
            else:
                print WARNING_DTD % ('document', line_number, tag_name)
                element = stack.pop()

        #### TEXT ELEMENT ####
        elif event == TEXT:
            if stack:
                value = normalize(value)
                if len(value) > 0 and value != ' ':
                    value = XML.encode(value) # entities
                content.append(value)
                has_content = True


def hr_stream(stream, _tag_name, _attributes):
    """
        Create a hr widget.

        stream : parser stream
    """

    stack = []
    stack.append((_tag_name, _attributes, None))
    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            stack.append((tag_name, attributes, None))
        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == _tag_name:
                widget = create_hr(_attributes)
                return widget
            else:
                element = stack.pop()
        #### TEXT ELEMENT ####
        elif event == TEXT:
            pass


def ol_stream(stream , tag_name, attributes):
    """
        stream : parser stream
    """

    stack = []
    content = []
    has_content = False
    stack.append((tag_name, attributes, None))
    attrs = {}
    if exist_attribute(attributes, ['type']):
      attrs['type'] = attributes.get((None,'type')).lower()
      if attrs['type'] == 'upper roman':
        content.append("<seqFormat value='I'></seq>")
      if attrs['type'] == 'lower roman':
        content.append("<seqFormat value='i'></seq>")
      if attrs['type'] == 'lower alpha':
        content.append("<seqFormat value='a'></seq>")
      if attrs['type'] == 'upper alpha':
        content.append("<seqFormat value='A'></seq>")
      else:
        content.append("<seqFormat value='1'></seq>")
    else:
      content.append("<seqFormat value='1'></seq>")

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            if tag_name == 'ol':
                print WARNING_DTD % ('document', line_number, tag_name)
            elif tag_name in ('i', 'em', 'b', 'strong', 'u', 'sup', 'sub'):
                content.append(build_start_tag(p_format_map.get(tag_name, 'b')))
            elif tag_name == 'li':
                content.append("<seq> ")
            elif tag_name == 'a':
                content += link_stream(stream, tag_name, attributes)
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes, None))

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == 'ol':
                content.append("<seqReset/>")
                return content
            elif tag_name in ('i', 'em', 'b', 'strong', 'u', 'sup', 'sub'):
                content.append(build_end_tag(p_format_map.get(tag_name, 'b')))
            elif tag_name == 'li':
                content.append("</seq><br/>")
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes, None))

        #### TEXT ELEMENT ####
        elif event == TEXT:
            value = normalize(value)
            if len(value) > 0:
                # alow to write :
                # <para><u><i>foo</i> </u></para>
                value = XML.encode(value) # entities
                value = value.lstrip()
                content.append(value)
                has_content = True


def ul_stream(stream , tag_name, attributes):
    """
        stream : parser stream
    """

    stack = []
    story = []
    content = []
    has_content = False
    stack.append((tag_name, attributes, None))
    content.append("<br/>")

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            if tag_name == 'ul':
                print WARNING_DTD % ('document', line_number, tag_name)
            elif tag_name == 'li':
                content.append('- ')
            elif tag_name in ('i', 'em', 'b', 'strong', 'u', 'sup', 'sub'):
                content.append(build_start_tag(p_format_map.get(tag_name, 'b')))
            elif tag_name == 'a':
                content += link_stream(stream, tag_name, attributes)
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes, None))

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == 'ul':
                return content
            elif tag_name in ('i', 'em', 'b', 'strong', 'u', 'sup', 'sub'):
                content.append(build_end_tag(p_format_map.get(tag_name, 'b')))
            elif tag_name == 'li':
                content.append("<br/>")
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes, None))

        #### TEXT ELEMENT ####
        elif event == TEXT:
            value = normalize(value)
            if len(value) > 0:
                # alow to write :
                # <para><u><i>foo</i> </u></para>
                value = XML.encode(value) # entities
                value = value.lstrip()
                content.append(value)
                has_content = True


def link_stream(stream , tag_name, attributes):
    """
        stream : parser stream
    """

    stack = []
    story = []
    content = []
    has_content = False
    stack.append((tag_name, attributes, None))
    attrs = {}
    if exist_attribute(attributes, ['href']):
        attrs['href'] = attributes.get((None,'href')).lower()
        content.append("<a href=\"%s\">" % attrs['href'] )
    elif exist_attribute(attributes, ['id', 'name'], at_least=True):
        name = attributes.get((None, 'id'), attributes.get((None, 'name')))
        content.append("<a name=\"%s\">" % name)

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            if tag_name == 'a':
                print WARNING_DTD % ('document', line_number, tag_name)
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes, None))

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == 'a':
                content.append("</a>")
                return content
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes, None))

        #### TEXT ELEMENT ####
        elif event == TEXT:
            value = normalize(value)
            if len(value) > 0:
                # alow to write :
                # <para><u><i>foo</i> </u></para>
                value = XML.encode(value) # entities
                # FIXME
                value = value.lstrip()
                content.append(value)
                has_content = True


################################################################################
# Functions
################################################################################
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


def create_paragraph(pdf_stylesheet, alias_style, element, content):
    """
        Create a reportlab paragraph widget.
    """

    parent_style = 'Normal'
    style_attr = {}
    # Now, we strip each value in content before call create_paragraph
    # content = ['Hello', '<i>how are</i>', 'you?']
    # Another choice is to strip the content (1 time) here
    # content = ['  Hello\t\', '\t<i>how are</i>', '\tyou?']
    # tmp = ' '.join(content)
    # content = ' '.join(tmp.split())

    content = ''.join(content)
    bulletText = None

    for key, attr_value in element[1].iteritems():
        key = key[1] # (None, key)
        if key == 'style':
            parent_style = attr_value
        elif key == 'bulletText':
            bulletText = attr_value
        else:
            if key == 'align':
                key = 'alignment'
            if key == 'alignment':
                attr_value = __tab_para_alignment.get(attr_value.upper())
            elif key in ['leftIndent', 'rightIndent']:
                attr_value = rml_value(attr_value)
            style_attr[key] = attr_value

    style_name = parent_style
    parent_style = get_style(pdf_stylesheet, alias_style, parent_style)
    style = ParagraphStyle(style_name, parent=parent_style, **style_attr)
    return Paragraph(content, style, bulletText)


def create_preformatted(pdf_stylesheet, alias_style, element, content):
    """
        Create a reportlab preformatted widget.
    """

    content = ''.join(content)
    style_name = 'Normal'

    for key, attr_value in element[1].iteritems():
        if key[1] == 'style':
            style_name = attr_value

    if element[0] == 'pre':
        fn = Preformatted

    style = get_style(pdf_stylesheet, alias_style, style_name)

    widget = fn(content, style)
    return widget


def build_start_tag(tag_name, attributes={}):
    """
        Create the XML start tag from his name and his attributes
    """

    attr_str = ''.join([' %s="%s"' % (key[1], attributes[key])
                        for key in attributes.keys()])
    return '<%s%s>' % (tag_name, attr_str)


def build_end_tag(tag_name):
    """
        Create the XML end tag from his name.
    """

    return '</%s>' % tag_name


def create_hr(attributes):
    """
        Create a reportlab hr widget
    """

    attrs = {}
    attrs['width'] = "100%"
    for key in ['width', 'thickness', 'spaceBefore', 'spaceAfter']:
        if exist_attribute(attributes, [key]):
            attrs[key] = rml_value(attributes.get((None, key)))
    if exist_attribute(attributes, ['lineCap']):
        line_cap = attributes.get((None,'lineCap'))
        if line_cap not in ['butt', 'round', 'square']:
            line_cap = 'butt'
        attrs['lineCap'] = line_cap
    if exist_attribute(attributes, ['color']):
        attrs['color'] = get_color(attributes.get((None, 'color')))
    if exist_attribute(attributes, ['align']):
        hAlign = attributes.get((None, 'align'), '').upper()
        if hAlign in ['LEFT', 'RIGHT', 'CENTER', 'CENTRE']:
            attrs['hAlign'] = hAlign
    if exist_attribute(attributes, ['vAlign']):
        vAlign = attributes.get((None, 'vAlign'), '').upper()
        if vAlign in ['TOP', 'MIDDLE', 'BOTTOM']:
            attrs['vAlign'] = vAlign
    return HRFlowable(**attrs)


def get_style(stylesheet, alias, name):
    """
       Return the style corresponding to name or the style normal if it does
       not exist.
    """

    if name[:6] == 'style.':
        # <alias id="bt" value="style.BodyText"/>
        name = name[6:]

    # we use try except because StyleSheet1 class has no attribute 'get'
    try:
        style = stylesheet[name]
        return style
    except KeyError:
        try:
            style = stylesheet[alias[name]]
            return style
        except KeyError:
            return stylesheet['Normal']


def exist_attribute(attrs, keys, at_least=False):
    """
        if at_least is False
        Return True if all key in keys
        are contained in the dictionnary attrs
    """

    if at_least is False:
        for key in keys:
            if attrs.has_key((None, key)) is False:
                return False
        return True
    else:
        for key in keys:
            if attrs.has_key((None, key)) is True:
                return True
        return False


def rml_value(value, default=None):
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
    if not is_str(value):
        return value

    value = value.strip()
    if value == "None":
        return None
    if value[-2:] == 'in':
        coef = inch
        value = value[:-2]
    elif value[-2:] == 'cm':
        coef = cm
        value = value[:-2]
    elif value[-2:] == 'mm':
        coef = mm
        value = value[:-2]
    elif value[-4:] == 'pica':
        coef = pica
        value = value[:-4]

    elif value[-1:] == '%':
        return value

    try:
        value = float(value) * coef
    except ValueError:
        value = default
    return value


def is_str(str, check_is_unicode=True):
    """
        Check is str is a string.
    """

    if type(str) != type(''):
        if not check_is_unicode:
            return False
        return type(str) == type(u'')
    return True

