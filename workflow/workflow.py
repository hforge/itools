# -*- coding: UTF-8 -*-
# Copyright (C) 2002 Thilo Ernst  <Thilo.Ernst@dlr.de>
# Copyright (C) 2002-2004, 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

"""
The workflow module simplifies the task of writing workflow systems.

The development of a workflow system can be splitted in three steps:

 1. Define the workflow as a graph with the 'Workflow' class:

    1.1 Create an instance of the 'Workflow' class;

    1.2 Add to this instance the different states and optionally
        set the initial state;

    1.3 Add the transitions that let to go from one state to another.

 2. Define the objects that will follow the workflow:

    2.1 inherite from the 'WorkflowAware' class;

    2.2 introduce each object into the workflow with the 'enter_workflow'
        method.

 3. Associate the application semantics to the workflow aware objects
    by implementing the 'onenter', 'onleave' and 'ontrans' methods.

    Examples of "application semantics" are:

    - change the security settings of an object so it becomes public or
      private;

    - send an email to a user or a mailing list;
"""



class WorkflowError(Exception):
    pass


class Workflow(object):
    """
    This class is used to describe a workflow (actually it's just a
    graph). A workflow has states (one of them is the initial state),
    and states have transitions that go to another state.
    """

    def __init__(self):
        """
        Initialize the workflow.
        """
        self.states = {}
        self.initstate = None


    def add_state(self, name, **kw):
        """
        Adds a new state.

        The keywords argument lets to add arbitrary metadata to
        describe the transition.
        """
        self.states[name] = State(**kw)


    def set_initstate(self, name):
        """
        Sets the default initial state.
        """
        if name not in self.states:
            raise WorkflowError, "invalid initial state: '%s'" % name
        self.initstate = name


    def add_trans(self, name, state_from, state_to, **kw):
        """
        Adds a new transition, 'state_from' and 'state_to' are
        respectively the origin and destination states of the
        transition.

        The keywords argument lets to add arbitrary metadata to
        describe the transition.
        """
        transition = Transition(state_from, state_to, **kw)
        try:    
            state_from = self.states[state_from]
        except KeyError:
            raise WorkflowError, "unregistered state: '%s'" % state_from
        try:
            state_to = self.states[state_to]
        except KeyError:
            raise WorkflowError, "unregistered state: '%s'" % state_to
        state_from.add_trans(name, transition)



class State(object):
    """
    This class is used to describe a state. An state has transitions
    to other states.
    """

    def __init__(self, **kw):
        """
        Initialize the state.
        """
        self.transitions = {}
        self.metadata = kw


    def add_trans(self, name, transition):
        """
        Adds a new transition.
        """
        self.transitions[name] = transition


    def __getitem__(self, key):
        """
        Access to the metadata as a mapping.
        """
        return self.metadata.get(key)



class Transition(object):
    """
    This class is used to describe transitions. Transitions come from
    one state and go to another.
    """

    def __init__(self, state_from, state_to, **kw):
        """
        Initialize the transition.
        """
        self.state_from = state_from
        self.state_to = state_to
        self.metadata = kw


    def __getitem__(self, key):
        """
        Access to the metadata as a mapping.
        """
        return self.metadata.get(key)



class WorkflowAware(object):
    """
    Mixin class to be used for workflow aware objects. The instances of
    a class that inherits from WorkflowAware can be "within" the workflow,
    this means that they keep track of the current state of the object.

    Specific application semantics for states and transitions can be
    implemented as methods of the WorkflowAware-derived "developer 
    class". These methods get associated with the individual
    states and transitions by a simple naming scheme. For example, 
    if a workflow has two states 'private' and 'public', and a 
    transition 'publish' that goes from 'private' to 'public', 
    the following happens when the transition is executed:

      1. if implemented, the method 'onleave_private' is called
         (it is called each time the object leaves the 'private' state)

      2. if implemented, the method 'ontrans_publish' is called
         (it is called whenever this transition is executed)

      3. if implemented, the method 'onenter_public' is called
         (it is called each time the object enters the 'public' state)

    These state/transition "handlers" can also be passed arguments
    from the caller of the transition; for instance, in a web-based
    system it might be useful to have the HTTP request that triggered 
    the current transition available in the handlers.

    A simple stack with three methods, 'pushdata', 'popdata' adn 'getdata',
    is implemented. It can be used, for example, to keep record of the states
    the object has been in.
    """

    def enter_workflow(self, workflow=None, initstate=None, *args, **kw):
        """
        [Re-]Bind this object to a specific workflow, if the 'workflow'
        parameter is omitted then the object associated workflow is kept.
        This lets, for example, to specify the associate workflow with a
        class varible instead of with an instance attribute.

        The 'initstate' parameter is the workflow state that should be
        taken on initially (if omitted or None, the workflow must provide
        a default initial state).

        Extra arguments args are passed to the enter-state handler (if any)
        of the initial state. 
        """
        # Set the associated workflow
        if workflow is not None:
            self.workflow = workflow

        # Set the initial state
        if initstate is None:
            initstate = self.workflow.initstate

        if not initstate:
            raise WorkflowError, 'undefined initial state'

        if not self.workflow.states.has_key(initstate):
            raise WorkflowError, "invalid initial state: '%s'" % initstate

        self.workflow_state = initstate

        # Call app-specific enter-state handler for initial state, if any
        name = 'onenter_%s' % initstate
        if hasattr(self, name):
            getattr(self, name)(*args, **kw)


    def do_trans(self, transname, *args, **kw):
        """
        Performs a transition, changes the state of the object and
        runs any defined state/transition handlers. Extra 
        arguments are passed down to all handlers called.
        """
        # Get the workflow
        workflow = self.workflow

        # Get the current state
        state = workflow.states[self.workflow_state]
        
        try:
            # Get the new state name
            state = state.transitions[transname].state_to
        except KeyError:
            raise WorkflowError, \
                  "transition '%s' is invalid from state '%s'" \
                  % (transname, self.workflow_state)
        
        # call app-specific leave- state  handler if any
        name = 'onleave_%s' % self.workflow_state
        if hasattr(self, name):
            getattr(self, name)(*args, **kw)

        # Set the new state
        self.workflow_state = state

        # call app-specific transition handler if any
        name = 'ontrans_%s' % transname
        if hasattr(self, name):
            getattr(self, name)(*args, **kw)

        # call app-specific enter-state handler if any
        name = 'onenter_%s' % state
        if hasattr(self, name):
            getattr(self, name)(*args, **kw)


    def get_statename(self):
        """Return the name of the current state."""
        return self.workflow_state


    def get_state(self):
        """Returns the current state instance."""
        statename = self.get_statename()
        return self.workflow.states.get(statename)


##    # Implements a stack that could be used to keep a record of the
##    # object way through the workflow.
##    # A tuple is used instead of a list so it will work nice with
##    # the ZODB.
##    workflow_history = ()


##    def pushdata(self, data):
##        """
##        Adds a new element to the top of the stack.
##        """
##        self.workflow_history = self.workflow_history + (data,)


##    def popdata(self):
##        """
##        Removes and returns the top stack element.
##        """
##        if len(self.workflow_history) == 0:
##            return None
##        data = self.workflow_history[-1]
##        self.workflow_history = self.workflow_history[:-1]
##        return data


##    def getdata(self):
##        """
##        Returns the data from the top element without removing it.
##        """
##        if len(self.workflow_history) == 0:
##            return None
##        return self.workflow_history[-1]


##class Token(WorkflowAware):
##    """
##    This class should be used when the document can be in different
##    states at the same time (likely states that belong to different
##    workflows).

##    In this situation the class shouldn't inherit from WorkflowAware,
##    instead it should contain as many tokens as needed, which would
##    be the ones that follow the workflow.
##    """
