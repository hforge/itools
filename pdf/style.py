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

from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from utils import (URI, FONT, font_value, format_size, get_color_as_hexa,
                   get_color, get_int_value)

P_ALIGNMENTS = {'left': TA_LEFT, 'right': TA_RIGHT, 'center': TA_CENTER,
              'justify': TA_JUSTIFY}
TAB_V_ALIGN = ('top', 'middle', 'bottom')
TAB_H_ALIGN = {'left': 'LEFT', 'right': 'RIGHT', 'center': 'CENTER',
               'justify': 'LEFT'}

H_ALIGN = ('left', 'right', 'center')
V_ALIGN = ('top', 'middle', 'bottom')

P_PADDINGS = {'padding-top' : 'spaceBefore', 'padding-bottom': 'spaceAfter',
              'padding-left': 'leftIndent', 'padding-right': 'rightIndent'}

HEADING = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')

TABLE_PADDINGS = { 'padding-top':'TOPPADDING',
                   'padding-bottom': 'BOTTOMPADDING',
                   'padding-left': 'LEFTPADDING',
                   'padding-right': 'RIGHTPADDING'}


def get_align(attributes):
    attrs = {}
    hAlign = attributes.get((URI, 'align'), None)
    if hAlign in H_ALIGN:
        attrs['hAlign'] = hAlign.upper()
    vAlign = attributes.get((URI, 'valign'), None)
    if vAlign in V_ALIGN:
        attrs['vAlign'] = vAlign.upper()
    return attrs


def p_border_style(key, value):
    style_attrs = {}
    if key == 'border':
        tab = value.split()
        for element in tab:
            size = format_size(element, None)
            if size:
                style_attrs['borderWidth'] = size
                continue
            color = get_color_as_hexa(element, None)
            if color:
                style_attrs['borderColor'] = color
                continue
    elif key == 'border-color':
        color = get_color_as_hexa(value, None)
        if color:
            style_attrs['borderColor'] = color
    elif key == 'border-width':
        size = format_size(value, None)
        if size:
            style_attrs['borderWidth'] = size
    return style_attrs


def table_border_style(border, start, stop):
    width = border.get('borderWidth', None)
    if width is not None and width > 0:
        color = get_color(border.get('borderColor', 'grey'))
        return [('GRID', start, stop, width, color)]
    return []


def inline_color_style(key, value, context):
    style = None
    if key == 'color':
        style = ('span', {(URI, key): get_color_as_hexa(value)})
    elif key in ('background-color'):
        style = ('span', {(URI, 'backColor'): get_color_as_hexa(value)})
    return style
    

def inline_text_style(key, value, context):
    style = None
    if key == 'text-decoration':
        if value == 'underline':
            style = ('u', {})
    return style


def inline_font_style(key, value, context):
    style = None
    if key == 'font-family':
        style = ('span', {(URI, 'fontName'): FONT.get(value, 'Helvetica')})
    elif key == 'font-style':
        if value in ('italic', 'oblique'):
            style = ('i', {})
        elif value != 'normal':
            print 'Warning font-style not valid'
    elif key == 'font-size':
        style = ('span', {(URI, 'fontSize'): font_value(value)})
    return style


def p_font_style(key, value, context):
    style_attr = {}
    if key == 'font-family':
        style_attr['fontName'] = FONT.get(value, 'Helvetica')
    elif key == 'font-style':
        if value in ('italic', 'oblique'):
            context.style_tag_stack.append(('i'))
        elif value != 'normal':
            print 'Warning font-style not valid'
    elif key == 'font-size':
        style_attr['fontSize'] = font_value(value)
    elif key == 'font-weight':
        if len(value):
            if value[0].isalpha() and value in ('bold', 'bolder'):
                context.style_tag_stack.append(('b'))
            elif not get_int_value(value, 400) < 700:
                context.style_tag_stack.append(('b'))
    return style_attr


def p_padding_style(key, value):
    style_attr = {}
    size = format_size(value, None)
    if size:
        if key == 'padding':
            for padding in P_PADDINGS.values():
                style_attr[padding] = size
        elif key in P_PADDINGS.keys():
            style_attr[P_PADDINGS[key]] = size
    return style_attr


def table_padding_style(key, value, start, stop):
    style = []
    size = format_size(value, None)
    if size:
        if key == 'padding':
            for padding in TABLE_PADDINGS.values():
                style.append((padding, start, stop, size))
        elif key in TABLE_PADDINGS.keys():
            style.append((TABLE_PADDINGS[key], start, stop, size))
    return style


def table_bg_style(key, value, start, stop):
    style = []
    if key == 'background-color':
        color = get_color(value)
        style.append(('BACKGROUND', start, stop, color))
    return style


def table_align_style(key, value, start, stop):

    style = []
    if key == 'vertical-align':
        if value in TAB_V_ALIGN:
            style.append(('VALIGN', start, stop, key.upper()))
    elif key == 'text-align':
        val = TAB_H_ALIGN.get(value, 'LEFT')
        style.append(('ALIGN', start, stop, val))
    return style


def build_paragraph_style(context, element, style_css):
    style_attr = {}
    # The default style is Normal
    parent_style_name = 'Normal'
    bulletText = None

    style_attr['autoLeading'] = 'max'

    #FIXME must be moved in default css
    style_attr['spaceAfter'] = 0.2 * cm
    for key, value in style_css.iteritems():
        if key == 'color':
            style_attr['textColor'] = get_color_as_hexa(value)
        elif key in ('background-color'):
            style_attr['backColor'] = get_color_as_hexa(value)
        elif key == 'text-align':
            if value in P_ALIGNMENTS.keys():
                style_attr['alignment'] = P_ALIGNMENTS.get(value)
        elif element[0] not in ('td', 'th') and key.startswith('border'):
            style_attr.update(p_border_style(key, value))
        elif key.startswith('font'):
            style_attr.update(p_font_style(key, value, context))
        elif key.startswith('padding'):
            style_attr.update(p_padding_style(key, value))

    # Overload the attributes values
    for key, attr_value in element[1].iteritems():
        key = key[1] # (None, key)
        if key == 'class':
            # Set the parent style for inheritance
            parent_style_name = attr_value
        elif key == 'bulletText':
            bulletText = attr_value

    if element[0] in HEADING + ('toctitle', ):
        parent_style_name = element[0]
    style_name = parent_style_name
    parent_style = context.get_style(parent_style_name)
    return (ParagraphStyle(style_name, parent=parent_style, **style_attr),
            bulletText)


def build_inline_style(context, tag_name, style_css):
    style = {}
    for key, value in style_css.iteritems():
        if key.endswith('color'):
            tag_and_attrs = inline_color_style(key, value, context)
        elif key.startswith('font'):
            tag_and_attrs = inline_font_style(key, value, context)
        elif key.startswith('text'):
            tag_and_attrs = inline_text_style(key, value, context)
        else:
            continue
        if tag_and_attrs:
            tag, attrs = tag_and_attrs
            if style.has_key(tag):
                style[tag].update(attrs)
            else:
                style[tag] = attrs
    for tag, attrs in style.iteritems():
        context.tag_stack[0].append((tag, attrs))


def get_table_style(context, attributes, start, stop):
    style_css = context.get_css_props()
    table_style = []
    border = {}

    for key, value in style_css.iteritems():
        if key.startswith('border'):
            border.update(p_border_style(key, value))
        elif key.startswith('padding'):
            table_style.extend(table_padding_style(key, value, start, stop))
        elif key.startswith('background'):
            table_style.extend(table_bg_style(key, value, start, stop))
        elif key.endswith('align'):
            table_style.extend(table_align_style(key, value, start, stop))

    for key, value in attributes.iteritems():
        if key == (URI, 'border') and start == (0, 0) and stop == (-1,-1):
            border.update(p_border_style('border-width', value))
        if key[0] == URI and key[1] in ATTR_TO_STYLE.keys():
            function, style_key = ATTR_TO_STYLE[key[1]]
            table_style.extend(function(style_key, value, start, stop))
    table_style.extend(table_border_style(border, start, stop))
    return table_style


def makeTocHeaderStyle(level, delta, epsilon, fontName='Times-Roman'):
    """
        Make a header style for different levels.
    """

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


# This map of functions is defined here
# to avoid definition's problems
ATTR_TO_STYLE = {'cellpadding': (table_padding_style, 'padding'),
                 'bgcolor': (table_bg_style, 'background-color')}
