# -*- coding: UTF-8 -*-
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

# Import from python
from re import match, compile, DOTALL, MULTILINE

# Import from itools
from itools.xml import XMLParser, XML_DECL, START_ELEMENT, END_ELEMENT, TEXT
from itools.handlers import TextFile, register_handler_class


class SRXFile(TextFile):
    """ A handler for the Segmentation Rules eXchange format (SRX)
    """

    class_mimetypes = ['text/x-srx']
    class_extension = 'srx'


    def _load_state_from_file(self, file):
        # Default values
        encoding = 'utf-8'
        self.header = {'segmentsubflows': True,
                       'cascade': None,
                       'formathandle_start': False,
                       'formathandle_end': True,
                       'formathandle_isolated': False}
        self.language_rules = {}
        self.map_rules = []

        srx_uri = 'http://www.lisa.org/srx20'

        for type, value, line in XMLParser(file.read()):
            if type == XML_DECL:
                encoding = value[1]
            elif type == START_ELEMENT:
                tag_uri, tag_name, attrs = value
                if tag_uri == srx_uri:
                    # header
                    if tag_name == 'header':
                        # segmentsubflows
                        segmentsubflows = attrs[None, 'segmentsubflows']
                        self.header['segmentsubflows'] =\
                            segmentsubflows.lower() != 'no'
                        # cascade
                        cascade = attrs[None, 'cascade']
                        self.header['cascade'] = cascade.lower() != 'no'
                    # formathandle
                    elif tag_name == 'formathandle':
                        type_value = attrs[None, 'type']
                        include = attrs[None, 'include']
                        include = include.lower() != 'no'
                        self.header['formathandle_'+type_value] = include
                    # languagerule
                    elif tag_name == 'languagerule':
                        languagerulename = unicode(
                                            attrs[None, 'languagerulename'],
                                            encoding)
                        current_language =\
                            self.language_rules[languagerulename] = []
                    # rule
                    elif tag_name == 'rule':
                        current_break = True
                        current_before_break = None
                        current_after_break = None
                        if (None, 'break') in attrs:
                            break_value = attrs[None, 'break']
                            current_break = break_value.lower() != 'no'
                    # languagemap
                    elif tag_name == 'languagemap':
                        languagepattern = unicode(
                            attrs[None, 'languagepattern'], encoding)
                        languagerulename= unicode(
                            attrs[None, 'languagerulename'], encoding)
                        self.map_rules.append((languagepattern,
                                              languagerulename))
                current_text = u''
            elif type == TEXT:
                current_text = unicode(value, encoding)
            elif type == END_ELEMENT:
                tag_uri, tag_name = value
                if tag_uri == srx_uri:
                    # beforebreak
                    if tag_name == 'beforebreak':
                        current_before_break = current_text
                    # afterbreak
                    if tag_name == 'afterbreak':
                        current_after_break = current_text
                    # rule
                    if tag_name == 'rule':
                        current_language.append((current_break,
                            current_before_break, current_after_break))

    #########################################################################
    # API
    #########################################################################
    def get_compiled_rules(self, language):
        result = []
        for rule in self.get_rules(language):
            break_value, before_break, after_break = rule
            regexp = before_break or '.*?'
            if after_break:
                regexp += '(?=%s)' % after_break
            regexp = compile(regexp, DOTALL | MULTILINE)
            result.append((break_value, regexp))
        return result


    def get_languages(self):
        return self.language_rules.keys()


    def get_rules(self, language):
        language_rules = self.language_rules
        cascade = self.header['cascade']

        result = []
        for pattern, lang in self.map_rules:
            if match(pattern, language, DOTALL | MULTILINE):
                if cascade:
                    result.extend(language_rules[lang])
                else:
                    return language_rules[lang]
        return result


register_handler_class(SRXFile)


