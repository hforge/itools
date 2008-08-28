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


    def __init__(self, name, attributes, **kw):
        ElementSchema.__init__(self, name, **kw)
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
    BlockElement('a', common_attrs + []),
    BlockElement('alphabetical-index', common_attrs + []),
    BlockElement('alphabetical-index-auto-mark-file', common_attrs + []),
    BlockElement('alphabetical-index-entry-template', common_attrs + []),
    BlockElement('alphabetical-index-mark', common_attrs + []),
    BlockElement('alphabetical-index-mark-end', common_attrs + []),
    BlockElement('alphabetical-index-mark-start', common_attrs + []),
    BlockElement('alphabetical-index-source', common_attrs + []),
    #'anchor-page-number'
    #'anchor-type'
    #'animation'
    #'animation-delay'
    #'animation-direction'
    #'animation-repeat'
    #'animation-start-inside'
    #'animation-steps'
    #'animation-stop-inside'
    BlockElement('author-initials', common_attrs + []),
    BlockElement('author-name', common_attrs + []),
    BlockElement('bibliography', common_attrs + []),
    BlockElement('bibliography-configuration', common_attrs + []),
    BlockElement('bibliography-entry-template', common_attrs + []),
    BlockElement('bibliography-mark', common_attrs + []),
    BlockElement('bibliography-source', common_attrs + []),
    BlockElement('bookmark', common_attrs + []),
    BlockElement('bookmark-end', common_attrs + []),
    BlockElement('bookmark-ref', common_attrs + []),
    BlockElement('bookmark-start', common_attrs + []),
    #'bullet-char'
    BlockElement('change', common_attrs + []),
    BlockElement('change-end', common_attrs + []),
    BlockElement('change-start', common_attrs + []),
    BlockElement('changed-region', common_attrs + []),
    BlockElement('chapter', common_attrs + []),
    #'character-count' (FIXME Check whether creation-date is empty
    # or not)
    BlockElement('conditional-text', common_attrs + []),
    BlockElement('creation-date', common_attrs + []),
    BlockElement('creation-time', common_attrs + [], translate_content=False),
    BlockElement('creator', common_attrs + []),
    BlockElement('database-display', common_attrs + []),
    BlockElement('database-name', common_attrs + []),
    BlockElement('database-next', common_attrs + []),
    BlockElement('database-row-number', common_attrs + []),
    BlockElement('database-row-select', common_attrs + []),
    BlockElement('date', common_attrs + [], translate_content=False),
    #'date-value'
    BlockElement('dde-connection', common_attrs + []),
    BlockElement('dde-connection-decl', common_attrs + []),
    BlockElement('dde-connection-decls', common_attrs + []),
    BlockElement('deletion', common_attrs + []),
    BlockElement('description', common_attrs + []),
    #'dont-balance-text-columns'
    BlockElement('editing-cycles', common_attrs + []),
    BlockElement('editing-duration', common_attrs + []),
    BlockElement('execute-macro', common_attrs + []),
    BlockElement('expression', common_attrs + []),
    BlockElement('file-name', common_attrs + []),
    BlockElement('format-change', common_attrs + []),
    BlockElement('h', common_attrs + []),
    BlockElement('hidden-paragraph', common_attrs + []),
    BlockElement('hidden-text', common_attrs + []),
    BlockElement('illustration-index', common_attrs + []),
    BlockElement('illustration-index-entry-template', common_attrs + []),
    BlockElement('illustration-index-source', common_attrs + []),
    #'image-count'
    BlockElement('index-body', common_attrs + []),
    BlockElement('index-entry-bibliography', common_attrs + []),
    BlockElement('index-entry-chapter', common_attrs + []),
    BlockElement('index-entry-link-end', common_attrs + []),
    BlockElement('index-entry-link-start', common_attrs + []),
    BlockElement('index-entry-page-number', common_attrs + []),
    BlockElement('index-entry-span', common_attrs + []),
    BlockElement('index-entry-tab-stop', common_attrs + []),
    BlockElement('index-entry-text', common_attrs + []),
    BlockElement('index-source-style', common_attrs + []),
    BlockElement('index-source-styles', common_attrs + []),
    BlockElement('index-title', common_attrs + []),
    BlockElement('index-title-template', common_attrs + []),
    BlockElement('initial-creator', common_attrs + []),
    BlockElement('insertion', common_attrs + []),
    BlockElement('keywords', common_attrs + []),
    #'level'
    EmptyElement('line-break', common_attrs + []),
    BlockElement('linenumbering-configuration', common_attrs + []),
    BlockElement('linenumbering-separator', common_attrs + []),
    BlockElement('list', common_attrs + []),
    BlockElement('list-header', common_attrs + []),
    BlockElement('list-item', common_attrs + []),
    BlockElement('list-level-style-bullet', common_attrs + []),
    BlockElement('list-level-style-image', common_attrs + []),
    BlockElement('list-level-style-number', common_attrs + []),
    BlockElement('list-style', common_attrs + []),
    BlockElement('measure', common_attrs + []),
    #min-label-width
    BlockElement('modification-date', common_attrs + []),
    BlockElement('modification-time', common_attrs + []),
    BlockElement('note', common_attrs + []),
    BlockElement('note-body', common_attrs + []),
    BlockElement('note-citation', common_attrs + []),
    BlockElement('note-continuation-notice-backward', common_attrs + []),
    BlockElement('note-continuation-notice-forward', common_attrs + []),
    BlockElement('note-ref', common_attrs + []),
    BlockElement('notes-configuration', common_attrs + []),
    BlockElement('number', common_attrs + []),
    BlockElement('numbered-paragraph', common_attrs + []),
    BlockElement('object-count', common_attrs + []),
    BlockElement('object-index', common_attrs + []),
    BlockElement('object-index-entry-template', common_attrs + []),
    BlockElement('object-index-source', common_attrs + []),
    BlockElement('outline-level-style', common_attrs + []),
    BlockElement('outline-style', common_attrs + []),
    BlockElement('p', common_attrs + []),
    BlockElement('page', common_attrs + []),
    BlockElement('page-continuation', common_attrs + []),
    Element('page-count', common_attrs + [], translate_content=False),
    Element('page-number', common_attrs + [], translate_content=False),
    BlockElement('page-sequence', common_attrs + []),
    BlockElement('page-variable-get', common_attrs + []),
    BlockElement('page-variable-set', common_attrs + []),
    #'paragraph-count'
    BlockElement('placeholder', common_attrs + []),
    BlockElement('print-date', common_attrs + []),
    BlockElement('print-time', common_attrs + []),
    BlockElement('printed-by', common_attrs + []),
    BlockElement('reference-mark', common_attrs + []),
    BlockElement('reference-mark-end', common_attrs + []),
    BlockElement('reference-mark-start', common_attrs + []),
    BlockElement('reference-ref', common_attrs + []),
    BlockElement('ruby', common_attrs + []),
    BlockElement('ruby-base', common_attrs + []),
    #'ruby-text':
    EmptyElement('s', common_attrs + []),
    BlockElement('script', common_attrs + []),
    BlockElement('section', common_attrs + []),
    BlockElement('section-source', common_attrs + []),
    BlockElement('sender-city', common_attrs + []),
    BlockElement('sender-company', common_attrs + []),
    BlockElement('sender-country', common_attrs + []),
    BlockElement('sender-email', common_attrs + []),
    BlockElement('sender-fax', common_attrs + []),
    BlockElement('sender-firstname', common_attrs + []),
    BlockElement('sender-initials', common_attrs + []),
    BlockElement('sender-lastname', common_attrs + []),
    BlockElement('sender-phone-private', common_attrs + []),
    BlockElement('sender-phone-work', common_attrs + []),
    BlockElement('sender-position', common_attrs + []),
    BlockElement('sender-postal-code', common_attrs + []),
    BlockElement('sender-state-or-province', common_attrs + []),
    BlockElement('sender-street', common_attrs + []),
    BlockElement('sender-title', common_attrs + []),
    BlockElement('sequence', common_attrs + [], translate_content=False),
    BlockElement('sequence-decl', common_attrs + []),
    BlockElement('sequence-decls', common_attrs + []),
    BlockElement('sequence-ref', common_attrs + []),
    BlockElement('sheet-name', common_attrs + []),
    BlockElement('sort-key', common_attrs + []),
    #'space-before'
    Element('span', common_attrs + []),
    #'style-name'
    BlockElement('subject', common_attrs + []),
    EmptyElement('tab', common_attrs + []),
    #'table-count'
    BlockElement('table-formula', common_attrs + []),
    BlockElement('table-index', common_attrs + []),
    BlockElement('table-index-entry-template', common_attrs + []),
    BlockElement('table-index-source', common_attrs + []),
    BlockElement('table-of-content', common_attrs + []),
    BlockElement('table-of-content-entry-template', common_attrs + []),
    BlockElement('table-of-content-source', common_attrs + []),
    BlockElement('template-name', common_attrs + []),
    BlockElement('text-input', common_attrs + []),
    BlockElement('time', common_attrs + [], translate_content = False),
    #'time-value'
    BlockElement('title', common_attrs + []),
    BlockElement('toc-mark', common_attrs + []),
    BlockElement('toc-mark-end', common_attrs + []),
    BlockElement('toc-mark-start', common_attrs + []),
    BlockElement('tracked-changes', common_attrs + []),
    BlockElement('user-defined', common_attrs + []),
    BlockElement('user-field-decl', common_attrs + []),
    BlockElement('user-field-decls', common_attrs + []),
    BlockElement('user-field-get', common_attrs + []),
    BlockElement('user-field-input', common_attrs + []),
    BlockElement('user-index', common_attrs + []),
    BlockElement('user-index-entry-template', common_attrs + []),
    BlockElement('user-index-mark', common_attrs + []),
    BlockElement('user-index-mark-end', common_attrs + []),
    BlockElement('user-index-mark-start', common_attrs + []),
    BlockElement('user-index-source', common_attrs + []),
    BlockElement('variable-decl', common_attrs + []),
    BlockElement('variable-decls', common_attrs + []),
    BlockElement('variable-get', common_attrs + []),
    BlockElement('variable-input', common_attrs + []),
    BlockElement('variable-set', common_attrs + [])
    #'word-count'
    ]
odf_office_elements = [
    BlockElement('annotation', common_attrs + []),
    BlockElement('automatic-styles', common_attrs + []),
    BlockElement('binary-data', common_attrs + []),
    BlockElement('body', common_attrs + []),
    BlockElement('change-info', common_attrs + []),
    BlockElement('chart', common_attrs + []),
    BlockElement('dde-source', common_attrs + []),
    BlockElement('document', common_attrs + []),
    BlockElement('document-content', common_attrs + []),
    BlockElement('document-meta', common_attrs + []),
    BlockElement('document-settings', common_attrs + []),
    BlockElement('document-styles', common_attrs + []),
    BlockElement('drawing', common_attrs + []),
    BlockElement('event-listeners', common_attrs + []),
    BlockElement('font-face-decls', common_attrs + []),
    BlockElement('forms', common_attrs + []),
    BlockElement('image', common_attrs + []),
    BlockElement('master-styles', common_attrs + []),
    BlockElement('meta', common_attrs + []),
    BlockElement('presentation', common_attrs + []),
    BlockElement('script', common_attrs + []),
    BlockElement('scripts', common_attrs + []),
    BlockElement('settings', common_attrs + []),
    BlockElement('spreadsheet', common_attrs + []),
    BlockElement('styles', common_attrs + []),
    BlockElement('text', common_attrs + [])]
odf_style_elements = [
    BlockElement('background-image', common_attrs + []),
    #'border-line-width
    BlockElement('chart-properties', common_attrs + []),
    BlockElement('column', common_attrs + []),
    BlockElement('column-sep', common_attrs + []),
    #'column-width
    BlockElement('columns', common_attrs + []),
    BlockElement('default-style', common_attrs + []),
    #'display-name
    BlockElement('drawing-page-properties', common_attrs + []),
    BlockElement('drop-cap', common_attrs + []),
    #'family
    #'family-properties
    #'first-page-number
    #'font-decl
    BlockElement('font-face', common_attrs + []),
    #'font-name
    #'font-relief
    BlockElement('footer', common_attrs + []),
    BlockElement('footer-left', common_attrs + []),
    BlockElement('footer-style', common_attrs + []),
    #'footnote-max-height
    BlockElement('footnote-sep', common_attrs + []),
    BlockElement('graphic-properties', common_attrs + []),
    BlockElement('handout-master', common_attrs + []),
    BlockElement('header', common_attrs + []),
    BlockElement('header-footer-properties', common_attrs + []),
    BlockElement('header-left', common_attrs + []),
    BlockElement('header-style', common_attrs + []),
    #'horizontal-pos
    #'horizontal-rel
    #'leader-text
    #'line-spacing
    BlockElement('list-level-properties', common_attrs + []),
    BlockElement('map', common_attrs + []),
    BlockElement('master-page', common_attrs + []),
    #'may-break-between-rows
    #'min-row-height
    #'mirror
    #'name
    #'num-format
    #'number-wrapped-paragraphs
    BlockElement('page-layout', common_attrs + []),
    BlockElement('page-layout-properties', common_attrs + []),
    BlockElement('paragraph-properties', common_attrs + []),
    #'position
    BlockElement('presentation-page-layout', common_attrs + []),
    #'print
    #'print-orientation
    #'print-page-order
    BlockElement('region-center', common_attrs + []),
    BlockElement('region-left', common_attrs + []),
    BlockElement('region-right', common_attrs + []),
    #'rel-column-width
    #'rel-width
    #'repeat
    #'row-height
    BlockElement('ruby-properties', common_attrs + []),
    #'scale-to
    BlockElement('section-properties', common_attrs + []),
    BlockElement('style', common_attrs + []),
    BlockElement('tab-stop', common_attrs + []),
    BlockElement('tab-stops', common_attrs + []),
    BlockElement('table', common_attrs + []),
    BlockElement('table-cell', common_attrs + []),
    BlockElement('table-cell-properties', common_attrs + []),
    BlockElement('table-column', common_attrs + []),
    BlockElement('table-column-properties', common_attrs + []),
    BlockElement('table-header-rows', common_attrs + []),
    BlockElement('table-properties', common_attrs + []),
    BlockElement('table-row', common_attrs + []),
    BlockElement('table-row-properties', common_attrs + []),
    #'text-blinking
    #'text-outline
    #'text-position
    #'text-propertie
    BlockElement('text-properties', common_attrs + [])
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
    BlockElement('body', common_attrs + []),
    BlockElement('calculation-settings', common_attrs + []),
    BlockElement('cell-adress', common_attrs + []),
    BlockElement('cell-content-change', common_attrs + []),
    BlockElement('cell-content-deletion', common_attrs + []),
    BlockElement('cell-range-source', common_attrs + []),
    BlockElement('change-deletion', common_attrs + []),
    BlockElement('change-track-table-cell', common_attrs + []),
    BlockElement('consolidation', common_attrs + []),
    BlockElement('content-validation', common_attrs + []),
    BlockElement('content-validations', common_attrs + []),
    BlockElement('covered-table-cell', common_attrs + []),
    BlockElement('cut-offs', common_attrs + []),
    BlockElement('data-pilot-display-info', common_attrs + []),
    BlockElement('data-pilot-field', common_attrs + []),
    BlockElement('data-pilot-field-reference', common_attrs + []),
    BlockElement('data-pilot-group', common_attrs + []),
    BlockElement('data-pilot-group-member', common_attrs + []),
    BlockElement('data-pilot-groups', common_attrs + []),
    BlockElement('data-pilot-layout-info', common_attrs + []),
    BlockElement('data-pilot-level', common_attrs + []),
    BlockElement('data-pilot-member', common_attrs + []),
    BlockElement('data-pilot-members', common_attrs + []),
    BlockElement('data-pilot-sort-info', common_attrs + []),
    BlockElement('data-pilot-subtotal', common_attrs + []),
    BlockElement('data-pilot-subtotals', common_attrs + []),
    BlockElement('data-pilot-table', common_attrs + []),
    BlockElement('data-pilot-tables', common_attrs + []),
    BlockElement('database-range', common_attrs + []),
    BlockElement('database-ranges', common_attrs + []),
    BlockElement('database-source-query', common_attrs + []),
    BlockElement('database-source-sql', common_attrs + []),
    BlockElement('database-source-table', common_attrs + []),
    BlockElement('dde-link', common_attrs + []),
    BlockElement('dde-links', common_attrs + []),
    BlockElement('deletion', common_attrs + []),
    BlockElement('deletions', common_attrs + []),
    BlockElement('dependencies', common_attrs + []),
    BlockElement('dependency', common_attrs + []),
    BlockElement('detective', common_attrs + []),
    #'end-cell-address'
    #'end-x/y'
    BlockElement('error-macro', common_attrs + []),
    BlockElement('error-message', common_attrs + []),
    BlockElement('even-columns', common_attrs + []),
    BlockElement('even-rows', common_attrs + []),
    BlockElement('filter', common_attrs + []),
    BlockElement('filter-and', common_attrs + []),
    BlockElement('filter-condition', common_attrs + []),
    BlockElement('filter-or', common_attrs + []),
    BlockElement('first-column', common_attrs + []),
    BlockElement('first-row', common_attrs + []),
    BlockElement('help-message', common_attrs + []),
    BlockElement('highlighted-range', common_attrs + []),
    BlockElement('insertion', common_attrs + []),
    BlockElement('insertion-cut-off', common_attrs + []),
    BlockElement('iteration', common_attrs + []),
    BlockElement('label-range', common_attrs + []),
    BlockElement('label-ranges', common_attrs + []),
    BlockElement('last-column', common_attrs + []),
    BlockElement('last-row', common_attrs + []),
    BlockElement('movement', common_attrs + []),
    BlockElement('movement-cut-off', common_attrs + []),
    BlockElement('named-expression', common_attrs + []),
    BlockElement('named-expressions', common_attrs + []),
    BlockElement('named-range', common_attrs + []),
    BlockElement('null-date', common_attrs + []),
    BlockElement('odd-columns', common_attrs + []),
    BlockElement('odd-rows', common_attrs + []),
    BlockElement('operation', common_attrs + []),
    BlockElement('previous', common_attrs + []),
    BlockElement('scenario', common_attrs + []),
    BlockElement('shapes', common_attrs + []),
    BlockElement('sort', common_attrs + []),
    BlockElement('sort-by', common_attrs + []),
    BlockElement('sort-groups', common_attrs + []),
    BlockElement('source-cell-range', common_attrs + []),
    BlockElement('source-range-address', common_attrs + []),
    BlockElement('source-service', common_attrs + []),
    BlockElement('subtotal-field', common_attrs + []),
    BlockElement('subtotal-rule', common_attrs + []),
    BlockElement('subtotal-rules', common_attrs + []),
    BlockElement('table', common_attrs + []),
    BlockElement('table-cell', common_attrs + []),
    BlockElement('table-column', common_attrs + []),
    BlockElement('table-column-group', common_attrs + []),
    BlockElement('table-columns', common_attrs + []),
    BlockElement('table-header-columns', common_attrs + []),
    BlockElement('table-header-rows', common_attrs + []),
    BlockElement('table-row', common_attrs + []),
    BlockElement('table-row-group', common_attrs + []),
    BlockElement('table-rows', common_attrs + []),
    BlockElement('table-source', common_attrs + []),
    BlockElement('table-template', common_attrs + []),
    BlockElement('target-range-address', common_attrs + []),
    BlockElement('tracked-changes', common_attrs + [])]
odf_drawing_elements = [
    BlockElement('a', common_attrs + []),
    BlockElement('applet', common_attrs + []),
    BlockElement('area-circle', common_attrs + []),
    BlockElement('area-polygon', common_attrs + []),
    BlockElement('area-rectangle', common_attrs + []),
    BlockElement('caption', common_attrs + []),
    BlockElement('circle', common_attrs + []),
    BlockElement('connector', common_attrs + []),
    BlockElement('contour-path', common_attrs + []),
    BlockElement('contour-polygon', common_attrs + []),
    BlockElement('control', common_attrs + []),
    BlockElement('custom-shape', common_attrs + []),
    BlockElement('ellipse', common_attrs + []),
    BlockElement('enhanced-geometry', common_attrs + []),
    BlockElement('equation', common_attrs + []),
    BlockElement('fill-image', common_attrs + []),
    BlockElement('floating-frame', common_attrs + []),
    BlockElement('frame', common_attrs + []),
    BlockElement('g', common_attrs + []),
    BlockElement('glue-point', common_attrs + []),
    BlockElement('gradient', common_attrs + []),
    BlockElement('handle', common_attrs + []),
    BlockElement('hatch', common_attrs + []),
    BlockElement('image', common_attrs + []),
    BlockElement('image-map', common_attrs + []),
    BlockElement('layer', common_attrs + []),
    BlockElement('layer-set', common_attrs + []),
    BlockElement('line', common_attrs + []),
    BlockElement('marker', common_attrs + []),
    BlockElement('measure', common_attrs + []),
    BlockElement('object', common_attrs + []),
    BlockElement('object-ole', common_attrs + []),
    BlockElement('opacity', common_attrs + []),
    BlockElement('page', common_attrs + []),
    BlockElement('page-thumbnail', common_attrs + []),
    BlockElement('param', common_attrs + []),
    BlockElement('path', common_attrs + []),
    BlockElement('plugin', common_attrs + []),
    BlockElement('polygon', common_attrs + []),
    BlockElement('polyline', common_attrs + []),
    BlockElement('rect', common_attrs + []),
    BlockElement('regular-polygon', common_attrs + []),
    BlockElement('stroke-dash', common_attrs + []),
    BlockElement('text-box', common_attrs + [])]
odf_meta_elements = [
    # XXX the meta:user-defined element schema has an attribute 'name'.
    # This attribute define the name of the field. So it could be potentially
    # translated. But we currently don't do it.
    BlockElement('auto-reload', common_attrs + []),
    BlockElement('creation-date', common_attrs + [], translate_content=False),
    BlockElement('date-string', common_attrs + []),
    BlockElement('document-statistic', common_attrs + []),
    BlockElement('editing-cycles', common_attrs + [], translate_content=False),
    BlockElement('editing-duration', common_attrs + [],
                 translate_content=False),
    BlockElement('generator', common_attrs + [], translate_content=False),
    BlockElement('hyperlink-behaviour', common_attrs + []),
    BlockElement('initial-creator', common_attrs + []),
    BlockElement('keyword', common_attrs + []),
    BlockElement('print-date', common_attrs + [], translate_content=False),
    BlockElement('printed-by', common_attrs + []),
    BlockElement('template', common_attrs + []),
    BlockElement('user-defined', common_attrs + [])]
odf_svg_elements = [
    BlockElement('definition-src', common_attrs + []),
    BlockElement('desc', common_attrs + []),
    BlockElement('font-face-format', common_attrs + []),
    BlockElement('font-face-name', common_attrs + []),
    BlockElement('font-face-src', common_attrs + []),
    BlockElement('font-face-uri', common_attrs + []),
    BlockElement('linearGradient', common_attrs + []),
    BlockElement('radialGradient', common_attrs + []),
    BlockElement('stop', common_attrs + [])]
odf_dr3d_elements = [
    BlockElement('cube', common_attrs + []),
    BlockElement('extrude', common_attrs + []),
    BlockElement('light', common_attrs + []),
    BlockElement('rotate', common_attrs + []),
    BlockElement('scene', common_attrs + []),
    BlockElement('sphere', common_attrs + [])]
odf_form_elements = [
    BlockElement('button', common_attrs + []),
    BlockElement('checkbox', common_attrs + []),
    BlockElement('column', common_attrs + []),
    BlockElement('combobox', common_attrs + []),
    BlockElement('connection-resource', common_attrs + []),
    BlockElement('date', common_attrs + []),
    BlockElement('file', common_attrs + []),
    BlockElement('fixed-text', common_attrs + []),
    BlockElement('form', common_attrs + []),
    BlockElement('formatted-text', common_attrs + []),
    BlockElement('frame', common_attrs + []),
    BlockElement('generic-control', common_attrs + []),
    BlockElement('grid', common_attrs + []),
    BlockElement('hidden', common_attrs + []),
    BlockElement('image', common_attrs + []),
    BlockElement('image-frame', common_attrs + []),
    BlockElement('item', common_attrs + []),
    BlockElement('list-property', common_attrs + []),
    BlockElement('list-value', common_attrs + []),
    BlockElement('listbox', common_attrs + []),
    BlockElement('number', common_attrs + []),
    BlockElement('option', common_attrs + []),
    BlockElement('password', common_attrs + []),
    BlockElement('properties', common_attrs + []),
    BlockElement('property', common_attrs + []),
    BlockElement('radio', common_attrs + []),
    BlockElement('text', common_attrs + []),
    BlockElement('textarea', common_attrs + []),
    BlockElement('time', common_attrs + []),
    BlockElement('value-range', common_attrs + [])]
odf_script_elements = [
    BlockElement('event-listener', common_attrs + [])]
odf_data_style_elements = [
    BlockElement('am-pm', common_attrs + []),
    BlockElement('boolean', common_attrs + []),
    BlockElement('boolean-style', common_attrs + []),
    BlockElement('currency-style', common_attrs + []),
    BlockElement('currency-symbol', common_attrs + [],
                 translate_content=False),
    BlockElement('date-style', common_attrs + []),
    BlockElement('day', common_attrs + []),
    BlockElement('day-of-week', common_attrs + []),
    BlockElement('embedded-text', common_attrs + []),
    BlockElement('era', common_attrs + []),
    BlockElement('fraction', common_attrs + []),
    BlockElement('hours', common_attrs + []),
    BlockElement('minutes', common_attrs + []),
    BlockElement('month', common_attrs + []),
    BlockElement('number', common_attrs + []),
    BlockElement('number-style', common_attrs + []),
    BlockElement('percentage-style', common_attrs + []),
    BlockElement('quarter', common_attrs + []),
    BlockElement('scientific-number', common_attrs + []),
    BlockElement('seconds', common_attrs + []),
    BlockElement('text', common_attrs + []),
    BlockElement('text-content', common_attrs + []),
    BlockElement('text-style', common_attrs + []),
    BlockElement('time-style', common_attrs + []),
    BlockElement('week-of-year', common_attrs + []),
    BlockElement('year', common_attrs + [])]
odf_animation_elements = [
    BlockElement('animate', common_attrs + []),
    BlockElement('animateColor', common_attrs + []),
    BlockElement('animateMotion', common_attrs + []),
    BlockElement('animateTransform', common_attrs + []),
    BlockElement('audio', common_attrs + []),
    BlockElement('command', common_attrs + []),
    BlockElement('iterate', common_attrs + []),
    BlockElement('par', common_attrs + []),
    BlockElement('param', common_attrs + []),
    BlockElement('seq', common_attrs + []),
    BlockElement('set', common_attrs + []),
    BlockElement('transitionFilter', common_attrs + [])]
odf_chart_elements = [
    BlockElement('axis', common_attrs + []),
    BlockElement('categories', common_attrs + []),
    BlockElement('chart', common_attrs + []),
    BlockElement('data-point', common_attrs + []),
    BlockElement('domain', common_attrs + []),
    BlockElement('error-indicator', common_attrs + []),
    BlockElement('floor', common_attrs + []),
    BlockElement('footer', common_attrs + []),
    BlockElement('grid', common_attrs + []),
    BlockElement('legend', common_attrs + []),
    BlockElement('mean-value', common_attrs + []),
    BlockElement('plot-area', common_attrs + []),
    BlockElement('regression-curve', common_attrs + []),
    BlockElement('series', common_attrs + []),
    BlockElement('stock-gain-marker', common_attrs + []),
    BlockElement('stock-loss-marker', common_attrs + []),
    BlockElement('stock-range-line', common_attrs + []),
    BlockElement('subtitle', common_attrs + []),
    BlockElement('symbol-image', common_attrs + []),
    BlockElement('title', common_attrs + []),
    BlockElement('wall', common_attrs + [])]
odf_config_elements = [
    BlockElement('config-item', common_attrs + []),
    BlockElement('config-item-map-entry', common_attrs + []),
    BlockElement('config-item-map-indexed', common_attrs + []),
    BlockElement('config-item-map-named', common_attrs + []),
    BlockElement('config-item-set', common_attrs + [])]
odf_manifest_elements = [
    BlockElement('algorithm', common_attrs + []),
    BlockElement('encryption-data', common_attrs + []),
    BlockElement('file-entry', common_attrs + []),
    BlockElement('key-derivation', common_attrs + []),
    BlockElement('manifest', common_attrs + [])]
odf_presentation_elements = [
    BlockElement('animation-group', common_attrs + []),
    BlockElement('animations', common_attrs + []),
    BlockElement('date-time', common_attrs + []),
    BlockElement('date-time-decl', common_attrs + []),
    BlockElement('dim', common_attrs + []),
    BlockElement('event-listener', common_attrs + []),
    BlockElement('footer', common_attrs + []),
    BlockElement('footer-decl', common_attrs + []),
    BlockElement('header', common_attrs + []),
    BlockElement('header-decl', common_attrs + []),
    BlockElement('hide-shape', common_attrs + []),
    BlockElement('hide-text', common_attrs + []),
    BlockElement('notes', common_attrs + []),
    BlockElement('placeholder', common_attrs + []),
    BlockElement('play', common_attrs + []),
    BlockElement('settings', common_attrs + []),
    BlockElement('show', common_attrs + []),
    BlockElement('show-shape', common_attrs + []),
    BlockElement('show-text', common_attrs + []),
    BlockElement('sound', common_attrs + [])]


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
