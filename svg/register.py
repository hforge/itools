# -*- coding: UTF-8 -*-
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
from itools.core import get_abspath
from itools.xml import register_dtd


# Register -//W3C//DTD SVG 1.1//EN
register_dtd(get_abspath('svg11.dtd'),
             urn='urn:publicid:-:W3C:DTD+SVG+1.1:EN')

# Register -//W3C//DTD SVG 1.1 Basic//EN
register_dtd(get_abspath('svg11-basic.dtd'),
             urn='urn:publicid:-:W3C:DTD+SVG+1.1+Basic:EN')

# Register -//W3C//DTD SVG 1.1 Tiny//EN
register_dtd(get_abspath('svg11-tiny.dtd'),
             urn='urn:publicid:-:W3C:DTD+SVG+1.1+Tiny:EN')

# Register -//W3C//ENTITIES SVG 1.1 Basic Graphics Attribute//EN
register_dtd(get_abspath('svg-basic-graphics-attrib.mod'),
             urn='urn:publicid:-:W3C:ENTITIES+SVG+1.1+Basic+Graphics+Attribute:EN')

# Register -//W3C//ENTITIES SVG 1.1 Document Model//EN
register_dtd(get_abspath('svg11-model.mod'),
             urn='urn:publicid:-:W3C:ENTITIES+SVG+1.1+Document+Model:EN')

# Register -//W3C//ELEMENTS SVG 1.1 Basic Filter//EN
register_dtd(get_abspath('svg-basic-filter.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+Basic+Filter:EN')

# Register -//W3C//ELEMENTS SVG 1.1 Basic Color//EN
register_dtd(get_abspath('svg-basic-color.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+Basic+Color:EN')

# Register -//W3C//ENTITIES SVG 1.1 Basic Attribute Collection//EN
register_dtd(get_abspath('svg11-basic-attribs.mod'),
             urn='urn:publicid:-:W3C:ENTITIES+SVG+1.1+Basic+Attribute+Collection:EN')

# Register -//W3C//ENTITIES SVG 1.1 Graphics Attribute//EN
register_dtd(get_abspath('svg-graphics-attrib.mod'),
             urn='urn:publicid:-:W3C:ENTITIES+SVG+1.1+Graphics+Attribute:EN')

# Register -//W3C//ELEMENTS SVG 1.1 Shape//EN
register_dtd(get_abspath('svg-shape.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+Shape:EN')

# Register -//W3C//ENTITIES SVG 1.1 Paint Attribute//EN
register_dtd(get_abspath('svg-paint-attrib.mod'),
             urn='urn:publicid:-:W3C:ENTITIES+SVG+1.1+Paint+Attribute:EN')

# Register -//W3C//ENTITIES SVG 1.1 Core Attribute//EN
register_dtd(get_abspath('svg-core-attrib.mod'),
             urn='urn:publicid:-:W3C:ENTITIES+SVG+1.1+Core+Attribute:EN')

# Register -//W3C//ELEMENTS SVG 1.1 Basic Structure//EN
register_dtd(get_abspath('svg-basic-structure.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+Basic+Structure:EN')

# Register -//W3C//ENTITIES SVG 1.1 Container Attribute//EN
register_dtd(get_abspath('svg-container-attrib.mod'),
             urn='urn:publicid:-:W3C:ENTITIES+SVG+1.1+Container+Attribute:EN')

# Register -//W3C//ELEMENTS SVG 1.1 Image//EN
register_dtd(get_abspath('svg-image.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+Image:EN')

# Register -//W3C//ELEMENTS SVG 1.1 Color//EN
register_dtd(get_abspath('svg-color.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+Color:EN')

# Register -//W3C//ENTITIES SVG 1.1 Tiny Attribute Collection//EN
register_dtd(get_abspath('svg11-tiny-attribs.mod'),
             urn='urn:publicid:-:W3C:ENTITIES+SVG+1.1+Tiny+Attribute+Collection:EN')

# Register -//W3C//ENTITIES SVG 1.1 Attribute Collection//EN
register_dtd(get_abspath('svg11-attribs.mod'),
             urn='urn:publicid:-:W3C:ENTITIES+SVG+1.1+Attribute+Collection:EN')

# Register -//W3C//ENTITIES SVG 1.1 Paint Opacity Attribute//EN
register_dtd(get_abspath('svg-opacity-attrib.mod'),
             urn='urn:publicid:-:W3C:ENTITIES+SVG+1.1+Paint+Opacity+Attribute:EN')

# Register -//W3C//ELEMENTS SVG 1.1 Basic Clip//EN
register_dtd(get_abspath('svg-basic-clip.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+Basic+Clip:EN')

# Register -//W3C//ELEMENTS SVG 1.1 View//EN
register_dtd(get_abspath('svg-view.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+View:EN')

# Register -//W3C//ELEMENTS SVG 1.1 Conditional Processing//EN
register_dtd(get_abspath('svg-conditional.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+Conditional+Processing:EN')

# Register -//W3C//ELEMENTS SVG 1.1 Hyperlinking//EN
register_dtd(get_abspath('svg-hyperlink.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+Hyperlinking:EN')

# Register -//W3C//ENTITIES SVG 1.1 Viewport Attribute//EN
register_dtd(get_abspath('svg-viewport-attrib.mod'),
             urn='urn:publicid:-:W3C:ENTITIES+SVG+1.1+Viewport+Attribute:EN')

# Register -//W3C//ELEMENTS SVG 1.1 Extensibility//EN
register_dtd(get_abspath('svg-extensibility.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+Extensibility:EN')

# Register -//W3C//ELEMENTS SVG 1.1 Filter//EN
register_dtd(get_abspath('svg-filter.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+Filter:EN')

# Register -//W3C//ENTITIES SVG 1.1 XLink Attribute//EN
register_dtd(get_abspath('svg-xlink-attrib.mod'),
             urn='urn:publicid:-:W3C:ENTITIES+SVG+1.1+XLink+Attribute:EN')

# Register -//W3C//ENTITIES SVG 1.1 Modular Framework//EN
register_dtd(get_abspath('svg-framework.mod'),
             urn='urn:publicid:-:W3C:ENTITIES+SVG+1.1+Modular+Framework:EN')

# Register -//W3C//ENTITIES SVG 1.1 Tiny Document Model//EN
register_dtd(get_abspath('svg11-tiny-model.mod'),
             urn='urn:publicid:-:W3C:ENTITIES+SVG+1.1+Tiny+Document+Model:EN')

# Register -//W3C//ELEMENTS SVG 1.1 Basic Text//EN
register_dtd(get_abspath('svg-basic-text.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+Basic+Text:EN')

# Register -//W3C//ELEMENTS SVG 1.1 Pattern//EN
register_dtd(get_abspath('svg-pattern.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+Pattern:EN')

# Register -//W3C//ELEMENTS SVG 1.1 Marker//EN
register_dtd(get_abspath('svg-marker.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+Marker:EN')

# Register -//W3C//ENTITIES SVG 1.1 Graphical Element Events Attribute//EN
register_dtd(get_abspath('svg-graphevents-attrib.mod'),
             urn='urn:publicid:-:W3C:ENTITIES+SVG+1.1+Graphical+Element+Events+Attribute:EN')

# Register -//W3C//ELEMENTS SVG 1.1 Gradient//EN
register_dtd(get_abspath('svg-gradient.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+Gradient:EN')

# Register -//W3C//ENTITIES SVG 1.1 Document Events Attribute//EN
register_dtd(get_abspath('svg-docevents-attrib.mod'),
             urn='urn:publicid:-:W3C:ENTITIES+SVG+1.1+Document+Events+Attribute:EN')

# Register -//W3C//ELEMENTS SVG 1.1 Text//EN
register_dtd(get_abspath('svg-text.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+Text:EN')

# Register -//W3C//ELEMENTS SVG 1.1 Clip//EN
register_dtd(get_abspath('svg-clip.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+Clip:EN')

# Register -//W3C//ELEMENTS SVG 1.1 Structure//EN
register_dtd(get_abspath('svg-structure.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+Structure:EN')

# Register -//W3C//ENTITIES SVG 1.1 Basic Paint Attribute//EN
register_dtd(get_abspath('svg-basic-paint-attrib.mod'),
             urn='urn:publicid:-:W3C:ENTITIES+SVG+1.1+Basic+Paint+Attribute:EN')

# Register -//W3C//ELEMENTS SVG 1.1 Font//EN
register_dtd(get_abspath('svg-font.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+Font:EN')

# Register -//W3C//ENTITIES SVG 1.1 Animation Events Attribute//EN
register_dtd(get_abspath('svg-animevents-attrib.mod'),
             urn='urn:publicid:-:W3C:ENTITIES+SVG+1.1+Animation+Events+Attribute:EN')

# Register -//W3C//ELEMENTS SVG 1.1 Style//EN
register_dtd(get_abspath('svg-style.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+Style:EN')

# Register -//W3C//ENTITIES SVG 1.1 Qualified Name//EN
register_dtd(get_abspath('svg-qname.mod'),
             urn='urn:publicid:-:W3C:ENTITIES+SVG+1.1+Qualified+Name:EN')

# Register -//W3C//ENTITIES SVG 1.1 Datatypes//EN
register_dtd(get_abspath('svg-datatypes.mod'),
             urn='urn:publicid:-:W3C:ENTITIES+SVG+1.1+Datatypes:EN')

# Register -//W3C//ELEMENTS SVG 1.1 Scripting//EN
register_dtd(get_abspath('svg-script.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+Scripting:EN')

# Register -//W3C//ELEMENTS SVG 1.1 Animation//EN
register_dtd(get_abspath('svg-animation.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+Animation:EN')

# Register -//W3C//ENTITIES SVG 1.1 Basic Document Model//EN
register_dtd(get_abspath('svg11-basic-model.mod'),
             urn='urn:publicid:-:W3C:ENTITIES+SVG+1.1+Basic+Document+Model:EN')

# Register -//W3C//ENTITIES SVG 1.1 External Resources Attribute//EN
register_dtd(get_abspath('svg-extresources-attrib.mod'),
             urn='urn:publicid:-:W3C:ENTITIES+SVG+1.1+External+Resources+Attribute:EN')

# Register -//W3C//ELEMENTS SVG 1.1 Color Profile//EN
register_dtd(get_abspath('svg-profile.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+Color+Profile:EN')

# Register -//W3C//ELEMENTS SVG 1.1 Cursor//EN
register_dtd(get_abspath('svg-cursor.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+Cursor:EN')

# Register -//W3C//ELEMENTS SVG 1.1 Basic Font//EN
register_dtd(get_abspath('svg-basic-font.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+Basic+Font:EN')

# Register -//W3C//ELEMENTS SVG 1.1 Mask//EN
register_dtd(get_abspath('svg-mask.mod'),
             urn='urn:publicid:-:W3C:ELEMENTS+SVG+1.1+Mask:EN')

