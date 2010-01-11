# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
# Copyright (C) 2009 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2009 Henry Obein <henry@itaapy.com>
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
from re import finditer

# Import from itools
from itools.xml import XMLParser, START_ELEMENT, END_ELEMENT, COMMENT


###########################################################################
# Sanitize
###########################################################################
safe_tags = frozenset([
    'a', 'abbr', 'acronym', 'address', 'area', 'b', 'big', 'blockquote', 'br',
    'button', 'caption', 'center', 'cite', 'code', 'col', 'colgroup', 'dd',
    'del', 'dfn', 'dir', 'div', 'dl', 'dt', 'em', 'fieldset', 'font', 'form',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img', 'input', 'ins',
    'kbd', 'label', 'legend', 'li', 'map', 'menu', 'ol', 'optgroup', 'option',
    'p', 'pre', 'q', 's', 'samp', 'select', 'small', 'span', 'strike',
    'strong', 'sub', 'sup', 'table', 'tbody', 'td', 'textarea', 'tfoot', 'th',
    'thead', 'tr', 'tt', 'u', 'ul', 'var',
    # flash
    'embed', 'object', 'param',
    # iframe
    'iframe'])

safe_attrs = frozenset([
    'abbr', 'accept', 'accept-charset', 'accesskey', 'action', 'align', 'alt',
    'axis', 'border', 'cellpadding', 'cellspacing', 'char', 'charoff',
    'charset', 'checked', 'cite', 'class', 'clear', 'cols', 'colspan',
    'color', 'compact', 'coords', 'datetime', 'dir', 'disabled', 'enctype',
    'for', 'frame', 'headers', 'height', 'href', 'hreflang', 'hspace', 'id',
    'ismap', 'label', 'lang', 'longdesc', 'maxlength', 'media', 'method',
    'multiple', 'name', 'nohref', 'noshade', 'nowrap', 'prompt', 'readonly',
    'rel', 'rev', 'rows', 'rowspan', 'rules', 'scope', 'selected', 'shape',
    'size', 'span', 'src', 'start', 'style', 'summary', 'tabindex', 'target',
    'title', 'type', 'usemap', 'valign', 'value', 'vspace', 'width',
    # flash,
    'data',
    # iframe
    'frameborder', 'marginheight', 'marginwidth', 'scrolling'])


uri_attrs = frozenset([
    'action', 'background', 'data', 'dynsrc', 'href', 'lowsrc', 'src'])

safe_schemes = frozenset([
    'file', 'ftp', 'http', 'https', 'irc', 'mailto', None])


def sanitize_stream(stream):
    """Method that removes potentially dangerous HTML tags and attributes
    from the events
    """

    skip = 0

    for event in stream:
        type, value, line = event
        if type == START_ELEMENT:
            # Check we are not within a dangerous element
            if skip > 0:
                skip += 1
                continue
            # Check it is a safe tag
            tag_uri, tag_name, attributes = value
#            if tag_uri != xhtml_uri or tag_name not in safe_tags:
            if tag_name not in safe_tags:
                skip = 1
                continue
            # Check unsafe object
            if tag_name == 'object':
                attr_value = attributes.get((None, 'type'))
                if attr_value != 'application/x-shockwave-flash':
                    skip = 1
                    continue
            # Filter attributes
            attributes = attributes.copy()
            for attr_key in attributes.keys():
                attr_value = attributes[attr_key]
                attr_uri, attr_name = attr_key
                # Check it is a safe attribute
                if attr_name not in safe_attrs:
                    del attributes[attr_key]
                # Check it is a safe URI scheme
                elif attr_name in uri_attrs and ':' in attr_value:
                    scheme = attr_value.split(':')[0]
                    if scheme not in safe_schemes:
                        del attributes[attr_key]
                # Check CSS
                elif attr_name == 'style':
                    # TODO Clean attribute value instead
                    for m in finditer(r'url\s*\(([^)]+)', attr_value):
                        href = m.group(1)
                        if ':' in href:
                            scheme = href.split(':')[0]
                            if scheme not in safe_schemes:
                                del attributes[attr_key]
                                break
            # Ok
            yield type, (tag_uri, tag_name, attributes), line
        elif type == END_ELEMENT:
            if skip > 0:
                skip -= 1
                continue
            yield event
        elif type == COMMENT:
            # Skip comments
            continue
        else:
            if skip == 0:
                yield event



def sanitize_str(str):
    stream = XMLParser(str)
    return sanitize_stream(stream)



