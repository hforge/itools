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

from collections import OrderedDict
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
    patterns = {'word': r'\w+',
                'alpha': r'[a-zA-Z]+',
                'digits': r'\d+',
                'number': r'\d*.?\d+',
                'chunk': r'[^/^.]+',
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
            name = f'__pos{self._pos}'
            self._pos += 1
        return f'(?P<{name}>{pattern})'


    def _lastly(self, regex):
        """Process the result of __call__ right before it returns.
        Adds the ^ and the $ to the beginning and the end, respectively.
        """
        return f"^{regex}$"


    def _parse(self, text):
        """Turn a path expression into regex."""
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

    patterns = OrderedDict()
    parser = URIPatternsParser

    def add(self, pattern, data):
        """Register a route pattern paired with some data"""
        parser = self.parser()
        regex = parser.get_regex(pattern)
        compiled_regex = re.compile(regex)
        self.patterns[pattern] = (compiled_regex, data)


    def resolve(self, path):
        """
        Path resolution, look for a corresponding registered pattern
        and return associated data along with the extracted parameters.
        """
        for pattern, values in self.patterns.items():
            compiled_regex, data = values
            match = compiled_regex.search(path)
            if match:
                return data, match.groupdict()
        return None

