# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


# End of Input
EOI = 0



class Tokenizer(object):

    def __init__(self, lexical_table):
        self.lexical_table = lexical_table


    def get_token(self, data):
        lexical_table = self.lexical_table
        data_len = len(data)
        data_idx = 0

        # Read the first token
        while data_idx < data_len:
            char = data[data_idx]
            token = lexical_table[ord(char)]
            if token is None:
                msg = 'lexical error, unexpected character %s at byte %s'
                raise ValueError, msg % (repr(char), data_idx)

            yield token, data_idx
            data_idx += 1

        # End Of Input
        yield EOI, data_idx
