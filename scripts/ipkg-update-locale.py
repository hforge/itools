# -*- coding: UTF-8 -*-
# Copyright (C) 2006, 2010 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2006-2010 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2007-2008, 2010 Sylvain Taverne <taverne.sylvain@gmail.com>
# Copyright (C) 2008 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2008 Wynand Winterbach <wynand.winterbach@gmail.com>
# Copyright (C) 2009 Dumont Sébastien <sebastien.dumont@itaapy.com>
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

# Import from itools
import itools
from itools.database.ro import ro_database
from itools.pkg import update_locale


if __name__ == '__main__':
    # The command line parser
    version = f'itools {itools.__version__}'
    description = ('Updates the message catalogs (POT and PO files) in the'
                   ' "locale" directory, with the messages found in the'
                   ' source.')
    parser = OptionParser('%prog', version=version, description=description)

    parser.add_option('-s', '--srx',
                      help='Use an other SRX file than the default one.')

    options, args = parser.parse_args()
    if len(args) != 0:
        parser.error('incorrect number of arguments')

    # The SRX file
    if options.srx is not None:
        srx_handler = ro_database.get_handler(options.srx)
    else:
        srx_handler = None
    # Update locale
    exclude_folders = ('archive', 'docs', 'skeleton', 'test')
    update_locale(srx_handler, exclude_folders)
