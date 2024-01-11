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
from itools.core import proto_lazy_property
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
    # HTML5
    'controls': String,
    }


# Predefined sets of attributes

# https://www.w3.org/TR/html5/single-page.html#global-attributes
global_attrs = [
    'accesskey', 'class', 'contenteditable', 'dir', 'hidden',
    'id', 'lang', 'spellcheck', 'style', 'tabindex', 'title',
    'translate']

# https://www.w3.org/TR/html5/single-page.html#global-attributes
event_attrs = [
    'onabort', 'onblur', 'oncancel', 'oncanplay', 'oncanplaythrough',
    'onchange', 'onclick', 'oncuechange', 'ondblclick', 'ondurationchange',
    'onemptied', 'onended', 'onerror', 'onfocus', 'oninput', 'oninvalid',
    'onkeydown', 'onkeypress', 'onkeyup', 'onload', 'onloadeddata',
    'onloadedmetadata', 'onloadstart', 'onmousedown', 'onmouseenter',
    'onmouseleave', 'onmousemove', 'onmouseout', 'onmouseover', 'onmouseup',
    'onmousewheel', 'onpause', 'onplay', 'onplaying', 'onprogress', 'onratechange',
    'onreset', 'onresize', 'onscroll', 'onseeked', 'onseeking', 'onselect',
    'onshow', 'onstalled', 'onsubmit', 'onsuspend', 'ontimeupdate', 'ontoggle',
    'onvolumechange', 'onwaiting',]

# https://www.w3.org/TR/html5/single-page.html#custom-data-attribute
custom_attr = []

aria_attrs = ['aria-atomic', 'aria-busy', 'aria-controls', 'aria-describedby',
              'aria-disabled', 'aria-dropeffect', 'aria-flowto', 'aria-grabbed',
              'aria-haspopup', 'aria-hidden', 'aria-invalid', 'aria-label',
              'aria-labelledby', 'aria-live', 'aria-owns', 'aria-relevant',
              'aria-expanded', 'aria-valuemin', 'aria-valuemax', 'aria-valuenow',
              'role']

common_attrs = global_attrs + event_attrs + custom_attr + aria_attrs



###########################################################################
# Elements
###########################################################################
html_uri = 'http://www.w3.org/1999/xhtml'


class Element(ElementSchema):

    # Default
    strict = True
    is_empty = False
    is_inline = True
    attributes = []
    obsolete_attributes = []
    free_attributes = html_attributes

    def get_attr_datatype(self, name, attr_attributes):
        attributes = common_attrs + self.attributes + self.obsolete_attributes
        if name not in attributes and not name.startswith(('data-', 'ng-')):
            if self.strict:
                message = 'unexpected "{}" attribute for "{}" element'
                raise XMLError(message.format(name, self.name))
            else:
                msg = "WARNING HTML5: {} isn't an attribute for element {}"
                print(msg.format(name, self.name))
                return String
        if name in self.obsolete_attributes:
            msg = 'WARNING HTML5: {} is an obsolete attribute for element {}'
            print(msg.format(name, self.name))
        # Configured datatype
        if self.free_attributes.get(name, None):
            return self.free_attributes.get(name)
        # Proxy
        return String


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
        proxy = super(InputElement, self)
        return proxy.get_attr_datatype(attr_name, attributes)


class WebComponentElement(BlockElement):

    def get_attr_datatype(self, attr_name, attributes):
        return String

###########################################################################
# Namespace
###########################################################################
obsolete_html_elements = [
    Element(name='applet', obsolete_attributes=['datasrc', 'datafld']),
    Element(name='acronym'),
    Element(name='bgsound'),
    Element(name='dir'),
    EmptyBlockElement(
        name='frame',
        attributes=['longdesc', 'name', 'src',
          'frameborder', 'marginwidth', 'marginheight', 'noresize',
          'scrolling'],
        obsolete_attributes=['datasrc', 'datafld']),
    BlockElement(name='frameset', attributes=['rows', 'cols', 'onload',
        'onunload']),
    BlockElement(name='noframes'),
    BlockElement(name='hgroup'),
    BlockElement(name='isindex', attributes=['prompt']),
    BlockElement(name='listing', attributes=['prompt']),
    BlockElement(name='nextid', attributes=['prompt']),
    BlockElement(name='noembed', attributes=['prompt']),
    BlockElement(name='plaintext', attributes=['prompt']),
    Element(name='strike'),
    Element(name='xmp'),
    EmptyElement(name='basefont', attributes=['id', 'size', 'color', 'face']),
    EmptyElement(name='big', attributes=['id', 'size', 'color', 'face']),
    EmptyElement(name='blink', attributes=['id', 'size', 'color', 'face']),
    BlockElement(name='center'),
    Element(name='font', attributes=['size', 'color', 'face']),
    Element(
        name='marquee',
        attributes=['size', 'color', 'face'],
        obsolete_attributes=['datasrc', 'datafld', 'dataformatas']),
    Element(name='multicol', attributes=['size', 'color', 'face']),
    Element(name='nobr', attributes=['size', 'color', 'face']),
    Element(name='spacer', attributes=['size', 'color', 'face']),
    Element(name='tt'),
]

# FIXME This is a lie, <select> elements *are* inline
# TODO Do not use the inline/block for i18n, define instead another
# variable for this purpose.

html_elements = [
    Element(
      name='a',
      attributes=['href', 'target', 'download', 'rel', 'hreflang', 'type'],
      obsolete_attributes=['charset', 'coords', 'shape', 'methods', 'name',
                           'urn', 'datasrc', 'datafld'],
      context='link'),
    Element(name='abbr'),
    BlockElement(name='address'),
    EmptyBlockElement(
        name='area',
        attributes=['alt', 'coords', 'shape', 'href', 'target', 'download',
                    'rel', 'hreflang', 'type'],
        obsolete_attributes=['nohref']),
    BlockElement(name='article'),
    BlockElement(name='aside'),
    BlockElement(
        name='audio',
        attributes=['src', 'crossorigin', 'preload', 'autoplay', 'mediagroup',
                    'loop', 'muted', 'controls']),
    Element(name='b'),
    EmptyBlockElement(
        name='base',
        attributes=['href', 'target']),
    Element(name='bdi'),
    Element(name='bdo'),
    BlockElement(name='blockquote', attributes=['cite']),
    BlockElement(
        name='body',
        attributes=['onafterprint', 'onbeforeprint', 'onbeforeunload',
                    'onhashchange', 'onmessage', 'onoffline', 'ononline',
                    'onpagehide', 'onpageshow', 'onpopstate', 'onstorage',
                    'onunload'],
        obsolete_attributes=['alink', 'bgcolor', 'link', 'marginbottom',
              'marginheight', 'marginleft', 'marginright', 'margintop',
              'marginwidth', 'text', 'vlink', 'background']),
    EmptyElement(
        name='br',
        obsolete_attributes=['clear']),
    Element(
        name='button',
        attributes=['autofocus', 'disabled', 'form', 'formaction',
                    'formenctype', 'formmethod', 'formonvalidate',
                    'formtarget', 'name', 'type', 'value'],
        obsolete_attributes=['datasrc', 'datafld', 'dataformatas']),
    BlockElement(name='canvas', attributes=['width', 'height']),
    BlockElement(
        name='caption',
        obsolete_attributes=['align']),
    Element(name='cite'),
    Element(name='code'),
    EmptyBlockElement(
        name='col',
        attributes=['span'],
        obsolete_attributes=['align', 'char', 'charoff', 'valign', 'width']),
    BlockElement(
        name='colgroup',
        attributes=['span'],
        obsolete_attributes=['width']),
    BlockElement(name='data', attributes=['value']),
    BlockElement(name='datalist'),
    BlockElement(name='dd'),
    BlockElement(name='del', attributes=['cite', 'datetime']),
    BlockElement(name='dfn'),
    BlockElement(
        name='div',
        obsolete_attributes=['datasrc', 'datafld', 'dataformatas', 'align',
                             'valign']),
    BlockElement(
        name='dl',
        obsolete_attributes=['compact']),
    BlockElement(name='dt'),
    Element(name='em', context="emphasis"),
    EmptyBlockElement(
      name='embed',
      attributes=['src', 'type', 'width', 'height', 'any* XXX '],
      obsolete_attributes=['name', 'align', 'hspace', 'vspace',]),
    BlockElement(
        name='fieldset',
        attributes=['disabled', 'form', 'name'],
        obsolete_attributes=['datafld']),
    BlockElement(name='figcaption'),
    BlockElement(name='figure'),
    BlockElement(name='footer'),
    BlockElement(
        name='form',
        attributes=['accept-charset', 'action', 'autocomplete', 'enctype',
                    'method', 'name', 'novalidate', 'target'],
        obsolete_attributes=['accept']),
    BlockElement(name='h1', obsolete_attributes=['align'], context='heading'),
    BlockElement(name='h2', obsolete_attributes=['align'], context='heading'),
    BlockElement(name='h3', obsolete_attributes=['align'], context='heading'),
    BlockElement(name='h4', obsolete_attributes=['align'], context='heading'),
    BlockElement(name='h5', obsolete_attributes=['align'], context='heading'),
    BlockElement(name='h6', obsolete_attributes=['align'], context='heading'),
    BlockElement(name='head', obsolete_attributes=['profile']),
    BlockElement(name='header'),
    EmptyBlockElement(
        name='hr',
        obsolete_attributes=['align', 'color', 'noshade', 'size', 'width']),
    BlockElement(
          name='html',
          attributes=['manifest'],
          obsolete_attributes=['version']),
    Element(name='i'),
    BlockElement(
        name='iframe',
        attributes=['src', 'srcdoc', 'name', 'sandbox', 'width', 'height'],
        obsolete_attributes=['datasrc', 'datafld', 'align', 'allowtransparency',
                            'frameborder', 'hspace', 'marginheight',
                            'marginwidth', 'scrolling', 'vspace']),
    EmptyElement(
        name='img',
        attributes=['src', 'alt', 'crossorigin', 'usemap', 'ismap', 'width',
                    'height'],
        obsolete_attributes=['name', 'lowsrc', 'datasrc', 'datafld', 'align',
                             'border', 'hspace', 'vspace']),
    InputElement(
        name='input',
        attributes=[
        'accept', 'alt', 'autocomplete', 'autofocus', 'checked', 'dirname',
        'disabled', 'form', 'formaction', 'formenctype', 'formmethod',
        'formnovalidate', 'formtarget',
        'height', 'list', 'max', 'maxlength', 'min', 'minlength', 'multiple',
        'name', 'pattern', 'placeholder', 'readonly', 'required', 'size',
        'src', 'step', 'type', 'value', 'width'],
        obsolete_attributes=['ismap', 'usemap', 'datasrc', 'datafld',
          'dataformatas', 'align', 'hspace', 'vspace']),
    Element(name='ins', attributes=['cite', 'datetime']),
    Element(name='kbd'),
    Element(name='keygen', attributes=['autofocus', 'challenge', 'disabled',
                                       'form', 'keytype', 'name']),
    Element(
        name='label',
        attributes=['form', 'for'],
        obsolete_attributes=['datasrc', 'datafld', 'dataformatas']),
    BlockElement(
        name='legend',
        obsolete_attributes=['datasrc', 'datafld', 'dataformatas', 'align']),
    BlockElement(
        name='li',
        attributes=['value'],
        obsolete_attributes=['type']),
    EmptyElement(
        name='link',
        attributes=['href', 'crossorigin', 'rel', 'media', 'hreflang', 'type',
                    'sizes'],
        obsolete_attributes=['charset', 'methods', 'urn', 'target']),
    BlockElement(name='main'),
    BlockElement(name='map', attributes=['name']),
    EmptyElement(name='mark'),
    EmptyElement(
          name='meta',
          attributes=['http-equiv', 'name', 'content', 'scheme'],
          obsolete_attributes=['scheme']),
    BlockElement(
          name='meter',
          attributes=['value', 'min', 'max', 'low', 'high', 'optimum']),
    BlockElement(name='nav'),
    BlockElement(name='noscript'),
    BlockElement(
        name='object',
        attributes=['data', 'type', 'typemustmatch', 'name',
                    'usemap', 'form', 'width', 'height'],
        obsolete_attributes=['archive', 'classid', 'code', 'codebase',
                        'codetype', 'declare', 'standby', 'datasrc', 'datafld',
                        'dataformatas', 'align', 'border', 'hspace', 'vspace']),
    BlockElement(
        name='ol',
        attributes=['reversed', 'start', 'type'],
        obsolete_attributes=['compact']),
    BlockElement(name='optgroup', attributes=['disabled', 'label']),
    BlockElement(
        name='option',
        attributes=['selected', 'disabled', 'label', 'value'],
        obsolete_attributes=['name', 'datasrc', 'datafld', 'dataformatas']),
    BlockElement(name='output', attributes=['for', 'form', 'name']),
    BlockElement(
          name='p',
          context='paragraph',
          obsolete_attributes=['align']),
    EmptyElement(
        name='param',
        attributes=['name', 'value'],
        obsolete_attributes=['type', 'valuetype']),
    BlockElement(
        name='pre',
        keep_spaces=True,
        obsolete_attributes=['width']),
    BlockElement(name='progress', attributes=['value', 'max']),
    Element(name='q', attributes=['cite']),
    Element(name='rb'),
    Element(name='rp'),
    Element(name='rt'),
    Element(name='rtc'),
    Element(name='ruby'),
    Element(name='s'),
    Element(name='samp'),
    BlockElement(
        name='script',
        attributes=['src', 'charset', 'type', 'async', 'defer', 'crossorigin'],
        obsolete_attributes=['language', 'event', 'for'],
        skip_content=True),
    Element(name='section'),
    BlockElement(
        name='select',
        attributes=['autofocus', 'disabled', 'form', 'multiple', 'name',
                    'required', 'size'],
        obsolete_attributes=['datasrc', 'datafld', 'dataformatas']),
    Element(name='small'),
    EmptyBlockElement(name='source', attributes=['src', 'type', 'media']),
    Element(
        name='span',
        obsolete_attributes=['datasrc', 'datafld', 'dataformatas']),
    Element(name='strong', context="emphasis"),
    BlockElement(name='style', attributes=['media', 'type'], skip_content=True),
    Element(name='sub'),
    Element(name='sup'),
    BlockElement(
        name='table',
        attributes=['border'],
        obsolete_attributes=['datapagesize', 'summary', 'datasrc', 'datafld',
                        'dataformatas', 'align', 'bgcolor', 'bordercolor',
                        'cellpadding', 'cellspacing', 'frame', 'rules',
                        'width', 'background']),
    BlockElement(
        name='tbody',
        obsolete_attributes=['align', 'char', 'charoff',
                             'valign', 'background']),
    BlockElement(
        name='td',
        attributes=['colspan', 'rowspan', 'headers'],
        obsolete_attributes=['axis', 'scope', 'align', 'bgcolor', 'char',
                             'charoff', 'height', 'nowrap',
                             'valign', 'width', 'background'],
        context='table cell'),
    BlockElement(name='template'),
    Element(
          name='textarea',
          attributes=['autofocus', 'cols', 'dirname', 'disabled', 'form',
                      'maxlength', 'minlength', 'name',
                      'placeholder', 'readonly', 'required', 'rows', 'wrap',],
          obsolete_attributes=['datasrc', 'datafld']),
    BlockElement(
        name='tfoot',
        obsolete_attributes=['align', 'char', 'charoff', 'valign', 'background']),
    BlockElement(
          name='th',
          attributes=['colspan', 'rowspan', 'headers', 'scope', 'abbr'],
          obsolete_attributes=['axis', 'align', 'bgcolor', 'char', 'charoff',
                               'height', 'nowrap', 'valign', 'width',
                               'background'],
          context='table cell'),
    BlockElement(
        name='thead',
        obsolete_attributes=['align', 'char', 'charoff', 'valign', 'background']),
    BlockElement(name='time', attributs=['datetime']),
    BlockElement(name='title'),
    BlockElement(
          name='tr',
          obsolete_attributes=['align', 'bgcolor', 'char', 'charoff', 'valign', 'background']),
    BlockElement(
          name='track',
          attributes=['default', 'kind', 'label', 'src', 'srclang']),
    BlockElement(name='u'),
    BlockElement(
        name='ul',
        obsolete_attributes=['compact', 'type']
        ),
    Element(name='var'),
    BlockElement(
        name='video',
        attributes=['src', 'crossorigin', 'poster',
                    'preload', 'autoplay', 'mediagroup', 'loop', 'muted',
                    'controls', 'width', 'height']),
    BlockElement(name='wbr'),
    ]


class HTML5Namespace(XMLNamespace):

    uri = html_uri
    prefix = None
    elements = html_elements
    obsolete_elements = obsolete_html_elements
    attributes = html_attributes
    strict = True

    @proto_lazy_property
    def obsolete_elements_kw(self):
        kw = {}
        for element in self.obsolete_elements:
            name = element.name
            if name in self.elements:
                raise ValueError('element "%s" is defined twice' % name)
            kw[name] = element
        return kw

    def get_element_schema(self, name):
        element = self.elements_kw.get(name)
        if element is not None:
            context = element.context or name
            return element(strict=self.strict, context=context)
        # Obsolete elements
        obsolete_element = self.obsolete_elements_kw.get(name)
        if obsolete_element is not None:
            if self.strict:
                message = 'unexpected element "{}"'
                raise XMLError(message.format(name))
            msg = 'WARNING HTML5: {} is an obsolete element'
            print(msg.format(name))
            context = obsolete_element.context or name
            return obsolete_element(strict=self.strict, context=context)
        # Custom elements are authorized if contains "-"
        # https://www.w3.org/TR/html5/infrastructure.html#extensibility-0
        # <itools-users></itools-users>
        if '-' in name:
            return WebComponentElement(
                  name=name, strict=self.strict, context=name)
        raise XMLError('unexpected element "%s"' % name)


html_namespace = HTML5Namespace(strict=False)
###########################################################################
# Register
###########################################################################
register_namespace(html_namespace)
