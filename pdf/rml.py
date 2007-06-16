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
import logging
import os

# Import from itools
from itools.datatypes import Unicode, XML
from itools.xml.parser import Parser, START_ELEMENT, END_ELEMENT, TEXT, CDATA
from itools.stl.stl import stl

# Import from the reportlab Library
import reportlab
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph, BaseDocTemplate, \
                               SimpleDocTemplate, PageTemplate, \
                               XPreformatted, Preformatted, \
                               Frame, FrameBreak, NextPageTemplate, \
                               KeepInFrame, PageBreak, Image, Table, \
                               TableStyle, Spacer, Indenter
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.platypus.flowables import Flowable, HRFlowable
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, cm, mm, pica
from reportlab.rl_config import defaultPageSize
from reportlab.lib.pagesizes import letter, legal, elevenSeventeen, \
                                    A0, A1, A2, A3, A4, A5, A6, \
                                    B0, B1, B2, B3, B4, B5, B6, \
                                    landscape, portrait
from reportlab.lib import pagesizes, colors
from reportlab.lib.colors import Color, CMYKColor, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

__tab_para_alignment = {'LEFT': TA_LEFT, 'RIGHT': TA_RIGHT, 
                        'CENTER': TA_CENTER, 'JUSTIFY': TA_JUSTIFY}
__tab_page_size = {'LETTER': letter, 'LEGAL': legal, 
                   #'elevenSeventeen': elevenSeventeen,
                   'A0': A0, 'A1': A1, 'A2': A2, 'A3': A3, 
                   'A4': A4, 'A5': A5, 'A6': A6,
                   'B0': B0, 'B1': B1, 'B2': B2, 'B3': B3, 
                   'B4': B4, 'B5': B5, 'B6': B6}

encoding = 'UTF-8'
TAG_NOT_SUPPORTED = '%s: line %s tag "%s" is currently not supported.'

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


class iIllustration(Flowable):

    def __init__(self, stream, _tag_uri, _tag_name, _attributes):
        self.width = rml_value(_attributes.get((None, 'width')))
        self.height = rml_value(_attributes.get((None, 'height')))
        self.pageGraphics = iPageGraphics(stream, _tag_name, {})

    
    def wrap(self, *args):
        return (self.width, self.height)


    def draw(self):
        self.pageGraphics.render(self.canv, None)


class iCanvas(object):

    def __init__(self, story):
        self.story = story

    def render(self, cnv, doc):
        fn_draw_string = {'drawString': cnv.drawString, 
                          'drawRightString': cnv.drawRightString, 
                          'drawCentredString': cnv.drawCentredString, 
                          'drawCenteredString': cnv.drawCentredString}
        fn_no_change = {'setFont': cnv.setFont, 'fill': cnv.setFillColorRGB, 
                        'stroke': cnv.setStrokeColorRGB, 'ellipse': cnv.ellipse,
                        'lineWidth': cnv.setLineWidth, 'lineDash': cnv.setDash, 
                        'lineJoin': cnv.setLineJoin, 'lineCap': cnv.setLineCap,
                        'circle': cnv.circle, 'lines': cnv.lines, 
                        'curves': cnv.bezier, 'grid': cnv.grid,
                        'translate': cnv.translate, 'scale': cnv.scale,
                        'rotate': cnv.rotate, 'skew': cnv.skew,
                        'transform': cnv.transform, 'image': cnv.drawImage}

        cnv.saveState()
        for obj in self.story:
            fn, attrs = obj
            if fn in ['drawString', 'drawRightString', 'drawCentredString', 
                      'drawCenteredString']:
                if doc is not None:
                    attrs2 = attrs.copy()
                    text = attrs2['text']
                    page_nb = str(doc.page)
                    text = text.replace('<pageNumber></pageNumber>', page_nb)
                    attrs2['text'] = text.strip()
                    fn_draw_string[fn](**attrs2)
                else:
                    fn_draw_string[fn](**attrs)
            elif fn_no_change.has_key(fn):
                try:
                    fn_no_change[fn](**attrs)
                except IOError, msg:
                    print msg
            elif fn == 'saveState':
                cnv.saveState()
            elif fn == 'restoreState':
                cnv.restoreState()
            elif fn == 'rect':
                if attrs.has_key('radius') == True:
                    cnv.roundRect(**attrs)
                else:
                    cnv.rect(**attrs)
        cnv.restoreState()


class iPageGraphics(object):
    __tab_join = {'round': 1, 'mitered': 0, 'bevelled': 2}
    __tab_cap = {'default': 0, 'round': 1, 'square': 2}

    def __init__(self, stream, _tag_name, _attributes):
        self.story = []

        stack = []
        stack.append((_tag_name, _attributes, None))
        fn_attrs = None
        content = None
        while True:
            event, value, line_number = stream_next(stream)
            if event == None:
                break
            #### START ELEMENT ####
            if event == START_ELEMENT:
                tag_uri, tag_name, attrs = value
                if tag_name in ['drawString', 'drawRightString', 
                                'drawCentredString', 'drawCenteredString']:
                    if exist_attribute(attrs, ['x', 'y']) == True:
                        content = []
                        fn_attrs = {}
                        fn_attrs['x'] = rml_value(attrs.get((None,  'x')), 0)
                        fn_attrs['y'] = rml_value(attrs.get((None,  'y')), 0)
                elif tag_name == 'setFont':
                    if exist_attribute(attrs, ['name', 'size']) == True:
                        fn_attrs = {}
                        size = attrs.get((None, 'size'))
                        fn_attrs['psfontname'] = attrs.get((None, 'name'))
                        fn_attrs['size'] = to_int(attrs.get((None, 'size'), 5))
                elif tag_name in ['saveState', 'restoreState']:
                    fn_attrs = {}
                elif tag_name == 'image':
                    if exist_attribute(attrs, ['file', 'x', 'y']):
                        fn_attrs = {}
                        image = attrs.get((None, 'file'))
                        fn_attrs['x'] = rml_value(attrs.get((None, 'x')))
                        fn_attrs['y'] = rml_value(attrs.get((None, 'y')))
                        fn_attrs['image'] = image

                        for k in ['width', 'height']:
                            if exist_attribute(attrs, [k]):
                                fn_attrs[k] = rml_value(attrs.get((None, k)))
                        if exist_attribute(attrs, ['preserveAspectRatio']):
                            preserve = attrs.get((None, 'preserveAspectRatio'))
                            fn_attrs['preserveAspectRatio'] = to_bool(preserve)
                        if exist_attribute(attrs, ['anchor']):
                            anchor = attrs.get((None, 'anchor')).lower()
                            if anchor in ['nw', 'n', 'ne', 'w', 'c', 'e', 
                                          'sw', 's', 'se']:
                                fn_attrs['anchor'] = anchor

                elif tag_name == 'rect':
                    if exist_attribute(attrs, ['x', 'y', 'width', 
                                               'height']) == True:
                        fn_attrs = {}
                        fn_attrs['x'] = rml_value(attrs.get((None, 'x')))
                        fn_attrs['y'] = rml_value(attrs.get((None, 'y')))
                        fn_attrs['width'] = rml_value(attrs.get((None, 
                                                                 'width')))
                        fn_attrs['height'] = rml_value(attrs.get((None, 
                                                                  'height')))
                        if exist_attribute(attrs, ['fill']) == True:
                            fill = to_bool(attrs.get((None, 'fill')))
                            fn_attrs['fill'] = fill
                        if exist_attribute(attrs, ['round']) == True:
                            round = rml_value(attrs.get((None, 'round')))
                            fn_attrs['radius'] = round
                        if exist_attribute(attrs, ['stroke']) == True:
                            stroke = to_bool(attrs.get((None, 'stroke')))
                            fn_attrs['stroke'] = stroke
                elif tag_name in ['fill', 'stroke']:
                    if exist_attribute(attrs, ['color']) == True:
                        fn_attrs = {}
                        r, g, b = get_color(attrs.get((None, 'color'))).rgb()
                        fn_attrs['r'] = r
                        fn_attrs['g'] = g
                        fn_attrs['b'] = b
                elif tag_name == 'lineMode':
                    if exist_attribute(attrs, ['width']) == True:
                        width = rml_value(attrs.get((None, 'width')))
                        self.story.append(('lineWidth', {'width': width}))
                    if exist_attribute(attrs, ['dash']) == True:
                        dash = []
                        for elt in attrs.get((None, 'dash')).split(','):
                            dash.append(rml_value(elt))
                        self.story.append(('lineDash', {'array': dash}))
                    if exist_attribute(attrs, ['join']) == True:
                        join = attrs.get((None, 'join'))
                        if join in ['round', 'mitered', 'bevelled']:
                            mode = iPageGraphics.__tab_join[join]
                            self.story.append(('lineJoin', {'mode': mode}))
                    if exist_attribute(attrs, ['cap']) == True:
                        cap = attrs.get((None, 'cap'))
                        if cap in ['default', 'round', 'square']:
                            mode = iPageGraphics.__tab_cap[cap]
                            self.story.append(('lineCap', {'mode': mode}))
                elif tag_name == 'circle':
                    if exist_attribute(attrs, ['x', 'y', 'radius']):
                        fn_attrs = {}
                        fn_attrs['x_cen'] = rml_value(attrs.get((None, 'x')))
                        fn_attrs['y_cen'] = rml_value(attrs.get((None, 'y')))
                        fn_attrs['r'] = rml_value(attrs.get((None, 'radius')))
                        if exist_attribute(attrs, ['fill']):
                            fn_attrs['fill'] = to_bool(attrs.get((None, 
                                                                  'fill')))
                        if exist_attribute(attrs, ['stroke']):
                            fn_attrs['stroke'] = to_bool(attrs.get((None, 
                                                                    'stroke')))
                elif tag_name == 'ellipse':
                    if exist_attribute(attrs, ['x', 'y', 'width', 
                                               'height']) == True:
                        fn_attrs = {}
                        fn_attrs['x1'] = rml_value(attrs.get((None, 'x')))
                        fn_attrs['y1'] = rml_value(attrs.get((None, 'y')))
                        fn_attrs['x2'] = rml_value(attrs.get((None, 'width')))
                        fn_attrs['y2'] = rml_value(attrs.get((None, 'height')))
                        if exist_attribute(attrs, ['fill']) == True:
                            fill = attrs.get((None, 'fill'))
                            fn_attrs['fill'] = to_bool(fill)
                        if exist_attribute(attrs, ['stroke']) == True:
                            stroke = attrs.get((None, 'stroke'))
                            fn_attrs['stroke'] = to_bool(stroke)
                elif tag_name == 'lines':
                    fn_attrs = {}
                    content = ''
                elif tag_name == 'curves':
                    fn_attrs = {}
                    content = ''
                elif tag_name == 'grid':
                    fn_attrs = {}
                    if exist_attribute(attrs, ['xs', 'ys']):
                        xs = attrs.get((None, 'xs')).split(',')
                        ys = attrs.get((None, 'ys')).split(',')
                        xlist = [rml_value(elt) for elt in xs]
                        ylist = [rml_value(elt) for elt in ys]
                        fn_attrs['xlist'] = xlist
                        fn_attrs['ylist'] = ylist
                elif tag_name == 'translate':
                    fn_attrs = {}
                    for key in ['dx', 'dy']:
                        if exist_attribute(attrs, [key]):
                            fn_attrs[key] = rml_value(attrs.get((None, key)))
                        else:
                            fn_attrs[key] = 0
                elif tag_name == 'scale':
                    fn_attrs = {}
                    for key in ['sx', 'sy']:
                        if exist_attribute(attrs, [key]):
                            fn_attrs[key[1]] = rml_value(attrs.get((None, key)))
                        else:
                            fn_attrs[key[1]] = 1
                elif tag_name == 'rotate':
                    if exist_attribute(attrs, ['degrees']):
                        theta = to_float(attrs.get((None, 'degrees')))
                        fn_attrs = {'theta': theta}
                elif tag_name == 'skew':
                    if exist_attribute(attrs, ['alpha', 'beta']):
                        fn_attrs = {}
                        for key in ['alpha', 'beta']:
                            fn_attrs[key] = to_float(attrs.get((None, key)))
                elif tag_name == 'transform':
                    fn_attrs = {}
                    content = ''
                elif tag_name == 'pageNumber' and content is not None:
                    content.append(build_start_tag(tag_name, attrs))
                else:
                    print TAG_NOT_SUPPORTED % (_tag_name, line_number, tag_name)
                stack.append((tag_name, attrs, None))
            #### END ELEMENT ####   
            elif event == END_ELEMENT:
                tag_uri, tag_name = value
                if tag_name == _tag_name:
                    break
                else:
                    if tag_name == 'pageNumber' and content is not None:
                        content.append(build_end_tag(tag_name))
                    elif fn_attrs is not None:
                        push = True
                        if tag_name in ['drawString', 'drawRightString', 
                                       'drawCentredString', 
                                       'drawCenteredString']:
                            if content is not None:
                                fn_attrs['text'] = ''.join(content) 
                                content = None
                        elif tag_name == 'lines':
                            content = content.split()
                            lines = []
                            while len(content) > 3:
                                lines.append([rml_value(v) 
                                              for v in content[0:4]])
                                content = content[4:]
                            fn_attrs['linelist'] = lines
                        elif tag_name == 'curves':
                            push = False
                            content = content.split()
                            while len(content) > 7:
                                d = {}
                                for i, elt in enumerate(['x1', 'y1', 'x2', 
                                                         'y2', 'x3', 'y3', 
                                                         'x4', 'y4']):
                                    d[elt] = rml_value(content[i])
                                    self.story.append((tag_name, d))
                                content = content[8:]
                        elif tag_name == 'transform':
                            content = content.split()
                            if len(content) == 6:
                                for index, key in enumerate(['a','b','c','d',
                                                             'e','f']):
                                    fn_attrs[key] = to_float(content[index])
                            else:
                                push = False
                        if push == True:
                            self.story.append((tag_name, fn_attrs))
                        fn_attrs = None
                    # unknown tag
                    stack.pop()
            elif event == TEXT:
                prev_elt = stack[-1]
                if fn_attrs is not None:
                    if prev_elt[0] in ['drawString', 'drawRightString', 
                                       'drawCentredString', 
                                       'drawCenteredString']:
                        content.append(XML.encode(value))
                    elif prev_elt[0] in ['lines', 'curves', 'transform']:
                        content = value
       
        o = iCanvas(self.story)
        self.render = o.render


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

    document_attrs = { 'leftMargin': inch, 'rightMargin': inch,
                       'topMargin': inch, 'bottomMargin': inch,
                       'pageSize': pagesizes.A4, 'title': None,
                       'author': None, 'rotation': 0,
                       'showBoundary': 0, 'allowSplitting': 1,
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
            tag_uri, tag_name, attributes = value
            if tag_name == 'document':
                pdf_filename = attributes.get((None, 'filename'), 'noname.pdf')
                stack.append((tag_name, attributes, None))
            elif tag_name == 'docinit':
                docinit_stream(stream, tag_uri, tag_name, attributes)
            elif tag_name == 'template':
                page_templates = template_stream(stream, tag_uri, tag_name, 
                                attributes, document_attrs)
            elif tag_name == 'stylesheet':
                alias_style = stylesheet_stream(stream, tag_uri, tag_name, 
                                                attributes, pdf_stylesheet, 
                                                pdf_table_style, alias_style)
            elif tag_name == 'story':
              story = story_stream(stream, tag_uri,tag_name, attributes,
                                   pdf_stylesheet, pdf_table_style,
                                   alias_style)
            else: 
                print TAG_NOT_SUPPORTED % ('document', line_number, tag_name)
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
    # rml attribute != reportlab attribute --> pageSize
    document_attrs['pagesize'] = document_attrs['pageSize']
    if len(page_templates) > 0:
        doc = BaseDocTemplate(pdf_stream, **document_attrs)
        doc.addPageTemplates(page_templates)
    else:
        doc = SimpleDocTemplate(pdf_stream, **document_attrs)

    if is_test == True:
        _story = list(story)

    doc.build(story)

    if is_test == True:
        return (_story, pdf_stylesheet)


def docinit_stream(stream, _tag_uri, _tag_name, _attributes):
    """ 
        stream : parser stream
        Register external font
    """

    stack = []
    stack.append((_tag_name, _attributes, None))

    # register font
    register_font_folder = os.path.dirname(reportlab.__file__)
    register_font_folder += os.sep + 'fonts'
    afmFile = None
    pfbFile = None
    tag_registerType1Face = False

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            return
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            stack.append((tag_name, attributes, None))
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            prev_elt = stack[-1]
            if prev_elt[0] == _tag_name:
                if tag_name == _tag_name:
                    return

            elif prev_elt[0] == 'registerTTFont':
                tag_registerType1Face = False
                attrs = prev_elt[1]
                # <registerTTFont faceName="rina" fileName="rina.ttf"/>

                if exist_attribute(attrs, ['faceName', 'fileName']) == True:
                    face_name = attrs.get((None, 'faceName'))
                    file_name = attrs.get((None, 'fileName'))
                    ttfont = TTFont(face_name, file_name)
                    pdfmetrics.registerFont(ttfont)
                else:
                    # not well formed
                    pass

            elif prev_elt[1] == 'registerType1Face':
                tag_registerType1Face = False
                attrs = prev_elt[1]
                if exist_attribute(attrs, ['afmFile', 'pfbFile']) == True:
                    tag_registerType1Face = True
                    afmFile = os.path.join(register_font_folder, 
                                           attrs.get((None, 'afmFile')))
                    pfbFile = os.path.join(register_font_folder, 
                                           attrs.get((None, 'pfbFile')))

            elif prev_elt[1] == 'registerFont':
                if tag_registerType1Face == True:
                    if exist_attribute(attrs, ['name', 'faceName', 
                                               'encName']) == True: 
                        name = attrs.get((None, 'name'))
                        faceName = attrs.get((None, 'faceName'))
                        encName = attrs.get((None, 'encName'))

                        justFace = pdfmetrics.EmbeddedType1Face(afmFile, 
                                                                pfbFile)
                        pdfmetrics.registerTypeFace(justFace)
                        justFont = pdfmetrics.Font(name, faceName, encName)
                        pdfmetrics.registerFont(justFont)
                tag_registerType1Face = False
            else:
                print TAG_NOT_SUPPORTED % (_tag_name, line_number, tag_name)
            stack.pop()


def template_stream(stream, _tag_uri, _tag_name, _attributes, document_attrs):
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
        rml_value(document_attrs['leftMargin'])
    document_attrs['rightMargin'] = \
        rml_value(document_attrs['rightMargin'])
    document_attrs['topMargin'] = \
        rml_value(document_attrs['topMargin'])
    document_attrs['bottomMargin'] = \
        rml_value(document_attrs['bottomMargin'])
    document_attrs['showBoundary'] = \
        to_int(document_attrs['showBoundary'], 0)
    document_attrs['allowSplitting'] = \
        to_bool(document_attrs['allowSplitting'])

    show_boundary = document_attrs['showBoundary']
    on_page_function = None
    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            if tag_name == 'pageTemplate':
                on_page_function = None
                page_template_data = {'frame':[]}
                attrs = attributes 
                id = attrs.get((None, 'id'))
                rotation = attrs.get((None, 'rotation'))
                page_size = attrs.get((None, 'pageSize'))
                if rotation is None:
                    rotation = document_attrs['rotation']
                else:
                    rotation = to_int(rotation)
                if page_size is None:
                    page_size = document_attrs['pageSize']
                else:
                    page_size = get_value_page_size(page_size)

                if id is None:
                    pass # tag not well formed
                    template_attrs = None
                    page_template_data =None
                else:
                    template_attrs = {'id': id, 
                                      'frames': page_template_data['frame'],
                                      'pagesize': page_size}
                stack.append((tag_name, attributes, None))
            elif tag_name == 'pageGraphics':
                o = iPageGraphics(stream, tag_name, attributes)
                on_page_function = o.render
            else:
                stack.append((tag_name, attributes, None))
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            prev_elt = stack[-1]
            if prev_elt[0] == _tag_name:
                if tag_name == _tag_name:
                    return page_templates
            elif prev_elt[0] == 'pageTemplate':
                if tag_name == 'pageTemplate':
                    if template_attrs is not None:
                        if on_page_function is not None:
                            template_attrs['onPage'] = on_page_function
                        page_template = PageTemplate(**template_attrs)
                        page_templates.append(page_template)
                        page_template_data = None
            elif prev_elt[0] == 'frame':
                if tag_name == 'frame' and page_template_data is not None:
                    frame = create_frame(prev_elt[1], template_attrs, 
                                         document_attrs)
                    if frame is not None:
                        page_template_data['frame'].append(frame)
            
            stack.pop()


def stylesheet_stream(stream, _tag_uri, _tag_name, _attributes,
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
            tag_uri, tag_name, attributes = value
            if tag_name == 'initialize':
                alias_style = {}
                initialize_stream(stream, tag_uri, tag_name, attributes, 
                                  pdf_stylesheet, alias_style)
            elif tag_name == 'paraStyle':
                stylesheet_xml.append(attributes)
            elif tag_name == 'blockTableStyle':
                tableStyle_stream(stream, tag_uri, tag_name, attributes, 
                                  pdf_stylesheet, pdf_table_style)
            else:
                print TAG_NOT_SUPPORTED % (_tag_name, line_number, tag_name)
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
                      pdf_stylesheet, alias_style):
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
            tag_uri, tag_name, attributes = value
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


def tableStyle_stream(stream, _tag_uri, _tag_name, _attributes,
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
            tag_uri, tag_name, attributes = value
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
                              'blockBackground', 'lineStyle', 'blockSpan']:
                element = stack.pop()
                current_table_style.append(element)
            else:
                print TAG_NOT_SUPPORTED % (_tag_name, line_number, tag_name)
                stack.pop()


def story_stream(stream, _tag_uri, _tag_name, _attributes, pdf_stylesheet,
                 pdf_table_style, alias_style):
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
    indent_stack = []

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            return story
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
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
                                             attributes, pdf_stylesheet,
                                             pdf_table_style, alias_style)
                if widget is not None:
                    story.append(widget)
            elif tag_name in ['h1', 'h2', 'h3']:
                story.append(heading_stream(stream, tag_uri, tag_name, 
                             attributes, pdf_stylesheet, alias_style))
            elif tag_name == 'hr':
                story.append(hr_stream(stream, tag_uri, tag_name, 
                                       attributes))
            elif tag_name == 'para':
                story.append(paragraph_stream(stream, tag_uri, tag_name, 
                                              attributes, pdf_stylesheet,
                                              alias_style))
            elif tag_name in ['pre', 'xpre']:
                story.append(preformatted_stream(stream, tag_uri, tag_name,
                                                 attributes, pdf_stylesheet,
                                                 alias_style))
            elif tag_name == 'image':
                widget = image_stream(stream, tag_uri, tag_name,
                                      attributes, pdf_stylesheet)
                if widget is not None:
                    story.append(widget)
            elif tag_name == 'spacer':
                widget = spacer_stream(stream, tag_uri, tag_name,
                                       attributes, pdf_stylesheet)
                if widget is not None:
                    story.append(widget)
            elif tag_name == 'blockTable':
                widget = table_stream(stream, tag_uri, tag_name,
                                      attributes, pdf_stylesheet,
                                      pdf_table_style, alias_style)
                if widget is not None:
                    story.append(widget)
            elif tag_name == 'indent':
                attrs = {}
                attrs['left'] = rml_value(attributes.get((None, 'left')), 0)
                attrs['right'] = rml_value(attributes.get((None, 'right')), 0)
                story.append(Indenter(**attrs))
                indent_stack.append(attrs)
                stack.append((tag_name, attributes, None))
            elif tag_name == 'illustration':
                if exist_attribute(attributes, ['width', 'height']):
                    story.append(iIllustration(stream, tag_uri, tag_name, 
                                               attributes))
            else:
##                print TAG_NOT_SUPPORTED % (_tag_name, line_number, tag_name)
                # unknown tag
                stack.append((tag_name, attributes, None))
        #### END ELEMENT ####   
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            prev_elt = stack[-1]
            if prev_elt[0] == _tag_name:
                return story
            elif prev_elt[0] == 'indent':
                attrs = indent_stack[-1]
                for key in attrs.keys():
                    attrs[key] = -attrs[key]
                story.append(Indenter(**attrs))
                indent_stack.pop()
                stack.pop()
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


def keepinframe_stream(stream, _tag_uri, _tag_name, _attributes,
                       pdf_stylesheet, pdf_table_style, alias_style):
    """
        Create a KeepInFrame widget.
        Childs : keepInFrame, h1, h2, h3, para, pre, xpre, image, spacer,
                 blockTable
    """
    
    story = []
    stack = []
    stack.append((_tag_name, _attributes, None))

    max_width = to_int(_attributes.get((None, 'maxWidth'), 0), 0)
    max_height = to_int(_attributes.get((None, 'maxHeight'), 0), 0)
    name = _attributes.get((None, 'id'), '')
    mode = _attributes.get((None, 'onOverflow'))
    merge_space = _attributes.get((None, 'mergeSpace'))

    attrs = {'maxWidth': max_width, 'maxHeight': max_height}
    if mode is not None:
        attrs['mode'] = mode
    if merge_space is not None:
        attrs['mergeSpace'] = to_bool(merge_space)
    
    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            if tag_name == 'keepInFrame':
                widget = keepinframe_stream(stream, tag_uri, tag_name,
                                            attributes, pdf_stylesheet,
                                            pdf_table_style, alias_style)
                if widget is not None:
                    story.append(widget)
            elif tag_name in ['h1', 'h2', 'h3']:
                story.append(heading_stream(stream, tag_uri, tag_name, 
                             attributes, pdf_stylesheet))
            elif tag_name == 'hr':
                story.append(hr_stream(stream, tag_uri, tag_name, 
                                       attributes))
            elif tag_name == 'para':
                story.append(paragraph_stream(stream, tag_uri, tag_name, 
                                              attributes, pdf_stylesheet,
                                              alias_style))
            elif tag_name in ['pre', 'xpre']:
                story.append(preformatted_stream(stream, tag_uri, tag_name,
                                                 attributes, pdf_stylesheet,
                                                 alias_style))
            elif tag_name == 'image':
                widget = image_stream(stream, tag_uri, tag_name,
                                      attributes, pdf_stylesheet)
                if widget is not None:
                    story.append(widget)
            elif tag_name == 'spacer':
                widget = spacer_stream(stream, tag_uri, tag_name,
                                      attributes, pdf_stylesheet)
                if widget is not None:
                    story.append(widget)
            elif tag_name == 'blockTable':
                widget = table_stream(stream, tag_uri, tag_name, attributes,
                                      pdf_stylesheet, pdf_table_style,
                                      alias_style)
                if widget is not None:
                    story.append(widget)
            else:
                print TAG_NOT_SUPPORTED % (_tag_name, line_number, tag_name)
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



def heading_stream(stream, _tag_uri, _tag_name, _attributes, pdf_stylesheet,
                   alias_style):
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
            tag_uri, tag_name, attributes = value
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


def hr_stream(stream, _tag_uri, _tag_name, _attributes):
    """
        Create a hr widget.
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


def paragraph_stream(stream, _tag_uri, _tag_name, _attributes, pdf_stylesheet,
                     alias_style):
    """
        Create a paragraph widget.
    """
    
    content = []
    stack = []
    stack.append((_tag_name, _attributes, None))
    has_content = False

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            if tag_name == 'br': 
                # check if the tag is a br tag
                # we trim at le right the previous text
                # in order to not include a default : 	a superfluous space 
                content[-1] = content[-1].rstrip()
            content.append(build_start_tag(tag_name, attributes))
            stack.append((tag_name, attributes, None))
        #### END ELEMENT ####   
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == _tag_name:
                content = ''.join(content)
                element = stack.pop()
                return create_paragraph(pdf_stylesheet, alias_style, element,
                                        content)
            else:
                element = stack.pop()
                content.append(build_end_tag(element[0]))

        #### TEXT ELEMENT ####   
        elif event == TEXT:
            if stack:
                value = normalize(Unicode.decode(value, encoding), True)
                if len(value) > 0:
                    # alow to write : 
                    # <para><u><i>foo</i> </u></para>
                    value = XML.encode(value) # entities
                    if has_content and content[-1] == '</br>':
                        value = value.lstrip()
                    content.append(value)
                    has_content = True


def preformatted_stream(stream, _tag_uri, _tag_name, _attributes,
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
            tag_uri, tag_name, attributes = value
            content.append(build_start_tag(tag_name, attributes))
            stack.append((tag_name, attributes, None))
        #### END ELEMENT ####   
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            if tag_name == _tag_name:
                content = ''.join(content)
                element = stack.pop()
                widget = create_preformatted(pdf_stylesheet, alias_style, 
                                             element, content)
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


def image_stream(stream, _tag_uri, _tag_name, _attributes,
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
            tag_uri, tag_name, attributes = value
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


def spacer_stream(stream, _tag_uri, _tag_name, _attributes, pdf_stylesheet):
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
            tag_uri, tag_name, attributes = value
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


def table_stream(stream, _tag_uri, _tag_name, _attributes, pdf_stylesheet,
                 pdf_table_style, alias_style):
    """
        Create a table widget.
        Childs: blockTableStyle, tr, td
    """

    data_table = None
    table_td = None
    stack = []
    stack.append((_tag_name, _attributes, None))

    table_attrs = {}
    if exist_attribute(_attributes, ['align']):
        align = _attributes.get((None, 'align')).upper()
        if align in ['LEFT', 'RIGHT', 'CENTER', 'CENTRE']:
            table_attrs['hAlign'] = align
    if exist_attribute(_attributes, ['vAlign']):
        vAlign = _attributes.get((None, 'vAlign')).upper()
        if vAlign in ['TOP', 'MIDDLE', 'BOTTOM']:
            table_attrs['vAlign'] = vAlign
        
    data_table = []
    style_id = _attributes.get((None, 'style'))
    style_table = pdf_table_style.get(style_id, TableStyle())
    rowHeights_table = _attributes.get((None, 'rowHeights'))
    colWidths_table = _attributes.get((None, 'colWidths'))
    # reportlab default value
    table_attrs['repeatRows'] = to_int(_attributes.get((None, 'repeatRows')), 0)
    tr_number = -1
    td_number = -1
    tag_not_supported = False

    if rowHeights_table is not None:
        rowHeights_table_tab = rowHeights_table.split(',')
        rowHeights_table = []
        for rh in rowHeights_table_tab:
            rowHeights_table.append(rml_value(rh))

    if colWidths_table is not None:
        colWidths_table_tab = colWidths_table.split(',')
        colWidths_table = []
        for cw in colWidths_table_tab:
            colWidths_table.append(rml_value(cw))

    while True:
        event, value, line_number = stream_next(stream)
        if event == None:
            break
        #### START ELEMENT ####
        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            push = True
            if tag_name == 'blockTableStyle':
                # call tableStyle_stream et get the id of the table style
                # get the tablestyle from the id
                push = False
                id = tableStyle_stream(stream, tag_uri, tag_name, attributes, 
                                       pdf_stylesheet, pdf_table_style)
                style_table = pdf_table_style.get(id, TableStyle())
            elif tag_name == 'tr':
                table_tr = []
                end_tag_tr = False

                tr_number += 1
                td_number = -1
            elif tag_name == 'td':
                table_td = []
                td_only_text = True
                end_tag_td = False
                td_number += 1
                if len(attributes) > 0:
                    build_td_attributes(style_table, attributes, tr_number, 
                                        td_number)
            elif tag_name == 'image':
                if stack[-1][0] == 'td':
                    push = False
                    widget = image_stream(stream, tag_uri, tag_name,
                                          attributes, pdf_stylesheet, True)
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
                                              attributes, pdf_stylesheet,
                                              alias_style)
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
                                                 attributes, pdf_stylesheet,
                                                 alias_style)
                    if td_only_text == True:
                        table_td = [x for x in  table_td if not is_str(x)]
                    table_td.append(widget)
                    td_only_text = False
                else:
                    pass
            
            elif tag_name == 'hr':
                if stack[-1][0] == 'td':
                    push = False
                    widget = hr_stream(stream, tag_uri, tag_name, attributes)
                    if td_only_text == True:
                        table_td = [x for x in  table_td if not is_str(x)]
                    table_td.append(widget)
                    td_only_text = False
            elif tag_name == 'spacer':
                if stack[-1][0] == 'td':
                    push = False
                    widget = spacer_stream(stream, tag_uri, tag_name,
                                           attributes, pdf_stylesheet)
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
                                          attributes, pdf_stylesheet,
                                          pdf_table_style,
                                              alias_style)
                    if widget is not None:
                        if td_only_text == True:
                            table_td = [x for x in  table_td if not is_str(x)]
                        table_td.append(widget)
                        td_only_text = False
                else:
                    pass
            elif tag_name == 'illustration':
                if exist_attribute(attributes, ['width', 'height']):
                    push = False
                    if td_only_text == True:
                        table_td = [x for x in  table_td if not is_str(x)]
                    widget = iIllustration(stream, tag_uri, tag_name, 
                                           attributes)
                    table_td.append(widget)
                    td_only_text = False
            elif tag_name == 'bulkData':
                push = True
            elif tag_name in ['excelData']:
                tag_not_supported = True
                push = True
                print TAG_NOT_SUPPORTED % (_tag_name, line_number, tag_name)
            else:
                print TAG_NOT_SUPPORTED % (_tag_name, line_number, tag_name)
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
                try:
                    table_attrs['style'] = style_table
                    table_attrs['data'] = data_table
                    table_attrs['colWidths'] = colWidths_table
                    table_attrs['rowHeights'] = rowHeights_table
                    widget = Table(**table_attrs)
                    return widget
                except ValueError, msg:
                    if tag_not_supported == False:
                        raise ValueError, 'Error line %s, %s' % (line_number, 
                                                                 msg)
                    else:
                        return None
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
        elif event == CDATA:
            lines = value.strip().split('\n')
            for line in lines:
                data_table.append(line.split(','))


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


def create_hr(attributes):
    """ 
        Create a reportlab hr widget
    """
    
    attrs = {}
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
    else:
        fn = XPreformatted

    style = get_style(pdf_stylesheet, alias_style, style_name)
  
    widget = fn(content, style)
    return widget


def create_image(element, check_dimension):
    """ 
        Create a reportlab image widget.
        If check_dimension is true and the width and the height attributes
        are not set we return None
    """

    width, height = None, None
    filename = None

    for key, attr_value in element[1].iteritems():
        key = key[1]
        if key == 'file':
            filename = attr_value
        elif key == 'width':
            width = rml_value(attr_value)
        elif key == 'height':
            height = rml_value(attr_value)
    
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
        Create a reportlab spacer widget.
    """

    width, length = 0, None

    for key, attr_value in element[1].iteritems():
        key = key[1]
        if key == 'width':
            width = rml_value(attr_value)
        elif key == 'length':
            length = rml_value(attr_value)

    if length != None:
        return Spacer(width, length)
    else:
        return None


def create_frame(attributes, template_attrs, document_attrs):
    """
        Return a Reportlab Frame is attributes is well formed, None otherwise
    """
    attrs = {'id': attributes.get((None, 'id'))}
    vfp = {'x1': template_attrs['pagesize'][0],
           'y1': template_attrs['pagesize'][1],
           'width': template_attrs['pagesize'][0],
           'height':template_attrs['pagesize'][1]}
    show_boundary = document_attrs['showBoundary']

    for key in ['x1', 'y1', 'width', 'height']:
        temp = attributes.get((None, key))
        if temp is not None:
            if is_str(temp) and temp.find('%') != -1:
                attrs[key] = get_value_from_percentage(temp, vfp[key])
            else:
                attrs[key] = rml_value(temp)

    if len(attrs) == 5:
        attrs['showBoundary'] = show_boundary
        attrs['leftPadding'] = 0
        attrs['bottomPadding'] = 0
        attrs['rightPadding'] = 0
        attrs['topPadding'] = 0
        return Frame(**attrs)
    else:
        # frame tag not well formed
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
                           'bulletFontSize', 'bulletIndent', 
                           'borderWidth', 'borderPadding', 'borderRadius']:
                    attr_value = rml_value(attr_value)
                elif key in ['textColor', 'backColor', 'borderColor']:
                    attr_value = get_color(attr_value)
                elif key == 'keepWithNext':
                    attr_value = to_bool(attr_value)
                elif key == 'alignment':
                    attr_value = __tab_para_alignment.get(attr_value.upper(), 
                                                          None)
                    if attr_value is None:
                        # tag not well formed
                        attr_value = __tab_para_alignment.get('LEFT')
                
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
                attr['colorName'] = get_color(attr['colorName'])
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
                attr['colorName'] = get_color(attr['colorName'])
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
                attr['value'] = attr['value'].upper()
                if attr['value'] not in ['LEFT', 'RIGHT', 'CENTER', 
                                         'CENTRE', 'DECIMAL']:
                    # tag not well formed
                    attr['value'] = 'LEFT'
                
                style.add('ALIGNMENT', attr['start'], attr['stop'], 
                          attr['value'])
            else:
                # tag not well formed
                pass

        elif elt_id == 'blockValign':
            if attr.has_key('value') == True:
                attr['value'] = attr['value'].upper()
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
                attr['length'] = rml_value(attr['length'])
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
                attr['kind'] = attr['kind'].upper()
                if attr['kind'] not in kind_list: 
                    # tag not well formed
                    pass
                else:
                    attr['colorName'] = get_color(attr['colorName'])
                    if attr.has_key('thickness') == False:
                        attr['thickness'] = 1
                    if attr.has_key('count') == False:
                        attr['count'] = 1
                    else:
                        attr['count'] = to_int(attr['count'], 1)
                    attr['thickness'] = to_float(attr['thickness'], 1)
                    style.add(attr['kind'], attr['start'], attr['stop'], 
                              attr['thickness'], attr['colorName'], 
                              attr['count'])
            else:
                # tag not well formed
                pass
        
        elif elt_id == 'blockSpan':
            style.add('SPAN', attr['start'], attr['stop'])

    pdf_table_style[id] = style


def build_td_attributes(style, attributes, line, column):
    """ """
    start = (column, line)
    stop = start
    line_attributes = {}
    thickness_tab = {}

    for key, value in attributes.iteritems():
        key = key[1]
       
        if key == 'fontColor':
            color = get_color(value)
            style.add('TEXTCOLOR', start, stop, color)
        elif key == 'fontName':
            style.add('FONTNAME', start, stop, value)
        elif key == 'fontSize':
            size = to_int(value, 5)
            style.add('FONTSIZE', start, stop, size)
        elif key == 'leading':
            style.add('LEADING', start, stop, to_float(value))
        elif key in ['leftPadding', 'rightPadding', 'topPadding', 
                     'bottomPadding']:
            value = rml_value(value)
            style.add(key.upper(), start, stop, value)
        elif key == 'background':
            color = get_color(value)
            style.add('BACKGROUND', start, stop, color)
        elif key == 'align':
            value = value.upper()
            if value in ['LEFT', 'RIGHT', 'CENTER', 'CENTRE']:
                style.add('ALIGNMENT', start, stop, value)
        elif key == 'vAlign':
            value = value.upper()
            if value in ['TOP', 'MIDDLE', 'BOTTOM']:
                style.add('VALIGN', start, stop, value)
        elif key in ['lineBelowColor', 'lineAboveColor', 'lineLeftColor', 
                     'lineRightColor']:
            key_tab = key.replace('Color', '')
            color = get_color(value)
            if thickness_tab.has_key(key_tab) == False:
                d = {}
                d['color'] = color
                d['thickness'] = 1
                thickness_tab[key_tab] = d
            else:
                thickness_tab[key_tab]['color'] = color

        elif key in ['lineBelowThickness', 'lineAboveThickness',
                     'lineLeftThickness', 'lineRightThickness']:
            thickness = rml_value(value)
            key_tab = key.replace('Thickness', '')
            if thickness_tab.has_key(key_tab) == False:
                d = {}
                d['color'] = colors.black
                d['thickness'] = thickness
                thickness_tab[key_tab] = d
            else:
                thickness_tab[key_tab]['thickness'] = thickness

    for key, d in thickness_tab.iteritems():
        if key in ['lineAbove', 'lineBelow']:
            style.add(key.upper(), start, stop, d['thickness'], d['color'])
        elif key == 'lineLeft':
            style.add('LINEBEFORE', start, stop, d['thickness'], d['color'])
        elif key == 'lineRight':
            style.add('LINEAFTER', start, stop, d['thickness'], d['color'])


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
    true = [u'true', u'1', u'yes', 1]
    false = [u'false', u'0', u'no', 0]
    if str in false:
        return False
    elif str in true:
        return True
    else:
        if default in [False, True]:
            return default
        else:
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
        orienter, data = get_page_size_orientation(data)
        data = normalize(data)
        ps = __tab_page_size.get(data.upper())
        if ps is not None:
            return orienter(ps)

        if data[0] == '(':
            data = data[1:]
        if data[-1] == ')':
            data = data[0:-1]

        tab_size = data.split(',')
        if len(tab_size) >= 2:
            w = rml_value(tab_size[0])
            h = rml_value(tab_size[1])
            data = (w, h)
        else:
            data = pagesizes.A4
      
        return orienter(data)
    return pagesizes.A4
    

def get_page_size_orientation(data):
    """ 
        Return the orienter and the pagesize
        example: 
        data = 'letter landscape'
        return (landscape, 'letter')

        data = '(21cm,29.7cm)'
        return (portrait, '(21cm,29.7cm)')
    """

    index = data.find('portrait')
    if index != -1:
        data = data.replace('portrait', '')
        return (portrait, data)

    index = data.find('landscape')
    if index != -1:
        data = data.replace('landscape', '')
        return (landscape, data)
    
    return (portrait, data)


def exist_attribute(attrs, keys):
    """ 
        Return True if all key in keys
        are contained in the dictionnary attrs
    """

    for key in keys:
        if attrs.has_key((None, key)) == False:
            return False
    return True


def get_color(col_str):
    """ 
        col_str can be one of this value type

        red, blue, ... : color name
        1,0,1 : color components
        1,0,0,1 : color cyan/magenta/yellow/black
    """

    color = getattr(colors, col_str, None)
    if color is not None:
        return color

    color = col_str.replace('(', '').replace(')', '')
    color = color.replace('[', '').replace(']', '')
    color = color.strip()

    if len(color) > 2 and color[:2] == '0x':
        try:
            return HexColor(color)
        except ValueError:
            return colors.black

    components = color.split(',')
    if len(components) == 3:
        # RGB
        r = to_float(components[0])
        g = to_float(components[1])
        b = to_float(components[2])
        return Color(r, g, b)
    elif len(components) == 4:
        # CYAN/MAGENTA/YELLOW/BLACK
        cyan = to_float(components[0])
        magenta = to_float(components[1])
        yellow = to_float(components[2])
        black = to_float(components[3])
        return CMYKColor(cyan , magenta, yellow, black)
        
    return colors.black
