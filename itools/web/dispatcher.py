# -*- coding: UTF-8 -*-
# Copyright (C) 2016 Sylvain Taverne <taverne.sylvain@gmail.com>
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

# Import from standard library
import re

# Import from itools
from itools.core import prototype


class URIPatternsParser(prototype):
    """
    Inspired by this project: https://github.com/lukearno/selector
    Turn path expressions into regexes with named groups.

    .. code-block:: python
        URIPatternsParser()("/hello/{name}") == r"^\/hello\/(?P<name>[^\^.]+)$"

    """

    start, end = '{}'
    ostart, oend = '[]'
    patterns = {'word': r'\w+',
                'alpha': r'[a-zA-Z]+',
                'digits': r'\d+',
                'number': r'\d*.?\d+',
                'chunk': r'[^/^.]+',
                'segment': r'[^/]+',
                'any': r'.+'}
    default_pattern = 'chunk'


    def _lookup(self, name):
        """Return the replacement for the name found."""
        if ':' in name:
            name, pattern = name.split(':')
            pattern = self.patterns[pattern]
        else:
            pattern = self.patterns[self.default_pattern]
        if name == '':
            name = '__pos%s' % self._pos
            self._pos += 1
        return '(?P<%s>%s)' % (name, pattern)


    def _lastly(self, regex):
        """Process the result of __call__ right before it returns.

        Adds the ^ and the $ to the beginning and the end, respectively.
        """
        return "^%s$" % regex


    def _outermost_optionals_split(self, text):
        """Split out optional portions by outermost matching delims."""
        parts = []
        buffer = ""
        starts = ends = 0
        for c in text:
            if c == self.ostart:
                if starts == 0:
                    parts.append(buffer)
                    buffer = ""
                else:
                    buffer += c
                starts += 1
            elif c == self.oend:
                ends += 1
                if starts == ends:
                    parts.append(buffer)
                    buffer = ""
                    starts = ends = 0
                else:
                    buffer += c
            else:
                buffer += c
        if not starts == ends == 0:
            raise ValueError("Mismatch of optional portion delimiters.")
        parts.append(buffer)
        return parts


    def _parse(self, text):
        """Turn a path expression into regex."""
        if self.ostart in text:
            parts = self._outermost_optionals_split(text)
            parts = list(map(self._parse, parts))
            parts[1::2] = ["(%s)?" % p for p in parts[1::2]]
        else:
            parts = [part.split(self.end)
                     for part in text.split(self.start)]
            parts = [y for x in parts for y in x]
            parts[::2] = list(map(re.escape, parts[::2]))
            parts[1::2] = list(map(self._lookup, parts[1::2]))
        return ''.join(parts)


    def get_regex(self, url_pattern):
        """Turn a path expression into a regex."""
        self._pos = 0
        return self._lastly(self._parse(url_pattern))




class URIDispatcher(object):

    patterns = []
    parser = URIPatternsParser

    def add(self, pattern, data):
        parser = self.parser()
        regex = parser.get_regex(pattern)
        compiled_regex = re.compile(regex)
        self.patterns.append((pattern, compiled_regex, data))


    def select(self, path):
        for pattern, compiled_regex, data in self.patterns:
            match = compiled_regex.search(path)
            if match:
                return data, match.groupdict()
        return None


router = URIDispatcher()
router.add('/hello/{name}', 'ROUTE1')
router.add('/hello/{name}/world', 'ROUTE2')
router.add('/hello/{name}/worldismine', 'ROUTE3')
print router.select('/hello/sylvain')
print router.select('/hello/chat')
print router.select('/hello/sylvain/world')
print router.select('/hello/sylvain/worldismine')
print router.select('/hello/sylvain/worldismine/')
print router.select('/error')
