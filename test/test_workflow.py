# -*- coding: UTF-8 -*-
# Copyright (C) 2002 Thilo Ernst  <Thilo.Ernst@dlr.de>
# Copyright (C) 2002-2003, 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
import unittest
from unittest import TestCase

# Import from itools
from itools.workflow import Workflow, WorkflowAware


# Definition of the workflow
# Create the workflow object
workflow = Workflow()

# Specify the workflow states
workflow.add_state(
    'private', description='A private document only can be reached by'
                           ' authorized users.')
workflow.add_state(
    'pending', description='A pending document awaits review from'
                           ' authorized users to be published.')
workflow.add_state(
    'public', description='A public document can be reached by even'
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



class WorkflowTestCase(TestCase):

    def test(self):
        doc = Document()
        self.assertEqual(doc.get_statename(), 'private')
        doc.do_trans('request', 'First Request')
        self.assertEqual(doc.get_statename(), 'pending')
        doc.do_trans('reject', 'First Reject')
        self.assertEqual(doc.get_statename(), 'private')
        doc.do_trans('request', 'Second Request')
        self.assertEqual(doc.get_statename(), 'pending')
        doc.do_trans('accept', 'Final Accept')
        self.assertEqual(doc.get_statename(), 'public')



class Document(WorkflowAware):

    def __init__(self):
        # Associate this object with the workflow defined above
        self.enter_workflow(workflow, None, "Just Created")
        # self.enterworkflow(workflow, 'private0', "Just created")
        # nonexisting state


    # The following methods add the specific application semantics

    # state handlers
    def onenter_private(self, msg='Oops, no message'):
        pass

    def onleave_private(self, msg):
        pass
        
    def onenter_pending(self, msg):
        pass
        
    def onleave_pending(self, msg):
        pass

    def onenter_public(self, msg):
        pass

    # transition handlers        
    def ontrans_reject(self, msg):
        pass
        
    def ontrans_request(self, msg):
        pass
        
    def ontrans_accept(self, msg):
        pass
        


if __name__ == '__main__':
    unittest.main()
