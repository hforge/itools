# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004 Thierry Fromon <from.t@free.fr>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA


dictionary = {u'Monsieur': (u'Mr', u'M', u'M.', u'Mr.'),
              u'Madame': (u'Md', u'Md.')}

punctuations = [u'.', u',', u';', u'?', '!', u"'", u'"', u'¡', u'¿']


class SelectText(object):
    def __init__(self, text):
        self.text = text


    def create_new_text(self):
        """
        Return a text without abrevation.
        """
        t = ' '+self.text+' '
        for i in punctuations:
            t = t.replace(i , ' '+i+' ')
        for word, abrevations in dictionary.items():
            for abrevation in abrevations:
                t = t.replace(' '+abrevation+' ', ' '+word+' ')
        return t             



class Distance(object):
    def __init__(self, first_text, second_text):
        self.first_text =  first_text
        self.second_text = second_text


    def distance(self):
        """
        Return a gap and a percent that takes account of abrevations.
        """
        a = SelectText(self.first_text)
        b = SelectText(self.second_text)
        a_create = a.create_new_text()
        b_create = b.create_new_text()
        dist = max (len(a.text), len(b.text))
        dist_create = 5*(max (len(a_create), len(b_create)))
        gap = self.gap(self.first_text, self.second_text)
        gap_create = 5*(self.gap(a_create, b_create))
        percent = 100 - 100*(gap_create + gap)/(dist_create + dist)
        return gap_create + gap, percent
       

    def gap(self, a, b):
        """
        This function was giving by Magnus Lie Hetland. It calculates the gap
        (mathematical distance) between two strings with the cost of word's
        translation inside the string. 
        """
        c = {}
        n = len(a); m = len(b)
        for i in range(0,n+1):
            c[i,0] = i
        for j in range(0,m+1):
            c[0,j] = j
        for i in range(1,n+1):
            for j in range(1,m+1):
                x = c[i-1,j] + 1
                y = c[i,j-1] + 1
                if a[i-1] == b[j-1]:
                    z = c[i-1,j-1]
                else:
                    z = c[i-1,j-1] + 1
                c[i,j] = min(x,y,z)
        return c[n,m]

                
