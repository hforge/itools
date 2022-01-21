# -*- coding: UTF-8 -*-
# Copyright (C) 2016 Sylvain Taverne <sylvain@agicia.com>
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
from itools.gettext import MSG

# Import from here
from .base import BaseValidator


class UniqueValidator(BaseValidator):

    validator_id = 'unique'
    errors = {'unique': MSG(u'The field should be unique.')}
    field_name = None
    base_query = None

    def check(self, value):
        from itools.database import AndQuery, NotQuery
        from itools.database import PhraseQuery
        if not value:
            return
        context = self.context
        here = context.resource
        query = AndQuery(
            NotQuery(PhraseQuery('abspath', str(here.abspath))),
            PhraseQuery(self.field_name, value))
        if self.base_query:
            query.append(self.base_query)
        search = context.database.search(query)
        nb_results = len(search)
        if nb_results > 0:
            kw = {'nb_results': nb_results}
            self.raise_default_error(kw)
