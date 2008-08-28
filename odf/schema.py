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
from itools.datatypes import Unicode
from itools.xml import XMLError, XMLNamespace, register_namespace
from itools.xml import ElementSchema


###########################################################################
# Namespace URIs
###########################################################################
text_uri = 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'
office_uri = 'urn:oasis:names:tc:opendocument:xmlns:office:1.0'
style_uri = 'urn:oasis:names:tc:opendocument:xmlns:style:1.0'
table_uri = 'urn:oasis:names:tc:opendocument:xmlns:table:1.0'
draw_uri = 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0'
fo_uri = 'urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0'
meta_uri = 'urn:oasis:names:tc:opendocument:xmlns:meta:1.0'
svg_uri = 'urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0'
dr3d_uri = 'urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0'
form_uri = 'urn:oasis:names:tc:opendocument:xmlns:form:1.0'
script_uri = 'urn:oasis:names:tc:opendocument:xmlns:script:1.0'
ooo_uri = 'http://openoffice.org/2004/office'
ooow_uri = 'http://openoffice.org/2004/writer'
oooc_uri = 'http://openoffice.org/2004/calc'
number_uri = 'urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0'
anim_uri = 'urn:oasis:names:tc:opendocument:xmlns:animation:1.0'
chart_uri = 'urn:oasis:names:tc:opendocument:xmlns:chart:1.0'
config_uri = 'urn:oasis:names:tc:opendocument:xmlns:config:1.0'
manifest_uri = 'urn:oasis:names:tc:opendocument:xmlns:manifest:1.0'
presentation_uri = 'urn:oasis:names:tc:opendocument:xmlns:presentation:1.0'
smil_uri = 'urn:oasis:names:tc:opendocument:xmlns:smil-compatible:1.0'

###########################################################################
# Attributes
###########################################################################
odf_attributes = {'style-name': Unicode,
                  'version': Unicode,
                  'name': Unicode
                  }
common_attrs = []



class Element(ElementSchema):

    # Default
    is_empty = False
    is_inline = True


    def __init__(self, uri, name, attributes, **kw):
        ElementSchema.__init__(self, name, **kw)
        self.class_uri = uri
        self.attributes = frozenset(attributes)


    def get_attr_datatype(self, name, attributes):
        if name not in self.attributes:
            message = 'unexpected "%s" attribute for "%s" element'
            raise XMLError, message % (name, self.name)
        return odf_attributes[name]



class BlockElement(Element):

    is_inline = False



class EmptyElement(Element):

    is_empty = True



class EmptyBlockElement(Element):

    is_inline = False
    is_empty = True



odf_text_elements = [
    BlockElement(text_uri, 'a', common_attrs + []),
    BlockElement(text_uri, 'alphabetical-index', common_attrs + []),
    BlockElement(text_uri, 'alphabetical-index-auto-mark-file',
                 common_attrs + []),
    BlockElement(text_uri, 'alphabetical-index-entry-template',
                 common_attrs + []),
    BlockElement(text_uri, 'alphabetical-index-mark', common_attrs + []),
    BlockElement(text_uri, 'alphabetical-index-mark-end', common_attrs + []),
    BlockElement(text_uri, 'alphabetical-index-mark-start',
                 common_attrs + []),
    BlockElement(text_uri, 'alphabetical-index-source', common_attrs + []),
    #'anchor-page-number'
    #'anchor-type'
    #'animation'
    #'animation-delay'
    #'animation-direction'
    #'animation-repeat'
    #'animation-start-inside'
    #'animation-steps'
    #'animation-stop-inside'
    BlockElement(text_uri, 'author-initials', common_attrs + []),
    BlockElement(text_uri, 'author-name', common_attrs + []),
    BlockElement(text_uri, 'bibliography', common_attrs + []),
    BlockElement(text_uri, 'bibliography-configuration', common_attrs + []),
    BlockElement(text_uri, 'bibliography-entry-template', common_attrs + []),
    BlockElement(text_uri, 'bibliography-mark', common_attrs + []),
    BlockElement(text_uri, 'bibliography-source', common_attrs + []),
    BlockElement(text_uri, 'bookmark', common_attrs + []),
    BlockElement(text_uri, 'bookmark-end', common_attrs + []),
    BlockElement(text_uri, 'bookmark-ref', common_attrs + []),
    BlockElement(text_uri, 'bookmark-start', common_attrs + []),
    #'bullet-char'
    BlockElement(text_uri, 'change', common_attrs + []),
    BlockElement(text_uri, 'change-end', common_attrs + []),
    BlockElement(text_uri, 'change-start', common_attrs + []),
    BlockElement(text_uri, 'changed-region', common_attrs + []),
    BlockElement(text_uri, 'chapter', common_attrs + []),
    #'character-count' (FIXME Check whether creation-date is empty
    # or not)
    BlockElement(text_uri, 'conditional-text', common_attrs + []),
    BlockElement(text_uri, 'creation-date', common_attrs + []),
    BlockElement(text_uri, 'creation-time', common_attrs + [],
                 translate_content = False),
    BlockElement(text_uri, 'creator', common_attrs + []),
    BlockElement(text_uri, 'database-display', common_attrs + []),
    BlockElement(text_uri, 'database-name', common_attrs + []),
    BlockElement(text_uri, 'database-next', common_attrs + []),
    BlockElement(text_uri, 'database-row-number', common_attrs + []),
    BlockElement(text_uri, 'database-row-select', common_attrs + []),
    BlockElement(text_uri, 'date', common_attrs + [],
                 translate_content = False),
    #'date-value'
    BlockElement(text_uri, 'dde-connection', common_attrs + []),
    BlockElement(text_uri, 'dde-connection-decl', common_attrs + []),
    BlockElement(text_uri, 'dde-connection-decls', common_attrs + []),
    BlockElement(text_uri, 'deletion', common_attrs + []),
    BlockElement(text_uri, 'description', common_attrs + []),
    #'dont-balance-text-columns'
    BlockElement(text_uri, 'editing-cycles', common_attrs + []),
    BlockElement(text_uri, 'editing-duration', common_attrs + []),
    BlockElement(text_uri, 'execute-macro', common_attrs + []),
    BlockElement(text_uri, 'expression', common_attrs + []),
    BlockElement(text_uri, 'file-name', common_attrs + []),
    BlockElement(text_uri, 'format-change', common_attrs + []),
    BlockElement(text_uri, 'h', common_attrs + []),
    BlockElement(text_uri, 'hidden-paragraph', common_attrs + []),
    BlockElement(text_uri, 'hidden-text', common_attrs + []),
    BlockElement(text_uri, 'illustration-index', common_attrs + []),
    BlockElement(text_uri, 'illustration-index-entry-template',
                 common_attrs + []),
    BlockElement(text_uri, 'illustration-index-source', common_attrs + []),
    #'image-count'
    BlockElement(text_uri, 'index-body', common_attrs + []),
    BlockElement(text_uri, 'index-entry-bibliography', common_attrs + []),
    BlockElement(text_uri, 'index-entry-chapter', common_attrs + []),
    BlockElement(text_uri, 'index-entry-link-end', common_attrs + []),
    BlockElement(text_uri, 'index-entry-link-start', common_attrs + []),
    BlockElement(text_uri, 'index-entry-page-number', common_attrs + []),
    BlockElement(text_uri, 'index-entry-span', common_attrs + []),
    BlockElement(text_uri, 'index-entry-tab-stop', common_attrs + []),
    BlockElement(text_uri, 'index-entry-text', common_attrs + []),
    BlockElement(text_uri, 'index-source-style', common_attrs + []),
    BlockElement(text_uri, 'index-source-styles', common_attrs + []),
    BlockElement(text_uri, 'index-title', common_attrs + []),
    BlockElement(text_uri, 'index-title-template', common_attrs + []),
    BlockElement(text_uri, 'initial-creator', common_attrs + []),
    BlockElement(text_uri, 'insertion', common_attrs + []),
    BlockElement(text_uri, 'keywords', common_attrs + []),
    #'level'
    EmptyElement(text_uri, 'line-break', common_attrs + []),
    BlockElement(text_uri, 'linenumbering-configuration', common_attrs + []),
    BlockElement(text_uri, 'linenumbering-separator', common_attrs + []),
    BlockElement(text_uri, 'list', common_attrs + []),
    BlockElement(text_uri, 'list-header', common_attrs + []),
    BlockElement(text_uri, 'list-item', common_attrs + []),
    BlockElement(text_uri, 'list-level-style-bullet', common_attrs + []),
    BlockElement(text_uri, 'list-level-style-image', common_attrs + []),
    BlockElement(text_uri, 'list-level-style-number', common_attrs + []),
    BlockElement(text_uri, 'list-style', common_attrs + []),
    BlockElement(text_uri, 'measure', common_attrs + []),
    #min-label-width
    BlockElement(text_uri, 'modification-date', common_attrs + []),
    BlockElement(text_uri, 'modification-time', common_attrs + []),
    BlockElement(text_uri, 'note', common_attrs + []),
    BlockElement(text_uri, 'note-body', common_attrs + []),
    BlockElement(text_uri, 'note-citation', common_attrs + []),
    BlockElement(text_uri, 'note-continuation-notice-backward',
                 common_attrs + []),
    BlockElement(text_uri, 'note-continuation-notice-forward',
                 common_attrs + []),
    BlockElement(text_uri, 'note-ref', common_attrs + []),
    BlockElement(text_uri, 'notes-configuration', common_attrs + []),
    BlockElement(text_uri, 'number', common_attrs + []),
    BlockElement(text_uri, 'numbered-paragraph', common_attrs + []),
    BlockElement(text_uri, 'object-count', common_attrs + []),
    BlockElement(text_uri, 'object-index', common_attrs + []),
    BlockElement(text_uri, 'object-index-entry-template', common_attrs + []),
    BlockElement(text_uri, 'object-index-source', common_attrs + []),
    BlockElement(text_uri, 'outline-level-style', common_attrs + []),
    BlockElement(text_uri, 'outline-style', common_attrs + []),
    BlockElement(text_uri, 'p', common_attrs + []),
    BlockElement(text_uri, 'page', common_attrs + []),
    BlockElement(text_uri, 'page-continuation', common_attrs + []),
    Element(text_uri, 'page-count', common_attrs + [],
            translate_content = False),
    Element(text_uri, 'page-number', common_attrs + [],
            translate_content = False),
    BlockElement(text_uri, 'page-sequence', common_attrs + []),
    BlockElement(text_uri, 'page-variable-get', common_attrs + []),
    BlockElement(text_uri, 'page-variable-set', common_attrs + []),
    #'paragraph-count'
    BlockElement(text_uri, 'placeholder', common_attrs + []),
    BlockElement(text_uri, 'print-date', common_attrs + []),
    BlockElement(text_uri, 'print-time', common_attrs + []),
    BlockElement(text_uri, 'printed-by', common_attrs + []),
    BlockElement(text_uri, 'reference-mark', common_attrs + []),
    BlockElement(text_uri, 'reference-mark-end', common_attrs + []),
    BlockElement(text_uri, 'reference-mark-start', common_attrs + []),
    BlockElement(text_uri, 'reference-ref', common_attrs + []),
    BlockElement(text_uri, 'ruby', common_attrs + []),
    BlockElement(text_uri, 'ruby-base', common_attrs + []),
    #'ruby-text':
    EmptyElement(text_uri, 's', common_attrs + []),
    BlockElement(text_uri, 'script', common_attrs + []),
    BlockElement(text_uri, 'section', common_attrs + []),
    BlockElement(text_uri, 'section-source', common_attrs + []),
    BlockElement(text_uri, 'sender-city', common_attrs + []),
    BlockElement(text_uri, 'sender-company', common_attrs + []),
    BlockElement(text_uri, 'sender-country', common_attrs + []),
    BlockElement(text_uri, 'sender-email', common_attrs + []),
    BlockElement(text_uri, 'sender-fax', common_attrs + []),
    BlockElement(text_uri, 'sender-firstname', common_attrs + []),
    BlockElement(text_uri, 'sender-initials', common_attrs + []),
    BlockElement(text_uri, 'sender-lastname', common_attrs + []),
    BlockElement(text_uri, 'sender-phone-private', common_attrs + []),
    BlockElement(text_uri, 'sender-phone-work', common_attrs + []),
    BlockElement(text_uri, 'sender-position', common_attrs + []),
    BlockElement(text_uri, 'sender-postal-code', common_attrs + []),
    BlockElement(text_uri, 'sender-state-or-province', common_attrs + []),
    BlockElement(text_uri, 'sender-street', common_attrs + []),
    BlockElement(text_uri, 'sender-title', common_attrs + []),
    BlockElement(text_uri, 'sequence', common_attrs + [],
                 translate_content = False),
    BlockElement(text_uri, 'sequence-decl', common_attrs + []),
    BlockElement(text_uri, 'sequence-decls', common_attrs + []),
    BlockElement(text_uri, 'sequence-ref', common_attrs + []),
    BlockElement(text_uri, 'sheet-name', common_attrs + []),
    BlockElement(text_uri, 'sort-key', common_attrs + []),
    #'space-before'
    Element(text_uri, 'span', common_attrs + []),
    #'style-name'
    BlockElement(text_uri, 'subject', common_attrs + []),
    EmptyElement(text_uri, 'tab', common_attrs + []),
    #'table-count'
    BlockElement(text_uri, 'table-formula', common_attrs + []),
    BlockElement(text_uri, 'table-index', common_attrs + []),
    BlockElement(text_uri, 'table-index-entry-template', common_attrs + []),
    BlockElement(text_uri, 'table-index-source', common_attrs + []),
    BlockElement(text_uri, 'table-of-content', common_attrs + []),
    BlockElement(text_uri, 'table-of-content-entry-template',
                 common_attrs + []),
    BlockElement(text_uri, 'table-of-content-source', common_attrs + []),
    BlockElement(text_uri, 'template-name', common_attrs + []),
    BlockElement(text_uri, 'text-input', common_attrs + []),
    BlockElement(text_uri, 'time', common_attrs + [],
                 translate_content = False),
    #'time-value'
    BlockElement(text_uri, 'title', common_attrs + []),
    BlockElement(text_uri, 'toc-mark', common_attrs + []),
    BlockElement(text_uri, 'toc-mark-end', common_attrs + []),
    BlockElement(text_uri, 'toc-mark-start', common_attrs + []),
    BlockElement(text_uri, 'tracked-changes', common_attrs + []),
    BlockElement(text_uri, 'user-defined', common_attrs + []),
    BlockElement(text_uri, 'user-field-decl', common_attrs + []),
    BlockElement(text_uri, 'user-field-decls', common_attrs + []),
    BlockElement(text_uri, 'user-field-get', common_attrs + []),
    BlockElement(text_uri, 'user-field-input', common_attrs + []),
    BlockElement(text_uri, 'user-index', common_attrs + []),
    BlockElement(text_uri, 'user-index-entry-template', common_attrs + []),
    BlockElement(text_uri, 'user-index-mark', common_attrs + []),
    BlockElement(text_uri, 'user-index-mark-end', common_attrs + []),
    BlockElement(text_uri, 'user-index-mark-start', common_attrs + []),
    BlockElement(text_uri, 'user-index-source', common_attrs + []),
    BlockElement(text_uri, 'variable-decl', common_attrs + []),
    BlockElement(text_uri, 'variable-decls', common_attrs + []),
    BlockElement(text_uri, 'variable-get', common_attrs + []),
    BlockElement(text_uri, 'variable-input', common_attrs + []),
    BlockElement(text_uri, 'variable-set', common_attrs + [])
    #'word-count'
    ]
odf_office_elements = [
    BlockElement(office_uri, 'annotation', common_attrs + []),
    BlockElement(office_uri, 'automatic-styles', common_attrs + []),
    BlockElement(office_uri, 'binary-data', common_attrs + []),
    BlockElement(office_uri, 'body', common_attrs + []),
    BlockElement(office_uri, 'change-info', common_attrs + []),
    BlockElement(office_uri, 'chart', common_attrs + []),
    BlockElement(office_uri, 'dde-source', common_attrs + []),
    BlockElement(office_uri, 'document', common_attrs + []),
    BlockElement(office_uri, 'document-content', common_attrs + []),
    BlockElement(office_uri, 'document-meta', common_attrs + []),
    BlockElement(office_uri, 'document-settings', common_attrs + []),
    BlockElement(office_uri, 'document-styles', common_attrs + []),
    BlockElement(office_uri, 'drawing', common_attrs + []),
    BlockElement(office_uri, 'event-listeners', common_attrs + []),
    BlockElement(office_uri, 'font-face-decls', common_attrs + []),
    BlockElement(office_uri, 'forms', common_attrs + []),
    BlockElement(office_uri, 'image', common_attrs + []),
    BlockElement(office_uri, 'master-styles', common_attrs + []),
    BlockElement(office_uri, 'meta', common_attrs + []),
    BlockElement(office_uri, 'presentation', common_attrs + []),
    BlockElement(office_uri, 'script', common_attrs + []),
    BlockElement(office_uri, 'scripts', common_attrs + []),
    BlockElement(office_uri, 'settings', common_attrs + []),
    BlockElement(office_uri, 'spreadsheet', common_attrs + []),
    BlockElement(office_uri, 'styles', common_attrs + []),
    BlockElement(office_uri, 'text', common_attrs + [])]
odf_style_elements = [
    BlockElement(style_uri, 'background-image', common_attrs + []),
    #'border-line-width
    BlockElement(style_uri, 'chart-properties', common_attrs + []),
    BlockElement(style_uri, 'column', common_attrs + []),
    BlockElement(style_uri, 'column-sep', common_attrs + []),
    #'column-width
    BlockElement(style_uri, 'columns', common_attrs + []),
    BlockElement(style_uri, 'default-style', common_attrs + []),
    #'display-name
    BlockElement(style_uri, 'drawing-page-properties', common_attrs + []),
    BlockElement(style_uri, 'drop-cap', common_attrs + []),
    #'family
    #'family-properties
    #'first-page-number
    #'font-decl
    BlockElement(style_uri, 'font-face', common_attrs + []),
    #'font-name
    #'font-relief
    BlockElement(style_uri, 'footer', common_attrs + []),
    BlockElement(style_uri, 'footer-left', common_attrs + []),
    BlockElement(style_uri, 'footer-style', common_attrs + []),
    #'footnote-max-height
    BlockElement(style_uri, 'footnote-sep', common_attrs + []),
    BlockElement(style_uri, 'graphic-properties', common_attrs + []),
    BlockElement(style_uri, 'handout-master', common_attrs + []),
    BlockElement(style_uri, 'header', common_attrs + []),
    BlockElement(style_uri, 'header-footer-properties', common_attrs + []),
    BlockElement(style_uri, 'header-left', common_attrs + []),
    BlockElement(style_uri, 'header-style', common_attrs + []),
    #'horizontal-pos
    #'horizontal-rel
    #'leader-text
    #'line-spacing
    BlockElement(style_uri, 'list-level-properties', common_attrs + []),
    BlockElement(style_uri, 'map', common_attrs + []),
    BlockElement(style_uri, 'master-page', common_attrs + []),
    #'may-break-between-rows
    #'min-row-height
    #'mirror
    #'name
    #'num-format
    #'number-wrapped-paragraphs
    BlockElement(style_uri, 'page-layout', common_attrs + []),
    BlockElement(style_uri, 'page-layout-properties', common_attrs + []),
    BlockElement(style_uri, 'paragraph-properties', common_attrs + []),
    #'position
    BlockElement(style_uri, 'presentation-page-layout', common_attrs + []),
    #'print
    #'print-orientation
    #'print-page-order
    BlockElement(style_uri, 'region-center', common_attrs + []),
    BlockElement(style_uri, 'region-left', common_attrs + []),
    BlockElement(style_uri, 'region-right', common_attrs + []),
    #'rel-column-width
    #'rel-width
    #'repeat
    #'row-height
    BlockElement(style_uri, 'ruby-properties', common_attrs + []),
    #'scale-to
    BlockElement(style_uri, 'section-properties', common_attrs + []),
    BlockElement(style_uri, 'style', common_attrs + []),
    BlockElement(style_uri, 'tab-stop', common_attrs + []),
    BlockElement(style_uri, 'tab-stops', common_attrs + []),
    BlockElement(style_uri, 'table', common_attrs + []),
    BlockElement(style_uri, 'table-cell', common_attrs + []),
    BlockElement(style_uri, 'table-cell-properties', common_attrs + []),
    BlockElement(style_uri, 'table-column', common_attrs + []),
    BlockElement(style_uri, 'table-column-properties', common_attrs + []),
    BlockElement(style_uri, 'table-header-rows', common_attrs + []),
    BlockElement(style_uri, 'table-properties', common_attrs + []),
    BlockElement(style_uri, 'table-row', common_attrs + []),
    BlockElement(style_uri, 'table-row-properties', common_attrs + []),
    #'text-blinking
    #'text-outline
    #'text-position
    #'text-propertie
    BlockElement(style_uri, 'text-properties', common_attrs + [])
    #'text-rotation-angle
    #'text-scale
    #'text-underline-style
    #'use-optimal-row-height
    #'vertical-pos
    #'vertical-rel
    #'wrap
    ]
odf_table_elements = [
    #'align'
    BlockElement(table_uri, 'body', common_attrs + []),
    BlockElement(table_uri, 'calculation-settings', common_attrs + []),
    BlockElement(table_uri, 'cell-adress', common_attrs + []),
    BlockElement(table_uri, 'cell-content-change', common_attrs + []),
    BlockElement(table_uri, 'cell-content-deletion', common_attrs + []),
    BlockElement(table_uri, 'cell-range-source', common_attrs + []),
    BlockElement(table_uri, 'change-deletion', common_attrs + []),
    BlockElement(table_uri, 'change-track-table-cell', common_attrs + []),
    BlockElement(table_uri, 'consolidation', common_attrs + []),
    BlockElement(table_uri, 'content-validation', common_attrs + []),
    BlockElement(table_uri, 'content-validations', common_attrs + []),
    BlockElement(table_uri, 'covered-table-cell', common_attrs + []),
    BlockElement(table_uri, 'cut-offs', common_attrs + []),
    BlockElement(table_uri, 'data-pilot-display-info', common_attrs + []),
    BlockElement(table_uri, 'data-pilot-field', common_attrs + []),
    BlockElement(table_uri, 'data-pilot-field-reference', common_attrs + []),
    BlockElement(table_uri, 'data-pilot-group', common_attrs + []),
    BlockElement(table_uri, 'data-pilot-group-member', common_attrs + []),
    BlockElement(table_uri, 'data-pilot-groups', common_attrs + []),
    BlockElement(table_uri, 'data-pilot-layout-info', common_attrs + []),
    BlockElement(table_uri, 'data-pilot-level', common_attrs + []),
    BlockElement(table_uri, 'data-pilot-member', common_attrs + []),
    BlockElement(table_uri, 'data-pilot-members', common_attrs + []),
    BlockElement(table_uri, 'data-pilot-sort-info', common_attrs + []),
    BlockElement(table_uri, 'data-pilot-subtotal', common_attrs + []),
    BlockElement(table_uri, 'data-pilot-subtotals', common_attrs + []),
    BlockElement(table_uri, 'data-pilot-table', common_attrs + []),
    BlockElement(table_uri, 'data-pilot-tables', common_attrs + []),
    BlockElement(table_uri, 'database-range', common_attrs + []),
    BlockElement(table_uri, 'database-ranges', common_attrs + []),
    BlockElement(table_uri, 'database-source-query', common_attrs + []),
    BlockElement(table_uri, 'database-source-sql', common_attrs + []),
    BlockElement(table_uri, 'database-source-table', common_attrs + []),
    BlockElement(table_uri, 'dde-link', common_attrs + []),
    BlockElement(table_uri, 'dde-links', common_attrs + []),
    BlockElement(table_uri, 'deletion', common_attrs + []),
    BlockElement(table_uri, 'deletions', common_attrs + []),
    BlockElement(table_uri, 'dependencies', common_attrs + []),
    BlockElement(table_uri, 'dependency', common_attrs + []),
    BlockElement(table_uri, 'detective', common_attrs + []),
    #'end-cell-address'
    #'end-x/y'
    BlockElement(table_uri, 'error-macro', common_attrs + []),
    BlockElement(table_uri, 'error-message', common_attrs + []),
    BlockElement(table_uri, 'even-columns', common_attrs + []),
    BlockElement(table_uri, 'even-rows', common_attrs + []),
    BlockElement(table_uri, 'filter', common_attrs + []),
    BlockElement(table_uri, 'filter-and', common_attrs + []),
    BlockElement(table_uri, 'filter-condition', common_attrs + []),
    BlockElement(table_uri, 'filter-or', common_attrs + []),
    BlockElement(table_uri, 'first-column', common_attrs + []),
    BlockElement(table_uri, 'first-row', common_attrs + []),
    BlockElement(table_uri, 'help-message', common_attrs + []),
    BlockElement(table_uri, 'highlighted-range', common_attrs + []),
    BlockElement(table_uri, 'insertion', common_attrs + []),
    BlockElement(table_uri, 'insertion-cut-off', common_attrs + []),
    BlockElement(table_uri, 'iteration', common_attrs + []),
    BlockElement(table_uri, 'label-range', common_attrs + []),
    BlockElement(table_uri, 'label-ranges', common_attrs + []),
    BlockElement(table_uri, 'last-column', common_attrs + []),
    BlockElement(table_uri, 'last-row', common_attrs + []),
    BlockElement(table_uri, 'movement', common_attrs + []),
    BlockElement(table_uri, 'movement-cut-off', common_attrs + []),
    BlockElement(table_uri, 'named-expression', common_attrs + []),
    BlockElement(table_uri, 'named-expressions', common_attrs + []),
    BlockElement(table_uri, 'named-range', common_attrs + []),
    BlockElement(table_uri, 'null-date', common_attrs + []),
    BlockElement(table_uri, 'odd-columns', common_attrs + []),
    BlockElement(table_uri, 'odd-rows', common_attrs + []),
    BlockElement(table_uri, 'operation', common_attrs + []),
    BlockElement(table_uri, 'previous', common_attrs + []),
    BlockElement(table_uri, 'scenario', common_attrs + []),
    BlockElement(table_uri, 'shapes', common_attrs + []),
    BlockElement(table_uri, 'sort', common_attrs + []),
    BlockElement(table_uri, 'sort-by', common_attrs + []),
    BlockElement(table_uri, 'sort-groups', common_attrs + []),
    BlockElement(table_uri, 'source-cell-range', common_attrs + []),
    BlockElement(table_uri, 'source-range-address', common_attrs + []),
    BlockElement(table_uri, 'source-service', common_attrs + []),
    BlockElement(table_uri, 'subtotal-field', common_attrs + []),
    BlockElement(table_uri, 'subtotal-rule', common_attrs + []),
    BlockElement(table_uri, 'subtotal-rules', common_attrs + []),
    BlockElement(table_uri, 'table', common_attrs + []),
    BlockElement(table_uri, 'table-cell', common_attrs + []),
    BlockElement(table_uri, 'table-column', common_attrs + []),
    BlockElement(table_uri, 'table-column-group', common_attrs + []),
    BlockElement(table_uri, 'table-columns', common_attrs + []),
    BlockElement(table_uri, 'table-header-columns', common_attrs + []),
    BlockElement(table_uri, 'table-header-rows', common_attrs + []),
    BlockElement(table_uri, 'table-row', common_attrs + []),
    BlockElement(table_uri, 'table-row-group', common_attrs + []),
    BlockElement(table_uri, 'table-rows', common_attrs + []),
    BlockElement(table_uri, 'table-source', common_attrs + []),
    BlockElement(table_uri, 'table-template', common_attrs + []),
    BlockElement(table_uri, 'target-range-address', common_attrs + []),
    BlockElement(table_uri, 'tracked-changes', common_attrs + [])]
odf_drawing_elements = [
    BlockElement(draw_uri, 'a', common_attrs + []),
    BlockElement(draw_uri, 'applet', common_attrs + []),
    BlockElement(draw_uri, 'area-circle', common_attrs + []),
    BlockElement(draw_uri, 'area-polygon', common_attrs + []),
    BlockElement(draw_uri, 'area-rectangle', common_attrs + []),
    BlockElement(draw_uri, 'caption', common_attrs + []),
    BlockElement(draw_uri, 'circle', common_attrs + []),
    BlockElement(draw_uri, 'connector', common_attrs + []),
    BlockElement(draw_uri, 'contour-path', common_attrs + []),
    BlockElement(draw_uri, 'contour-polygon', common_attrs + []),
    BlockElement(draw_uri, 'control', common_attrs + []),
    BlockElement(draw_uri, 'custom-shape', common_attrs + []),
    BlockElement(draw_uri, 'ellipse', common_attrs + []),
    BlockElement(draw_uri, 'enhanced-geometry', common_attrs + []),
    BlockElement(draw_uri, 'equation', common_attrs + []),
    BlockElement(draw_uri, 'fill-image', common_attrs + []),
    BlockElement(draw_uri, 'floating-frame', common_attrs + []),
    BlockElement(draw_uri, 'frame', common_attrs + []),
    BlockElement(draw_uri, 'g', common_attrs + []),
    BlockElement(draw_uri, 'glue-point', common_attrs + []),
    BlockElement(draw_uri, 'gradient', common_attrs + []),
    BlockElement(draw_uri, 'handle', common_attrs + []),
    BlockElement(draw_uri, 'hatch', common_attrs + []),
    BlockElement(draw_uri, 'image', common_attrs + []),
    BlockElement(draw_uri, 'image-map', common_attrs + []),
    BlockElement(draw_uri, 'layer', common_attrs + []),
    BlockElement(draw_uri, 'layer-set', common_attrs + []),
    BlockElement(draw_uri, 'line', common_attrs + []),
    BlockElement(draw_uri, 'marker', common_attrs + []),
    BlockElement(draw_uri, 'measure', common_attrs + []),
    BlockElement(draw_uri, 'object', common_attrs + []),
    BlockElement(draw_uri, 'object-ole', common_attrs + []),
    BlockElement(draw_uri, 'opacity', common_attrs + []),
    BlockElement(draw_uri, 'page', common_attrs + []),
    BlockElement(draw_uri, 'page-thumbnail', common_attrs + []),
    BlockElement(draw_uri, 'param', common_attrs + []),
    BlockElement(draw_uri, 'path', common_attrs + []),
    BlockElement(draw_uri, 'plugin', common_attrs + []),
    BlockElement(draw_uri, 'polygon', common_attrs + []),
    BlockElement(draw_uri, 'polyline', common_attrs + []),
    BlockElement(draw_uri, 'rect', common_attrs + []),
    BlockElement(draw_uri, 'regular-polygon', common_attrs + []),
    BlockElement(draw_uri, 'stroke-dash', common_attrs + []),
    BlockElement(draw_uri, 'text-box', common_attrs + [])]
odf_meta_elements = [
    # XXX the meta:user-defined element schema has an attribute 'name'.
    # This attribute define the name of the field. So it could be potentially
    # translated. But we currently don't do it.
    BlockElement(meta_uri, 'auto-reload', common_attrs + []),
    BlockElement(meta_uri, 'creation-date', common_attrs + [],
                 translate_content = False),
    BlockElement(meta_uri, 'date-string', common_attrs + []),
    BlockElement(meta_uri, 'document-statistic', common_attrs + []),
    BlockElement(meta_uri, 'editing-cycles', common_attrs + [],
                 translate_content = False),
    BlockElement(meta_uri, 'editing-duration', common_attrs + [],
                 translate_content = False),
    BlockElement(meta_uri, 'generator', common_attrs + [],
                 translate_content = False),
    BlockElement(meta_uri, 'hyperlink-behaviour', common_attrs + []),
    BlockElement(meta_uri, 'initial-creator', common_attrs + []),
    BlockElement(meta_uri, 'keyword', common_attrs + []),
    BlockElement(meta_uri, 'print-date', common_attrs + [],
                 translate_content = False),
    BlockElement(meta_uri, 'printed-by', common_attrs + []),
    BlockElement(meta_uri, 'template', common_attrs + []),
    BlockElement(meta_uri, 'user-defined', common_attrs + [])]
odf_svg_elements = [
    BlockElement(svg_uri, 'definition-src', common_attrs + []),
    BlockElement(svg_uri, 'desc', common_attrs + []),
    BlockElement(svg_uri, 'font-face-format', common_attrs + []),
    BlockElement(svg_uri, 'font-face-name', common_attrs + []),
    BlockElement(svg_uri, 'font-face-src', common_attrs + []),
    BlockElement(svg_uri, 'font-face-uri', common_attrs + []),
    BlockElement(svg_uri, 'linearGradient', common_attrs + []),
    BlockElement(svg_uri, 'radialGradient', common_attrs + []),
    BlockElement(svg_uri, 'stop', common_attrs + [])]
odf_dr3d_elements = [
    BlockElement(dr3d_uri, 'cube', common_attrs + []),
    BlockElement(dr3d_uri, 'extrude', common_attrs + []),
    BlockElement(dr3d_uri, 'light', common_attrs + []),
    BlockElement(dr3d_uri, 'rotate', common_attrs + []),
    BlockElement(dr3d_uri, 'scene', common_attrs + []),
    BlockElement(dr3d_uri, 'sphere', common_attrs + [])]
odf_form_elements = [
    BlockElement(form_uri, 'button', common_attrs + []),
    BlockElement(form_uri, 'checkbox', common_attrs + []),
    BlockElement(form_uri, 'column', common_attrs + []),
    BlockElement(form_uri, 'combobox', common_attrs + []),
    BlockElement(form_uri, 'connection-resource', common_attrs + []),
    BlockElement(form_uri, 'date', common_attrs + []),
    BlockElement(form_uri, 'file', common_attrs + []),
    BlockElement(form_uri, 'fixed-text', common_attrs + []),
    BlockElement(form_uri, 'form', common_attrs + []),
    BlockElement(form_uri, 'formatted-text', common_attrs + []),
    BlockElement(form_uri, 'frame', common_attrs + []),
    BlockElement(form_uri, 'generic-control', common_attrs + []),
    BlockElement(form_uri, 'grid', common_attrs + []),
    BlockElement(form_uri, 'hidden', common_attrs + []),
    BlockElement(form_uri, 'image', common_attrs + []),
    BlockElement(form_uri, 'image-frame', common_attrs + []),
    BlockElement(form_uri, 'item', common_attrs + []),
    BlockElement(form_uri, 'list-property', common_attrs + []),
    BlockElement(form_uri, 'list-value', common_attrs + []),
    BlockElement(form_uri, 'listbox', common_attrs + []),
    BlockElement(form_uri, 'number', common_attrs + []),
    BlockElement(form_uri, 'option', common_attrs + []),
    BlockElement(form_uri, 'password', common_attrs + []),
    BlockElement(form_uri, 'properties', common_attrs + []),
    BlockElement(form_uri, 'property', common_attrs + []),
    BlockElement(form_uri, 'radio', common_attrs + []),
    BlockElement(form_uri, 'text', common_attrs + []),
    BlockElement(form_uri, 'textarea', common_attrs + []),
    BlockElement(form_uri, 'time', common_attrs + []),
    BlockElement(form_uri, 'value-range', common_attrs + [])]
odf_script_elements = [
    BlockElement(script_uri, 'event-listener', common_attrs + [])]
odf_data_style_elements = [
    BlockElement(number_uri, 'am-pm', common_attrs + []),
    BlockElement(number_uri, 'boolean', common_attrs + []),
    BlockElement(number_uri, 'boolean-style', common_attrs + []),
    BlockElement(number_uri, 'currency-style', common_attrs + []),
    BlockElement(number_uri, 'currency-symbol', common_attrs + [],
                 translate_content = False),
    BlockElement(number_uri, 'date-style', common_attrs + []),
    BlockElement(number_uri, 'day', common_attrs + []),
    BlockElement(number_uri, 'day-of-week', common_attrs + []),
    BlockElement(number_uri, 'embedded-text', common_attrs + []),
    BlockElement(number_uri, 'era', common_attrs + []),
    BlockElement(number_uri, 'fraction', common_attrs + []),
    BlockElement(number_uri, 'hours', common_attrs + []),
    BlockElement(number_uri, 'minutes', common_attrs + []),
    BlockElement(number_uri, 'month', common_attrs + []),
    BlockElement(number_uri, 'number', common_attrs + []),
    BlockElement(number_uri, 'number-style', common_attrs + []),
    BlockElement(number_uri, 'percentage-style', common_attrs + []),
    BlockElement(number_uri, 'quarter', common_attrs + []),
    BlockElement(number_uri, 'scientific-number', common_attrs + []),
    BlockElement(number_uri, 'seconds', common_attrs + []),
    BlockElement(number_uri, 'text', common_attrs + []),
    BlockElement(number_uri, 'text-content', common_attrs + []),
    BlockElement(number_uri, 'text-style', common_attrs + []),
    BlockElement(number_uri, 'time-style', common_attrs + []),
    BlockElement(number_uri, 'week-of-year', common_attrs + []),
    BlockElement(number_uri, 'year', common_attrs + [])]
odf_animation_elements = [
    BlockElement(anim_uri, 'animate', common_attrs + []),
    BlockElement(anim_uri, 'animateColor', common_attrs + []),
    BlockElement(anim_uri, 'animateMotion', common_attrs + []),
    BlockElement(anim_uri, 'animateTransform', common_attrs + []),
    BlockElement(anim_uri, 'audio', common_attrs + []),
    BlockElement(anim_uri, 'command', common_attrs + []),
    BlockElement(anim_uri, 'iterate', common_attrs + []),
    BlockElement(anim_uri, 'par', common_attrs + []),
    BlockElement(anim_uri, 'param', common_attrs + []),
    BlockElement(anim_uri, 'seq', common_attrs + []),
    BlockElement(anim_uri, 'set', common_attrs + []),
    BlockElement(anim_uri, 'transitionFilter', common_attrs + [])]
odf_chart_elements = [
    BlockElement(chart_uri, 'axis', common_attrs + []),
    BlockElement(chart_uri, 'categories', common_attrs + []),
    BlockElement(chart_uri, 'chart', common_attrs + []),
    BlockElement(chart_uri, 'data-point', common_attrs + []),
    BlockElement(chart_uri, 'domain', common_attrs + []),
    BlockElement(chart_uri, 'error-indicator', common_attrs + []),
    BlockElement(chart_uri, 'floor', common_attrs + []),
    BlockElement(chart_uri, 'footer', common_attrs + []),
    BlockElement(chart_uri, 'grid', common_attrs + []),
    BlockElement(chart_uri, 'legend', common_attrs + []),
    BlockElement(chart_uri, 'mean-value', common_attrs + []),
    BlockElement(chart_uri, 'plot-area', common_attrs + []),
    BlockElement(chart_uri, 'regression-curve', common_attrs + []),
    BlockElement(chart_uri, 'series', common_attrs + []),
    BlockElement(chart_uri, 'stock-gain-marker', common_attrs + []),
    BlockElement(chart_uri, 'stock-loss-marker', common_attrs + []),
    BlockElement(chart_uri, 'stock-range-line', common_attrs + []),
    BlockElement(chart_uri, 'subtitle', common_attrs + []),
    BlockElement(chart_uri, 'symbol-image', common_attrs + []),
    BlockElement(chart_uri, 'title', common_attrs + []),
    BlockElement(chart_uri, 'wall', common_attrs + [])]
odf_config_elements = [
    BlockElement(config_uri, 'config-item', common_attrs + []),
    BlockElement(config_uri, 'config-item-map-entry', common_attrs + []),
    BlockElement(config_uri, 'config-item-map-indexed', common_attrs + []),
    BlockElement(config_uri, 'config-item-map-named', common_attrs + []),
    BlockElement(config_uri, 'config-item-set', common_attrs + [])]
odf_manifest_elements = [
    BlockElement(manifest_uri, 'algorithm', common_attrs + []),
    BlockElement(manifest_uri, 'encryption-data', common_attrs + []),
    BlockElement(manifest_uri, 'file-entry', common_attrs + []),
    BlockElement(manifest_uri, 'key-derivation', common_attrs + []),
    BlockElement(manifest_uri, 'manifest', common_attrs + [])]
odf_presentation_elements = [
    BlockElement(presentation_uri, 'animation-group', common_attrs + []),
    BlockElement(presentation_uri, 'animations', common_attrs + []),
    BlockElement(presentation_uri, 'date-time', common_attrs + []),
    BlockElement(presentation_uri, 'date-time-decl', common_attrs + []),
    BlockElement(presentation_uri, 'dim', common_attrs + []),
    BlockElement(presentation_uri, 'event-listener', common_attrs + []),
    BlockElement(presentation_uri, 'footer', common_attrs + []),
    BlockElement(presentation_uri, 'footer-decl', common_attrs + []),
    BlockElement(presentation_uri, 'header', common_attrs + []),
    BlockElement(presentation_uri, 'header-decl', common_attrs + []),
    BlockElement(presentation_uri, 'hide-shape', common_attrs + []),
    BlockElement(presentation_uri, 'hide-text', common_attrs + []),
    BlockElement(presentation_uri, 'notes', common_attrs + []),
    BlockElement(presentation_uri, 'placeholder', common_attrs + []),
    BlockElement(presentation_uri, 'play', common_attrs + []),
    BlockElement(presentation_uri, 'settings', common_attrs + []),
    BlockElement(presentation_uri, 'show', common_attrs + []),
    BlockElement(presentation_uri, 'show-shape', common_attrs + []),
    BlockElement(presentation_uri, 'show-text', common_attrs + []),
    BlockElement(presentation_uri, 'sound', common_attrs + [])]


odf_text_namespace = XMLNamespace(text_uri, 'text', odf_text_elements)
odf_office_namespace = XMLNamespace(office_uri, 'office', odf_office_elements)
odf_style_namespace = XMLNamespace(style_uri, 'style', odf_style_elements)
odf_table_namespace = XMLNamespace(table_uri, 'table', odf_table_elements)
odf_drawing_namespace = XMLNamespace(draw_uri, 'draw', odf_drawing_elements)
odf_fo_namespace = XMLNamespace(fo_uri, 'fo', [])
odf_meta_namespace = XMLNamespace(meta_uri, 'meta', odf_meta_elements)
odf_svg_namespace = XMLNamespace(svg_uri, 'svg', odf_svg_elements)
odf_dr3d_namespace = XMLNamespace(dr3d_uri, 'dr3d', odf_dr3d_elements)
odf_form_namespace = XMLNamespace(form_uri, 'form', odf_form_elements)
odf_script_namespace = XMLNamespace(script_uri, 'script', odf_style_elements)
odf_ooo_namespace = XMLNamespace(ooo_uri, 'ooo', [])
odf_ooow_namespace = XMLNamespace(ooow_uri, 'ooow', [])
odf_oooc_namespace = XMLNamespace(oooc_uri, 'oooc', [])
odf_data_style_namespace = XMLNamespace(number_uri, 'number',
                                        odf_data_style_elements)
odf_animation_namespace = XMLNamespace(anim_uri, 'anim',
                                       odf_animation_elements)
odf_chart_namespace = XMLNamespace(chart_uri, 'chart', odf_animation_elements)
odf_config_namespace = XMLNamespace(config_uri, 'config', odf_config_elements)
odf_manifest_namespace = XMLNamespace(manifest_uri, 'manifest',
                                      odf_manifest_elements)
odf_presentation_namespace = XMLNamespace(presentation_uri, 'presentation',
                                          odf_presentation_elements)
odf_smil_namespace = XMLNamespace(smil_uri, 'uri', [])
for namespace in [odf_text_namespace, odf_office_namespace,
                  odf_style_namespace, odf_table_namespace,
                  odf_drawing_namespace, odf_meta_namespace,
                  odf_svg_namespace, odf_dr3d_namespace, odf_form_namespace,
                  odf_script_namespace, odf_data_style_namespace,
                  odf_animation_namespace, odf_chart_namespace,
                  odf_config_namespace, odf_manifest_namespace,
                  odf_presentation_namespace]:
    register_namespace(namespace)
