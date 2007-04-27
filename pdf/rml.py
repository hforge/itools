# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
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
import re
from cStringIO import StringIO

# Import from itools
from itools.datatypes import Unicode, XML
from itools.xml.parser import Parser, START_ELEMENT, END_ELEMENT, TEXT
from itools.stl.stl import stl

# Import from the reportlab Library
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate
from reportlab.platypus import XPreformatted, Preformatted
from reportlab.platypus import Image, Table, TableStyle, Spacer
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, cm
from reportlab.rl_config import defaultPageSize
from reportlab.lib import pagesizes, colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

__tab_para_alignment = {'left': TA_LEFT, 'right': TA_RIGHT, 
                        'center': TA_CENTER, 'justify': TA_JUSTIFY}

encoding = 'UTF-8'
def rmltopdf_test(filename):
    file = open(filename, 'r')
    stream = Parser(file.read())
    return document_stream(stream, StringIO(), True)


def stl_rmltopdf_test(handler, namespace):
    temp = stl(handler, namespace)
    stream = Parser(temp)
    return document_stream(stream, StringIO(), True)


def rmltopdf(filename):
    file = open(filename, 'r')
    stream = Parser(file.read())
    iostream = StringIO()
    document_stream(stream, iostream)
    return iostream.getvalue()


def stl_rmltopdf(handler, namespace):
    temp = stl(handler, namespace)
    stream = Parser(temp)
    iostream = StringIO()
    document_stream(stream, iostream)
    return iostream.getvalue()


def rmlFirstPage(canvas, doc):
    pass


def rmlLaterPages(canvas, doc):
    pass


def document_stream(stream, pdf_stream, is_test=False):
    """ 
        stream : parser stream
        pdf_stream : reportlab write the pdf into pdf_stream
    """

    document_attrs = {'showBoundary': 0,
            'leftMargin': inch,
            'rightMargin': inch,
            'topMargin': inch,
            'bottomMargin': inch,
            'pageSize': pagesizes.A4,
            'title': None,
            'author': None,
            'rotation': 0,
            'showBoundary': 0,
            'allowSplitting': 1
            }

    pdf_stylesheet = getSampleStyleSheet()
    pdf_table_style = {}
    stack = []
    story = []
    while True:
        try:
            event, value, line_number = stream.next()
        except StopIteration:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes, ns_decls = value
            if tag_name == 'document':
                pdf_filename = attributes.get((None, 'filename'), 'noname.pdf')
                stack.append((tag_name, attributes, None))
            elif tag_name == 'template':
                template_stream(stream, tag_uri, tag_name, 
                                attributes, ns_decls, document_attrs)
            elif tag_name == 'stylesheet':
                stylesheet_stream(stream, tag_uri, tag_name, attributes, 
                                ns_decls, pdf_stylesheet, pdf_table_style) 
            elif tag_name == 'story':
              story = story_stream(stream, tag_uri, tag_name, attributes, 
                                   ns_decls, pdf_stylesheet, pdf_table_style)
            else: 
                # unknown tag
                stack.append((tag_name, attributes, None))
        #### END ELEMENT ####   
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == 'document':
                break
            else:
                # unknown tag
                stack.pop()

    #### BUILD PDF ####
    doc = SimpleDocTemplate(pdf_stream, **document_attrs)
    
    if is_test == True:
        _story = list(story)
    doc.build(story, onFirstPage=rmlFirstPage, onLaterPages=rmlLaterPages)
    if is_test == True:
        return (_story, pdf_stylesheet)


def template_stream(stream, _tag_uri, _tag_name, _attributes, _ns_decls, 
                    document_attrs):
    """ """
    stack = []
    stack.append((_tag_name, _attributes, None))
    while True:
        try:
            event, value, line_number = stream.next()
        except StopIteration:
            return 
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes, ns_decls = value
            stack.append((tag_name, attributes, None))
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == _tag_name:
                for key in document_attrs.keys():
                    if _attributes.has_key((None, key)):
                        document_attrs[key] = _attributes[(None, key)]

                if len(document_attrs['pageSize']) == 2:
                    f = get_value_reportlab(document_attrs['pageSize'][0])
                    s = get_value_reportlab(document_attrs['pageSize'][0])
                    document_attrs['pageSize'] = (f, s)
                else:
                    document_attrs['pageSize'] = pagesizes.A4
                document_attrs['rotation'] = \
                        to_int(document_attrs['rotation'])
                document_attrs['leftMargin'] = \
                        get_value_reportlab(document_attrs['leftMargin'])
                document_attrs['rightMargin'] = \
                        get_value_reportlab(document_attrs['rightMargin'])
                document_attrs['topMargin'] = \
                        get_value_reportlab(document_attrs['topMargin'])
                document_attrs['bottomMargin'] = \
                        get_value_reportlab(document_attrs['bottomMargin'])
                
                document_attrs['showBoundary'] = \
                        to_bool(document_attrs['showBoundary'])
                document_attrs['allowSplitting'] = \
                        to_bool(document_attrs['allowSplitting'])

                return
            else:
                stack.pop()


def stylesheet_stream(stream, _tag_uri, _tag_name, _attributes, _ns_decls, 
                      pdf_stylesheet, pdf_table_style):
    """ """
    stack = []
    stack.append((_tag_name, _attributes, None))
    stylesheet_xml = []
    while True:
        try:
            event, value, line_number = stream.next()
        except StopIteration:
            return 
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes, ns_decls = value
            if tag_name == 'initialize':
                pass
            elif tag_name == 'paraStyle':
                stylesheet_xml.append(attributes)
            elif tag_name == 'blockTableStyle':
                tableStyle_stream(stream, tag_uri, tag_name, attributes, 
                                  ns_decls, pdf_stylesheet, pdf_table_style)
            else:
                stack.append((tag_name, attributes, None))

        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == _tag_name:
                build_stylesheet(pdf_stylesheet, stylesheet_xml)
                return
            else:
                pass


def tableStyle_stream(stream, _tag_uri, _tag_name, _attributes, _ns_decls, 
                      pdf_stylesheet, pdf_table_style):
    """ """
    stack = []
    stack.append((_tag_name, _attributes, None))
    current_table_style = []
    while True:
        try:
            event, value, line_number = stream.next()
        except StopIteration:
            return 
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes, ns_decls = value
            if tag_name in ['blockFont', 'blockTextColor', 'blockLeading',
                            'blockAlignment', 'blockValign', 
                            'blockLeftPadding', 'blockRightPadding', 
                            'blockBottomPadding', 'blockTopPadding', 
                            'blockBackground', 'lineStyle']:
                # blockTableStyle child
                pass
            else:
                pass
                #warning_msg('blockTableStyle -> unknown tag child')

            stack.append((tag_name, attributes, None))

        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == _tag_name:
                element = stack.pop()
                id = element[1].get((None, 'id'), None)
                if id is None:
                    pass
                    #warning_msg('blockTableStyle -> id attribute is required')
                else:
                    add_table_style(pdf_table_style, id, current_table_style)
                return
            elif tag_name in ['blockFont', 'blockTextColor', 'blockLeading',
                              'blockAlignment', 'blockValign', 
                              'blockLeftPadding', 'blockRightPadding', 
                              'blockBottomPadding', 'blockTopPadding', 
                              'blockBackground', 'lineStyle']:
                element = stack.pop()
                current_table_style.append(element)
            else:
                stack.pop()


def story_stream(stream, _tag_uri, _tag_name, _attributes, _ns_decls, 
                 pdf_stylesheet, pdf_table_style):
    stack = []
    story = []
    stack.append((_tag_name, _attributes, None))
    while True:
        try:
            event, value, line_number = stream.next()
        except StopIteration:
            return story
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes, ns_decls = value
            if tag_name in ['h1', 'h2', 'h3']:
                story.append(heading_stream(stream, tag_uri, tag_name, 
                             attributes, ns_decls, pdf_stylesheet))
            elif tag_name == 'para':
                widget = paragraph_stream(stream, tag_uri, tag_name, 
                                          attributes, ns_decls, pdf_stylesheet)
                if widget is not None:
                    story.append(widget)
            elif tag_name in ['pre', 'xpre']:
                widget = preformatted_stream(stream, tag_uri, tag_name,
                                             attributes, ns_decls, 
                                             pdf_stylesheet)
                if widget is not None:
                    story.append(widget)
            elif tag_name == 'image':
                widget = image_stream(stream, tag_uri, tag_name,
                                      attributes, ns_decls, pdf_stylesheet)
                if widget is not None:
                    story.append(widget)
            elif tag_name == 'spacer':
                widget = spacer_stream(stream, tag_uri, tag_name,
                                      attributes, ns_decls, pdf_stylesheet)
                if widget is not None:
                    story.append(widget)
            elif tag_name == 'blockTable':
                widget = table_stream(stream, tag_uri, tag_name,
                                      attributes, ns_decls, pdf_stylesheet,
                                      pdf_table_style)
                if widget is not None:
                    story.append(widget)
            else:
                stack.append((tag_name, attributes, None))
        #### END ELEMENT ####   
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            prev_elt = stack[-1]
            if prev_elt[0] == _tag_name:
                return story
            else:
                stack.pop()

        #### TEXT ELEMENT ####   
        elif event == TEXT:
            if stack:
                prev_elt = stack[-1]
                if prev_elt[0] == _tag_name:
                    value = strip(Unicode.decode(value, encoding), True)
                    if len(value) > 0 and value != ' ':
                        value = XML.encode(value) # entities
                        story.append(value)


def heading_stream(stream, _tag_uri, _tag_name, _attributes, _ns_decls, 
                   pdf_stylesheet):
    content = []
    stack = []
    stack.append((_tag_name, _attributes, None))
    try:
        style = pdf_stylesheet[_tag_name]
    except KeyError:
        style = pdf_stylesheet['Normal']

    while True:
        try:
            event, value, line_number = stream.next()
        except StopIteration:
            return None
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes, ns_decls = value
            content.append(build_start_tag(tag_name, attributes))
            stack.append((tag_name, attributes, None))
        #### END ELEMENT ####   
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == _tag_name:
                content = ''.join(content)
                widget = Paragraph(content, style)
                return widget 
            else:
                element = stack.pop()
                content.append(build_end_tag(element[0]))

        #### TEXT ELEMENT ####   
        elif event == TEXT:
            if stack:
                value = strip(Unicode.decode(value, encoding), True)
                if len(value) > 0 and value != ' ':
                    value = XML.encode(value) # entities
                    content.append(value)


def paragraph_stream(stream, _tag_uri, _tag_name, _attributes, _ns_decls, 
                     pdf_stylesheet):
    content = []
    stack = []
    stack.append((_tag_name, _attributes, None))

    while True:
        try:
            event, value, line_number = stream.next()
        except StopIteration:
            return None
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes, ns_decls = value
            content.append(build_start_tag(tag_name, attributes))
            stack.append((tag_name, attributes, None))
        #### END ELEMENT ####   
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == _tag_name:
                content = ''.join(content)
                element = stack.pop()
                widget = create_paragraph(pdf_stylesheet, element, content)
                return widget 
            else:
                element = stack.pop()
                content.append(build_end_tag(element[0]))

        #### TEXT ELEMENT ####   
        elif event == TEXT:
            if stack:
                value = strip(Unicode.decode(value, encoding), True)
                #if len(value) > 0 and value != ' ':
                # alow to write : <para><u><i>Choix de l'appareillage</i> </u></para>
                if len(value) > 0:
                    value = XML.encode(value) # entities
                    content.append(value)


def preformatted_stream(stream, _tag_uri, _tag_name, _attributes, _ns_decls, 
                     pdf_stylesheet):
    content = []
    stack = []
    stack.append((_tag_name, _attributes, None))
    try:
        style = pdf_stylesheet[_tag_name]
    except KeyError:
        style = pdf_stylesheet['Normal']

    while True:
        try:
            event, value, line_number = stream.next()
        except StopIteration:
            return None
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes, ns_decls = value
            content.append(build_start_tag(tag_name, attributes))
            stack.append((tag_name, attributes, None))
        #### END ELEMENT ####   
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == _tag_name:
                content = ''.join(content)
                element = stack.pop()
                widget = create_preformatted(pdf_stylesheet, element, content)
                return widget 
            else:
                element = stack.pop()
                content.append(build_end_tag(element[0]))

        #### TEXT ELEMENT ####   
        elif event == TEXT:
            if stack:
                # we dont strip the string --> preformatted widget
                value = XML.encode(Unicode.decode(value, encoding)) # entities
                content.append(value)

def image_stream(stream, _tag_uri, _tag_name, _attributes, _ns_decls, 
                 pdf_stylesheet, check_dimension=False):
    stack = []
    stack.append((_tag_name, _attributes, None))

    while True:
        try:
            event, value, line_number = stream.next()
        except StopIteration:
            return None
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes, ns_decls = value
            stack.append((tag_name, attributes, None))
        #### END ELEMENT ####   
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == _tag_name:
                element = stack.pop()
                widget = create_image(element, check_dimension)
                return widget 
            else:
                stack.pop()

        #### TEXT ELEMENT ####   
        elif event == TEXT:
            pass

def spacer_stream(stream, _tag_uri, _tag_name, _attributes, _ns_decls, 
                  pdf_stylesheet):
    stack = []
    stack.append((_tag_name, _attributes, None))

    while True:
        try:
            event, value, line_number = stream.next()
        except StopIteration:
            return None
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes, ns_decls = value
            stack.append((tag_name, attributes, None))
            #warning_msg('Spacer can not have child')
        #### END ELEMENT ####   
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == _tag_name:
                element = stack.pop()
                widget = create_spacer(element)
                return widget 
            else:
                element = stack.pop()

        #### TEXT ELEMENT ####   
        elif event == TEXT:
            pass
            #if stack:
            #    warning_msg('Spacer can not have containt')


def table_stream(stream, _tag_uri, _tag_name, _attributes, _ns_decls, 
                 pdf_stylesheet, pdf_table_style):
    data_table = None
    table_td = None
    stack = []
    stack.append((_tag_name, _attributes, None))

    data_table = []
    style_id = _attributes.get((None, 'style'), None)
    style_table = pdf_table_style.get(style_id, TableStyle())
    rowHeights_table = _attributes.get((None, 'rowHeights'), None)
    colWidths_table = _attributes.get((None, 'colWidths'), None)
    # reportlab default value
    splitByRow_table = 1
    repeatRows_table = to_int(_attributes.get((None, 'repeatRows'), 1), 1)

    if rowHeights_table is not None:
        rowHeights_table_tab = rowHeights_table.split(',')
        rowHeights_table = []
        for rh in rowHeights_table_tab:
            rowHeights_table.append(get_value_reportlab(rh))

    if colWidths_table is not None:
        colWidths_table_tab = colWidths_table.split(',')
        colWidths_table = []
        for cw in colWidths_table_tab:
            colWidths_table.append(get_value_reportlab(cw))

    while True:
        try:
            event, value, line_number = stream.next()
        except StopIteration:
            return None
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes, ns_decls = value
            push = True
            if tag_name == 'tr':
                table_tr = []
                end_tag_tr = False
            elif tag_name == 'td':
                table_td = []
                end_tag_td = False
            elif tag_name == 'image':
                if stack[-1][0] == 'td':
                    push = False
                    widget = image_stream(stream, tag_uri, tag_name,
                                          attributes, ns_decls, pdf_stylesheet,
                                          True)
                    if widget is not None:
                        table_td.append(widget)
                    #else:
                    #    print 'image widget is None'
                else:
                    pass
                    #warning_msg('tr tags can only have td childs')
            elif tag_name == 'para':
                if stack[-1][0] == 'td':
                    push = False
                    widget = paragraph_stream(stream, tag_uri, tag_name,
                                              attributes, ns_decls, 
                                              pdf_stylesheet)
                    if widget is not None:
                        table_td.append(widget)
                else:
                    pass
                    #warning_msg('tr tags can only have td childs --> %s' 
                    #            % tag_name)
            
            elif tag_name in ['pre', 'xpre']:
                if stack[-1][0] == 'td':
                    push = False
                    widget = preformatted_stream(stream, tag_uri, tag_name,
                                                 attributes, ns_decls, 
                                                pdf_stylesheet)
                    if widget is not None:
                        table_td.append(widget)
                else:
                    pass
                    #warning_msg('tr tags can only have td childs --> %s' 
                    #            % tag_name)
            
            elif tag_name == 'spacer':
                if stack[-1][0] == 'td':
                    push = False
                    widget = spacer_stream(stream, tag_uri, tag_name,
                                              attributes, ns_decls, 
                                              pdf_stylesheet)
                    if widget is not None:
                        table_td.append(widget)
                else:
                    pass
                    #warning_msg('tr tags can only have td childs --> %s' 
                    #            % tag_name)
            
            elif tag_name == 'blockTable':
                if stack[-1][0] == 'td':
                    push = False
                    widget = table_stream(stream, tag_uri, tag_name,
                                              attributes, ns_decls, 
                                              pdf_stylesheet, pdf_table_style)
                    if widget is not None:
                        table_td.append(widget)
                else:
                    pass
                    #warning_msg('tr tags can only have td childs --> %s' 
                    #            % tag_name)


            if push:
                stack.append((tag_name, attributes, None))
        #### END ELEMENT ####   
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if stack[-1][0] == _tag_name:
                element = stack.pop()
                widget = Table(data_table, colWidths_table, 
                               rowHeights_table, style_table,
                               splitByRow=splitByRow_table, 
                               repeatRows=repeatRows_table)
                return widget
            elif stack[-1][0] == 'tr':
                data_table.append(table_tr)
                stack.pop()
                end_tag_tr = True
                table_tr = None
            elif stack[-1][0] == 'td':
                end_tag_td = True
                if len(table_td) == 1:
                    table_td = table_td[0]
                table_tr.append(table_td)
                table_td = None
                stack.pop()

        #### TEXT ELEMENT ####   
        elif event == TEXT:
            if stack[-1][0] == 'blockTable':
                pass
            elif stack[-1][0] == 'tr':
                pass
            elif stack[-1][0] == 'td':
                value = strip(Unicode.decode(value, encoding))
                if len(value) > 0 and value != ' ':
                    value = XML.encode(value) # entities
                    table_td.append(value)
            else:
                pass
                #warning_msg('blockTable child must be on of these tags: tr, td')


###############################################################################
# FUNCTION

def warning_msg(msg):
    """ """
    print '** Warning ** : %s' % msg

def strip(str, least=False):
    """ 
        Strip a string
        Remove all ' ', '\n', '\r' and '\t' 
        at the begin and the end of the string
    """
    # start space
    m = re.search('^((\r|\n|\t)+|( )+)*', str)
    if m is not None and m.group(0) != '':
        str = ' ' + str[len(m.group(0)):]

    # end space
    m = re.search('((\r|\n)+|( )+)*\Z', str)
    if m is not None and m.group(0) != '':
        str = str[:-len(m.group(0))] + ' '

    return str

def build_start_tag(tag_name, attributes):
    """ """
    attr_str = ''.join([' %s="%s"' % (key[1], attributes[key])  
                        for key in attributes.keys()])
    return '<%s%s>' % (tag_name, attr_str)


def build_end_tag(tag_name):
    """ """
    return '</%s>' % tag_name


def create_paragraph(pdf_stylesheet, element, content):
    """ """
    parent_style = 'Normal'
    style_attr = {}
    content = ''.join(content)
    bulletText = None

    for key, attr_value in element[1].iteritems():
        key = key[1]
        if key == 'style':
            parent_style = attr_value
        elif key == 'bulletText':
            bulletText = attr_value
        else:
            if key == 'alignment':
                attr_value = __tab_para_alignment.get(attr_value, 
                                               __tab_para_alignment['left'])
            elif key in ['leftIndent', 'rightIndent']:
                attr_value = get_value_reportlab(attr_value)

            style_attr[key] = attr_value

    if not pdf_stylesheet.has_key(parent_style):
        parent_style = 'Normal'

    style = ParagraphStyle('', parent=pdf_stylesheet[parent_style], 
                           **style_attr)
    return Paragraph(content, style, bulletText)


def create_preformatted(pdf_stylesheet, element, content):
    """ """
    content = ''.join(content)
    style_name = 'Normal'
    
    for key, attr_value in element[1].iteritems():
        if key[1] == 'style':
            style_name = attr_value

    if element[0] == 'pre':
        fn = Preformatted
    else:
        fn = XPreformatted

    if not pdf_stylesheet.has_key(style_name):
        style_name = 'Normal'
  
    if content == '':
        return None
    else:
        widget = fn(content, pdf_stylesheet[style_name])
        return widget


def create_image(element, check_dimension):
    """ """
    width, height = None, None
    filename = None

    for key, attr_value in element[1].iteritems():
        key = key[1]
        if key == 'file':
            filename = attr_value
        elif key == 'width':
            width = float(attr_value)
        elif key == 'height':
            height = float(attr_value)
    
    if filename is None:
        return None

    if check_dimension and width == None and height == None:
        #warning_msg('Image tag: width and height attributes are required')
        return None

    # Image dont throw exception if file dont exist
    # perhaps bug ?
    try:
        f = open(filename, 'r')
        f.close()
    except IOError, msg:
        #warning_msg(msg)
        return None

    try:
        I = Image(filename)
        if not width is None:
            I.drawHeight = width
        if not height is None:
            I.drawWidth = height
        return I
    except IOError, msg:
        warnings(msg)
        return None
    except Exception, msg:
        #warning_msg(msg)
        return None


def create_spacer(element):
    """ """
    width, length = 0, None

    for key, attr_value in element[1].iteritems():
        key = key[1]
        if key == 'width':
            width = get_value_reportlab(attr_value)
        elif key == 'length':
            length = get_value_reportlab(attr_value)

    if length != None:
        return Spacer(width, length)
    else:
        #warning_msg('Spacer length attribute is required')
        return None


def build_stylesheet(pdf_stylesheet, styles):
    """ """
    for style in styles:
        style_attr = {}
        name = ''
        parent_style = None
        for key, attr_value in style.iteritems():
            key = key[1]

            if key in ['fontSize', 'leading', 'leftIndent', 'rightIndent', 
                       'firstLineIndent', 'spaceBefore', 'spaceAfter',
                       'bulletIndent']:
                attr_value = get_value_reportlab(attr_value)

            if key == 'name':
                name = attr_value
            elif key == 'parent':
                parent_style = attr_value
            else:
                style_attr[key] = attr_value

        if not pdf_stylesheet.has_key(parent_style):
            parent_style = 'Normal'

        if style_attr.has_key('fontSize') and not style_attr.has_key('leading'):
            style_attr['leading'] = 1.2 * float(style_attr['fontSize'])

        try:
            nstyle = ParagraphStyle(name, parent=pdf_stylesheet[parent_style], 
                                    **style_attr)
            pdf_stylesheet.add(nstyle)
        except KeyError:
            new_style= pdf_stylesheet[name]
            for key, value in style_attr.iteritems():
                setattr(new_style, key, value)


def add_table_style(pdf_table_style, id, table_style):
    """ """
    exist = pdf_table_style.get(id, None)
    if exist is None:
        style = TableStyle()
        for elt in table_style:
            elt_id, attrs, xxx = elt
            # default start & stop
            start = (0, 0)
            stop = (-1, -1)
            attr = {} # attributes bag 
            for key, value in attrs.iteritems():
                key = key[1]
                # start and stop value
                if key in  ['start', 'stop']:
                    t = value.split(',')
                    _tuple = []
                    for v in t:
                        try:
                            _tuple.append(int(float(v)))
                        except ValueError:
                            pass
                    if len(_tuple) >= 2:
                        if key == 'start':
                            start = tuple(_tuple)
                        else:
                            stop = tuple(_tuple)
                else:
                    attr[key] = value
                
            attr['start'] = start
            attr['stop'] = stop
            if elt_id == 'blockTextColor':
                if attr.has_key('colorName'):
                    attr['colorName'] = getattr(colors, attr['colorName'], 
                                                colors.black)
                    style.add('TEXTCOLOR', attr['start'], attr['stop'], 
                              attr['colorName'])
                    #warning_msg('TEXTCOLOR, start=%s, stop=%s, colorName=%s' % 
                    #           (attr['start'], attr['stop'], attr['colorName']))
                else:
                    pass
                    #warning_msg('blockTextColor has one required attribute: '\
                    #            'colorName')
            elif elt_id == 'blockFont':
                if attr.has_key('name') == True:
                    # fontname, optional fontsize and optional leading
                    if attr.has_key('size') == False:
                        style.add('FONT', attr['start'], attr['stop'], 
                                  attr['name'])
                    else:
                        if attr.has_key('leading') == False:
                            attr['size'] = to_float(attr['size'])
                            style.add('FONT', attr['start'], attr['stop'], 
                                  attr['name'], attr['size'])
                        else:
                            attr['size'] = to_float(attr['size'])
                            attr['leading'] = to_float(attr['leading'])

                            style.add('FONT', attr['start'], attr['stop'], 
                                  attr['name'], attr['size'], attr['leading'])
                else:
                    pass
                    #warning_msg('blockFont has one required attribute: name')
            
            elif elt_id == 'blockBackground':
                if attr.has_key('colorName') == True:
                    attr['colorName'] = getattr(colors, attr['colorName'], 
                                                colors.black)
                    style.add('BACKGROUND', attr['start'], attr['stop'], 
                              attr['colorName'])
                else:
                    pass
                    #warning_msg('blockBackground has one required attribute: '\
                    #            'colorName')
            
            elif elt_id == 'blockLeading':
                if attr.has_key('length') == True:
                    attr['length'] = to_float(attr['length'])
                    style.add('LEADING', attr['start'], attr['stop'], 
                              attr['length'])
                else:
                    pass
                    #warning_msg('blockLeading has one required attribute: '\
                    #            'length')
                      
            elif elt_id == 'blockAlignment':
                if attr.has_key('value') == True:
                    if attr['value'] not in ['LEFT', 'RIGHT', 'CENTER', 
                                             'CENTRE']:
                        attr['value'] = 'LEFT'
                        #warning_msg('blockAlignment value attribute must be '\
                        #            'one of these values : LEFT, RIGHT,  '\
                        #            'CENTER, CENTRE')

                    style.add('ALIGNMENT', attr['start'], attr['stop'], 
                              attr['value'])
                else:
                    pass
                    #warning_msg('blockAlignment has one required attribute: '\
                    #            'value')

            elif elt_id == 'blockValign':
                if attr.has_key('value') == True:
                    if attr['value'] not in ['TOP', 'MIDDLE', 'BOTTOM']:
                        attr['value'] = 'BOTTOM'
                        #warning_msg('blockValign value attribute must be one '\
                        #            'of these values : TOP, MIDDLE, BOTTOM')

                    style.add('VALIGN', attr['start'], attr['stop'], 
                              attr['value'])
                else:
                    pass
                    #warning_msg('blockValign has one required attribute: value')

            elif elt_id in ['blockLeftPadding', 'blockRightPadding', 
                            'blockTopPadding', 'blockBottomPadding']:
                if attr.has_key('length') == True:
                    attr['length'] = get_value_reportlab(attr['length'])
                    style.add(elt_id[5:].upper(), attr['start'], attr['stop'], 
                              attr['length'])
                else:
                    pass
                    #warning_msg('block[Left,Right,Top,Bottom]Padding has one '\
                    #            'required attribute: length')
            
            elif elt_id == 'lineStyle':
                kind_ok = attr.has_key('kind')
                color_ok = attr.has_key('colorName')
                if kind_ok and color_ok:
                    if attr['kind'] not in ['GRID', 'BOX', 'OUTLINE', 
                                            'INNERGRID', 'LINEBELOW', 
                                            'LINEABOVE', 'LINEBEFORE', 
                                            'LINEAFTER']:
                        pass
                        #warning_msg('lineStyle value attribute must be one '\
                        #            'of these values : TOP, MIDDLE, BOTTOM')
                    else:
                        attr['colorName'] = getattr(colors, attr['colorName'], 
                                                   colors.black)
                        if attr.has_key('thickness') == False:
                            attr['thickness'] = 1
                        attr['thickness'] = to_float(attr['thickness'], 1)

                        style.add(attr['kind'], attr['start'], attr['stop'], 
                                  attr['thickness'], attr['colorName'])
                else:
                    pass
                    #warning_msg('lineStyle has two required attributes: '\
                    #            'kind and colorName')

        pdf_table_style[id] = style
    else:
        pass
        #warning_msg('tableStyle width id "%s" already exist' % id)


def is_str(str, check_is_unicode=True):
    """ """
    if type(str) != type(''):
        if not check_is_unicode:
            return False
        return type(str) == type(u'')
    return True


def to_float(str, default=0):
    """ 
        Return the float value of str.
        If ValueError exception is raised return default value
    """

    if type(default) != type(0.0) and type(default) != type(0):
        default = 0.0
    try:
        return float(str)
    except ValueError:
        return default
    except:
        return default


def to_int(str, default=0):
    """ 
        Return the integer value of str.
        If ValueError exception is raised return default value
    """
    
    if type(default) != type(0):
        default = 0
    try:
        return int(str)
    except ValueError:
        return default
    except:
        return default

def to_bool(str, default=False):
    """
         Return the boolean value of str.
    """

    if str == 'false':
        return False
    elif str == 'true':
        return True
    else:
        if default in [False, True]:
            return default
        else:
            return False


def get_value_reportlab(value, default=None):
    """ 
       Return the reportlab value of value
       only if value is a string
       '2cm' -> 2 * cm
       '2in' -> 2 * inch
       '2%' -> '2%'
    """
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
    elif value[-1:] == '%':
        return value
    
    try:
        value = float(value) * coef
    except ValueError:
        value = default
    return value
