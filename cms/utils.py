# -*- coding: UTF-8 -*-
# Copyright (C) 2002-2005, 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Nicolas Deram <nicolas@itaapy.com>
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
    [tokens.remove(char) for char in ('1', 'l', '0', 'O')]
    password = random.sample(tokens, length)
    return ''.join(password)


###########################################################################
# Generate next name
###########################################################################
def generate_name(name, used, suffix='_'):
    """
    Generate a name which is not in list "used" based on name and suffix.
    Example:
      With name='toto.txt', used=['toto.txt', 'toto_0.txt']
      --> toto.txt and toto_0.txt are used so it returns toto_1.txt
      With name='toto.txt', used=['toto.txt', 'toto_0.txt'], suffix='_copy_'
      --> toto.txt is used so it returns toto_copy_0.txt
    """
    if name not in used:
        return name

    items = name.split('.', 1)
    basename = items[0]
    extent = ''
    if len(items) > 1:
        extent = '.%s' % items[1]

    # 1st time called
    if suffix not in basename:
        index = 0
    else:
        basename, index = basename.rsplit(suffix, 1)
        try:
            index = int(index) + 1
        except ValueError:
            basename = '%s%s%s' % (basename, suffix, index)
            index = 0

    name = ''.join([basename, suffix, str(index), extent])
    while name in used:
        index += 1
        name = ''.join([basename, suffix, str(index), extent])

    return str(name)

