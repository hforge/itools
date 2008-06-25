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
from itools.datatypes import Unicode, XMLContent
from itools.vfs import vfs
from itools.xml import XMLParser, START_ELEMENT, END_ELEMENT, TEXT
import itools.http

#Import from the reportlab Library
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import(getSampleStyleSheet as getBaseStyleSheet,
                                 ParagraphStyle)
from reportlab.lib.units import inch, cm, mm, pica
from reportlab.platypus.flowables import HRFlowable
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Preformatted,
                                Image, Indenter)

encoding = 'UTF-8'
URI = None
# Mapping HTML -> REPORTLAB
P_FORMAT = {'i': 'i', 'em': 'i', 'b': 'b', 'strong': 'b', 'u': 'u',
            'span': 'font', 'sup': 'super', 'sub': 'sub'}

TAG_OK = ('a', 'b', 'big', 'br', 'em', 'i', 'img', 'small', 'span', 'strong',
          'sub', 'sup', 'tt', 'u')

FONT = {'monospace': 'courier', 'times-new-roman': 'times-roman',
        'arial': 'helvetica', 'serif': 'times',
        'sans-serif': 'helvetica', 'helvetica': 'helvetica',
        'symbol': 'symbol'}

# ALIGNMENT
ALIGNMENTS = {'LEFT': TA_LEFT, 'RIGHT': TA_RIGHT, 'CENTER': TA_CENTER,
              'JUSTIFY': TA_JUSTIFY}

TAG_NOT_SUPPORTED = '%s: line %s tag "%s" is currently not supported.'
WARNING_DTD = '%s: line %s tag "%s" is unapproprieted here.'


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
        test_data = list(story), pdf_stylesheet

    doc = SimpleDocTemplate(pdf_stream, pagesize = letter)
    doc.build(story)

    if is_test == True:
        return test_data


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
            if tag_name in ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
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
            elif tag_name in ('ol', 'ul'):
                story.extend(list_stream(stream, tag_name, attributes,
                                         pdf_stylesheet))
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

    stack = []
    story = []
    content = []
    stack.append((elt_tag_name, elt_attributes))
    cpt = 0
    end_tag = False
    has_content = False

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            if tag_name in TAG_OK:
                if tag_name in ('i', 'em', 'b', 'strong', 'u', 'sup', 'sub'):
                    # FIXME
                    tag = P_FORMAT.get(tag_name, 'b')
                    if cpt or has_content:
                        content[-1] += build_start_tag(tag)
                    else:
                        content.append(build_start_tag(tag))
                    cpt += 1
                elif tag_name == 'span':
                    tag = P_FORMAT.get(tag_name)
                    if cpt or has_content:
                        content[-1] += span_stream(stream , tag, attributes)
                    else:
                        content.append(span_stream(stream , tag, attributes))
                    cpt += 1
                elif tag_name == 'br':
                    continue
                elif tag_name == 'a':
                    if cpt or has_content:
                        content[-1] += link_stream(stream, tag_name,
                                                   attributes)
                    else:
                        content.append(link_stream(stream, tag_name,
                                                   attributes))
                    cpt += 1
                else:
                    print TAG_NOT_SUPPORTED % ('document', line_number,
                                               tag_name)
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
            elif tag_name == 'span':
                cpt -= 1
                end_tag = True
                content[-1] += build_end_tag(P_FORMAT.get(tag_name, 'b'))
            elif tag_name in TAG_OK:
                cpt -= 1
                end_tag = True
                content[-1] += build_end_tag(P_FORMAT.get(tag_name, 'b'))
            elif tag_name == 'br':
                content.append('<br/>')
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes))

        #### TEXT ELEMENT ####
        elif event == TEXT:
            if len(value) > 0:
                # alow to write :
                # <para><u><i>foo</i> </u></para>
                value = XMLContent.encode(value) # entities
                # FIXME
                if has_content and content[-1].endswith('<br/>') :
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
                value = XMLContent.encode(value) # entities
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


def list_stream(stream , _tag_name, attributes, pdf_stylesheet, id=0):
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
                    story.append(create_paragraph(pdf_stylesheet, stack[0],
                                                  content))
                    content = ["<seqDefault id='%s'/>" % strid]
                    story += list_stream(stream, tag_name, attributes,
                                         pdf_stylesheet, id+1)
                else:
                    print WARNING_DTD % ('document', line_number, tag_name)
            elif tag_name == 'li':
                li_state = 1
                content.append(bullet)
            elif tag_name in ('i', 'em', 'b', 'strong', 'u', 'sup', 'sub'):
                content.append(build_start_tag(P_FORMAT.get(tag_name, 'b')))
            elif tag_name == 'a':
                content += link_stream(stream, tag_name, attributes)
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes))

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name in ('ul', 'ol'):
                story.append(create_paragraph(pdf_stylesheet, stack.pop(),
                             content))
                content = []
                story.append(Indenter(left=-INDENT_VALUE))
                return story
            elif tag_name in ('i', 'em', 'b', 'strong', 'u', 'sup', 'sub'):
                content.append(build_end_tag(P_FORMAT.get(tag_name, 'b')))
            elif tag_name == 'li':
                story.append(create_paragraph(pdf_stylesheet, stack[0],
                                              content))
                content = []
                li_state = 0
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
                content.append(value)
                has_content = True


def link_stream(stream , _tag_name, attributes):
    """
        stream : parser stream
    """

    content = []
    has_content = False
    attrs = {}
    if exist_attribute(attributes, ['href']):
        attrs['href'] = attributes.get((URI, 'href'))
        # Reencode the entities because the a tags
        # are decoded again by the reportlab para parser.
        href = XMLContent.encode(attrs['href'])
        content.append('<a href="%s">' % href)
    elif exist_attribute(attributes, ['id', 'name'], at_least=True):
        name = attributes.get((URI, 'id'), attributes.get((URI, 'name')))
        content.append('<a name="%s">' % name)

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

        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == 'a':
                content.append('</a>')
                return ''.join(content)
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)

        #### TEXT ELEMENT ####
        elif event == TEXT:
            if len(value) > 0:
                # alow to write :
                # <para><u><i>foo</i> </u></para>
                value = XMLContent.encode(value) # entities
                content.append(value)
                has_content = True


def span_stream(stream , _tag_name, attributes):

    content = []
    tag_stack = []
    attrs = {}
    cpt = 0
    end_tag = False
    has_content = False

    if exist_attribute(attributes, ['style']):
        style = ''.join(attributes.pop((URI, 'style')).split()).rstrip(';')
        if style:
            stylelist = style.split(';')
            for element in stylelist:
                element_list = element.split(':')
                attrs[element_list[0].lower()] = element_list[1].lower()
            if attrs.has_key('color'):
                x = attrs['color']
                if x[0:3] == 'rgb':
                    attrs['color'] = get_color_hexa(x)
                    if attrs['color'] is None:
                        del attrs['color']
            if attrs.has_key('font-family'):
                x = attrs.pop('font-family')
                attrs['face'] = FONT.get(x, 'helvetica')
            if attrs.has_key('font-size'):
                x = attrs.pop('font-size')
                attrs['size'] = font_value(x)
            if attrs.has_key('font-style'):
                x = attrs.pop('font-style')
                if x in ('italic', 'oblique'):
                    tag_stack.append('i')
                elif x != 'normal':
                    print 'Warning font-style not valid'

    # Why not use build_start_tag ?
    attr_str = ''.join([' %s="%s"' % (key, attrs[key])
                        for key in attrs.keys()])
    if attr_str:
        start_tag = '<%s %s>' % (_tag_name, attr_str)
    else:
        start_tag = '<%s>' % _tag_name
    if tag_stack:
        start_tag = '<%s>' % tag_stack

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            if tag_name in TAG_OK:
                if tag_name in ('i', 'em', 'b', 'strong', 'u', 'sup', 'sub'):
                    # FIXME
                    tag = P_FORMAT.get(tag_name, 'b')
                    if cpt or has_content:
                        content[-1] += build_start_tag(tag)
                    else:
                        content.append(build_start_tag(tag))
                    cpt += 1
                elif tag_name == 'span':
                    tag = P_FORMAT.get(tag_name)
                    if cpt or has_content:
                        content[-1] += span_stream(stream, tag, attributes)
                    else:
                        content.append(span_stream(stream, tag, attributes))
                    cpt += 1
                elif tag_name == 'br':
                    continue
                elif tag_name == 'a':
                    if cpt or has_content:
                        content[-1] += link_stream(stream, tag_name,
                                                   attributes)
                    else:
                        content.append(link_stream(stream, tag_name,
                                                   attributes))
                    cpt += 1
                else:
                    print TAG_NOT_SUPPORTED % ('document', line_number,
                                               tag_name)
            else:
                print WARNING_DTD % ('document', line_number, tag_name)


        #### END ELEMENT ####
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == 'span':
                while tag_stack:
                    content[-1] += '<%s>' % tag_stack.pop()
                content[-1] += '</font>'
                return '%s%s' % (start_tag, ' '.join(content))
            elif tag_name in TAG_OK:
                cpt -= 1
                end_tag = True
                content[-1] += build_end_tag(P_FORMAT.get(tag_name, 'b'))
            elif tag_name == 'br':
                content.append('<br/>')
            else:
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)

        #### TEXT ELEMENT ####
        elif event == TEXT:
            if len(value) > 0:
                value = XMLContent.encode(value) # entities
                # FIXME
                if has_content and content[-1].endswith('<br/>') :
                    value = value.lstrip()
                    content[-1] += value
                    end_tag = False
                elif not (len(value.strip()) or has_content):
                    has_content = False
                elif has_content and content[-1].endswith('</span>'):
                    content[-1] += value
                    end_tag = False
                elif end_tag or cpt:
                    content[-1] += value
                    end_tag = False
                else:
                    has_content = True
                    content.append(value)


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

    # DEBUG
    #print 0, content
    content = normalize(' '.join(content))
    #print 1, content
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
                attr_value = ALIGNMENTS.get(attr_value.upper())
            elif key in ['leftIndent', 'rightIndent']:
                attr_value = rml_value(attr_value)
            style_attr[key] = attr_value

    style_name = parent_style_name
    if element[0] in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
        parent_style_name = element[0]
    parent_style = get_style(pdf_stylesheet, parent_style_name)
    return (ParagraphStyle(style_name, parent=parent_style, **style_attr),
            bulletText)


def create_preformatted(pdf_stylesheet, element, content):
    """
        Create a reportlab preformatted widget.
    """

    content = ''.join(content)
    style_name = 'Normal'

    for key, attr_value in element[1].iteritems():
        if key[1] == 'style':
            style_name = attr_value
    style = get_style(pdf_stylesheet, style_name)
    widget = Preformatted(content, style)
    return widget


def create_hr(attributes):
    """
        Create a reportlab hr widget
    """

    attrs = {}
    attrs['width'] = '100%'
    for key in ('width', 'thickness', 'spaceBefore', 'spaceAfter'):
        if exist_attribute(attributes, [key]):
            attrs[key] = rml_value(attributes.get((URI, key)))

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
    elif str_value[-1] == '%':
        value = (int(str_value.rstrip('%')) * style_size) / 100
    else:
        try:
            value = int(str_value)
        except ValueError:
            value = style_size
    return value


def build_start_tag(tag_name, attributes={}):
    """
        Create the XML start tag from his name and his attributes
        span => font (map)
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


def get_color_hexa(x):
    x = x.lstrip('#rgb(').rstrip(')').split(',')
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


def get_style(stylesheet, name):
    """
       Return the style corresponding to name or the style normal if it does
       not exist.
    """

    if stylesheet.has_key(name):
        return stylesheet[name]
    return stylesheet['Normal']


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

    if value == 'None':
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


def is_str(s, check_is_unicode=True):
    """
        Check is str is a string.
    """

    if isinstance(s, str) is False:
        if not check_is_unicode:
            return False
        return isinstance(s, unicode)
    return True
