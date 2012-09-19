# -*- coding: UTF-8 -*-
# Copyright (C) 2008 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2008 Nicolas Deram <nderam@gmail.com>
# Copyright (C) 2008-2010 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2008-2011 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2010 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2010 Norman Khine <khinester@aqoon.local>
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
    'accesskey': String,
    'action': URI,
    'align': String,
    'alink': String,
    'alt': Unicode,
    'archive': String,
    'axis': String,
    'background': URI,
    'bgcolor': String,
    'border': Integer,
    # XXX Check, http://www.w3.org/TR/html4/index/attributes.html
    'cellpadding': String,
    'cellspacing': String,
    'char': String,
    'charoff': String,
    'charset': String,
    'checked': Boolean,
    'cite': URI,
    'class': String,
    'classid': URI,
    'clear': String,
    'code': String,
    'codebase': URI,
    'codetype': String,
    'color': String,
    'cols': Integer,
    'colspan': Integer(default=1),
    'compact': Boolean,
    'content': String,
    'coords': String,
    'data': URI,
    'datetime': String,
    'declare': Boolean,
    'defer': Boolean,
    'dir': String,
    'disabled': Boolean,
    'enctype': String,
    'face': String,
    'for': String,
    'frame': String,
    'frameborder': String,
    'headers': String,
    'height': String,
    'href': URI,
    'hreflang': String,
    'hspace': String,
    'http-equiv': String,
    'id': String,
    'ismap': Boolean,
    'label': Unicode,
    'lang': String,
    'language': String,
    'link': String,
    'longdesc': URI,
    'marginheight': Integer,
    'marginwidth': Integer,
    'maxlength': Integer,
    'media': String,
    'method': String,
    'multiple': Boolean,
    'name': String,
    'nohref': Boolean,
    'noresize': Boolean,
    'noshade': Boolean,
    'nowrap': Boolean,
    'object': String,
    'onblur': String,
    'onchange': String,
    'onclick': String,
    'ondblclick': String,
    'onfocus': String,
    'onkeydown': String,
    'onkeypress': String,
    'onkeyup': String,
    'onload': String,
    'onmousedown': String,
    'onmousemove': String,
    'onmouseout': String,
    'onmouseover': String,
    'onmouseup': String,
    'onreset': String,
    'onselect': String,
    'onsubmit': String,
    'onunload': String,
    'profile': URI,
    'prompt': Unicode,
    'readonly': Boolean,
    'rel': String,
    'rev': String,
    'rows': String,
    'rowspan': Integer(default=1),
    'rules': String,
    'scheme': String,
    'scope': String,
    'scrolling': String,
    'selected': Boolean,
    'shape': String,
    'size': String,
    'span': Integer(default=1),
    'src': URI,
    'standby': Unicode,
    'start': Integer,
    'style': String,
    'summary': Unicode,
    'tabindex': Integer,
    'target': String,
    'text': String,
    'title': Unicode(context="title attribute"),
    'type': String,
    'usemap': URI,
    'valign': String,
    'value': String,
    'valuetype': String,
    'version': String,
    'vlink': String,
    'vspace': Integer,
    'width': String,
    # FIXME Not standard
    'autocomplete': String, # <input>
    'pluginspage': String, # <embed>
    'quality': String, # <embed>
    'autoplay': Boolean, # <embed>
    'wrap': String,
    'index': Integer,
    'min': String, # <input>
    'max': String, # <input>
    'data-icon': String, # <input>
    'data-icon1': String, # <input>
    'data-icon2': String, # <input>
    'mp': String, # <a>
    'm4v': String, # <a>
    'm4a': String, # <a>
    'oga': String, # <a>
    'ogg': String, # <a>
    'ogv': String, # <a>
    'webmv': String, # <a>
    'poster': String, # <a>
    'allowTransparency': String, # <iframe>
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
html_uri = 'http://www.w3.org/1999/xhtml'


class Element(ElementSchema):

    # Default
    is_empty = False
    is_inline = True


    def __init__(self, name, attributes, **kw):
        # By default: context = name of element
        self.context = '%s' % name

        ElementSchema.__init__(self, name, **kw)
        self.attributes = frozenset(attributes)


    def get_attr_datatype(self, name, attributes):
        if name not in self.attributes:
            message = 'unexpected "%s" attribute for "%s" element'
            raise XMLError, message % (name, self.name)
        return html_attributes[name]



class BlockElement(Element):

    is_inline = False



class EmptyElement(Element):

    is_empty = True



class EmptyBlockElement(Element):

    is_inline = False
    is_empty = True



class InputElement(Element):

    is_inline = True
    is_empty = True


    def get_attr_datatype(self, attr_name, attributes):
        if attr_name == 'value':
            key1 = (html_uri, 'type')
            key2 = (None, 'type')
            if (attributes.get(key1) == 'submit' or
                attributes.get(key2) == 'submit'):
                return Unicode(context='button')

        return Element.get_attr_datatype(self, attr_name, attributes)


###########################################################################
# Namespace
###########################################################################

html_elements = [
    # XHTML 1.0 strict
    Element('a', common_attrs + ['charset', 'type', 'name', 'href',
        'hreflang', 'rel', 'rev', 'accesskey', 'shape', 'coords', 'tabindex',
        'target', 'onfocus', 'onblur', 'mp', 'm4a', 'm4v', 'oga', 'ogg', 'ogv',
        'index', 'poster', 'webmv'], context='link'),
    Element('abbr', common_attrs),
    Element('acronym', common_attrs),
    BlockElement('address', common_attrs),
    EmptyBlockElement('area', common_attrs + ['shape', 'coords', 'href',
        'nohref', 'alt', 'tabindex', 'accesskey', 'onfocus', 'onblur']),
    Element('b', common_attrs),
    EmptyBlockElement('base', ['href']),
    Element('bdo', common_attrs),
    Element('big', common_attrs),
    BlockElement('blockquote', common_attrs + ['cite']),
    BlockElement('body', common_attrs + ['onload', 'onunload']),
    EmptyElement('br', core_attrs),
    Element('button', common_attrs + focus_attrs + ['name', 'value', 'type',
        'disabled']),
    BlockElement('caption', common_attrs),
    Element('cite', common_attrs),
    Element('code', common_attrs),
    EmptyBlockElement('col', common_attrs + cellhalign_attrs +
        cellvalign_attrs + ['span', 'width']),
    Element('dfn', common_attrs),
    BlockElement('dd', common_attrs),
    BlockElement('div', common_attrs + ['align', 'index']),
    BlockElement('dl', common_attrs + ['compact']),
    BlockElement('dt', common_attrs),
    Element('em', common_attrs, context="emphasis"),
    BlockElement('fieldset', common_attrs),
    BlockElement('form', common_attrs + ['action', 'method', 'enctype',
        'onsubmit', 'onreset', 'accept', 'accept-charset', 'name', 'target']),
    BlockElement('h1', common_attrs + ['align'], context='heading'),
    BlockElement('h2', common_attrs + ['align'], context='heading'),
    BlockElement('h3', common_attrs + ['align'], context='heading'),
    BlockElement('h4', common_attrs + ['align'], context='heading'),
    BlockElement('h5', common_attrs + ['align'], context='heading'),
    BlockElement('h6', common_attrs + ['align'], context='heading'),
    BlockElement('head', i18n_attrs + ['profile']),
    EmptyBlockElement('hr', common_attrs + ['align', 'noshade', 'size',
        'width']),
    BlockElement('html', i18n_attrs),
    Element('i', common_attrs),
    EmptyElement('img', common_attrs + ['src', 'alt', 'longdesc', 'height',
        'width', 'usemap', 'ismap', 'name', 'align', 'border', 'hspace',
        'vspace']),
    InputElement('input', common_attrs + focus_attrs + ['type', 'name',
        'value', 'checked', 'disabled', 'readonly', 'size', 'maxlength',
        'src', 'alt', 'usemap', 'onselect', 'onchange', 'accept', 'align',
        'autocomplete']),
    Element('kbd', common_attrs),
    Element('label', common_attrs + ['for', 'accesskey', 'onfocus',
                                     'onblur']),
    BlockElement('legend', common_attrs + ['accesskey', 'align']),
    BlockElement('li', common_attrs + ['type', 'value']),
    EmptyElement('link', common_attrs + ['charset', 'href', 'hreflang',
        'type', 'rel', 'rev', 'media']),
    BlockElement('map', i18n_attrs + event_attrs + ['id', 'class', 'style',
        'title', 'name']),
    EmptyElement('meta', i18n_attrs + ['http-equiv', 'name', 'content',
        'scheme']),
    BlockElement('object', common_attrs + ['declare', 'classid', 'codebase',
        'data', 'type', 'codetype', 'archive', 'standby', 'height', 'width',
        'usemap', 'name', 'tabindex', 'align', 'border', 'hspace', 'vspace']),
    BlockElement('ol', common_attrs + ['type', 'compact', 'start']),
    BlockElement('optgroup', common_attrs + ['disabled', 'label']),
    BlockElement('option', common_attrs + ['selected', 'disabled', 'label',
        'value']),
    BlockElement('p', common_attrs, context='paragraph'),
    EmptyElement('param', ['id', 'name', 'value', 'valuetype', 'type']),
    BlockElement('pre', common_attrs, keep_spaces=True),
    Element('q', common_attrs + ['cite']),
    Element('samp', common_attrs),
    BlockElement('script', ['id', 'charset', 'type', 'language', 'src',
        'defer'], skip_content=True),
    BlockElement('noscript', ['id']),
    # FIXME This is a lie, <select> elements *are* inline
    # TODO Do not use the inline/block for i18n, define instead another
    # variable for this purpose.
    BlockElement('select', common_attrs + ['name', 'size', 'multiple',
        'disabled', 'tabindex', 'onfocus', 'onblur', 'onchange']),
    Element('small', common_attrs),
    Element('span', common_attrs),
    Element('strong', common_attrs, context="emphasis"),
    Element('sub', common_attrs),
    Element('sup', common_attrs),
    BlockElement('style', i18n_attrs + ['type', 'media', 'title'],
        skip_content=True),
    BlockElement('table', common_attrs + ['summary', 'width', 'border',
        'frame', 'rules', 'cellspacing', 'cellpadding', 'align', 'bgcolor']),
    BlockElement('td', common_attrs + cellhalign_attrs + cellvalign_attrs +
        ['abbr', 'axis', 'headers', 'scope', 'rowspan', 'colspan', 'nowrap',
         'bgcolor', 'width', 'height'], context='table cell'),
    Element('textarea', common_attrs + ['name', 'rows', 'cols', 'disabled',
        'readonly', 'tabindex', 'accesskey', 'onfocus', 'onblur', 'onselect',
        'onchange', 'wrap']),
    BlockElement('th', common_attrs + cellhalign_attrs + cellvalign_attrs +
        ['abbr', 'axis', 'headers', 'scope', 'rowspan', 'colspan', 'nowrap',
         'bgcolor', 'width', 'height'], context='table cell'),
    BlockElement('colgroup', common_attrs + cellhalign_attrs +
                             cellvalign_attrs + ['span', 'width']),
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
    BlockElement('center', core_attrs),
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
    # HTML 5
    # TODO Complete and check against an official description or schema (there
    # is not a DTD in HTML5)
    EmptyBlockElement('canvas', common_attrs + ['width', 'height']),
    # Vendor specific, not approved by W3C
    # for a talk about <embed> see:
    #   http://alistapart.com/articles/byebyeembed
    # FIXME Check the attribute list for <embed>
    EmptyBlockElement('embed', ['quality', 'pluginspage', 'src', 'type',
        'autoplay', 'width', 'height']),
    ]



html_namespace = XMLNamespace(html_uri, None, html_elements)


###########################################################################
# Register
###########################################################################
register_namespace(html_namespace)

