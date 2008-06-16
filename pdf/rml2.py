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
from itools.datatypes import Unicode, XML
from itools.vfs import vfs
import itools.http

from itools.xml import XMLParser, START_ELEMENT, END_ELEMENT, TEXT

#Import from the reportlab Library
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import(getSampleStyleSheet as getBaseStyleSheet,
                                 ParagraphStyle)
from reportlab.lib.units import inch, cm, mm, pica
from reportlab.platypus.flowables import HRFlowable
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Preformatted,
                                Image, Indenter)


# Mapping HTML -> REPORTLAB
p_format_map = {'i': 'i', 'em': 'i', 'b': 'b', 'strong': 'b', 'u': 'u',
                'sup': 'super', 'sub': 'sub'}

__tab_para_alignment = {'LEFT': TA_LEFT, 'RIGHT': TA_RIGHT,
                        'CENTER': TA_CENTER, 'JUSTIFY': TA_JUSTIFY}
TAG_NOT_SUPPORTED = '%s: line %s tag "%s" is currently not supported.'
WARNING_DTD = '%s: line %s tag "%s" is unapproprieted here.'
encoding = 'UTF-8'


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


def getSampleStyleSheet():
    stylesheet = getBaseStyleSheet()

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


def document_stream(stream, pdf_stream, document_name, is_test=False):
    """
        stream : parser stream
        pdf_stream : reportlab write the pdf into pdf_stream.
        document_name : name of the source file

        Childs : template, stylesheet, story
    """

    stack = []
    story = []
    pdf_stylesheet = getSampleStyleSheet()
    state = 0
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
            elif tag_name == 'body':
                if state == 1:
                    state = 2
                    story += body_stream(stream, tag_name, attributes,
                                         pdf_stylesheet)
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
        _story = list(story), pdf_stylesheet


    doc = SimpleDocTemplate(pdf_stream, pagesize = letter)
    doc.build(story)

    if is_test == True:
        return _story


def body_stream(stream, _tag_name, _attributes, pdf_stylesheet):
    """
        stream : parser stream
    """

    stack = []
    story = []
    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break

        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            if tag_name in ('p','h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                story.append(paragraph_stream(stream, tag_name, attributes,
                                              pdf_stylesheet))
            elif tag_name == 'pre':
                story.append(pre_stream(stream, tag_name, attributes,
                                        pdf_stylesheet))
            elif tag_name == 'hr':
                story.append(hr_stream(stream, tag_name, attributes))
            elif tag_name == 'img':
                widget = img_stream(stream, tag_name, attributes)
                if widget:
                    story.append(widget)
            elif tag_name == 'ol':
                story.extend(ol_stream(stream, tag_name, attributes,
                    pdf_stylesheet))
            elif tag_name == 'ul':
                story.extend(ul_stream(stream, tag_name, attributes, pdf_stylesheet))
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes))

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == 'body':
                break
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes))
    return story


def paragraph_stream(stream , elt_tag_name, elt_attributes, pdf_stylesheet):
    """
        stream : parser stream
    """
    tag_ok=('i', 'em', 'b', 'strong', 'u', 'sup', 'sub','br','small','big','tt')
    stack = []
    story = []
    content = []
    stack.append((elt_tag_name, elt_attributes))
    has_content = False
    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            if tag_name in tag_ok:
                if tag_name in ('i', 'em', 'b', 'strong', 'u', 'sup', 'sub'):
                    content.append(build_start_tag(p_format_map.get(tag_name,
                                                                    'b')))
                elif tag_name == 'br':
                    continue
                elif tag_name == 'a':
                    content += link_stream(stream, tag_name, attributes)
                else:
                    print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                    # unknown tag
                    stack.append((tag_name, attributes))
            else:
                print WARNING_DTD % ('document', line_number, tag_name)

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == elt_tag_name:
                # stack.pop --> stack[0]
                return create_paragraph(pdf_stylesheet, stack.pop(), content)
            elif tag_name in ('i', 'em', 'b', 'strong', 'u', 'sup', 'sub'):
                # Must be upgrade (too slow)
                content.append(build_end_tag(p_format_map.get(tag_name, 'b')))
                content = [''.join(content)]
            elif tag_name == 'br':
                content.append("<br/>")
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes))

        #### TEXT ELEMENT ####
        elif event == TEXT:
            if len(value) > 0:
                # alow to write :
                # <para><u><i>foo</i> </u></para>
                value = XML.encode(value) # entities
                # FIXME
                if has_content and content[-1].endswith('<br/>'):
                    # <p>
                    #   foo          <br />
                    #     bar   <br />     team
                    # </p>
                    # equal
                    # <p>foo <br />bar <br />team</p>
                    value = value.lstrip()
                    content[-1] += value
                else:
                    has_content = True
                    content.append(value)


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
                return create_preformatted(pdf_stylesheet, stack.pop(),
                                           content)
            else:
                print WARNING_DTD % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes))

        #### TEXT ELEMENT ####
        elif event == TEXT:
            if stack:
                # we dont strip the string --> preformatted widget
                value = XML.encode(value) # entities
                content.append(value)


def hr_stream(stream, _tag_name, _attributes):
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
                widget = create_hr(_attributes)
                return widget
        #### TEXT ELEMENT ####
        elif event == TEXT:
            pass
        else:
            print WARNING_DTD % ('document', line_number, tag_name)


def img_stream(stream , _tag_name, _attributes):

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
                widget = create_img(_attributes)
                return widget
        #### TEXT ELEMENT ####
        elif event == TEXT:
            pass
        else:
            print WARNING_DTD % ('document', line_number, tag_name)


def ol_stream(stream , tag_name, attributes, pdf_stylesheet, id = 0):
    """
        stream : parser stream
    """
    stack = []
    INDENT_VALUE = 1 * cm
    story = [Indenter(left=INDENT_VALUE)]
    strid = str(id)
    content = ["<seqDefault id='" + strid + "'/><seqReset id='" + strid + "'/>"]
    has_content = False
    stack.append((tag_name, attributes))
    liopenstate = 0
    attrs = {}
    if exist_attribute(attributes, ['type']):
        attrs['type'] = attributes.get((None,'type'))
        content.append("<seqFormat id='" + strid + "' value='" + attrs['type'] + "'/>")
    else:
        content.append("<seqFormat id='" + strid + "' value='1'/>")

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            if tag_name == 'ol':
                if liopenstate:
                    story.append(create_paragraph(pdf_stylesheet, stack[0], content))
                    content = ["<seqDefault id='" + strid + "'/>"]
                    story += ol_stream(stream, tag_name, attributes,
                                       pdf_stylesheet, id+1)
                else:
                    print WARNING_DTD % ('document', line_number, tag_name)
            elif tag_name == 'ul':
                if liopenstate:
                    story.append(create_paragraph(pdf_stylesheet, stack[0], content))
                    content = []
                    story += ul_stream(stream, tag_name, attributes,
                                       pdf_stylesheet, id+1)
                else:
                    print WARNING_DTD % ('document', line_number, tag_name)
            elif tag_name in ('i', 'em', 'b', 'strong', 'u', 'sup', 'sub'):
                content.append(build_start_tag(p_format_map.get(tag_name,
                                                                'b')))
            elif tag_name == 'li':
                liopenstate=1
                content.append("<bullet bulletIndent='-0.4cm'><seq id='" + strid + "'/>.</bullet>")
            elif tag_name == 'a':
                content += link_stream(stream, tag_name, attributes)
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes))

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == 'ol':
                story.append(create_paragraph(pdf_stylesheet, stack.pop(), content))
                content = []
                story.append(Indenter(left=-INDENT_VALUE))
                return story
            elif tag_name in ('i', 'em', 'b', 'strong', 'u', 'sup', 'sub'):
                content.append(build_end_tag(p_format_map.get(tag_name, 'b')))
            elif tag_name == 'li':
                story.append(create_paragraph(pdf_stylesheet, stack[0], content))
                content = []
                liopenstate = 0
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                # pop the unknown tag --> 1 push => 1 pop
                stack.append((tag_name, attributes))

        #### TEXT ELEMENT ####
        elif event == TEXT:
            if liopenstate:
                # alow to write :
                # <para><u><i>foo</i> </u></para>
                value = XML.encode(value) # entities
                content.append(value)
                has_content = True


def ul_stream(stream , tag_name, attributes, pdf_stylesheet, id = 0):
    """
        stream : parser stream
    """

    stack = []
    INDENT_VALUE=1 * cm
    story = [Indenter(left=INDENT_VALUE)]
    content = []
    has_content = False
    stack.append((tag_name, attributes))
    liopenstate = 0
    strid = str(id)
    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            if tag_name == 'ol':
                if liopenstate:
                    story.append(create_paragraph(pdf_stylesheet, stack[0], content))
                    content = ["<seqDefault id='" + strid + "'/>"]
                    story += ol_stream(stream, tag_name, attributes,
                                       pdf_stylesheet, id+1)
                else:
                    print WARNING_DTD % ('document', line_number, tag_name)
            elif tag_name == 'ul':
                if liopenstate:
                    story.append(create_paragraph(pdf_stylesheet, stack[0], content))
                    content = []
                    story += ul_stream(stream, tag_name, attributes,
                                       pdf_stylesheet, id+1)
                else:
                    print WARNING_DTD % ('document', line_number, tag_name)
            elif tag_name == 'li':
                liopenstate=1
                content.append("<bullet bulletIndent='-0.4cm' font='Symbol'>\xe2\x80\xa2</bullet>")
            elif tag_name in ('i', 'em', 'b', 'strong', 'u', 'sup', 'sub'):
                content.append(build_start_tag(p_format_map.get(tag_name,
                                                                'b')))
            elif tag_name == 'a':
                content += link_stream(stream, tag_name, attributes)
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes))

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == 'ul':
                story.append(create_paragraph(pdf_stylesheet, stack.pop(), content))
                story.append(Indenter(left=-INDENT_VALUE))
                return story
            elif tag_name in ('i', 'em', 'b', 'strong', 'u', 'sup', 'sub'):
                content.append(build_end_tag(p_format_map.get(tag_name, 'b')))
            elif tag_name == 'li':
                liopenstate = 0
                story.append(create_paragraph(pdf_stylesheet, stack[0], content))
                content = []
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes))

        #### TEXT ELEMENT ####
        elif event == TEXT:
             if liopenstate:
                # alow to write :
                # <para><u><i>foo</i> </u></para>
                value = XML.encode(value) # entities
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
    stack.append((tag_name, attributes))
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
                stack.append((tag_name, attributes))

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == 'a':
                content.append("</a>")
                return content
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes))

        #### TEXT ELEMENT ####
        elif event == TEXT:
            if len(value) > 0:
                # alow to write :
                # <para><u><i>foo</i> </u></para>
                value = XML.encode(value) # entities
                content.append(value)
                has_content = True


##############################################################################
# Reportlab widget                                                           #
##############################################################################
def create_paragraph(pdf_stylesheet, element, content):
    """
        Create a reportlab paragraph widget.
    """

    # Now, we strip each value in content before call create_paragraph
    # content = ['Hello', '<i>how are</i>', 'you?']
    # Another choice is to strip the content (1 time) here
    # content = ['  Hello\t\', '\t<i>how are</i>', '\tyou?']
    content = normalize(' '.join(content))
    style, bulletText = build_style(pdf_stylesheet, element)
    return Paragraph(content, style, bulletText)


def build_style(pdf_stylesheet, element):
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
                attr_value = __tab_para_alignment.get(attr_value.upper())
            elif key in ['leftIndent', 'rightIndent']:
                attr_value = rml_value(attr_value)
            style_attr[key] = attr_value

    style_name = parent_style_name
    if element[0] in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
        parent_style_name = element[0]
    parent_style = get_style(pdf_stylesheet, parent_style_name)
    return (ParagraphStyle(style_name, parent=parent_style, **style_attr), bulletText)

    
def create_preformatted(pdf_stylesheet, element, content):
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

    style = get_style(pdf_stylesheet, style_name)
    widget = fn(content, style)
    return widget


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


def create_img(attributes, check_dimension=False):
    """
        Create a reportlab image widget.
        If check_dimension is true and the width and the height attributes
        are not set we return None
    """

    width, height = None, None
    filename = None

    for key, attr_value in attributes.iteritems():
        key = key[1]
        if key == 'src':
            filename = attr_value
        elif key == 'width':
            width = rml_value(attr_value)
        elif key == 'height':
            height = rml_value(attr_value)

    if filename is None:
        print u'/!\ Filename is None'
        return None

    if check_dimension and width == None and height == None:
        print u'/!\ Cannot add an image inside a td without predefined size'
        return None

    if vfs.exists(filename) is False:
        print u"/!\ The filename doesn't exist"
        return None

    # Remote file
    if filename.startswith('http://'):
        filename = StringIO(vfs.open(filename))

    try:
        I = Image(filename)
        if height is not None:
            I.drawHeight = height
        if width is not None:
            I.drawWidth = width
        return I
    except IOError, msg:
        print msg
        return None
    except Exception, msg:
        print msg
        return None


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


def get_color(value):
    raise NotImplementedError


def get_style(stylesheet, name):
    """
       Return the style corresponding to name or the style normal if it does
       not exist.
    """

    if stylesheet.has_key(name):
        return stylesheet[name]
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
