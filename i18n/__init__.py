# -*- coding: UTF-8 -*-
# Copyright (C) 2002-2003 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from itools
from accept import AcceptLanguageType, get_accept
from base import has_language, get_languages, get_language_name, Multilingual
from fuzzy import get_distance, get_similarity, is_similar, get_most_similar
from locale_ import format_date, format_time, format_datetime
from oracle import guess_language
from segment import Message



__all__ = [
    # accept
    'AcceptLanguageType',
    'get_accept',
    # fuzzy
    'get_distance',
    'get_similarity',
    'is_similar',
    'get_most_similar',
    # locale
    'format_date',
    'format_time',
    'format_datetime',
    # oracle
    'guess_language',
    # segment
    'Message',
    # languages
    'has_language',
    'get_languages',
    'get_language_name',
    # Abstract classes
    'Multilingual']


