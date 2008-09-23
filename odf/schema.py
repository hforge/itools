# -*- coding: UTF-8 -*-
# Copyright (C) 2008 David Versmisse <david.versmisse@itaapy.com>
# Copyright (C) 2008 Romain Gauthier <romain.gauthier@itaapy.com>
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
from itools import get_abspath
from itools.relaxng import RelaxNGFile
from itools.xml import register_namespace
from itools.xml.namespaces import has_namespace


###########################################################################
# Metadata
###########################################################################
config_uri = 'urn:oasis:names:tc:opendocument:xmlns:config:1.0'
dc_uri = 'http://purl.org/dc/elements/1.1/'
form_uri = 'urn:oasis:names:tc:opendocument:xmlns:form:1.0'
meta_uri = 'urn:oasis:names:tc:opendocument:xmlns:meta:1.0'
number_uri = 'urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0'
office_uri = 'urn:oasis:names:tc:opendocument:xmlns:office:1.0'
presentation_uri = 'urn:oasis:names:tc:opendocument:xmlns:presentation:1.0'
text_uri = 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'
svg_uri = 'urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0'

inline_elements = [
    (text_uri, 'page-count'),
    (text_uri, 'page-number'),

    (text_uri, 'a'),
    (text_uri, 'line-break'),
    (text_uri, 'ruby-base'),
    (text_uri, 's'),
    (text_uri, 'span'),
    (text_uri, 'tab')]

no_translate_content_elements = [

    # Config
    (config_uri, 'config-item'),

    # Dublin core
    (dc_uri, 'creator'),
    (dc_uri, 'date'),
    #(dc_uri, 'description'),
    (dc_uri, 'language'),
    #(dc_uri, 'subject'),
    #(dc_uri, 'title'),

    # Form
    (form_uri, 'item'),
    (form_uri, 'option'),

    # Meta
    (meta_uri, 'creation-date'),
    (meta_uri, 'date-string'),
    (meta_uri, 'editing-cycles'),
    (meta_uri, 'editing-duration'),
    (meta_uri, 'generator'),
    (meta_uri, 'initial-creator'),
    #(meta_uri, 'keyword'),
    (meta_uri, 'printed-by'),
    (meta_uri, 'print-date'),
    (meta_uri, 'user-defined'),

    # Number
    (number_uri, 'currency-symbol'),
    (number_uri, 'embedded-text'),
    (number_uri, 'text'),

    # Office
    (office_uri, 'binary-data'),

    # Presentation
    (presentation_uri, 'date-time-decl'),
    #(presentation_uri, 'footer-decl'),
    #(presentation_uri, 'header-decl'),

    # Text
    (text_uri, 'author-initials'),
    (text_uri, 'author-name'),
    # XXX (text_uri, 'bibliography-mark'),
    (text_uri, 'bookmark-ref'),
    #(text_uri, 'chapter'),
    (text_uri, 'character-count'),
    #(text_uri, 'conditional-text'),
    (text_uri, 'creation-date'),
    (text_uri, 'creation-time'),
    (text_uri, 'creator'),
    (text_uri, 'date'),
    (text_uri, 'dde-connection'),
    #(text_uri, 'description'),
    (text_uri, 'editing-cycles'),
    (text_uri, 'editing-duration'),
    (text_uri, 'expression'),
    (text_uri, 'file-name'),
    #(text_uri, 'hidden-paragraph'),
    #(text_uri, 'hidden-text'),
    (text_uri, 'image-count'),
    #(text_uri, 'index-entry-span'),
    (text_uri, 'index-title-template'),
    (text_uri, 'initial-creator'),
    #(text_uri, 'keywords'),
    (text_uri, 'linenumbering-separator'),
    (text_uri, 'measure'),
    (text_uri, 'modification-date'),
    (text_uri, 'modification-time'),
    #(text_uri, 'note-citation'),
    #(text_uri, 'note-continuation-notice-backward'),
    #(text_uri, 'note-continuation-notice-forward'),
    (text_uri, 'note-ref'),
    (text_uri, 'number'),
    (text_uri, 'object-count'),
    (text_uri, 'page-continuation'),
    (text_uri, 'page-count'),
    (text_uri, 'page-number'),
    (text_uri, 'page-variable-get'),
    (text_uri, 'page-variable-set'),
    (text_uri, 'paragraph-count'),
    #(text_uri, 'placeholder'),
    (text_uri, 'print-date'),
    (text_uri, 'print-time'),
    (text_uri, 'printed-by'),
    (text_uri, 'reference-ref'),
    #(text_uri, 'ruby-text'),
    (text_uri, 'script'),
    (text_uri, 'sender-city'),
    (text_uri, 'sender-company'),
    (text_uri, 'sender-country'),
    (text_uri, 'sender-email'),
    (text_uri, 'sender-fax'),
    (text_uri, 'sender-firstname'),
    (text_uri, 'sender-initials'),
    (text_uri, 'sender-lastname'),
    (text_uri, 'sender-phone-private'),
    (text_uri, 'sender-phone-work'),
    #(text_uri, 'sender-position'),
    (text_uri, 'sender-postal-code'),
    (text_uri, 'sender-state-or-province'),
    (text_uri, 'sender-street'),
    #(text_uri, 'sender-title'),
    (text_uri, 'sequence'),
    (text_uri, 'sequence-ref'),
    (text_uri, 'sheet-name'),
    #(text_uri, 'subject'),
    (text_uri, 'table-count'),
    (text_uri, 'table-formula'),
    (text_uri, 'template-name'),
    (text_uri, 'text-input'),
    (text_uri, 'time'),
    #(text_uri, 'title'),
    (text_uri, 'user-defined'),
    (text_uri, 'user-field-get'),
    (text_uri, 'user-field-input'),
    (text_uri, 'variable-get'),
    (text_uri, 'variable-input'),
    (text_uri, 'variable-set'),
    (text_uri, 'word-count'),

    # SVG
    #(svg_uri, 'title'),
    #(svg_uri, 'desc')
    ]


###########################################################################
# Make the namespaces
###########################################################################

# Read the Relax NG schema
rng_file = RelaxNGFile(get_abspath('OpenDocument-strict-schema-v1.1.rng'))
namespaces = rng_file.get_namespaces()

# Apply the metadata
for uri, element_name in inline_elements:
    element = namespaces[uri].get_element_schema(element_name)
    element.is_inline = True
for uri, element_name in no_translate_content_elements:
    element = namespaces[uri].get_element_schema(element_name)
    element.translate_content = False

# Register the namespaces
for uri, namespace in namespaces.iteritems():
    if not has_namespace(uri):
        register_namespace(namespace)


