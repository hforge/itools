# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from itools
from itools.datatypes import Boolean, Integer, Unicode, String, URI
from itools.xml import XMLError, XMLNamespace, register_namespace
from itools.xml import ElementSchema



###########################################################################
# Attributes
###########################################################################
class Boolean(Boolean):

    @staticmethod
    def decode(value):
        return value


    @staticmethod
    def encode(value):
        return value


html_attributes = {
    'abbr': Unicode,
    'accept-charsert': String,
    'accept': String,
    'accesskey': Unicode,
    'action': URI,
    'align': String,
    'alink': String,
    'alt': Unicode,
    'archive': Unicode,
    'axis': Unicode,
    'background': URI,
    'bgcolor': String,
    'border': Integer,
    # XXX Check, http://www.w3.org/TR/html4/index/attributes.html
    'cellpadding': Unicode,
    'cellspacing': Unicode,
    'char': Unicode,
    'charoff': Unicode,
    'charset': Unicode,
    'checked': Boolean,
    'cite': Unicode,
    'class': Unicode,
    'classid': Unicode,
    'clear': Unicode,
    'code': Unicode,
    'codebase': Unicode,
    'codetype': Unicode,
    'color': Unicode,
    'cols': Unicode,
    'colspan': Unicode,
    'compact': Boolean,
    'content': Unicode,
    'coords': Unicode,
    'data': Unicode,
    'datetime': Unicode,
    'declare': Boolean,
    'defer': Boolean,
    'dir': Unicode,
    'disabled': Boolean,
    'enctype': Unicode,
    'face': Unicode,
    'for': Unicode,
    'frame': Unicode,
    'frameborder': Unicode,
    'headers': Unicode,
    'height': Unicode,
    'href': URI,
    'hreflang': Unicode,
    'hspace': Unicode,
    'http-equiv': Unicode,
    'id': Unicode,
    'ismap': Boolean,
    'label': Unicode,
    'lang': Unicode,
    'language': Unicode,
    'link': Unicode,
    'longdesc': Unicode,
    'marginheight': Unicode,
    'marginwidth': Unicode,
    'maxlength': Unicode,
    'media': Unicode,
    'method': Unicode,
    'multiple': Boolean,
    'name': Unicode,
    'nohref': Unicode,
    'noresize': Boolean,
    'noshade': Boolean,
    'nowrap': Boolean,
    'object': Unicode,
    'onblur': Unicode,
    'onchange': Unicode,
    'onclick': Unicode,
    'ondblclick': Unicode,
    'onfocus': Unicode,
    'onkeydown': Unicode,
    'onkeypress': Unicode,
    'onkeyup': Unicode,
    'onload': Unicode,
    'onmousedown': Unicode,
    'onmousemove': Unicode,
    'onmouseout': Unicode,
    'onmouseover': Unicode,
    'onmouseup': Unicode,
    'onreset': Unicode,
    'onselect': Unicode,
    'onsubmit': Unicode,
    'onunload': Unicode,
    'profile': Unicode,
    'prompt': Unicode,
    'readonly': Boolean,
    'rel': Unicode,
    'rev': Unicode,
    'rows': Unicode,
    'rowspan': Unicode,
    'rules': Unicode,
    'scheme': Unicode,
    'scope': Unicode,
    'scrolling': Unicode,
    'selected': Boolean,
    'shape': Unicode,
    'size': Unicode,
    'span': Unicode,
    'src': URI,
    'standby': Unicode,
    'start': Unicode,
    'style': Unicode,
    'summary': Unicode,
    'tabindex': Unicode,
    'target': Unicode,
    'text': Unicode,
    'title': Unicode,
    'type': Unicode,
    'usemap': Unicode,
    'valign': Unicode,
    'value': Unicode,
    'valuetype': Unicode,
    'version': Unicode,
    'vlink': Unicode,
    'vspace': Unicode,
    'width': Unicode,
    }


# Predefined sets of attributes
core_attrs = [
    'id', 'class', 'style', 'title']

i18n_attrs = [
    'lang', 'dir']

event_attrs = [
    'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover',
    'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

focus_attrs = [
    'accesskey', 'tabindex', 'onfocus', 'onblur']

common_attrs = core_attrs + i18n_attrs + event_attrs

cellhalign_attrs = ['align', 'char', 'charoff']

cellvalign_attrs = ['valign']



###########################################################################
# Elements
###########################################################################
class Element(ElementSchema):

    class_uri = 'http://www.w3.org/1999/xhtml'

    # Default
    is_empty = False
    is_inline = True
    translatable_attributes = frozenset(['title'])


    def __init__(self, name, attributes, **kw):
        ElementSchema.__init__(self, name, **kw)
        self.attributes = frozenset(attributes)


    def _get_attr_datatype(self, name):
        if name not in self.attributes:
            message = 'unexpected "%s" attribute for "%s" element'
            raise XMLError, message % (name, self.name)
        return html_attributes[name]


    def is_translatable(self, attributes, attribute_name):
        return attribute_name in self.translatable_attributes



class BlockElement(Element):
    
    is_inline = False



class EmptyElement(Element):

    is_empty = True



class EmptyBlockElement(Element):

    is_inline = False
    is_empty = True



class ImgElement(Element):

    is_inline = True
    is_empty = True
    translatable_attributes = frozenset(['alt', 'title'])



class InputElement(Element):

    is_inline = True
    is_empty = True

    def is_translatable(self, attributes, attribute_name):
        if attribute_name == 'value':
            key1 = (self.class_uri, 'type')
            key2 = (None, 'type')
            if attributes.get(key1) == 'submit':
                return True
            if attributes.get(key2) == 'submit':
                return True
            return False

        return Element.is_translatable(self, attributes, attribute_name)


###########################################################################
# Namespace
###########################################################################

html_elements = [
    # XHTML 1.0 strict
    Element('a', common_attrs + ['charset', 'type', 'name', 'href',
        'hreflang', 'rel', 'rev', 'accesskey', 'shape', 'coords', 'tabindex',
        'onfocus', 'onblur']),
    Element('abbr', common_attrs),
    Element('acronym', common_attrs),
    EmptyBlockElement('area', common_attrs + ['shape', 'coords', 'href',
        'nohref', 'alt', 'tabindex', 'accesskey', 'onfocus', 'onblur']),
    Element('b', common_attrs),
    EmptyBlockElement('base', ['href']),
    Element('bdo', common_attrs),
    Element('big', common_attrs),
    BlockElement('body', common_attrs + ['onload', 'onunload']),
    EmptyElement('br', core_attrs),
    Element('cite', common_attrs),
    Element('code', common_attrs),
    EmptyBlockElement('col', common_attrs + cellhalign_attrs +
        cellvalign_attrs + ['span', 'width']),
    Element('dfn', common_attrs),
    BlockElement('dd', common_attrs),
    BlockElement('div', common_attrs),
    BlockElement('dl', common_attrs + ['compact']),
    BlockElement('dt', common_attrs),
    Element('em', common_attrs),
    BlockElement('fieldset', common_attrs),
    BlockElement('form', common_attrs + ['action', 'method', 'enctype',
        'onsubmit', 'onreset', 'accept', 'accept-charset', 'name', 'target']),
    BlockElement('h1', common_attrs + ['TextAlign']),
    BlockElement('h2', common_attrs + ['TextAlign']),
    BlockElement('h3', common_attrs + ['TextAlign']),
    BlockElement('h4', common_attrs + ['TextAlign']),
    BlockElement('h5', common_attrs + ['TextAlign']),
    BlockElement('h6', common_attrs + ['TextAlign']),
    BlockElement('head', i18n_attrs + ['profile']),
    EmptyBlockElement('hr', common_attrs),
    BlockElement('html', i18n_attrs),
    Element('i', common_attrs),
    ImgElement('img', common_attrs + ['src', 'alt', 'longdesc', 'height',
        'width', 'usemap', 'ismap', 'name', 'align', 'border', 'hspace',
        'vspace']),
    InputElement('input', common_attrs + focus_attrs + ['type', 'name',
        'value', 'checked', 'disabled', 'readonly', 'size', 'maxlength',
        'src', 'alt', 'usemap', 'onselect', 'onchange', 'accept', 'align']),
    Element('kbd', common_attrs),
    Element('label', common_attrs + ['for', 'accesskey', 'onfocus', 'onblur']),
    BlockElement('legend', common_attrs + ['accesskey', 'align']),
    BlockElement('li', common_attrs + ['type', 'value']),
    EmptyElement('link', common_attrs + ['charset', 'href', 'hreflang',
        'type', 'rel', 'rev', 'media']),
    EmptyElement('meta', i18n_attrs + ['http-equiv', 'name', 'content',
        'scheme']),
    BlockElement('option', common_attrs + ['selected', 'disabled', 'label',
        'value']),
    BlockElement('p', common_attrs),
    EmptyElement('param', ['id', 'name', 'value', 'valuetype', 'type']),
    BlockElement('pre', common_attrs),
    Element('q', common_attrs + ['cite']),
    Element('samp', common_attrs),
    BlockElement('script', ['id', 'charset', 'type', 'language', 'src',
        'defer'], translate_content=False),
    # FIXME This is a lie, <select> elements *are* inline
    # TODO Do not use the inline/block for i18n, define instead another
    # variable for this purpose.
    BlockElement('select', common_attrs + ['name', 'size', 'multiple',
        'disabled', 'tabindex', 'onfocus', 'onblur', 'onchange']),
    Element('small', common_attrs),
    Element('span', common_attrs),
    Element('strong', common_attrs),
    Element('sub', common_attrs),
    Element('sup', common_attrs),
    BlockElement('style', i18n_attrs + ['type', 'media', 'title'],
        translate_content=False),
    BlockElement('table', common_attrs + ['summary', 'width', 'border',
        'frame', 'rules', 'cellspacing', 'cellpadding', 'align', 'bgcolor']),
    BlockElement('td', common_attrs + cellhalign_attrs + cellvalign_attrs +
        ['abbr', 'axis', 'headers', 'scope', 'rowspan', 'colspan', 'nowrap',
            'bgcolor', 'width', 'height']),
    Element('textarea', common_attrs + ['name', 'rows', 'cols', 'disabled',
        'readonly', 'tabindex', 'accesskey', 'onfocus', 'onblur', 'onselect',
        'onchange']),
    BlockElement('th', common_attrs + cellhalign_attrs + cellvalign_attrs +
        ['abbr', 'axis', 'headers', 'scope', 'rowspan', 'colspan', 'nowrap',
            'bgcolor', 'width', 'height']),
    BlockElement('colgroup', common_attrs + cellhalign_attrs + cellvalign_attrs
            + ['span', 'width']),
    BlockElement('tbody', common_attrs + cellhalign_attrs + cellvalign_attrs),
    BlockElement('tfoot', common_attrs + cellhalign_attrs + cellvalign_attrs),
    BlockElement('thead', common_attrs + cellhalign_attrs + cellvalign_attrs),
    BlockElement('title', i18n_attrs),
    BlockElement('tr', common_attrs + cellhalign_attrs + cellvalign_attrs),
    Element('tt', common_attrs),
    BlockElement('ul', common_attrs + ['type', 'compact']),
    Element('var', common_attrs),
    # XHTML 1.0 transitional
    EmptyElement('basefont', ['id', 'size', 'color', 'face']),
    Element('font', core_attrs + i18n_attrs + ['size', 'color', 'face']),
    EmptyBlockElement('isindex', core_attrs + i18n_attrs + ['prompt']),
    Element('s', common_attrs),
    Element('strike', common_attrs),
    Element('u', common_attrs),
    # XHTML 1.0 frameset
    EmptyBlockElement('frame', core_attrs + ['longdesc', 'name', 'src',
        'frameborder', 'marginwidth', 'marginheight', 'noresize',
        'scrolling']),
    BlockElement('frameset', core_attrs + ['rows', 'cols', 'onload',
        'onunload']),
    BlockElement('iframe', core_attrs + ['longdesc', 'name', 'src',
        'frameborder', 'marginwidth', 'marginheight', 'scrolling', 'align',
        'height', 'width']),
    BlockElement('noframes', common_attrs),
    # Vendor specific, not approved by W3C
    # for a talk about <embed> see:
    #   http://alistapart.com/articles/byebyeembed
    # FIXME Check the attribute list for <embed>
    EmptyBlockElement('embed', []),
    ]



html_namespace = XMLNamespace(
    'http://www.w3.org/1999/xhtml', None,
    html_elements)


###########################################################################
# Register
###########################################################################
register_namespace(html_namespace)

