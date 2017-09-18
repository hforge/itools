# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2012 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2006-2009 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2007-2008 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2008 Gautier Hayoun <gautier.hayoun@supinfo.com>
# Copyright (C) 2008, 2010-2011 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2009 Sylvain Taverne <taverne.sylvain@gmail.com>
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
from itools.log import Logger


class AccessLogger(Logger):

    def format(self, domain, level, message):
        return message
