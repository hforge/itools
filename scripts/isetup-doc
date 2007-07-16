#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from optparse import OptionParser
from types import FunctionType, ClassType

# Import from itools
import itools
from itools import rest
from itools.xml import Document
from itools.stl import stl



def format_text(text, width=72, indent='  '):
    # Clean text
    text = text.strip()
    lines = [ x.strip() + '\n' for x in text.splitlines() ]
    text = ''.join(lines)
    # Split paragraphs
    paragraphs = []
    for paragraph in text.split('\n\n'):
        words = paragraph.split()
        word = words.pop(0)
        lines = [indent+word]
        while words:
            word = words.pop(0)
            if len(lines[-1]) + len(word) < width:
                lines[-1] += (' ' + word)
            else:
                lines[-1] += '\n'
                lines.append(indent + word)
        lines[-1] += '\n'
        paragraph = ''.join(lines)
        paragraph += '\n'
        paragraphs.append(paragraph)

    return ''.join(paragraphs)


def escape_latex(text):
    text = text.replace('_', '\_')
    text = text.replace('$', '\$')
    text = text.replace('#', '\#')
    text = text.replace('&', '\&')
    return text


def format_latex(text):
    text = unicode(text, 'utf-8')
    return rest.to_str(text, format='latex')



text_template = Document(string=
"""<block xmlns="http://xml.itools.org/namespaces/stl">
${name}

${doc}
<block if="exceptions">Exceptions
==========
    
<block repeat="item exceptions">* ${item/name}

${item/doc}</block></block>
<block if="constants">Constants
=========
    
<block repeat="item constants">* ${item/name}

${item/doc}</block></block>
<block if="functions">Functions
=========
    
<block repeat="item functions">* ${item/name}

${item/doc}</block></block>
<block if="classes">Classes
=======
    
<block repeat="item classes">* ${item/name}

${item/doc}</block></block>
</block>""")


latex_template = Document(string=
"""<block xmlns="http://xml.itools.org/namespaces/stl">
\\chapter{${name}}
\\index{${name}}

${doc}
<block if="exceptions">
\\section{Exceptions}
 
<block repeat="item exceptions">
\\subsubsection{${item/name}}
\\index{${item/name}}

${item/doc}</block></block>
<block if="constants">
\\section{Constants}

<block repeat="item constants">
\\subsubsection{${item/name}}
\\index{${item/name}}

${item/doc}</block></block>
<block if="functions">
\\section{Functions}

<block repeat="item functions">
\\subsubsection{${item/name}}
\\index{${item/name}}

${item/doc}</block></block>
<block if="classes">
\\section{Classes}
 
<block repeat="item classes">
\\subsubsection{${item/name}}
\\index{${item/name}}

${item/doc}</block></block>
</block>""")






def build_namespace(pkg, format, escape=lambda x: x):
    namespace = {}
    # Package name
    namespace['name'] = escape(pkg.__name__)
    # Documentation String
    doc = pkg.__doc__
    if doc is not None:
        doc = format(doc)
    namespace['doc'] = doc
    # Public API
    all = pkg.__all__
    if all is None:
        all = []

    all.sort(key=lambda x: x.lower())

    # Split into exceptions, constants, functions and classes
    exceptions = namespace['exceptions'] = []
    constants = namespace['constants'] = []
    functions = namespace['functions'] = []
    classes = namespace['classes'] = []
    for name in all:
        object = getattr(pkg, name)
        # Get the documentation string
        doc = object.__doc__
        if doc is not None:
            doc = doc.strip()
            doc = format(doc)
        # Build the item namespace
        title = escape(name)
        ns = {'name': title, 'doc': doc}
        # Do whatever 
        if isinstance(object, FunctionType):
            # Find out the function prototype
            # FIXME Remains to find the argument names
            func_code = object.func_code
            parameters = []
            defaults = object.func_defaults or ()
            arg_name = ord('a')
            for i in range(func_code.co_argcount - len(defaults)):
                parameters.append('%s' % chr(arg_name))
                arg_name += 1
            if defaults:
                for default in defaults:
                    parameters.append('%s=%s' % (chr(arg_name), default))
                    arg_name += 1
            if func_code.co_flags & 0x04:
                parameters.append('*args')
            if func_code.co_flags & 0x08:
                parameters.append('**kw')
            ns['name'] = '%s(%s)' % (title, ', '.join(parameters))
            functions.append(ns)
        elif isinstance(object, type):
            if issubclass(object, Exception):
                exceptions.append(ns)
            else:
                classes.append(ns)
        elif isinstance(object, ClassType):
            raise ValueError, ('"%s" is an old style class, don not use'
                'old style classes, they are obsolete') % name
        else:
            constants.append(ns)
            ns['doc'] = None

    return namespace



if __name__ == '__main__':
    # The command line parser
    usage = '%prog [OPTIONS] PACKAGE'
    version = 'itools %s' % itools.__version__
    description = 'Extract documentation from the given package.'
    parser = OptionParser(usage, version=version, description=description)
    parser.add_option('-f', '--format',
        help='the output FORMAT (defaults to text)')

    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error('incorrect number of arguments')

    # Find out the format
    format = options.format
    if not format:
        format = 'text'

    # Action
    exec('import %s as pkg' % args[0])
    if format == 'text':
        namespace = build_namespace(pkg, format_text)
        print stl(text_template, namespace)
    elif format == 'latex':
        namespace = build_namespace(pkg, format_latex, escape_latex)
        print stl(latex_template, namespace)
    else:
        raise ValueError
