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
from utils import FONT, font_value, format_size, get_color_as_hexa

ALIGNMENTS = {'left': TA_LEFT, 'right': TA_RIGHT, 'center': TA_CENTER,
              'justify': TA_JUSTIFY}

PADDINGS = {'padding-top' : 'spaceBefore', 'padding-bottom': 'spaceAfter',
            'padding-left': 'leftIndent', 'padding-right': 'rightIndent'}

HEADING = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')

def border_style(context, value):
    tab = value.split()
    style_attrs = {}
    for i in tab:
        size = format_size(i, None)
        if size:
            style_attrs['borderWidth'] = size
            continue
        color = get_color_as_hexa(i, None)
        if color:
            style_attrs['borderColor'] = color
            continue
    return style_attrs


def font_style(context, key, value):
    style_attr = {}
    if key == 'font-family':
        style_attr['fontName'] = FONT.get(value, 'Helvetica')
    elif key == 'font-size':
        style_attr['fontSize'] = font_value(value)
    return style_attr


def padding_style(context, key, value):
    style_attr = {}
    value = format_size(value, None)
    if value:
        if key == 'padding':
            for attr_key in PADDINGS.values():
                style_attr[attr_key] = value
        elif key in PADDINGS.keys():
            style_attr[PADDINGS[key]] = value
    return style_attr


def build_paragraph_style(context, element, style_css):
    style_attr = {}
    # The default style is Normal
    parent_style_name = 'Normal'
    bulletText = None

    #FIXME must be moved in default css
    style_attr['spaceAfter'] = 0.2 * cm
    for key in style_css.keys():
        if key == 'color':
            style_attr['textColor'] = get_color_as_hexa(style_css[key])
        elif key in ('background', 'background-color'):
            style_attr['backColor'] = get_color_as_hexa(style_css[key])
        elif key.startswith('border'):
            style_attr.update(border_style(context, style_css[key]))
        elif key.startswith('font'):
            style_attr.update(font_style(context, style_css[key]))
        elif key.startswith('padding'):
             style_attr.update(padding_style(context, key, style_css[key]))

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
                attr_value = ALIGNMENTS.get(attr_value, TA_LEFT)
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
