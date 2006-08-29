# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


lock_body = """<?xml version="1.0" encoding="utf-8" ?>
<d:prop xmlns:d="DAV:">
 <d:lockdiscovery>
   <d:activelock>
     <d:locktype><d:write/></d:locktype>
     <d:lockscope><d:exclusive/></d:lockscope>
     <d:depth>0</d:depth>
     <d:owner>%(owner)s</d:owner>
     <d:timeout>Second-720</d:timeout>
     <d:locktoken>
       <d:href>opaquelocktoken:%(locktoken)s</d:href>
     </d:locktoken>
   </d:activelock>
 </d:lockdiscovery>
</d:prop>
"""
