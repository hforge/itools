# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2010 David Versmisse <david.versmisse@itaapy.com>
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
from itools.xml import START_ELEMENT
from itools.xmlfile import XMLFile



def _get_root(events):
    for pos, (event, value, line) in enumerate(events):
        if event == START_ELEMENT:
            return pos, (event, value, line)
    else:
        raise ValueError, 'Invalid SVG file'



def _convert_unit(value):
    if value.endswith('px'):
        return float(value[:-2])
    elif value.endswith('pt'):
        return float(value[:-2]) * 1.25
    elif value.endswith('pc'):
        return float(value[:-2]) * 15
    elif value.endswith('mm'):
        return float(value[:-2]) * 3.543307
    elif value.endswith('cm'):
        return float(value[:-2]) * 35.43307
    elif value.endswith('in'):
        return float(value[:-2]) * 90

    return float(value)



class SVGFile(XMLFile):


    #######################################################################
    # API
    #######################################################################
    def make_WEB_compliant(self):
        events = self.events

        # Get the root element
        pos, (event, value, line) = _get_root(events)
        ns, tag, attributs = value

        # All OK ?
        if tag != 'svg':
            raise ValueError, 'Invalid SVG file'

        # Get width, height and viewBox
        w = attributs.get((None, 'width'))
        h = attributs.get((None, 'height'))
        viewBox = attributs.get((None, 'viewBox'))

        # Yet WEB compliant ?
        if viewBox:
            return

        # Make the SVG WEB compliant
        w = _convert_unit(w)
        h = _convert_unit(h)
        attributs[(None, 'width')] = '100%'
        attributs[(None, 'height')] = '100%'
        attributs[(None, 'viewBox')] = '0 0 %g %g' % (w, h)

        # Save the changes
        events[pos] = (event, (ns, tag, attributs), line)


    def get_size(self):
        events = self.events

        # Get the root element
        _, (_, value, _) = _get_root(events)
        _, tag, attributs = value

        # All OK ?
        if tag != 'svg':
            raise ValueError, 'Invalid SVG file'

        # Get width, height and viewBox
        w = attributs.get((None, 'width'))
        h = attributs.get((None, 'height'))
        viewBox = attributs.get((None, 'viewBox'))

        # WEB compliant ?
        if viewBox:
            w1, h1, w2, h2 = [ float(x) for x in viewBox.split() ]
            return int(w2 - w1), int(h2 - h1)

        return int(_convert_unit(w)), int(_convert_unit(h))



