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
from datetime import datetime
from email.parser import HeaderParser
import os
from signal import signal, SIGINT
from smtplib import SMTP
from socket import gaierror
from time import sleep
import traceback

# Import from itools
from itools.uri import get_absolute_reference2
from itools import vfs
from server import get_config



class Spool(object):

    def __init__(self, target):
        target = get_absolute_reference2(target)
        self.target = target
        self.spool = target.resolve2('spool')
        self._stop = False

        # Create the folder
        spool = str(self.spool.path)
        if not vfs.exists(spool):
            vfs.make_folder(spool)

        # The SMTP host
        config = get_config(target)
        self.smtp_host = config.get_value('smtp-host')

        # The logs
        self.activity_log = open('%s/spool_log' % target.path, 'a+')
        self.error_log = open('%s/spool_error_log' % target.path, 'a+')


    def get_pid(self):
        try:
            pid = open('%s/spool_pid' % self.target.path).read()
        except IOError:
            return None

        pid = int(pid)
        try:
            # XXX This only works on Unix
            os.getpgid(pid)
        except OSError:
            return None

        return pid


    def start(self):
        # Pid
        open('%s/spool_pid' % self.target.path, 'w').write(str(os.getpid()))

        # Graceful stop
        signal(SIGINT, self.stop)

        # Go
        spool = vfs.open(self.spool)
        smtp_host = self.smtp_host
        log = self.log_activity
        while self._stop is False:
            sleep(10)
            # Find out emails to send
            locks = set()
            names = set()
            for name in spool.get_names():
                if name[-5:] == '.lock':
                    locks.add(name[:-5])
                else:
                    names.add(name)
            names.difference_update(locks)
            # Is there something to send?
            if len(names) == 0:
                continue

            # Open connection
            try:
                smtp = SMTP(smtp_host)
            except gaierror, excp:
                log('%s: "%s"' % (excp[1], smtp_host))
                continue
            except:
                self.log_error()
                continue
            # Send emails
            try:
                for name in names:
                    # Send message
                    message = spool.open(name, 'r').read()
                    headers = HeaderParser().parsestr(message)
                    subject = headers['subject']
                    from_addr = headers['from']
                    to_addr = headers['to']
                    # Send message
                    smtp.sendmail(from_addr, to_addr, message)
                    # Remove
                    spool.remove(name)
                    # Log
                    log('SENT "%s" from "%s" to "%s"' % (subject, from_addr,
                        to_addr))
            except:
                self.log_error()
            finally:
                smtp.quit()

        # Close files
        self.activity_log.close()
        self.error_log.close()
        # Remove pid file
        os.remove('%s/spool_pid' % self.target.path)


    def stop(self, n, frame):
        self._stop = True
        print 'Shutting down the mail spool (gracefully)...'


    def log_activity(self, msg):
        log = self.activity_log
        log.write('%s - %s\n' % (datetime.now(), msg))
        log.flush()


    def log_error(self):
        log = self.error_log
        # The separator
        log.write('\n')
        log.write('%s\n' % ('*' * 78))
        # The date
        log.write('DATE: %s\n' % datetime.now())
        # The traceback
        log.write('\n')
        traceback.print_exc(file=log)
        log.flush()


