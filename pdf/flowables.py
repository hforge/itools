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
from itools.core import freeze

# Internal import
from utils import reportlab_value
from style import attribute_style_to_dict

# Import from reportlab
from reportlab.platypus import KeepInFrame
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
                 frame_attrs=freeze({}), attributes=freeze({})):
        Flowable.__init__(self)
        # get on story
        self.div_story = story

        # set frame style
        self.frame_attrs = {'leftPadding': 0, 'bottomPadding': 0,
                           'rightPadding': 0, 'topPadding': 0,
                           'showBoundary': 0}

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
        # fallback attribute
        if self.overflow is None:
            self.overflow = attributes.get(('overflow-y'), None)
        if self.overflow == 'hidden':
            self.overflow = 'truncate'
        else:
            self.overflow = None


    def draw(self):
        # set position for the frame
        self.pos_x, self.pos_y = self._get_current_position(self.canv)
        height = (self.drawHeight + self.frame_attrs['leftPadding'] +
                  self.frame_attrs['rightPadding'])
        width = (self.drawWidth + self.frame_attrs['topPadding'] +
                 self.frame_attrs['bottomPadding'])

        self.frame = Frame(self.pos_x, self.pos_y, width, height,
                           **self.frame_attrs)
        if self.overflow:
            self.frame.addFromList([self.keep_in_frame], self.canv)
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
                self.keep_in_frame = KeepInFrame(width, height,
                                                 self.div_story[:],
                                                 mode=self.overflow)
            else:
                width, height = availWidth, availHeight

            # Set the canva
            self.keep_in_frame.canv = canv
            w, h = self.keep_in_frame.wrap(width, height)
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
