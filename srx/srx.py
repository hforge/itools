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
from re import match, compile
# DOTALL is very important to be SRX compliant
from re import S as DOTALL

# Import from itools
from itools.xml import XMLParser, START_ELEMENT, END_ELEMENT, TEXT
from itools.handlers import TextFile, register_handler_class


class SRXFile(TextFile):
    """
    """

    class_mimetypes = ['text/xml', 'application/xml']
    class_extension = 'srx'

    def _load_state_from_file(self, file):
        """[lang:
            break_no:
                    [(before_break, after_break),...]
            break_yes:
                    [(before_break, after_break),...]
           ]
        """
        self.language_rules = {}
        self.language_map = {}

        data = file.read()
        events = XMLParser(data)

        current_lang = {}
        current_rule = None
        rule = [None, None]
        regexp = u''
        before_break = False
        after_break = False
        for event, value, line in events:
            if event == START_ELEMENT:
                tag_uri, tag_name, attrs = value
                if tag_name == 'languagerule':
                    attr_lang = attrs[(None, 'languagerulename')]
                    self.language_rules[attr_lang] = {}
                    current_lang = self.language_rules[attr_lang]
                    current_lang['break_no'] = []
                    current_lang['break_yes'] = []
                elif tag_name == 'rule':
                    break_value = attrs[(None, 'break')]
                    if break_value == 'no':
                        current_rule = current_lang['break_no']
                    elif break_value == 'yes':
                        current_rule = current_lang['break_yes']
                elif tag_name == 'beforebreak':
                    before_break = True
                elif tag_name == 'afterbreak':
                    after_break = True
                elif tag_name == 'languagemap':
                    language_pattern = attrs[(None, 'languagepattern')]
                    language_name = attrs[(None, 'languagerulename')]
                    self.language_map[language_pattern] = language_name
            elif event == END_ELEMENT:
                tag_uri, tag_name = value
                if tag_name == 'beforebreak':
                    rule[0] = regexp
                    regexp = u''
                    before_break = False
                elif tag_name == 'afterbreak':
                    rule[1] = regexp
                    regexp = u''
                    after_break = False
                elif tag_name == 'rule':
                    rule = tuple(rule)
                    current_rule.append(rule)
                    rule = [None, None]
            elif event == TEXT and (before_break or after_break):
                regexp = unicode(value, 'utf-8')


    def get_compiled_rules(self, lang):
        """[lang:
            break_no:
                    [exception1, exception2, ...]
            break_yes:
                    [rule1, rule2, ...]
           ]
        """
        rules = self.get_rules(lang)
        break_rules = []
        except_rules = []
        for break_rule in rules['break_yes']:
            before_break, after_break = break_rule
            before_break = before_break is not None and before_break or '.+?'
            after_break = after_break is not None and after_break or ''
            pattern = '%s(?=%s)' % (before_break, after_break)
            break_rules.append(compile(pattern, DOTALL))
        for except_rule in rules['break_no']:
            before_break, after_break = except_rule
            before_break = before_break is not None and before_break or '.+?'
            after_break = after_break is not None and after_break or ''
            pattern = '%s(?=%s)' % (before_break, after_break)
            except_rules.append(compile(pattern, DOTALL))
        return {'break_yes': break_rules, 'break_no': except_rules}


    def get_languages(self):
        return self.language_rules.keys()


    def get_rules(self, lang):
        for pattern in self.language_map:
            if match(pattern, lang):
                lang = self.language_map[pattern]
                return self.language_rules[lang]


register_handler_class(SRXFile)


