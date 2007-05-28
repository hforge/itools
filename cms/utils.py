# -*- coding: UTF-8 -*-
# Copyright (C) 2002-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from the Standard Library
from urllib import quote
import string
import random

# Import from itools
from itools.web import get_context




###########################################################################
# Navigation helper functions
###########################################################################
def get_parameters(prefix, **kw):
    """
    Gets the parameters from the request form, the keyword argument specifies
    which are the parameters to get and which are their default values.

    The prefix argument lets to create different namespaces for the
    parameters, so the same page web can have different sections with
    different but equivalent parameters.

    For example, call it like:

      get_parameters('objects', sortby='id', sortorder='up')
    """
    # Get the form field from the request (a zope idiom)
    form = get_context().request.form

    # Get the parameters
    parameters = {}
    for key, value in kw.items():
        parameters[key] = form.get('%s_%s' % (prefix, key), value)

    return parameters


def preserve_parameters(preserve=[]):
    """
    Returns an HTML snippet with hidden input html elements, there will
    be one element for each request parameter that starts with any of
    the prefixes contained in the preserve parameter.

    This lets to pass url request parameters through form actions, so we
    don't lose important navigation information.
    """
    snippet = []

    form = get_context().request.form
    for k, v in form.items():
        for prefix in preserve:
            if k.startswith(prefix):
                snippet.append('<input type="hidden" name="%s" value="%s">'
                               % (k, quote(v)))
                break

    return '\n'.join(snippet)



###########################################################################
# Languages
###########################################################################

# Mark for translatios
u'Basque'
u'Catalan'
u'English'
u'French'
u'German'
u'Hungarian'
u'Italian'
u'Japanese'
u'Portuguese'
u'Spanish'


###########################################################################
# String format for display
###########################################################################

def reduce_string(title='', word_treshold=15, phrase_treshold=40):
    """Reduce words and string size"""
    words = title.strip().split(' ')
    for i, word in enumerate(words):
        if len(word) > word_treshold:
            words.pop(i)
            word = word[:word_treshold] + '...'
            words.insert(i, word)
    title = ' '.join(words)
    if len(title) > phrase_treshold:
        title = title[:phrase_treshold] + '...'
    return title


###########################################################################
# User and Authentication
###########################################################################
def generate_password(length=6):
    tokens = list(string.ascii_letters + string.digits)
    # Remove ambiguity
    for char in ('1', 'l', '0', 'o'):
        tokens.remove(char)
    password = random.sample(tokens, length)
    return ''.join(password)


