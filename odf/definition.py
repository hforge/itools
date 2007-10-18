# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2007 Sylvain Taverne <sylvain@itaapy.com>
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from itools.xml import AbstractNamespace, set_namespace
from itools.schemas import Schema as BaseSchema, register_schema


########################################################################
############ urn:oasis:names:tc:opendocument:xmlns:text:1.0 ############
########################################################################


class OdtTextNamespace(AbstractNamespace):

    class_uri = 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'
    class_prefix = 'text'


    @staticmethod
    def get_element_schema(name):
        elements_schema = {
            'a': {'is_inline': False, 'is_empty': False},
            'alphabetical-index': {'is_inline': False, 'is_empty': False},
            'alphabetical-index-auto-mark-file': {'is_inline': False, 'is_empty': False},
            'alphabetical-index-entry-template': {'is_inline': False, 'is_empty': False},
            'alphabetical-index-mark': {'is_inline': False, 'is_empty': True},
            'alphabetical-index-mark-end': {'is_inline': False, 'is_empty': True},
            'alphabetical-index-mark-start': {'is_inline': False, 'is_empty': True},
            'alphabetical-index-source': {'is_inline': False, 'is_empty': False},
            #'anchor-page-number'
             #'anchor-type'
            #'animation'
            #'animation-delay'
            #'animation-direction'
            #'animation-repeat'
            #'animation-start-inside'
            #'animation-steps'
            #'animation-stop-inside'
            'author-initials': {'is_inline': False, 'is_empty': True},
            'author-name': {'is_inline': False, 'is_empty': True},
            'bibliography': {'is_inline': False, 'is_empty': False},
            'bibliography-configuration': {'is_inline': False, 'is_empty': False},
            'bibliography-entry-template': {'is_inline': False, 'is_empty': False},
            'bibliography-mark': {'is_inline': False, 'is_empty': True},
            'bibliography-source': {'is_inline': False, 'is_empty': False},
            'bookmark': {'is_inline': False, 'is_empty': True},
            'bookmark-end':  {'is_inline': False, 'is_empty': True},
            'bookmark-ref': {'is_inline': False, 'is_empty': True},
            'bookmark-start':  {'is_inline': False, 'is_empty': True},
            #'bullet-char'
            'change': {'is_inline': False, 'is_empty': True},
            'change-end': {'is_inline': False, 'is_empty': True},
            'change-start': {'is_inline': False, 'is_empty': True},
            'changed-region': {'is_inline': False, 'is_empty': False},
            'chapter': {'is_inline': False, 'is_empty': True},
            #'character-count'
            'conditional-text': {'is_inline': False, 'is_empty': True},
            'creation-date': {'is_inline': False, 'is_empty': True},
            'creation-time': {'is_inline': False, 'is_empty': True},
            'creator': {'is_inline': False, 'is_empty': True},
            'database-display': {'is_inline': False, 'is_empty': False},
            'database-name': {'is_inline': False, 'is_empty': False},
            'database-next': {'is_inline': False, 'is_empty': False},
            'database-row-number': {'is_inline': False, 'is_empty': False},
            'database-row-select': {'is_inline': False, 'is_empty': False},
            'date': {'is_inline': False, 'is_empty': True},
            #'date-value'
            'dde-connection': {'is_inline': False, 'is_empty': True},
            'dde-connection-decl': {'is_inline': False, 'is_empty': True},
            'dde-connection-decls': {'is_inline': False, 'is_empty': False},
            'deletion': {'is_inline': False, 'is_empty': False},
            'description': {'is_inline': False, 'is_empty': True},
            #'dont-balance-text-columns'
            'editing-cycles': {'is_inline': False, 'is_empty': True},
            'editing-duration': {'is_inline': False, 'is_empty': True},
            'execute-macro': {'is_inline': False, 'is_empty': False},
            'expression': {'is_inline': False, 'is_empty': True},
            'file-name': {'is_inline': False, 'is_empty': True},
            'format-change': {'is_inline': False, 'is_empty': False},
            'h': {'is_inline': False, 'is_empty': False},
            'hidden-paragraph': {'is_inline': False, 'is_empty': True},
            'hidden-text': {'is_inline': False, 'is_empty': True},
            'illustration-index': {'is_inline': False, 'is_empty': False},
            'illustration-index-entry-template': {'is_inline': False, 'is_empty': False},
            'illustration-index-source': {'is_inline': False, 'is_empty': False},
            #'image-count'
            'index-body': {'is_inline': False, 'is_empty': False},
            'index-entry-bibliography': {'is_inline': False, 'is_empty': True},
            'index-entry-chapter': {'is_inline': False, 'is_empty': True},
            'index-entry-link-end': {'is_inline': False, 'is_empty': True},
            'index-entry-link-start': {'is_inline': False, 'is_empty': True},
            'index-entry-page-number': {'is_inline': False, 'is_empty': True},
            'index-entry-span': {'is_inline': False, 'is_empty': True},
            'index-entry-tab-stop':{'is_inline': False, 'is_empty': True},
            'index-entry-text': {'is_inline': False, 'is_empty': True},
            'index-source-style': {'is_inline': False, 'is_empty': True},
            'index-source-styles': {'is_inline': False, 'is_empty': False},
            'index-title': {'is_inline': False, 'is_empty': False},
            'index-title-template': {'is_inline': False, 'is_empty': True},
            'initial-creator': {'is_inline': False, 'is_empty': True},
            'insertion': {'is_inline': False, 'is_empty': False},
            'keywords': {'is_inline': False, 'is_empty': True},
            #'level'
            'line-break': {'is_inline': False, 'is_empty': True},
            'linenumbering-configuration': {'is_inline': False,
                                            'is_empty': False},
            'linenumbering-separator': {'is_inline': False, 'is_empty': True},
            'list': {'is_inline': False, 'is_empty': False},
            'list-header':{'is_inline': False, 'is_empty': False},
            'list-item': {'is_inline': False, 'is_empty': False},
            'list-level-style-bullet': {'is_inline': False, 'is_empty': False},
            'list-level-style-image': {'is_inline': False, 'is_empty': False},
            'list-level-style-number': {'is_inline': False, 'is_empty': False},
            'list-style': {'is_inline': False, 'is_empty': False},
            'measure': {'is_inline': False, 'is_empty': True},
            #min-label-width
            'modification-date': {'is_inline': False, 'is_empty': True},
            'modification-time': {'is_inline': False, 'is_empty': True},
            'note': {'is_inline': False, 'is_empty': False},
            'note-body': {'is_inline': False, 'is_empty': False},
            'note-citation': {'is_inline': False, 'is_empty': True},
            'note-continuation-notice-backward': {'is_inline': False, 'is_empty': True},
            'note-continuation-notice-forward': {'is_inline': False, 'is_empty': True},
            'note-ref': {'is_inline': False, 'is_empty': True},
            'notes-configuration': {'is_inline': False, 'is_empty': False},
            'number': {'is_inline': False, 'is_empty': True},
            'numbered-paragraph': {'is_inline': False, 'is_empty': False},
            'object-count': {'is_inline': False, 'is_empty': True},
            'object-index': {'is_inline': False, 'is_empty': False},
            'object-index-entry-template': {'is_inline': False, 'is_empty': False},
            'object-index-source': {'is_inline': False, 'is_empty': False},
            'outline-level-style': {'is_inline': False, 'is_empty': False},
            'outline-style': {'is_inline': False, 'is_empty': False},
            'p': {'is_inline': False, 'is_empty': False},
            'page': {'is_inline': False, 'is_empty': True},
            'page-continuation': {'is_inline': False, 'is_empty': True},
            #'page-count'
            'page-number': {'is_inline': False, 'is_empty': True},
            'page-sequence': {'is_inline': False, 'is_empty': False},
            'page-variable-get': {'is_inline': False, 'is_empty': True},
            'page-variable-set': {'is_inline': False, 'is_empty': True},
            #'paragraph-count'
            'placeholder': {'is_inline': False, 'is_empty': True},
            'print-date': {'is_inline': False, 'is_empty': True},
            'print-time': {'is_inline': False, 'is_empty': True},
            'printed-by': {'is_inline': False, 'is_empty': True},
            'reference-mark': {'is_inline': False, 'is_empty': True},
            'reference-mark-end': {'is_inline': False, 'is_empty': True},
            'reference-mark-start': {'is_inline': False, 'is_empty': True},
            'reference-ref': {'is_inline': False, 'is_empty': False},
            'ruby': {'is_inline': False, 'is_empty': False},
            'ruby-base': {'is_inline': False, 'is_empty': False},
      #'ruby-text':
            's': {'is_inline': False, 'is_empty': True},
            'script': {'is_inline': False, 'is_empty': True},
            'section': {'is_inline': False, 'is_empty': False},
            'section-source': {'is_inline': False, 'is_empty': True},
            'sender-city': {'is_inline': False, 'is_empty': True},
            'sender-company': {'is_inline': False, 'is_empty': True},
            'sender-country': {'is_inline': False, 'is_empty': True},
            'sender-email': {'is_inline': False, 'is_empty': True},
            'sender-fax': {'is_inline': False, 'is_empty': True},
            'sender-firstname': {'is_inline': False, 'is_empty': True},
            'sender-initials': {'is_inline': False, 'is_empty': True},
            'sender-lastname': {'is_inline': False, 'is_empty': True},
            'sender-phone-private': {'is_inline': False, 'is_empty': True},
            'sender-phone-work': {'is_inline': False, 'is_empty': True},
            'sender-position': {'is_inline': False, 'is_empty': True},
            'sender-postal-code': {'is_inline': False, 'is_empty': True},
            'sender-state-or-province': {'is_inline': False, 'is_empty': True},
            'sender-street': {'is_inline': False, 'is_empty': True},
            'sender-title': {'is_inline': False, 'is_empty': True},
            'sequence': {'is_inline': False, 'is_empty': True,
                         'translate_content': False},
            'sequence-decl':  {'is_inline': False, 'is_empty': True},
            'sequence-decls': {'is_inline': False, 'is_empty': False},
            'sequence-ref': {'is_inline': False, 'is_empty': True},
            'sheet-name': {'is_inline': False, 'is_empty': True},
            'sort-key': {'is_inline': False, 'is_empty': True},
            #'space-before'
            'span': {'is_inline': True, 'is_empty': False},
            #'style-name'
            'subject': {'is_inline': False, 'is_empty': True},
            'tab': {'is_inline': False, 'is_empty': True},
            #'table-count'
            'table-formula': {'is_inline': False, 'is_empty': True},
            'table-index': {'is_inline': False, 'is_empty': False},
            'table-index-entry-template': {'is_inline': False, 'is_empty': False},
            'table-index-source': {'is_inline': False, 'is_empty': False},
            'table-of-content': {'is_inline': False, 'is_empty': False},
            'table-of-content-entry-template': {'is_inline': False, 'is_empty': False},
            'table-of-content-source': {'is_inline': False, 'is_empty': False},
            'template-name': {'is_inline': False, 'is_empty': True},
            'text-input': {'is_inline': False, 'is_empty': True},
            'time': {'is_inline': False, 'is_empty': True},
            #'time-value'
            'title': {'is_inline': False, 'is_empty': False},
            'toc-mark': {'is_inline': False, 'is_empty': True},
            'toc-mark-end': {'is_inline': False, 'is_empty': True},
            'toc-mark-start': {'is_inline': False, 'is_empty': True},
            'tracked-changes': {'is_inline': False, 'is_empty': False},
            'user-defined': {'is_inline': False, 'is_empty': True},
            'user-field-decl': {'is_inline': False, 'is_empty': True},
            'user-field-decls': {'is_inline': False, 'is_empty': False},
            'user-field-get':  {'is_inline': False, 'is_empty': True},
            'user-field-input': {'is_inline': False, 'is_empty': True},
            'user-index': {'is_inline': False, 'is_empty': False},
            'user-index-entry-template': {'is_inline': False, 'is_empty': False},
            'user-index-mark': {'is_inline': False, 'is_empty': True},
            'user-index-mark-end': {'is_inline': False, 'is_empty': True},
            'user-index-mark-start': {'is_inline': False, 'is_empty': True},
            'user-index-source': {'is_inline': False, 'is_empty': False},
            'variable-decl': {'is_inline': False, 'is_empty': True},
            'variable-decls': {'is_inline': False, 'is_empty': False},
            'variable-get': {'is_inline': False, 'is_empty': True},
            'variable-input': {'is_inline': False, 'is_empty': True},
            'variable-set': {'is_inline': False, 'is_empty': True},
            #'word-count'
        }
        default_schema = {'is_empty': False, 'is_inline': False}
        return elements_schema.get(name, default_schema)

set_namespace(OdtTextNamespace)


class OdtTextSchema(BaseSchema):

    class_uri = 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'
    class_prefix = 'text'

    datatypes = {'style-name': Unicode}

    @classmethod
    def get_datatype(cls, name):
        return cls.datatypes.get(name, Unicode)

register_schema(OdtTextSchema)



########################################################################
############ urn:oasis:names:tc:opendocument:xmlns:office:1.0 ##########
########################################################################


class OdtOfficeNamespace(AbstractNamespace):

    class_uri = 'urn:oasis:names:tc:opendocument:xmlns:office:1.0'
    class_prefix = 'office'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {
            'annotation': {'is_inline': False, 'is_empty': False},
            'automatic-styles': {'is_inline': False, 'is_empty': False},
            'binary-data': {'is_inline': False, 'is_empty': True},
            'body': {'is_inline': False, 'is_empty': False},
            'change-info': {'is_inline': False, 'is_empty': False},
            'chart': {'is_inline': False, 'is_empty': False},
            'dde-source': {'is_inline': False, 'is_empty': True},
            'document': {'is_inline': False, 'is_empty': False},
            'document-content': {'is_inline': False, 'is_empty': False},
            'document-meta': {'is_inline': False, 'is_empty': False},
            'document-settings': {'is_inline': False, 'is_empty': False},
            'document-styles': {'is_inline': False, 'is_empty': False},
            'drawing': {'is_inline': False, 'is_empty': False},
            'event-listeners': {'is_inline': False, 'is_empty': False},
            'font-face-decls': {'is_inline': False, 'is_empty': False},
            'forms': {'is_inline': False, 'is_empty': False},
            'image': {'is_inline': False, 'is_empty': False},
            'master-styles': {'is_inline': False, 'is_empty': False},
            'meta': {'is_inline': False, 'is_empty': False},
            'presentation': {'is_inline': False, 'is_empty': False},
            'script': {'is_inline': False, 'is_empty': False},
            'scripts': {'is_inline': False, 'is_empty': False},
            'settings': {'is_inline': False, 'is_empty': False},
            'spreadsheet': {'is_inline': False, 'is_empty': False},
            'styles': {'is_inline': False, 'is_empty': False},
            'text': {'is_inline': False, 'is_empty': False}
            }
        default_schema = {'is_empty': False, 'is_inline': False}
        return elements_schema.get(name, default_schema)

set_namespace(OdtOfficeNamespace)



class OdtOfficeSchema(BaseSchema):

    class_uri = 'urn:oasis:names:tc:opendocument:xmlns:office:1.0'
    class_prefix = 'office'

    datatypes = {'version': Unicode}

    @classmethod
    def get_datatype(cls, name):
        return cls.datatypes.get(name, Unicode)

register_schema(OdtOfficeSchema)



########################################################################
############ urn:oasis:names:tc:opendocument:xmlns:style:1.0  ##########
########################################################################


class OdtStyleNamespace(AbstractNamespace):

    class_uri = 'urn:oasis:names:tc:opendocument:xmlns:style:1.0'
    class_prefix = 'style'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {
            'background-image': {'is_inline': False, 'is_empty': False},
            #'border-line-width
            'chart-properties': {'is_inline': False, 'is_empty': False},
            'column': {'is_inline': False, 'is_empty': True},
            'column-sep': {'is_inline': False, 'is_empty': True},
            #'column-width
            'columns': {'is_inline': False, 'is_empty': False},
            'default-style': {'is_inline': False, 'is_empty': False},
            #'display-name
            'drawing-page-properties': {'is_inline': False, 'is_empty': False},
            'drop-cap': {'is_inline': False, 'is_empty': True},
            #'family
            #'family-properties
            #'first-page-number
            #'font-decl
            'font-face': {'is_inline': False, 'is_empty': False},
            #'font-name
            #'font-relief
            'footer': {'is_inline': False, 'is_empty': False},
            'footer-left': {'is_inline': False, 'is_empty': False},
            'footer-style': {'is_inline': False, 'is_empty': False},
            #'footnote-max-height
            'footnote-sep': {'is_inline': False, 'is_empty': True},
            'graphic-properties': {'is_inline': False, 'is_empty': False},
            'handout-master': {'is_inline': False, 'is_empty': False},
            'header': {'is_inline': False, 'is_empty': False},
            'header-footer-properties': {'is_inline': False, 'is_empty': False},
            'header-left': {'is_inline': False, 'is_empty': False},
            'header-style': {'is_inline': False, 'is_empty': False},
            #'horizontal-pos
            #'horizontal-rel
            #'leader-text
            #'line-spacing
            'list-level-properties': {'is_inline': False, 'is_empty': True},
            'map': {'is_inline': False, 'is_empty': True},
            'master-page': {'is_inline': False, 'is_empty': False},
            #'may-break-between-rows
            #'min-row-height
            #'mirror
            #'name
            #'num-format
            #'number-wrapped-paragraphs
            'page-layout': {'is_inline': False, 'is_empty': False},
            'page-layout-properties': {'is_inline': False, 'is_empty': False},
            'paragraph-properties': {'is_inline': False, 'is_empty': False},
            #'position
            'presentation-page-layout': {'is_inline': False, 'is_empty': False},
            #'print
            #'print-orientation
            #'print-page-order
            'region-center': {'is_inline': False, 'is_empty': False},
            'region-left': {'is_inline': False, 'is_empty': False},
            'region-right': {'is_inline': False, 'is_empty': False},
            #'rel-column-width
            #'rel-width
            #'repeat
            #'row-height
            'ruby-properties': {'is_inline': False, 'is_empty': True},
            #'scale-to
            'section-properties': {'is_inline': False, 'is_empty': False},
            'style': {'is_inline': False, 'is_empty': False},
            'tab-stop': {'is_inline': False, 'is_empty': True},
            'tab-stops': {'is_inline': False, 'is_empty': False},
            'table': {'is_inline': False, 'is_empty': False},
            'table-cell': {'is_inline': False, 'is_empty': False},
            'table-cell-properties': {'is_inline': False, 'is_empty': True},
            'table-column': {'is_inline': False, 'is_empty': True},
            'table-column-properties': {'is_inline': False, 'is_empty': True},
            'table-header-rows': {'is_inline': False, 'is_empty': False},
            'table-properties': {'is_inline': False, 'is_empty': False},
            'table-row': {'is_inline': False, 'is_empty': False},
            'table-row-properties': {'is_inline': False, 'is_empty': False},
            #'text-blinking
            #'text-outline
            #'text-position
            #'text-propertie
            'text-properties': {'is_inline': False, 'is_empty': True},
            #'text-rotation-angle
            #'text-scale
            #'text-underline-style
            #'use-optimal-row-height
            #'vertical-pos
            #'vertical-rel
            #'wrap
        }
        default_schema = {'is_empty': False, 'is_inline': False}
        return elements_schema.get(name, default_schema)

set_namespace(OdtStyleNamespace)



class OdtStyleSchema(BaseSchema):

    class_uri = 'urn:oasis:names:tc:opendocument:xmlns:style:1.0'
    class_prefix = 'style'

    datatypes = {'name': Unicode}

    @classmethod
    def get_datatype(cls, name):
        return cls.datatypes.get(name, Unicode)

register_schema(OdtStyleSchema)



########################################################################
############ urn:oasis:names:tc:opendocument:xmlns:table:1.0  ##########
########################################################################


class OdtTableNamespace(AbstractNamespace):

    class_uri = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
    class_prefix = 'table'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {
            #'align'
            'body': {'is_inline': False, 'is_empty': True},
            'calculation-settings': {'is_inline': False, 'is_empty': False},
            'cell-adress': {'is_inline': False, 'is_empty': True},
            'cell-content-change': {'is_inline': False, 'is_empty': False},
            'cell-content-deletion': {'is_inline': False, 'is_empty': False},
            'cell-range-source': {'is_inline': False, 'is_empty': True},
            'change-deletion': {'is_inline': False, 'is_empty': True},
            'change-track-table-cell': {'is_inline': False, 'is_empty': False},
            'consolidation': {'is_inline': False, 'is_empty': True},
            'content-validation': {'is_inline': False, 'is_empty': False},
            'content-validations': {'is_inline': False, 'is_empty': False},
            'covered-table-cell': {'is_inline': False, 'is_empty': True},
            'cut-offs': {'is_inline': False, 'is_empty': False},
            'data-pilot-display-info': {'is_inline': False, 'is_empty': True},
            'data-pilot-field': {'is_inline': False, 'is_empty': False},
            'data-pilot-field-reference': {'is_inline': False, 'is_empty': True},
            'data-pilot-group': {'is_inline': False, 'is_empty': False},
            'data-pilot-group-member': {'is_inline': False, 'is_empty': True},
            'data-pilot-groups': {'is_inline': False, 'is_empty': False},
            'data-pilot-layout-info': {'is_inline': False, 'is_empty': True},
            'data-pilot-level': {'is_inline': False, 'is_empty': False},
            'data-pilot-member': {'is_inline': False, 'is_empty': True},
            'data-pilot-members': {'is_inline': False, 'is_empty': False},
            'data-pilot-sort-info': {'is_inline': False, 'is_empty': True},
            'data-pilot-subtotal': {'is_inline': False, 'is_empty': True},
            'data-pilot-subtotals': {'is_inline': False, 'is_empty': False},
            'data-pilot-table': {'is_inline': False, 'is_empty': False},
            'data-pilot-tables': {'is_inline': False, 'is_empty': False},
            'database-range': {'is_inline': False, 'is_empty': False},
            'database-ranges': {'is_inline': False, 'is_empty': False},
            'database-source-query': {'is_inline': False, 'is_empty': True},
            'database-source-sql': {'is_inline': False, 'is_empty': True},
            'database-source-table': {'is_inline': False, 'is_empty': True},
            'dde-link': {'is_inline': False, 'is_empty': False},
            'dde-links': {'is_inline': False, 'is_empty': False},
            'deletion': {'is_inline': False, 'is_empty': False},
            'deletions': {'is_inline': False, 'is_empty': False},
            'dependencies': {'is_inline': False, 'is_empty': False},
            'dependency': {'is_inline': False, 'is_empty': True},
            'detective': {'is_inline': False, 'is_empty': False},
            #'end-cell-address'
            #'end-x/y'
            'error-macro': {'is_inline': False, 'is_empty': True},
            'error-message': {'is_inline': False, 'is_empty': False},
            'even-columns': {'is_inline': False, 'is_empty': True},
            'even-rows': {'is_inline': False, 'is_empty': True},
            'filter': {'is_inline': False, 'is_empty': False},
            'filter-and': {'is_inline': False, 'is_empty': False},
            'filter-condition': {'is_inline': False, 'is_empty': True},
            'filter-or': {'is_inline': False, 'is_empty': False},
            'first-column': {'is_inline': False, 'is_empty': True},
            'first-row': {'is_inline': False, 'is_empty': True},
            'help-message': {'is_inline': False, 'is_empty': False},
            'highlighted-range': {'is_inline': False, 'is_empty': True},
            'insertion': {'is_inline': False, 'is_empty': False},
            'insertion-cut-off': {'is_inline': False, 'is_empty': True},
            'iteration': {'is_inline': False, 'is_empty': True},
            'label-range': {'is_inline': False, 'is_empty': True},
            'label-ranges': {'is_inline': False, 'is_empty': False},
            'last-column': {'is_inline': False, 'is_empty': True},
            'last-row': {'is_inline': False, 'is_empty': True},
            'movement': {'is_inline': False, 'is_empty': False},
            'movement-cut-off': {'is_inline': False, 'is_empty': True},
            'named-expression': {'is_inline': False, 'is_empty': True},
            'named-expressions': {'is_inline': False, 'is_empty': False},
            'named-range': {'is_inline': False, 'is_empty': True},
            'null-date': {'is_inline': False, 'is_empty': True},
            'odd-columns': {'is_inline': False, 'is_empty': True},
            'odd-rows': {'is_inline': False, 'is_empty': True},
            'operation': {'is_inline': False, 'is_empty': True},
            'previous': {'is_inline': False, 'is_empty': False},
            'scenario': {'is_inline': False, 'is_empty': True},
            'shapes': {'is_inline': False, 'is_empty': False},
            'sort': {'is_inline': False, 'is_empty': False},
            'sort-by': {'is_inline': False, 'is_empty': True},
            'sort-groups': {'is_inline': False, 'is_empty': True},
            'source-cell-range': {'is_inline': False, 'is_empty': False},
            'source-range-address': {'is_inline': False, 'is_empty': True},
            'source-service': {'is_inline': False, 'is_empty': True},
            'subtotal-field': {'is_inline': False, 'is_empty': True},
            'subtotal-rule': {'is_inline': False, 'is_empty': False},
            'subtotal-rules': {'is_inline': False, 'is_empty': False},
            'table': {'is_inline': False, 'is_empty': False},
            'table-cell': {'is_inline': False, 'is_empty': False},
            'table-column': {'is_inline': False, 'is_empty': True},
            'table-column-group': {'is_inline': False, 'is_empty': False},
            'table-columns': {'is_inline': False, 'is_empty': False},
            'table-header-columns': {'is_inline': False, 'is_empty': False},
            'table-header-rows': {'is_inline': False, 'is_empty': False},
            'table-row': {'is_inline': False, 'is_empty': False},
            'table-row-group': {'is_inline': False, 'is_empty': False},
            'table-rows': {'is_inline': False, 'is_empty': False},
            'table-source': {'is_inline': False, 'is_empty': True},
            'table-template': {'is_inline': False, 'is_empty': False},
            'target-range-address': {'is_inline': False, 'is_empty': True},
            'tracked-changes': {'is_inline': False, 'is_empty': False}
        }
        default_schema = {'is_empty': False, 'is_inline': False}
        return elements_schema.get(name, default_schema)

set_namespace(OdtTableNamespace)



class OdtTableSchema(BaseSchema):

    class_uri = 'urn:oasis:names:tc:opendocument:xmlns:table:1.0'
    class_prefix = 'table'

    datatypes = {}

    @classmethod
    def get_datatype(cls, name):
        return cls.datatypes.get(name, Unicode)

register_schema(OdtTableSchema)



########################################################################
############ urn:oasis:names:tc:opendocument:xmlns:drawing:1.0  ########
########################################################################

class OdtDrawingNamespace(AbstractNamespace):

    class_uri = "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
    class_prefix = 'draw'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {
            'a': {'is_inline': False, 'is_empty': False},
            'applet': {'is_inline': False, 'is_empty': False},
            'area-circle': {'is_inline': False, 'is_empty': False},
            'area-polygon': {'is_inline': False, 'is_empty': False},
            'area-rectangle': {'is_inline': False, 'is_empty': False},
            'caption': {'is_inline': False, 'is_empty': False},
            'circle': {'is_inline': False, 'is_empty': False},
            'connector': {'is_inline': False, 'is_empty': False},
            'contour-path': {'is_inline': False, 'is_empty': True},
            'contour-polygon': {'is_inline': False, 'is_empty': True},
            'control': {'is_inline': False, 'is_empty': False},
            'custom-shape': {'is_inline': False, 'is_empty': False},
            'ellipse': {'is_inline': False, 'is_empty': False},
            'enhanced-geometry': {'is_inline': False, 'is_empty': False},
            'equation': {'is_inline': False, 'is_empty': True},
            'fill-image': {'is_inline': False, 'is_empty': True},
            'floating-frame': {'is_inline': False, 'is_empty': True},
            'frame': {'is_inline': False, 'is_empty': False},
            'g': {'is_inline': False, 'is_empty': False},
            'glue-point': {'is_inline': False, 'is_empty': True},
            'gradient': {'is_inline': False, 'is_empty': True},
            'handle': {'is_inline': False, 'is_empty': True},
            'hatch': {'is_inline': False, 'is_empty': True},
            'image': {'is_inline': False, 'is_empty': False},
            'image-map': {'is_inline': False, 'is_empty': False},
            'layer': {'is_inline': False, 'is_empty': True},
            'layer-set': {'is_inline': False, 'is_empty': False},
            'line': {'is_inline': False, 'is_empty': False},
            'marker': {'is_inline': False, 'is_empty': True},
            'measure': {'is_inline': False, 'is_empty': False},
            'object': {'is_inline': False, 'is_empty': False},
            'object-ole': {'is_inline': False, 'is_empty': False},
            'opacity': {'is_inline': False, 'is_empty': True},
            'page': {'is_inline': False, 'is_empty': False},
            'page-thumbnail': {'is_inline': False, 'is_empty': True},
            'param': {'is_inline': False, 'is_empty': True},
            'path': {'is_inline': False, 'is_empty': False},
            'plugin': {'is_inline': False, 'is_empty': False},
            'polygon': {'is_inline': False, 'is_empty': False},
            'polyline': {'is_inline': False, 'is_empty': False},
            'rect': {'is_inline': False, 'is_empty': False},
            'regular-polygon': {'is_inline': False, 'is_empty': False},
            'stroke-dash': {'is_inline': False, 'is_empty': True},
            'text-box': {'is_inline': False, 'is_empty': False},
        }
        default_schema = {'is_empty': False, 'is_inline': False}
        return elements_schema.get(name, default_schema)

set_namespace(OdtDrawingNamespace)



class OdtDrawingSchema(BaseSchema):

    class_uri = 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0'
    class_prefix = 'draw'

    datatypes = {}

    @classmethod
    def get_datatype(cls, name):
        return cls.datatypes.get(name, Unicode)

register_schema(OdtDrawingSchema)



################################################################################
############ urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0  ######
################################################################################

class OdtFoNamespace(AbstractNamespace):

    class_uri = "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
    class_prefix = 'fo'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {}
        default_schema = {'is_empty': False, 'is_inline': False}
        return elements_schema.get(name, default_schema)

set_namespace(OdtFoNamespace)



class OdtFoSchema(BaseSchema):

    class_uri = 'urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0'
    class_prefix = 'fo'

    datatypes = {}

    @classmethod
    def get_datatype(cls, name):
        return cls.datatypes.get(name, Unicode)

register_schema(OdtFoSchema)



###############################################################
######## urn:oasis:names:tc:opendocument:xmlns:meta:1.0  ######
###############################################################

class OdtMetaNamespace(AbstractNamespace):

    class_uri = "urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
    class_prefix = 'meta'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {
              'auto-reload': {'is_inline': False, 'is_empty': True},
              'creation-date': {'is_inline': False, 'is_empty': True},
              'date-string': {'is_inline': False, 'is_empty': True},
              'document-statistic': {'is_inline': False, 'is_empty': True},
              'editing-cycles': {'is_inline': False, 'is_empty': True},
              'editing-duration': {'is_inline': False, 'is_empty': True},
              'generator': {'is_inline': False, 'is_empty': True},
              'hyperlink-behaviour': {'is_inline': False, 'is_empty': True},
              'initial-creator': {'is_inline': False, 'is_empty': True},
              'keyword': {'is_inline': False, 'is_empty': True},
              'print-date': {'is_inline': False, 'is_empty': True},
              'printed-by': {'is_inline': False, 'is_empty': True},
              'template': {'is_inline': False, 'is_empty': True},
              'user-defined': {'is_inline': False, 'is_empty': True}
              }
        default_schema = {'is_empty': False, 'is_inline': False}
        return elements_schema.get(name, default_schema)

set_namespace(OdtMetaNamespace)



class OdtMetaSchema(BaseSchema):

    class_uri = 'urn:oasis:names:tc:opendocument:xmlns:meta:1.0'
    class_prefix = 'meta'

    datatypes = {}

    @classmethod
    def get_datatype(cls, name):
        return cls.datatypes.get(name, Unicode)

register_schema(OdtMetaSchema)



#########################################################################
######## urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0  ######
#########################################################################


class OdtSvgNamespace(AbstractNamespace):

    class_uri = "urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"
    class_prefix = 'svg'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {
            'definition-src': {'is_inline': False, 'is_empty': True},
            'desc': {'is_inline': False, 'is_empty': True},
            'font-face-format': {'is_inline': False, 'is_empty': True},
            'font-face-name': {'is_inline': False, 'is_empty': True},
            'font-face-src': {'is_inline': False, 'is_empty': False},
            'font-face-uri': {'is_inline': False, 'is_empty': False},
            'linearGradient': {'is_inline': False, 'is_empty': False},
            'radialGradient': {'is_inline': False, 'is_empty': False},
            'stop': {'is_inline': False, 'is_empty': False}
        }
        default_schema = {'is_empty': False, 'is_inline': False}
        return elements_schema.get(name, default_schema)

set_namespace(OdtSvgNamespace)



class OdtSvgSchema(BaseSchema):

    class_uri = "urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"
    class_prefix = 'svg'

    datatypes = {}

    @classmethod
    def get_datatype(cls, name):
        return cls.datatypes.get(name, Unicode)

register_schema(OdtSvgSchema)



################################################################
######## urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0   ######
################################################################

class OdtDr3dNamespace(AbstractNamespace):

    class_uri = "urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0"
    class_prefix = 'dr3d'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {
            'cube': {'is_inline': False, 'is_empty': False},
            'extrude': {'is_inline': False, 'is_empty': True},
            'light': {'is_inline': False, 'is_empty': True},
            'rotate': {'is_inline': False, 'is_empty': True},
            'scene': {'is_inline': False, 'is_empty': False},
            'sphere': {'is_inline': False, 'is_empty': True}
        }
        default_schema = {'is_empty': False, 'is_inline': False}
        return elements_schema.get(name, default_schema)

set_namespace(OdtDr3dNamespace)



class OdtDr3dSchema(BaseSchema):

    class_uri = "urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0"
    class_prefix = 'dr3d'

    datatypes = {}

    @classmethod
    def get_datatype(cls, name):
        return cls.datatypes.get(name, Unicode)

register_schema(OdtDr3dSchema)



#############################################################
######## urn:oasis:names:tc:opendocument:xmlns:form:1.0  ####
#############################################################

class OdtFormNamespace(AbstractNamespace):

    class_uri = "urn:oasis:names:tc:opendocument:xmlns:form:1.0"
    class_prefix = 'form'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {
            'button': {'is_inline': False, 'is_empty': False},
            'checkbox': {'is_inline': False, 'is_empty': False},
            'column': {'is_inline': False, 'is_empty': False},
            'combobox': {'is_inline': False, 'is_empty': False},
            'connection-resource': {'is_inline': False, 'is_empty': True},
            'date': {'is_inline': False, 'is_empty': False},
            'file': {'is_inline': False, 'is_empty': False},
            'fixed-text': {'is_inline': False, 'is_empty': False},
            'form': {'is_inline': False, 'is_empty': False},
            'formatted-text': {'is_inline': False, 'is_empty': False},
            'frame': {'is_inline': False, 'is_empty': False},
            'generic-control': {'is_inline': False, 'is_empty': False},
            'grid': {'is_inline': False, 'is_empty': False},
            'hidden': {'is_inline': False, 'is_empty': False},
            'image': {'is_inline': False, 'is_empty': False},
            'image-frame': {'is_inline': False, 'is_empty': False},
            'item': {'is_inline': False, 'is_empty': True},
            'list-property': {'is_inline': False, 'is_empty': False},
            'list-value': {'is_inline': False, 'is_empty': True},
            'listbox': {'is_inline': False, 'is_empty': False},
            'number': {'is_inline': False, 'is_empty': False},
            'option': {'is_inline': False, 'is_empty': True},
            'password': {'is_inline': False, 'is_empty': False},
            'properties': {'is_inline': False, 'is_empty': False},
            'property': {'is_inline': False, 'is_empty': True},
            'radio': {'is_inline': False, 'is_empty': False},
            'text': {'is_inline': False, 'is_empty': False},
            'textarea': {'is_inline': False, 'is_empty': False},
            'time': {'is_inline': False, 'is_empty': False},
            'value-range': {'is_inline': False, 'is_empty': False}
        }
        default_schema = {'is_empty': False, 'is_inline': False}
        return elements_schema.get(name, default_schema)

set_namespace(OdtFormNamespace)



class OdtFormSchema(BaseSchema):

    class_uri = "urn:oasis:names:tc:opendocument:xmlns:form:1.0"
    class_prefix = 'form'

    datatypes = {}

    @classmethod
    def get_datatype(cls, name):
        return cls.datatypes.get(name, Unicode)

register_schema(OdtFormSchema)



######################################################################
######   urn:oasis:names:tc:opendocument:xmlns:script:1.0     ########
######################################################################


class OdtScriptNamespace(AbstractNamespace):

    class_uri = "urn:oasis:names:tc:opendocument:xmlns:script:1.0"
    class_prefix = 'script'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {
            'event-listener': {'is_inline': False, 'is_empty': True}
        }
        default_schema = {'is_empty': False, 'is_inline': False}
        return elements_schema.get(name, default_schema)

set_namespace(OdtScriptNamespace)



class OdtScriptSchema(BaseSchema):

    class_uri =  "urn:oasis:names:tc:opendocument:xmlns:script:1.0"
    class_prefix = 'script'

    datatypes = {}

    @classmethod
    def get_datatype(cls, name):
        return cls.datatypes.get(name, Unicode)

register_schema(OdtScriptSchema)



################################################
######## http://openoffice.org/2004/office  ####
################################################

class OdtOooNamespace(AbstractNamespace):

    class_uri = "http://openoffice.org/2004/office"
    class_prefix = 'ooo'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {}
        default_schema = {'is_empty': False, 'is_inline': False}
        return elements_schema.get(name, default_schema)

set_namespace(OdtOooNamespace)



class OdtOooSchema(BaseSchema):

    class_uri = "http://openoffice.org/2004/office"
    class_prefix = 'ooo'

    datatypes = {}

    @classmethod
    def get_datatype(cls, name):
        return cls.datatypes.get(name, Unicode)

register_schema(OdtOooSchema)



################################################
######## http://openoffice.org/2004/writer  ####
################################################

class OdtWriterNamespace(AbstractNamespace):
    class_uri = "http://openoffice.org/2004/writer"
    class_prefix = 'ooow'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {}
        default_schema = {'is_empty': False, 'is_inline': False}
        return elements_schema.get(name, default_schema)

set_namespace(OdtWriterNamespace)



class OdtWriterSchema(BaseSchema):

    class_uri = "http://openoffice.org/2004/writer"
    class_prefix = 'ooow'

    datatypes = {}

    @classmethod
    def get_datatype(cls, name):
        return cls.datatypes.get(name, Unicode)

register_schema(OdtWriterSchema)



################################################
######## http://openoffice.org/2004/calc  ######
################################################

class OdtCalcNamespace(AbstractNamespace):
    class_uri = "http://openoffice.org/2004/calc"
    class_prefix = 'oooc'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {}
        default_schema = {'is_empty': False, 'is_inline': False}
        return elements_schema.get(name, default_schema)

set_namespace(OdtCalcNamespace)



class OdtCalcSchema(BaseSchema):

    class_uri = "http://openoffice.org/2004/calc"
    class_prefix = 'oooc'

    datatypes = {}

    @classmethod
    def get_datatype(cls, name):
        return cls.datatypes.get(name, Unicode)

register_schema(OdtCalcSchema)



#######################################################################
########  urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0 #########
#######################################################################


class OdtDataStyleNamespace(AbstractNamespace):

    class_uri = "urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0"
    class_prefix = 'number'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {
            'am-pm': {'is_inline': False, 'is_empty': True},
            'boolean': {'is_inline': False, 'is_empty': True},
            'boolean-style': {'is_inline': False, 'is_empty': False},
            'currency-style': {'is_inline': False, 'is_empty': False},
            'currency-symbol': {'is_inline': False, 'is_empty': True},
            'date-style': {'is_inline': False, 'is_empty': False},
            'day': {'is_inline': False, 'is_empty': True},
            'day-of-week': {'is_inline': False, 'is_empty': True},
            'embedded-text': {'is_inline': False, 'is_empty': True},
            'era': {'is_inline': False, 'is_empty': True},
            'fraction': {'is_inline': False, 'is_empty': True},
            'hours': {'is_inline': False, 'is_empty': True},
            'minutes': {'is_inline': False, 'is_empty': True},
            'month': {'is_inline': False, 'is_empty': True},
            'number': {'is_inline': False, 'is_empty': True},
            'number-style': {'is_inline': False, 'is_empty': False},
            'percentage-style': {'is_inline': False, 'is_empty': False},
            'quarter': {'is_inline': False, 'is_empty': True},
            'scientific-number': {'is_inline': False, 'is_empty': True},
            'seconds': {'is_inline': False, 'is_empty': True},
            'text': {'is_inline': False, 'is_empty': True},
            'text-content': {'is_inline': False, 'is_empty': True},
            'text-style': {'is_inline': False, 'is_empty': False},
            'time-style': {'is_inline': False, 'is_empty': False},
            'week-of-year': {'is_inline': False, 'is_empty': True},
            'year': {'is_inline': False, 'is_empty': True}
        }
        default_schema = {'is_empty': False, 'is_inline': False}
        return elements_schema.get(name, default_schema)

set_namespace(OdtDataStyleNamespace)



class OdtDataStyleSchema(BaseSchema):

    class_uri =  "urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0"
    class_prefix = 'number'

    datatypes = {}

    @classmethod
    def get_datatype(cls, name):
        return cls.datatypes.get(name, Unicode)

register_schema(OdtDataStyleSchema)



######################################################################
########  urn:oasis:names:tc:opendocument:xmlns:animation:1.0 #########
#######################################################################

class OdtAnimationNamespace(AbstractNamespace):

    class_uri = "urn:oasis:names:tc:opendocument:xmlns:animation:1.0"
    class_prefix = 'anim'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {
            'animate': {'is_inline': False, 'is_empty': True},
            'animateColor': {'is_inline': False, 'is_empty': True},
            'animateMotion': {'is_inline': False, 'is_empty': True},
            'animateTransform': {'is_inline': False, 'is_empty': True},
            'audio': {'is_inline': False, 'is_empty': True},
            'command': {'is_inline': False, 'is_empty': False},
            'iterate': {'is_inline': False, 'is_empty': False},
            'par': {'is_inline': False, 'is_empty':False},
            'param': {'is_inline': False, 'is_empty': True},
            'seq': {'is_inline': False, 'is_empty': False},
            'set': {'is_inline': False, 'is_empty': True},
            'transitionFilter': {'is_inline': False, 'is_empty': True}
        }
        default_schema = {'is_empty': False, 'is_inline': False}
        return elements_schema.get(name, default_schema)

set_namespace(OdtAnimationNamespace)



class OdtAnimationSchema(BaseSchema):

    class_uri =  "urn:oasis:names:tc:opendocument:xmlns:animation:1.0"
    class_prefix = 'anim'

    datatypes = {}

    @classmethod
    def get_datatype(cls, name):
        return cls.datatypes.get(name, Unicode)

register_schema(OdtAnimationSchema)



######################################################################
########  urn:oasis:names:tc:opendocument:xmlns:chart:1.0 #########
#######################################################################


class OdtChartNamespace(AbstractNamespace):

    class_uri = "urn:oasis:names:tc:opendocument:xmlns:chart:1.0"
    class_prefix = 'chart'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {
            'axis': {'is_inline': False, 'is_empty': False},
            'categories': {'is_inline': False, 'is_empty': True},
            'chart': {'is_inline': False, 'is_empty': False},
            'data-point': {'is_inline': False, 'is_empty': True},
            'domain': {'is_inline': False, 'is_empty': True},
            'error-indicator': {'is_inline': False, 'is_empty': True},
            'floor': {'is_inline': False, 'is_empty': True},
            'footer': {'is_inline': False, 'is_empty': False},
            'grid': {'is_inline': False, 'is_empty': True},
            'legend': {'is_inline': False, 'is_empty': True},
            'mean-value': {'is_inline': False, 'is_empty': True},
            'plot-area': {'is_inline': False, 'is_empty': False},
            'regression-curve': {'is_inline': False, 'is_empty': True},
            'series': {'is_inline': False, 'is_empty': False},
            'stock-gain-marker': {'is_inline': False, 'is_empty': True},
            'stock-loss-marker': {'is_inline': False, 'is_empty': True},
            'stock-range-line': {'is_inline': False, 'is_empty': True},
            'subtitle': {'is_inline': False, 'is_empty': False},
            'symbol-image': {'is_inline': False, 'is_empty': True},
            'title': {'is_inline': False, 'is_empty': False},
            'wall': {'is_inline': False, 'is_empty': True}
        }
        default_schema = {'is_empty': False, 'is_inline': False}
        return elements_schema.get(name, default_schema)

set_namespace(OdtChartNamespace)



class OdtChartSchema(BaseSchema):

    class_uri =  "urn:oasis:names:tc:opendocument:xmlns:chart:1.0"
    class_prefix = 'chart'

    datatypes = {}

    @classmethod
    def get_datatype(cls, name):
        return cls.datatypes.get(name, Unicode)

register_schema(OdtChartSchema)



######################################################################
######## urn:oasis:names:tc:opendocument:xmlns:config:1.0    #########
#######################################################################


class OdtConfigNamespace(AbstractNamespace):

    class_uri = "urn:oasis:names:tc:opendocument:xmlns:config:1.0"
    class_prefix = 'config'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {
            'config-item': {'is_inline': False, 'is_empty': True},
            'config-item-map-entry': {'is_inline': False, 'is_empty': False},
            'config-item-map-indexed': {'is_inline': False, 'is_empty': False},
            'config-item-map-named': {'is_inline': False, 'is_empty': False},
            'config-item-set': {'is_inline': False, 'is_empty': False}
        }
        default_schema = {'is_empty': False, 'is_inline': False}
        return elements_schema.get(name, default_schema)

set_namespace(OdtConfigNamespace)



class OdtConfigSchema(BaseSchema):

    class_uri =  "urn:oasis:names:tc:opendocument:xmlns:config:1.0"
    class_prefix = 'config'

    datatypes = {}

    @classmethod
    def get_datatype(cls, name):
        return cls.datatypes.get(name, Unicode)

register_schema(OdtConfigSchema)



######################################################################
######## urn:oasis:names:tc:opendocument:xmlns:manifest:1.0    #########
#######################################################################


class OdtManifestNamespace(AbstractNamespace):

    class_uri = "urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"
    class_prefix = 'manifest'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {
            'algorithm': {'is_inline': False, 'is_empty': True},
            'encryption-data': {'is_inline': False, 'is_empty': False},
            'file-entry': {'is_inline': False, 'is_empty': False},
            'key-derivation': {'is_inline': False, 'is_empty': True},
            'manifest': {'is_inline': False, 'is_empty': False}
        }
        default_schema = {'is_empty': False, 'is_inline': False}
        return elements_schema.get(name, default_schema)

set_namespace(OdtManifestNamespace)



class OdtManifestSchema(BaseSchema):

    class_uri =  "urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"
    class_prefix = 'manifest'

    datatypes = {}

    @classmethod
    def get_datatype(cls, name):
        return cls.datatypes.get(name, Unicode)

register_schema(OdtManifestSchema)



######################################################################
###### urn:oasis:names:tc:opendocument:xmlns:presentation:1.0 ########
######################################################################


class OdtPresentationNamespace(AbstractNamespace):

    class_uri = "urn:oasis:names:tc:opendocument:xmlns:presentation:1.0"
    class_prefix = 'presentation'

    @staticmethod
    def get_element_schema(name):
        elements_schema = {
            'animation-group': {'is_inline': False, 'is_empty': False},
            'animations': {'is_inline': False, 'is_empty': False},
            'date-time': {'is_inline': False, 'is_empty': True},
            'date-time-decl': {'is_inline': False, 'is_empty': True},
            'dim': {'is_inline': False, 'is_empty': False},
            'event-listener': {'is_inline': False, 'is_empty': False},
            'footer': {'is_inline': False, 'is_empty': True},
            'footer-decl': {'is_inline': False, 'is_empty': True},
            'header': {'is_inline': False, 'is_empty': True},
            'header-decl': {'is_inline': False, 'is_empty': True},
            'hide-shape': {'is_inline': False, 'is_empty': False},
            'hide-text': {'is_inline': False, 'is_empty': False},
            'notes': {'is_inline': False, 'is_empty': False},
            'placeholder': {'is_inline': False, 'is_empty': True},
            'play': {'is_inline': False, 'is_empty': True},
            'settings': {'is_inline': False, 'is_empty': False},
            'show': {'is_inline': False, 'is_empty': True},
            'show-shape': {'is_inline': False, 'is_empty': False},
            'show-text': {'is_inline': False, 'is_empty': False},
            'sound': {'is_inline': False, 'is_empty': True}
        }
        default_schema = {'is_empty': False, 'is_inline': False}
        return elements_schema.get(name, default_schema)

set_namespace(OdtPresentationNamespace)



class OdtPresentationSchema(BaseSchema):

    class_uri =  "urn:oasis:names:tc:opendocument:xmlns:presentation:1.0"
    class_prefix = 'presentation'

    datatypes = {}

    @classmethod
    def get_datatype(cls, name):
        return cls.datatypes.get(name, Unicode)

register_schema(OdtPresentationSchema)



#########################################################################
###### urn:oasis:names:tc:opendocument:xmlns:smil-compatible:1.0 ########
#########################################################################


class OdtSmilNamespace(AbstractNamespace):

    class_uri = "urn:oasis:names:tc:opendocument:xmlns:smil-compatible:1.0"
    class_prefix = 'smil'

    @staticmethod
    def get_element_schema(name):
        default_schema = {'is_empty': False, 'is_inline': False}
        return elements_schema.get(name, default_schema)

set_namespace(OdtSmilNamespace)



class OdtSmilSchema(BaseSchema):

    class_uri =  "urn:oasis:names:tc:opendocument:xmlns:smil-compatible:1.0"
    class_prefix = 'smil'

    datatypes = {}

    @classmethod
    def get_datatype(cls, name):
        return cls.datatypes.get(name, Unicode)

register_schema(OdtSmilSchema)
