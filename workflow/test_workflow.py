# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2002-2003  J. David Ibáñez <jdavid@itaapy.com>
#               2002  Thilo Ernst <Thilo.Ernst@dlr.de>
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



# Python unit test
##import unittest
##from unittest import TestCase

from workflow import Workflow, WorkflowAware


# Definition of the workflow

# Create the workflow object
workflow = Workflow()

# Specify the workflow states
workflow.add_state('private',
                   description='A private document only can be reached by'
                               ' authorized users.')
workflow.add_state('pending',
                   description='A pending document awaits review from'
                               ' authorized users to be published.')
workflow.add_state('public',
                   description='A public document can be reached by even'
                               ' anonymous users.')

# Specify the workflow transitions
workflow.add_trans('request', 'private', 'pending',
                   description='Request the document publication.')
workflow.add_trans('reject', 'pending', 'private',
                   description='Reject the document.')
workflow.add_trans('accept', 'pending', 'public',
                   description='Accept the document.')

# Specify the initial state (try outcommenting this)
workflow.set_initstate('private')



class Document(WorkflowAware):
    def __init__(self):
        # Associate this object with the workflow defined above
        self.enter_workflow(workflow, None, "Just Created")
        # self.enterworkflow(workflow, 'private0', "Just created")
        # nonexisting state


    # The following methods add the specific application semantics

    # state handlers
    def onenter_private(self, msg='Oops, no message'):
        print 'onenter_private:', msg

    def onleave_private(self, msg):
        print 'onleave_private:', msg
        
    def onenter_pending(self, msg):
        print 'onenter_pending:', msg
        
    def onleave_pending(self, msg):
        print 'onleave_pending:', msg

    def onenter_public(self, msg):
        print 'Yippie! onenter_public:', msg

    # transition handlers        
    def ontrans_reject(self, msg):
        print 'ontrans_reject: ', msg
        
    def ontrans_request(self, msg):
        print 'ontrans_request: ', msg
        
    def ontrans_accept(self, msg):
        print 'ontrans_accept: ', msg
        



def test():
    print "create workflow-aware Document object..."
    doc = Document(); # use default init state
    print "State now: %s (%s)" % (doc.get_statename(),
                                  doc.get_state()['description'])
    print "do first request transition..."
    doc.do_trans('request', 'First Request')
    print "State now:", doc.get_statename()
    print "do first reject transition..."
    doc.do_trans('reject', 'First Reject')
    print "State now:", doc.get_statename()
    print "do second request transition..."
    # doc.dotrans('accept')
    doc.do_trans('request', 'Second Request')
    print "State now:", doc.get_statename()
    print "do final accept transition..."
    doc.do_trans('accept', 'Final Accept')
    print "State now:", doc.get_statename()

if __name__ == '__main__':
##    unittest.main()
    test()
