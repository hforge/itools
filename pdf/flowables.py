# -*- coding: UTF-8 -*-

# Copyright (C) 2009 Henry Obein <henry@itaapy.com>
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
from itools.utils import freeze

# Internal import
from utils import reportlab_value
from style import attribute_style_to_dict

# Import from reportlab
from reportlab.platypus import KeepInFrame, PTOContainer
from reportlab.platypus import Paragraph as BaseParagraph
from reportlab.platypus.flowables import Flowable
from reportlab.platypus.frames import Frame, ShowBoundaryValue
from reportlab.platypus.paraparser import ParaFrag



FRAME_PADDINGS_KEYS = ('topPadding', 'bottomPadding', 'leftPadding',
                       'rightPadding')


class Paragraph(BaseParagraph):


    def __init__(self, text, style, context=None, bulletText=None,
                 frags=None, caseSensitive=1, encoding='utf8'):
        BaseParagraph.__init__(self, text, style, bulletText, frags,
                               caseSensitive, encoding)
        self.context = context
        self.save_before_change = None


    def wrap(self, availWidth, availHeight):
        if len(self.frags) and isinstance(self.frags[0], ParaFrag):
            if self.save_before_change is not None:
                # restore
                self.frags[0].text = self.save_before_change

            if self.context:
                page_num = self.context.pagenumber
                is_pagetotal = (
                        not self.frags[0].text.find(self.context.pagetotal) < 0)
                is_pagenumber = not self.frags[0].text.find(page_num) < 0
                if is_pagenumber or is_pagetotal:
                    if self.save_before_change is None:
                        # save
                        self.save_before_change = self.frags[0].text
                    if is_pagenumber:
                        page = str(self.context.current_page)
                        self.frags[0].text = self.frags[0].text.replace(page_num,
                                                                        page)
                    if is_pagetotal:
                        pages = str(self.context.number_of_pages)
                        self.frags[0].text = (
                          self.frags[0].text.replace(self.context.pagetotal,
                                                     pages))

        width = getattr(self.style, 'width', None)
        if width is not None:
            if width.endswith('%'):
                availWidth = reportlab_value(width, availWidth)
        return BaseParagraph.wrap(self, availWidth, availHeight)



class Div(Flowable):

    def __init__(self, story, height=None, width=None, pos_x=None, pos_y=None,
                 frame_attrs=freeze({}), attributes=freeze({}), pto_trailer=None,
                 pto_header=None):
        Flowable.__init__(self)
        # get on story
        self.div_story = story
        # set frame style
        self.frame_attrs = {'leftPadding': 0, 'bottomPadding': 0,
                           'rightPadding': 0, 'topPadding': 0,
                           'showBoundary': 0}
        # PTO initialisation
        self.pto_trailer = pto_trailer
        self.pto_header = pto_header

        if frame_attrs is not None:
            self.frame_attrs.update(frame_attrs)

        for margin in ('topMargin', 'bottomMargin', 'leftMargin',
                       'rightMargin'):
            if self.frame_attrs.has_key(margin):
                del self.frame_attrs[margin]

        border = self.frame_attrs['showBoundary']
        if isinstance(border, ShowBoundaryValue):
            border = border.width
        if border:
            for padding_attr in FRAME_PADDINGS_KEYS:
                self.frame_attrs[padding_attr] += border
        self.frame_width = width

        # Overflow
        # TODO to improve
        self.keep_in_frame = None
        style = attribute_style_to_dict(attributes.get((None, 'style'), ''))
        self.overflow = style.get('overflow-y', None)
        if self.overflow == 'hidden':
            self.overflow = 'truncate'
        else:
            self.overflow = None


    def draw(self):
        # set position for the frame
        self.pos_x, self.pos_y = self._get_current_position(self.canv)
        # XXX This is false, height=drawHeigh and drawHeight should take into
        # account the frame padding
        height = (self.drawHeight + self.frame_attrs['leftPadding'] +
                  self.frame_attrs['rightPadding'])
        width = (self.drawWidth + self.frame_attrs['topPadding'] +
                 self.frame_attrs['bottomPadding'])

        self.frame = Frame(self.pos_x, self.pos_y, width, height,
                           **self.frame_attrs)
        if self.overflow:
            # Hack, We lie by setting the new created frame as default frame
            # of the doc template
            # To avoid problems when calling keep_in_frame.wrap
            # See platypus.flowables "def _listWrapOn"
            _doctemplate = self.canv._doctemplate
            # save state
            current_frame = getattr(_doctemplate, 'frame', None)
            _doctemplate.frame = self.frame

            # Check if PTO is defined
            if self.pto_trailer or self.pto_header:
                ptocontainer = PTOContainer(self.div_story[:],
                                            self.pto_trailer, self.pto_header)
                ptocontainer.canv = self.canv
                pto_size = ptocontainer.wrap(self.drawWidth, self.drawHeight)
                # XXX Round the height to avoid problems with decimal
                if int(pto_size[1]) > int(self.drawHeight):
                    pto_story = ptocontainer.split(self.drawWidth,
                                                   self.drawHeight)
                    self.frame.addFromList(pto_story, self.canv)
                else:
                    self.frame.addFromList([self.keep_in_frame], self.canv)
            else:
                self.frame.addFromList([self.keep_in_frame], self.canv)
            # restore state
            if current_frame:
                _doctemplate.frame = current_frame
        else:
            self.frame.addFromList(self.div_story[:], self.canv)


    def wrap(self, availWidth, availHeight):
        canv = self.canv
        if self.overflow:
            if self.keep_in_frame is None:
                # FIXME if the availHeight is very small
                # We consider that there is no enough space
                # and we calculate the real size of the flowables
                if availHeight <= 0:
                    width, height = self._get_real_size(availWidth)
                else:
                    width, height = availWidth, availHeight

                # Dirty hack, get the current frame height and use it
                # if height is too small
                main_frame_height = self._get_main_frame_height(availHeight,
                                                                0.8)
                if height == -1e-06:
                    height = main_frame_height
                else:
                    height = min(height, main_frame_height)

                self.keep_in_frame = KeepInFrame(width, height,
                                                 self.div_story[:],
                                                 mode=self.overflow)
            else:
                width, height = availWidth, availHeight
                # FIXME Usefull ?
                # Dirty hack, get the current frame height and use it
                # if height is too small
                main_frame_height = self._get_main_frame_height(availHeight,
                                                                0.8)
                if height == -1e-06:
                    height = main_frame_height
                else:
                    height = min(height, main_frame_height)

            # Set the canva
            self.keep_in_frame.canv = canv

            # Hack, We remove the attribute _doctemplate of the canv
            # To avoid problems when calling keep_in_frame.wrap
            # See platypus.flowables "def _listWrapOn"
            if hasattr(canv, '_doctemplate'):
                _doctemplate = canv._doctemplate
                # Remove _doctemplate
                canv._doctemplate = None
            w, h = self.keep_in_frame.wrap(width, height)
            if hasattr(canv, '_doctemplate'):
                # Restore _doctemplate
                canv._doctemplate = _doctemplate

            self.drawWidth, self.drawHeight = w, h
        else:
            width, height = self._get_real_size(availWidth)
            self.drawWidth, self.drawHeight = width, height

        return self.drawWidth, self.drawHeight


    def getSpaceBefore(self):
        if self.overflow and self.keep_in_frame:
            return self.keep_in_frame.getSpaceBefore()

        # XXX default value
        return 0


    def getSpaceAfter(self):
        if self.overflow and self.keep_in_frame:
            return self.keep_in_frame.getSpaceAfter()

        # XXX default value
        return 0


    def _get_real_size(self, availWidth, availHeight=10000000):
        """By default we use a fake height to calculate the real
        height of the flowables"""
        self.drawWidth = self.width or availWidth
        self.drawWidth -= self.frame_attrs['leftPadding']
        self.drawWidth -= self.frame_attrs['rightPadding']
        self.drawHeight = 0
        at_top = True
        for element in self.div_story[:]:
            if at_top:
                at_top = False
            else:
                self.drawHeight += element.getSpaceBefore()
            flowHeight = element.wrap(availWidth,
                                      availHeight-self.drawHeight)[1]
            self.drawHeight += flowHeight
            self.drawHeight += element.getSpaceAfter()
        self.drawHeight += self.frame_attrs['topPadding']
        self.drawHeight += self.frame_attrs['bottomPadding']
        return (self.drawWidth, self.drawHeight)


    def _align_frame(self, available_width, hAlign):
        if hAlign == 'CENTER':
            self.pox_x = (available_width - self.frame_width) / 2 + self.pos_x
        elif hAlign == 'RIGHT':
            self.pos_x = available_width - self.frame_width + self.pox_x


    def _get_current_position(self, canv):
        return (canv._x, canv._y)


    def _get_current_absolute_position(self, canv):
        return canv.absolutePosition(canv._x, canv._y)


    def _get_main_frame_height(self, default, ratio=0.9):
        if self.canv is None:
            return default
        value = self.canv._doctemplate.main_frame_attr.get('height', default)
        return value * ratio
