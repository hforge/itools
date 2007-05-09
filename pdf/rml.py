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

###############################################################################
# Parastyle bulletsize bug fixed
# better implementation of pageSize attribute
# blockTableStyle tag inside blockTable implemented 
# paraStyle alignment bug fixed
# blockTable td bug fixed
# docinit tag implemented
# registerTTFont tag implemeted

# Import from the Standard Library
import re
from cStringIO import StringIO
import logging

# Import from itools
from itools.datatypes import Unicode, XML
from itools.xml.parser import Parser, START_ELEMENT, END_ELEMENT, TEXT
from itools.stl.stl import stl

# Import from the reportlab Library
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, PageTemplate
from reportlab.platypus import XPreformatted, Preformatted, Frame, FrameBreak
from reportlab.platypus import NextPageTemplate, KeepInFrame, PageBreak
from reportlab.platypus import Image, Table, TableStyle, Spacer
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, cm, mm, pica
from reportlab.rl_config import defaultPageSize
from reportlab.lib.pagesizes import letter, legal, elevenSeventeen
from reportlab.lib.pagesizes import A0, A1, A2, A3, A4, A5, A6
from reportlab.lib.pagesizes import B0, B1, B2, B3, B4, B5, B6
from reportlab.lib.pagesizes import landscape, portrait
from reportlab.lib import pagesizes, colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

__tab_para_alignment = {'left': TA_LEFT, 'right': TA_RIGHT, 
                        'center': TA_CENTER, 'justify': TA_JUSTIFY}
__tab_page_size = {'letter': letter, 'legal': legal, 
                   #'elevenSeventeen': elevenSeventeen,
                   'A0': A0, 'A1': A1, 'A2': A2, 'A3': A3, 
                   'A4': A4, 'A5': A5, 'A6': A6,
                   'B0': B0, 'B1': B1, 'B2': B2, 'B3': B3, 
                   'B4': B4, 'B5': B5, 'B6': B6}

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
        pdf_stream : reportlab write the pdf into pdf_stream.

        Childs : template, stylesheet, story
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
    # tag alias
    # Aliases allow you to assign more than one name to a paragraph style.
    alias_style = {} 
    page_templates = []
    stack = []
    story = []
    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes, ns_decls = value
            if tag_name == 'document':
                pdf_filename = attributes.get((None, 'filename'), 'noname.pdf')
                stack.append((tag_name, attributes, None))
            elif tag_name == 'docinit':
                docinit_stream(stream, tag_uri, tag_name, attributes, ns_decls)
            elif tag_name == 'template':
                page_templates = template_stream(stream, tag_uri, tag_name, 
                                attributes, ns_decls, document_attrs)
            elif tag_name == 'stylesheet':
                alias_style = stylesheet_stream(stream, tag_uri, tag_name, 
                                                attributes, ns_decls, 
                                                pdf_stylesheet, 
                                                pdf_table_style, alias_style)
            elif tag_name == 'story':
              story = story_stream(stream, tag_uri,tag_name, attributes,
                                   ns_decls, pdf_stylesheet, pdf_table_style,
                                   alias_style)
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
    doc.addPageTemplates(page_templates)

    if is_test == True:
        _story = list(story)
    doc.build(story, onFirstPage=rmlFirstPage, onLaterPages=rmlLaterPages)
    if is_test == True:
        return (_story, pdf_stylesheet)


def docinit_stream(stream, _tag_uri, _tag_name, _attributes, _ns_decls):
    """ """

    stack = []
    stack.append((_tag_name, _attributes, None))

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            return
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes, ns_decls = value
            stack.append((tag_name, attributes, None))
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            prev_elt = stack[-1]
            if prev_elt[0] == _tag_name:
                if tag_name == _tag_name:
                    return

            elif prev_elt[0] == 'registerTTFont':
                attrs = prev_elt[1]
                # <registerTTFont faceName="rina" fileName="rina.ttf"/>
                face_name = attrs.get((None, 'faceName'))
                file_name = attrs.get((None, 'fileName'))

                if face_name is None or file_name is None:
                    # not well formed
                    pass

                ttfont = TTFont(face_name, file_name)
                pdfmetrics.registerFont(ttfont)

            stack.pop()


def template_stream(stream, _tag_uri, _tag_name, _attributes, _ns_decls, 
                    document_attrs):
    """
        Get the document attributes and create the document templates.
        Child : pageTemplate
    """

    stack = []
    stack.append((_tag_name, _attributes, None))
    page_templates = []
    page_template_data = None
    show_boundary = False

    for key in document_attrs.keys():
        if _attributes.has_key((None, key)):
            document_attrs[key] = _attributes[(None, key)]
    
    document_attrs['pageSize'] = get_value_page_size(document_attrs['pageSize'])
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
        to_int(document_attrs['showBoundary'], 0)
    document_attrs['allowSplitting'] = \
        to_bool(document_attrs['allowSplitting'])

    show_boundary = document_attrs['showBoundary']

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes, ns_decls = value

            if tag_name == 'pageTemplate':
                 page_template_data = {'frame':[]}

            stack.append((tag_name, attributes, None))
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            prev_elt = stack[-1]
            if prev_elt[0] == _tag_name:
                if tag_name == _tag_name:
                    return page_templates

            elif prev_elt[0] == 'pageTemplate':
                if tag_name == 'pageTemplate':
                    attrs = prev_elt[1]
                    id = attrs.get((None, 'id'))
                    rotation = attrs.get((None, 'rotation'), 0)
                    page_size = attrs.get((None, 'pageSize'))
                    page_size = get_value_page_size(page_size)

                    if id is None:
                        # tag not well formed
                        pass
                    else:
                        template_attrs = {'id': id, 
                                      'frames': page_template_data['frame'], 
                                      'pagesize': page_size}

                        page_template = PageTemplate(**template_attrs)
                        page_templates.append(page_template)
                    page_template_data = None
            elif prev_elt[0] == 'frame':
                if tag_name == 'frame' and page_template_data is not None:
                    attrs = prev_elt[1]
                    id = attrs.get((None, 'id'))
                    x1 = get_value_reportlab(attrs.get((None, 'x1')), None)
                    y1 = get_value_reportlab(attrs.get((None, 'y1')), None)
                    if is_str(x1) and x1.find('%') != -1:
                        x1 = get_value_from_percentage(x1, 
                                document_attrs['pageSize'][0])
                    else:
                        x1 = to_float(x1)

                    if is_str(y1) and y1.find('%') != -1:
                        y1 = get_value_from_percentage(y1, 
                                document_attrs['pageSize'][1])
                    else:
                        y1 = to_float(y1)

                    width = get_value_reportlab(attrs.get((None, 'width')))
                    if is_str(width) and width.find('%') != 1:
                        width = get_value_from_percentage(width,
                                  document_attrs['pageSize'][0])
                    else:
                        width = to_float(width)

                    height = get_value_reportlab(attrs.get((None, 'height')))
                    if is_str(height) and height.find('%') != 1:
                        height = get_value_from_percentage(height,
                                  document_attrs['pageSize'][1])
                    else:
                        height = to_float(height)
                
                    not_ok = x1 is None or y1 is None or width is None \
                            or height is None or id is None
                    if not_ok:
                        # frame tag not well formed
                        pass
                    else:
                        frame_attrs = {'id': id, 'showBoundary': show_boundary,
                                       'leftPadding': 0, 'bottomPadding': 0,
                                       'rightPadding': 0, 'topPadding': 0, 
                                       'id': id, 'showBoundary': show_boundary}


                        frame = Frame(x1, y1, width, height, **frame_attrs)
                        page_template_data['frame'].append(frame)
            
            stack.pop()


def stylesheet_stream(stream, _tag_uri, _tag_name, _attributes, _ns_decls, 
                      pdf_stylesheet, pdf_table_style, alias_style):
    """ 
        Stylesheet define the different style of the document
        Childs : initialize, paraStyle, blockTableStyle
    """
    
    stack = []
    stack.append((_tag_name, _attributes, None))
    stylesheet_xml = []
    alias_style = {}
    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes, ns_decls = value
            if tag_name == 'initialize':
                alias_style = {}
                initialize_stream(stream, tag_uri, tag_name, attributes, 
                                  ns_decls, pdf_stylesheet, alias_style)
            elif tag_name == 'paraStyle':
                stylesheet_xml.append(attributes)
            elif tag_name == 'blockTableStyle':
                tableStyle_stream(stream, tag_uri, tag_name, attributes, 
                                  ns_decls, pdf_stylesheet, pdf_table_style)
            else:
                # unknown tag
                stack.append((tag_name, attributes, None))

        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == _tag_name:
                build_stylesheet(pdf_stylesheet, stylesheet_xml)
                return alias_style
            else:
                pass


def initialize_stream(stream, _tag_uri, _tag_name, _attributes, 
                      _ns_decls, pdf_stylesheet, alias_style):
    """ 
        Generate the document alias for the paragraph style
        Childs : alias
    """
    
    stack = []
    stack.append((_tag_name, _attributes, None))
    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes, ns_decls = value
            if tag_name == 'alias':
                id = attributes.get((None, 'id'))
                value = attributes.get((None, 'value'))
                if id is not None and value is not None:
                    if is_alias_style(alias_style, value) == True:
                        alias_style[id] = get_style_name(pdf_stylesheet, 
                                                         alias_style, value)
                    else:
                        if value[:6] == 'style.':
                            value = value[6:]
                        alias_style[id] = value
            stack.append((tag_name, attributes, None))
        #### END ELEMENT ####   
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == _tag_name:
                return
            else:
                stack.pop()

        #### TEXT ELEMENT ####   
        elif event == TEXT:
            pass


def tableStyle_stream(stream, _tag_uri, _tag_name, _attributes, _ns_decls, 
                      pdf_stylesheet, pdf_table_style):
    """  
       Childs : blockFont, blockTextColor, blockLeading, blockAlignment, 
                blockValign, blockLeftPadding, blockRightPadding, 
                blockBottomPadding, blockTopPadding, blockBackground, lineStyle
    """
    
    stack = []
    stack.append((_tag_name, _attributes, None))
    id = _attributes.get((None, 'id'), None)
    current_table_style = []
    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes, ns_decls = value
            stack.append((tag_name, attributes, None))
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == _tag_name:
                element = stack.pop()
                id = element[1].get((None, 'id'), None)
                if id is None:
                    # tag not well formed
                    pass
                else:
                    add_table_style(pdf_table_style, id, current_table_style)
                return id
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
                 pdf_stylesheet, pdf_table_style, alias_style):
    """
        Create the document 'story'.
        Childs : setNextTemplate, nextPage, nextFrame, keepInFrame, h1, h2, h3, 
                 para, pre, xpre, image, spacer, blockTable

        return (first_page_template, story)
    """
    
    stack = []
    story = []
    stack.append((_tag_name, _attributes, None))
    # FIXME firstPageTemplate is not yet implemeted
    # first_page_template = _attributes.get((None, 'firstPageTemplate'), None)

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            return story
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes, ns_decls = value
            if tag_name == 'setNextTemplate':
                name = attributes.get((None, 'name'))
                #current_template_name = name
                if name is not None:
                    story.append(NextPageTemplate(name))
                stack.append((tag_name, attributes, None))
            elif tag_name == 'nextPage':
                # FIXME attribute 'suppress' not implemented
                story.append(PageBreak())
                #if current_template_name is not None:
                #    story.append(NextPageTemplate(current_template_name))
                stack.append((tag_name, attributes, None))
            elif tag_name == 'nextFrame':
                #if attributes.has_key((None, 'name')) == False:
                story.append(FrameBreak())
                stack.append((tag_name, attributes, None))
            elif tag_name == 'keepInFrame':
                widget = keepinframe_stream(stream, tag_uri, tag_name,
                                             attributes, ns_decls, 
                                             pdf_stylesheet, pdf_table_style,
                                             alias_style)
                if widget is not None:
                    story.append(widget)
            elif tag_name in ['h1', 'h2', 'h3']:
                story.append(heading_stream(stream, tag_uri, tag_name, 
                             attributes, ns_decls, pdf_stylesheet, alias_style))
            elif tag_name == 'para':
                widget = paragraph_stream(stream, tag_uri, tag_name, 
                                          attributes, ns_decls, pdf_stylesheet,
                                          alias_style)
                if widget is not None:
                    story.append(widget)
            elif tag_name in ['pre', 'xpre']:
                widget = preformatted_stream(stream, tag_uri, tag_name,
                                             attributes, ns_decls, 
                                             pdf_stylesheet, alias_style)
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
                                      pdf_table_style, alias_style)
                if widget is not None:
                    story.append(widget)
            else:
                # unknown tag
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
                    value = normalize(Unicode.decode(value, encoding), True)
                    if len(value) > 0 and value != ' ':
                        value = XML.encode(value) # entities
                        story.append(value)


def keepinframe_stream(stream, _tag_uri, _tag_name, _attributes, _ns_decls, 
                   pdf_stylesheet, pdf_table_style, alias_style):
    """
        Create a KeepInFrame widget.
        Childs : keepInFrame, h1, h2, h3, para, pre, xpre, image, spacer,
                 blockTable
    """
    
    story = []
    stack = []
    stack.append((_tag_name, _attributes, None))

    mode = _attributes.get((None, 'onOverflow'), 'shrink')
    max_width = to_int(_attributes.get((None, 'maxWidth'), 0), 0)
    max_height = to_int(_attributes.get((None, 'maxHeight'), 0), 0)
    name = _attributes.get((None, 'id'), '')
    frame = _attributes.get((None, 'frame')) # not yet used
    merge_space = to_bool(_attributes.get((None, 'mergeSpace'), 1))

    attrs = {'maxWidth': max_width, 'maxHeight': max_height, 
             'mergeSpace': merge_space, 'mode': mode}
    
    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes, ns_decls = value
            if tag_name == 'keepInFrame':
                widget = keepinframe_stream(stream, tag_uri, tag_name,
                                             attributes, ns_decls, 
                                             pdf_stylesheet, pdf_table_style,
                                             alias_style)
                if widget is not None:
                    story.append(widget)

            elif tag_name in ['h1', 'h2', 'h3']:
                story.append(heading_stream(stream, tag_uri, tag_name, 
                             attributes, ns_decls, pdf_stylesheet))
            elif tag_name == 'para':
                widget = paragraph_stream(stream, tag_uri, tag_name, 
                                          attributes, ns_decls, pdf_stylesheet,
                                          alias_style)
                if widget is not None:
                    story.append(widget)
            elif tag_name in ['pre', 'xpre']:
                widget = preformatted_stream(stream, tag_uri, tag_name,
                                             attributes, ns_decls, 
                                             pdf_stylesheet, alias_style)
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
                                      pdf_table_style, alias_style)
                if widget is not None:
                    story.append(widget)
            else:
                stack.append((tag_name, attributes, None))
        #### END ELEMENT ####   
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            prev_elt = stack[-1]
            if prev_elt[0] == _tag_name:
                attrs['content'] = story
                return KeepInFrame(**attrs)
            else:
                stack.pop()

        #### TEXT ELEMENT ####   
        elif event == TEXT:
            if stack:
                prev_elt = stack[-1]
                if prev_elt[0] == _tag_name:
                    value = normalize(Unicode.decode(value, encoding), True)
                    if len(value) > 0 and value != ' ':
                        value = XML.encode(value) # entities
                        story.append(value)



def heading_stream(stream, _tag_uri, _tag_name, _attributes, _ns_decls, 
                   pdf_stylesheet, alias_style):
    """
        Create a heading widget.
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
                value = normalize(Unicode.decode(value, encoding), True)
                if len(value) > 0 and value != ' ':
                    value = XML.encode(value) # entities
                    content.append(value)


def paragraph_stream(stream, _tag_uri, _tag_name, _attributes, _ns_decls, 
                     pdf_stylesheet, alias_style):
    """
        Create a paragraph widget.
    """
    
    content = []
    stack = []
    stack.append((_tag_name, _attributes, None))

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
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
                widget = create_paragraph(pdf_stylesheet, alias_style, element, content)
                return widget 
            else:
                element = stack.pop()
                content.append(build_end_tag(element[0]))

        #### TEXT ELEMENT ####   
        elif event == TEXT:
            if stack:
                value = normalize(Unicode.decode(value, encoding), True)
                if len(value) > 0:
                    # alow to write : 
                    # <para><u><i>Choix de l'appareillage</i> </u></para>
                    value = XML.encode(value) # entities
                    content.append(value)


def preformatted_stream(stream, _tag_uri, _tag_name, _attributes, _ns_decls, 
                     pdf_stylesheet, alias_style):
    """
        Create a preformatted widget (pre or xpre)
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
            tag_uri, tag_name, attributes, ns_decls = value
            content.append(build_start_tag(tag_name, attributes))
            stack.append((tag_name, attributes, None))
        #### END ELEMENT ####   
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == _tag_name:
                content = ''.join(content)
                element = stack.pop()
                widget = create_preformatted(pdf_stylesheet, alias_style, element, 
                                             content)
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
    """
        Create an image widget.
    """
    
    stack = []
    stack.append((_tag_name, _attributes, None))

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
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
    """
        Create a spacer widget.
    """
    
    stack = []
    stack.append((_tag_name, _attributes, None))

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes, ns_decls = value
            stack.append((tag_name, attributes, None))
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


def table_stream(stream, _tag_uri, _tag_name, _attributes, _ns_decls, 
                 pdf_stylesheet, pdf_table_style, alias_style):
    """
        Create a table widget.
        Childs: blockTableStyle, tr, td
    """

    data_table = None
    table_td = None
    stack = []
    stack.append((_tag_name, _attributes, None))

    data_table = []
    style_id = _attributes.get((None, 'style'))
    style_table = pdf_table_style.get(style_id, TableStyle())
    rowHeights_table = _attributes.get((None, 'rowHeights'))
    colWidths_table = _attributes.get((None, 'colWidths'))
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
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes, ns_decls = value
            push = True
            if tag_name == 'blockTableStyle':
                # call tableStyle_stream et get the id of the table style
                # get the tablestyle from the id
                push = False
                id = tableStyle_stream(stream, tag_uri, tag_name, attributes, 
                                       ns_decls, pdf_stylesheet, 
                                       pdf_table_style)
                style_table = pdf_table_style.get(id, TableStyle())
            elif tag_name == 'tr':
                table_tr = []
                end_tag_tr = False
            elif tag_name == 'td':
                table_td = []
                td_only_text = True
                end_tag_td = False
            elif tag_name == 'image':
                if stack[-1][0] == 'td':
                    push = False
                    widget = image_stream(stream, tag_uri, tag_name,
                                          attributes, ns_decls, pdf_stylesheet,
                                          True)
                    if widget is not None:
                        if td_only_text == True:
                            table_td = [x for x in  table_td if not is_str(x)]
                        table_td.append(widget)
                        td_only_text = False
                else:
                    pass
            elif tag_name == 'para':
                if stack[-1][0] == 'td':
                    push = False
                    widget = paragraph_stream(stream, tag_uri, tag_name,
                                              attributes, ns_decls, 
                                              pdf_stylesheet, alias_style)
                    if widget is not None:
                        if td_only_text == True:
                            table_td = [x for x in  table_td if not is_str(x)]
                        table_td.append(widget)
                        td_only_text = False
                else:
                    pass
            
            elif tag_name in ['pre', 'xpre']:
                if stack[-1][0] == 'td':
                    push = False
                    widget = preformatted_stream(stream, tag_uri, tag_name,
                                                 attributes, ns_decls, 
                                                pdf_stylesheet, alias_style)
                    if widget is not None:
                        if td_only_text == True:
                            table_td = [x for x in  table_td if not is_str(x)]
                        table_td.append(widget)
                        td_only_text = False
                else:
                    pass
            
            elif tag_name == 'spacer':
                if stack[-1][0] == 'td':
                    push = False
                    widget = spacer_stream(stream, tag_uri, tag_name,
                                              attributes, ns_decls, 
                                              pdf_stylesheet)
                    if widget is not None:
                        if td_only_text == True:
                            table_td = [x for x in  table_td if not is_str(x)]
                        table_td.append(widget)
                        td_only_text = False
                else:
                    pass
            
            elif tag_name == 'blockTable':
                if stack[-1][0] == 'td':
                    push = False
                    widget = table_stream(stream, tag_uri, tag_name,
                                              attributes, ns_decls, 
                                              pdf_stylesheet, pdf_table_style,
                                              alias_style)
                    if widget is not None:
                        if td_only_text == True:
                            table_td = [x for x in  table_td if not is_str(x)]
                        table_td.append(widget)
                        td_only_text = False
                else:
                    pass
            else:
                # not implemeted tag or unknown tag
                if stack[-1][0] == 'td':
                    if td_only_text == True:
                        table_td.append(' ')

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
            else:
                stack.pop()

        #### TEXT ELEMENT ####   
        elif event == TEXT:
            if stack[-1][0] == 'blockTable':
                pass
            elif stack[-1][0] == 'tr':
                pass
            elif stack[-1][0] == 'td':
                if td_only_text == True:
                    # we dont normalize the td content
                    value = Unicode.decode(value, encoding).strip()
                    if len(value) > 0:
                        value = XML.encode(value) # entities
                        table_td.append(value)
            else:
                pass


###############################################################################
# FUNCTION

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


def normalize(data, least=False):
    """ 
        Normalize data
    """
    if least == True:
        data = u'X%sX' % data
    # we normalize the string
    data = u' '.join(data.split())
    if least == True:
        return data[1:-1]
    return data


def build_start_tag(tag_name, attributes):
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


def create_paragraph(pdf_stylesheet, alias_style, element, content):
    """ 
        Create a reportlab paragraph widget.
    """

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
                attr_value = __tab_para_alignment.get(attr_value) 
            elif key in ['leftIndent', 'rightIndent']:
                attr_value = get_value_reportlab(attr_value)
            style_attr[key] = attr_value

    parent_style = get_style(pdf_stylesheet, alias_style, parent_style)
    style = ParagraphStyle('', parent=parent_style, **style_attr)
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
    else:
        fn = XPreformatted

    style = get_style(pdf_stylesheet, alias_style, style_name)
  
    if content == '':
        return None
    else:
        widget = fn(content, style)
        return widget


def create_image(element, check_dimension):
    """ 
        Create a reportlab image widget.
    """

    width, height = None, None
    filename = None

    for key, attr_value in element[1].iteritems():
        key = key[1]
        if key == 'file':
            filename = attr_value
        elif key == 'width':
            width = get_value_reportlab(attr_value)
        elif key == 'height':
            height = get_value_reportlab(attr_value)
    
    if filename is None:
        return None

    if check_dimension and width == None and height == None:
        return None

    try:
        f = open(filename, 'r')
        f.close()
    except IOError, msg:
        return None

    try:
        I = Image(filename)
        if height is not None:
            I.drawHeight = height
        if width is not None:
            I.drawWidth = width
        return I
    except IOError, msg:
        warnings(msg)
        return None
    except Exception, msg:
        return None


def create_spacer(element):
    """ 
        Create a reportlan spacer widget.
    """

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
        return None


def build_stylesheet(pdf_stylesheet, styles):
    """ 
        Create the paragraph styles contained in the stylesheet tag.
        Add it to the pdf stylesheet.
    """

    for style in styles:
        style_attr = {}
        name = ''
        parent_style = None

        for key, attr_value in style.iteritems():
            key = key[1]
            if key == 'name':
                name = attr_value
            elif key == 'parent':
                parent_style = attr_value
            else:
                if key in ['fontSize', 'leading', 'leftIndent', 'rightIndent', 
                           'firstLineIndent', 'spaceBefore', 'spaceAfter',
                           'bulletFontSize', 'bulletIndent']:
                    attr_value = get_value_reportlab(attr_value)
                elif key == 'alignment':
                    attr_value = __tab_para_alignment.get(attr_value, None)
                    if attr_value is None:
                        # tag not well formed
                        attr_value = __tab_para_alignment.get('left')

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
    """ 
        Create the tableStyle and add it to the pdf table style.
        If the style id already exist, the old style will be erased.
    """

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
            else:
                # tag not well formed
                pass
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
                # tag not well formed
                pass
        
        elif elt_id == 'blockBackground':
            if attr.has_key('colorName') == True:
                attr['colorName'] = getattr(colors, attr['colorName'], 
                                            colors.black)
                style.add('BACKGROUND', attr['start'], attr['stop'], 
                          attr['colorName'])
            else:
                # tag not well formed
                pass
        
        elif elt_id == 'blockLeading':
            if attr.has_key('length') == True:
                attr['length'] = to_float(attr['length'])
                style.add('LEADING', attr['start'], attr['stop'], 
                          attr['length'])
            else:
                # tag not well formed
                pass
                  
        elif elt_id == 'blockAlignment':
            if attr.has_key('value') == True:
                if attr['value'] not in ['LEFT', 'RIGHT', 'CENTER', 
                                         'CENTRE']:
                    # tag not well formed
                    attr['value'] = 'LEFT'
                
                style.add('ALIGNMENT', attr['start'], attr['stop'], 
                          attr['value'])
            else:
                # tag not well formed
                pass

        elif elt_id == 'blockValign':
            if attr.has_key('value') == True:
                if attr['value'] not in ['TOP', 'MIDDLE', 'BOTTOM']:
                    attr['value'] = 'BOTTOM'

                style.add('VALIGN', attr['start'], attr['stop'], 
                          attr['value'])
            else:
                # tag not well formed
                pass

        elif elt_id in ['blockLeftPadding', 'blockRightPadding', 
                        'blockTopPadding', 'blockBottomPadding']:
            if attr.has_key('length') == True:
                attr['length'] = get_value_reportlab(attr['length'])
                style.add(elt_id[5:].upper(), attr['start'], attr['stop'], 
                          attr['length'])
            else:
                # tag not well formed
                pass
        
        elif elt_id == 'lineStyle':
            kind_ok = attr.has_key('kind')
            color_ok = attr.has_key('colorName')
            if kind_ok and color_ok:
                kind_list = ['GRID', 'BOX', 'OUTLINE', 'INNERGRID', 
                             'LINEBELOW', 'LINEABOVE', 'LINEBEFORE', 
                             'LINEAFTER']
                if attr['kind'] not in kind_list: 
                    # tag not well formed
                    pass
                else:
                    attr['colorName'] = getattr(colors, attr['colorName'], 
                                               colors.black)
                    if attr.has_key('thickness') == False:
                        attr['thickness'] = 1
                    attr['thickness'] = to_float(attr['thickness'], 1)

                    style.add(attr['kind'], attr['start'], attr['stop'], 
                              attr['thickness'], attr['colorName'])
            else:
                # tag not well formed
                pass

    pdf_table_style[id] = style


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


def get_style_name(stylesheet, alias, name):
    """
       Return the style name corresponding to name
       or None if no style exist.
    """

    if name[:6] == 'style.':
        # <alias id="bt" value="style.BodyText"/>
        name = name[6:]

    # we use try except because StyleSheet1 class has no attribute 'get'
    try:
        style = stylesheet[name]
        return name
    except KeyError:
        try:
            style = stylesheet[alias[name]]
            return style.name
        except KeyError:
            return None


def is_alias_style(alias, name):
    """ 
        Check id name is an alias.
    """

    if name[:6] == 'style.':
        # <alias id="bt" value="style.BodyText"/>
        name = name[6:]
    return alias.has_key(name)


def is_str(str, check_is_unicode=True):
    """
        Check is str is a string.
    """

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
    if str == u'false' or str == u'0':
        return False
    elif str == u'true' or str == u'1':
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
       '2in' -> 2 * mm
       '2in' -> 2 * pica
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


def get_value_from_percentage(value, ref):
    """ 
        Return the value percentage of ref
        example:
        get_value_from_percentage('10%', 400) = 40
    """
    if not is_str(value):
        return value

    index = value.find('%')
    if index != -1:
        value = value[:index]
    
    value = to_float(value)
    return ref * value / 100.0


def get_value_page_size(data):
    """ 
        Return a tuple (width, height)
    """
    if is_str(data):
        orientation, data = get_page_size_orientation(data)
        ps = __tab_page_size.get(data)
        if ps is not None:
            return orientation(ps)
        
        data = normalize(data)

        if data[0] == '(':
            data = data[1:]
        if data[-1] == ')':
            data = data[0:-1]

        tab_size = data.split(',')
        if len(tab_size) >= 2:
            w = get_value_reportlab(tab_size[0])
            h = get_value_reportlab(tab_size[1])
            data = (w, h)
        else:
            data = pagesizes.A4
        
        return orientation(data)
    
    return pagesizes.A4
    

def get_page_size_orientation(data):
    """ 
        Return the pagesize orientation
        example: 
        data = 'letter landscape'
        return (landscape, 'letter')

        data = '(21cm,29.7cm)'
        return (portrait, '(21cm,29.7cm)')
    """
    
    orientation = portrait
    sp = data.split(' ')
    if len(sp) == 1:
        return (orientation, data)

    if sp[0] == 'landscape':
        return (landscape, sp[1])
    elif sp[0] == 'portrait':
        return (portrait, sp[1])
    elif sp[1] == 'landscape':
        return (landscape, sp[0])
    elif sp[1] == 'portrait':
        return (portrait, sp[0])
    else:
        return (portrait, data)
