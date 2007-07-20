# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
import os
from Queue import Queue
from smtplib import SMTP
from socket import gaierror
import sys
from thread import start_new_thread
from time import sleep, time

# Import from itools
from itools.uri import get_absolute_reference2
from itools import vfs
from itools.catalog import Catalog
from itools.handlers import Config, get_transaction
from itools.web import Server as BaseServer
from itools.cms.database import DatabaseFS
from itools.cms.handlers import Metadata
from itools.cms import registry
from catalog import get_to_index, get_to_unindex


def ask_confirmation(message):
    sys.stdout.write(message)
    sys.stdout.flush()
    line = sys.stdin.readline()
    line = line.strip().lower()
    return line == 'y'



def get_config(target):
    return Config('%s/config.conf' % target)



def get_root_class(root):
    # Get the root resource
    metadata = Metadata(root.resolve2('.metadata'))
    format = metadata.get_property('format')
    # Build and return the root handler
    return registry.get_object_class(format)



class Server(BaseServer):

    def __init__(self, target, address=None, port=None):
        target = get_absolute_reference2(target)
        self.target = target

        # Load the config
        config = get_config(target)

        # Load Python packages and modules
        modules = config.get_value('modules')
        if modules is not None:
            for name in modules.split():
                name = name.strip()
                exec('import %s' % name)

        # Find out the IP to listen to
        if address:
            pass
        else:
            address = config.get_value('address')

        # Find out the port to listen
        if port:
            pass
        else:
            port = config.get_value('port')
            if port is not None:
                port = int(port)

        # The database
        root = target.resolve2('database')
        cls = get_root_class(root)
        database = DatabaseFS(target.path, cls=cls)
        self.database = database
        # The catalog
        self.catalog = Catalog('%s/catalog' % target)

        # Fix the root's name
        root = database.root
        root.name = root.class_title

        # Initialize
        path = target.path
        BaseServer.__init__(self, root, address=address, port=port,
                            access_log='%s/access_log' % path,
                            error_log='%s/error_log' % path,
                            pid_file='%s/pid' % path)

        # The SMTP host
        self.smtp_host = config.get_value('smtp-host')


    def get_pid(self):
        try:
            pid = open('%s/pid' % self.target.path).read()
        except IOError:
            return None

        pid = int(pid)
        try:
            # XXX This only works on Unix
            os.getpgid(pid)
        except OSError:
            return None

        return pid


    #######################################################################
    # EMail Out Queue
    #######################################################################
    def send_email_yes(self, from_addr, to_addr, message):
        self.email_queue.put((from_addr, to_addr, message, time()))


    def send_email_no(self, from_addr, to_addr, message):
        raise RuntimeError, 'Sending emails is not enabled.'


    def email_thread(self):
        queue = self.email_queue
        smtp_host = self.smtp_host
        while True:
            # Next message
            from_addr, to_addr, message, wait = queue.get()
            # Wait
            wait = wait - time()
            if wait > 0:
                sleep(wait)
            # Open connection
            try:
                smtp = SMTP(smtp_host)
            except gaierror:
                queue.put((from_addr, to_addr, message, time() + 10))
                continue
            except:
                self.log_error()
                continue
            # Send email
            try:
                smtp.sendmail(from_addr, to_addr, message)
            except:
                self.log_error()
            finally:
                smtp.quit()


    #######################################################################
    # Override
    #######################################################################
    def get_databases(self):
        return [self.database, self.catalog]


    def before_commit(self):
        catalog = self.catalog
        # Unindex Handlers
        to_unindex = get_to_unindex()
        for path in to_unindex:
            catalog.unindex_document(path)
        to_unindex.clear()

        # Index Handlers
        to_index = get_to_index()
        for handler in to_index:
            catalog.index_document(handler)
        to_index.clear()

        # XXX Versioning
        transaction = get_transaction()
        for handler in list(transaction):
            if hasattr(handler, 'before_commit'):
                handler.before_commit()


    def start(self):
        # Email
        if self.smtp_host is None:
            self.send_email = self.send_email_no
            print "Warning: the configuration variable 'smtp-host' is missing."
        else:
            self.send_email = self.send_email_yes
            self.email_queue = Queue(0)
            start_new_thread(self.email_thread, ())
        # Web
        BaseServer.start(self)

