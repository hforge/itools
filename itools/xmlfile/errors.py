# -*- coding: UTF-8 -*-
# Copyright (C) 2017 Florent Chenebault <florent.chenebault@gmail.com>
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

class TranslationError(Exception):
    """
    New exception for translation error
    """
    def __init__(self, line=None, source_file=None, language=None):
        self.line = line
        self.source_file = source_file
        self.language = language
        sub_message = 'Please check : {}:{} on file {}.po'.format(source_file, line, language)
        super(TranslationError, self).__init__(sub_message)
