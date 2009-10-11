# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from email.charset import add_charset, add_codec, QP
from email.header import Header
from email.mime.application import MIMEApplication
from email.MIMEImage import MIMEImage
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.parser import HeaderParser
from email.Utils import formatdate
from os import fdopen
from smtplib import SMTP, SMTPRecipientsRefused, SMTPResponseException
from socket import gaierror
from tempfile import mkstemp
from traceback import format_exc

# Import from pygobject
from gobject import idle_add, timeout_add_seconds

# Import from itools
from itools.log import log_info, log_warning, log_error
from itools import vfs


# Force email to send UTF-8 mails in plain text
add_charset('utf-8', QP, None, 'utf-8')
add_codec('utf-8', 'utf_8')



class MailSpool(object):

    def __init__(self, spool, smtp_from, smtp_host, smtp_login, smtp_password):
        self.spool = spool
        self.smtp_from = smtp_from
        self.smtp_host = smtp_host
        self.smtp_login = smtp_login
        self.smtp_password = smtp_password


    def send_email(self, to_addr, subject, from_addr=None, text=None,
                   html=None, encoding='utf-8', return_receipt=False,
                   attachment=None):
        # Check input data
        if not isinstance(subject, unicode):
            raise TypeError, 'the subject must be a Unicode string'
        if len(subject.splitlines()) > 1:
            raise ValueError, 'the subject cannot have more than one line'
        if text and not isinstance(text, unicode):
            raise TypeError, 'the text must be a Unicode string'
        if html and not isinstance(html, unicode):
            raise TypeError, 'the html must be a Unicode string'

        # Figure out the from address
        if not from_addr:
            from_addr = self.smtp_from

        # Build the message
        message = MIMEMultipart('related')
        message['Subject'] = Header(subject.encode(encoding), encoding)
        message['Date'] = formatdate(localtime=True)
        for key, addr in [('From', from_addr), ('To', to_addr)]:
            if type(addr) is tuple:
                real_name, address = addr
                addr = '%s <%s>' % (Header(real_name, encoding), address)
            message[key] = addr
        # Return Receipt
        if return_receipt is True:
            # Somewhat standard
            message['Disposition-Notification-To'] = from_addr
            # XXX For Outlook 2000
            message['Return-Receipt-To'] = from_addr
        # Create MIMEText
        if html:
            html = html.encode(encoding)
            message_html = MIMEText(html, 'html', _charset=encoding)
        if text:
            text = text.encode(encoding)
            message_text = MIMEText(text, _charset=encoding)
        # Attach MIMETEXT to message
        if text and html:
            message_alternative = MIMEMultipart('alternative')
            message.attach(message_alternative)
            message_alternative.attach(message_text)
            message_alternative.attach(message_html)
        elif html:
            message.attach(message_html)
        elif text:
            message.attach(message_text)
        # Attach attachment
        if attachment:
            subtype = attachment.get_mimetype()
            data = attachment.to_str()
            if subtype[:6] == 'image/':
                subtype = subtype[6:]
                mime_cls = MIMEImage
            else:
                mime_cls = MIMEApplication
            message_attachment = mime_cls(data, subtype)
            message_attachment.add_header('Content-Disposition', 'attachment',
                                          filename=attachment.name)
            message.attach(message_attachment)
        # Send email
        self.send_raw_email(message)


    def send_raw_email(self, message):
        if not self.smtp_host:
            raise ValueError, 'the SMTP host is not defined'

        tmp_file, tmp_path = mkstemp(dir=self.spool)
        with fdopen(tmp_file, 'w') as file:
            file.write(message.as_string())

        idle_add(self.smtp_send_idle_callback)


    def _smtp_send(self):
        smtp_host = self.smtp_host

        # Find out emails to send
        locks = set()
        names = set()
        for name in vfs.get_names(self.spool):
            if name[-5:] == '.lock':
                locks.add(name[:-5])
            else:
                names.add(name)
        names.difference_update(locks)
        # Is there something to send?
        if len(names) == 0:
            return 0

        # Open connection
        try:
            smtp = SMTP(smtp_host)
            if self.smtp_login and self.smtp_password:
                smtp.login(self.smtp_login, self.smtp_password)
        except gaierror, excp:
            log_warning('Failed to connect to SMTP host (%s)' % smtp_host,
                        domain='itools.mail')
            return 1
        except Exception:
            log_error('Failed to connect to SMTP host (%s)' % smtp_host,
                      domain='itools.mail')
            return 1

        # Send emails
        error = 0
        for name in names:
            try:
                # Send message
                message = spool.open(name).read()
                headers = HeaderParser().parsestr(message)
                subject = headers['subject']
                from_addr = headers['from']
                to_addr = headers['to']
                # Send message
                smtp.sendmail(from_addr, to_addr, message)
                # Remove
                spool.remove(name)
                # Log
                log_msg = 'Email "%s" sent from "%s" to "%s"'
                log_info(log_msg % (subject, from_addr, to_addr),
                         domain='itools.mail')
            except (SMTPRecipientsRefused, SMTPResponseException):
                # The SMTP server returns an error code or the recipient
                # addresses has been refused
                log_error('Failed to send email', domain='itools.mail')
                # Remove
                spool.remove(name)
                error = 1
            except Exception:
                # Other error ...
                log_error('Failed to send email', domain='itools.mail')
                error = 1

        # Close connection
        smtp.quit()

        return error


    def smtp_send_idle_callback(self):
        # Error: try again later
        if self._smtp_send() == 1:
            timeout_add_seconds(60, self.smtp_send_time_callback)

        return False


    def smtp_send_time_callback(self):
        # Error: keep trying
        if self._smtp_send() == 1:
            return True

        return False


    def connect_to_loop(self):
        idle_add(self.smtp_send_idle_callback)

