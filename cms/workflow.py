# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
import datetime

# Import from itools
from itools.workflow import Workflow, WorkflowAware as iWorkflowAware
from itools.stl import stl


# Workflow definition
workflow = Workflow()
# Specify the workflow states
workflow.add_state('private', title=u'Private',
                   description=(u'A private document only can be reached by'
                                u' authorized users.'))
workflow.add_state('pending', title=u'Pending',
                   description=(u'A pending document awaits review from'
                                u' authorized users to be published.'))
workflow.add_state('public', title=u'Public',
                   description=(u'A public document can be reached by even'
                                u' anonymous users.'))
# Specify the workflow transitions
workflow.add_trans('publish', 'private', 'public',
                   description=u'Publish the document.')
workflow.add_trans('request', 'private', 'pending',
                   description=u'Request the document publication.')
workflow.add_trans('unrequest', 'pending', 'private',
                   description=u'Retract the document.')
workflow.add_trans('reject', 'pending', 'private',
                   description=u'Reject the document.')
workflow.add_trans('accept', 'pending', 'public',
                   description=u'Accept the document.')
workflow.add_trans('retire', 'public', 'private',
                   description=u'Retire the document.')
# Specify the initial state (try outcommenting this)
workflow.set_initstate('private')




class WorkflowAware(iWorkflowAware):

    workflow = workflow


    ########################################################################
    # API
    ########################################################################
    def get_workflow_state(self):
        metadata = self.metadata
        if metadata.has_property('state'):
            return metadata.get_property('state')
        return self.workflow.initstate

    def set_workflow_state(self, value):
        self.set_property('state', value)

    workflow_state = property(get_workflow_state, set_workflow_state, None, '')


    def get_publication_date(self):
        # FIXME This method only has sense if the workflow has a 'public'
        # state with the intended meaning.
        state = self.get_property('state')
        if state != 'public':
            return None

        dates = []
        for transition in self.get_property('ikaaro:wf_transition'):
            date = transition.get(('dc', 'date'))
            # Be robust
            if date is None:
                continue
            dates.append(date)

        # Be robust
        if not dates:
            return None

        dates.sort()
        return dates[-1]


    ########################################################################
    # User Interface
    ########################################################################
    state_form__access__ = 'is_allowed_to_edit'
    state_form__label__ = u'State'
    state_form__sublabel__ = u'Workflow State'
    def state_form(self, context):
        namespace = {}
        # State
        namespace['statename'] = self.get_statename()
        state = self.get_state()
        namespace['state'] = self.gettext(state['title'])
        # Posible transitions
        ac = self.get_access_control()
        transitions = []
        for name, trans in state.transitions.items():
            if ac.is_allowed_to_trans(context.user, self, name) is False:
                continue
            description = self.gettext(trans['description'])
            transitions.append({'name': name, 'description': description})
        namespace['transitions'] = transitions
        # Workflow history
        transitions = []
        for transition in self.get_property('ikaaro:wf_transition'):
            date = transition[('dc', 'date')].strftime('%Y-%m-%d %H:%M')
            comments = transition[(None, 'comments')]
            # XXX The property comments should be a unicode string
            comments = unicode(comments, 'utf-8')
            transitions.append({'title': transition[(None, 'name')],
                                'date': date,
                                'user': transition[(None, 'user')],
                                'comments': comments})
        transitions.reverse()
        namespace['history'] = transitions

        handler = self.get_handler('/ui/WorkflowAware_state.xml')
        return stl(handler, namespace)


    edit_state__access__ = 'is_allowed_to_edit'
    def edit_state(self, context):
        transition = context.get_form_value('transition')
        comments = context.get_form_value('comments')
        # Check input data
        if transition is None:
            return context.come_back(u'A transition must be selected.')

        # Keep workflow history
        property = {('dc', 'date'): datetime.datetime.now(),
                    (None, 'user'): context.user.name,
                    (None, 'name'): transition,
                    (None, 'comments'): comments}

        self.set_property('ikaaro:wf_transition', property)
        # Change the state, through the itools.workflow way
        self.do_trans(transition)
        # Comeback
        return context.come_back(u'Transition done.')
