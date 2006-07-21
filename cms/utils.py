# -*- coding: ISO-8859-1 -*-
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
from copy import copy
from string import translate, maketrans
from urllib import quote

# Import from itools
from itools import uri
from itools.web import get_context


#############################################################################
# Misc
#############################################################################

src = ur""" ¹,;:!¡?ª$£¤+&/\"*#()[]{}'ÄÅÁÀÂÃäåáàâãÇçÉÈÊËéèêëæÍÌÎÏíìîïÑñÖÓÒÔÕØöóòôõøßÜÚÙÛüúùûÝ~ýÿ~^°"""
dst = ur"""--------------------------AAAAAAaaaaaaCcEEEEeeeeeIIIIiiiiNnOOOOOOooooooSUUUUuuuuY-yy---"""

transmap = {}
for i in range(len(src)):
    a, b = src[i], dst[i]
    transmap[ord(a)] = ord(b)


def checkid(id):
    """
    Checks wether the id is or not a valid Zope id. If it is the id is
    returned, but stripped. If it is a bad id None is returned to signal
    the error.
    """
    if isinstance(id, str):
        id = unicode(id, 'utf8')
    id = id.strip().translate(transmap).strip('-')

    # Check wether the id is empty
    if len(id) == 0:
        return None

    # Check for unallowed characters
    for c in id:
        if not c.isalnum() and c not in ('.', '-', '_', '@'):
            return None

    # The id is good
    return str(id)


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
