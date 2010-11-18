:mod:`itools.workflow` Workflow
*******************************

.. module:: itools.workflow
   :synopsis: Workflow

.. index:: Workflow

.. contents::


The package :mod:`itools.workflow` provides a programming interface to define
and implement *workflow systems*.


Workflow definition
===================

We define a workflow as a finite state machine. This is to say, a combination
of *states*, and *transitions* from one to other state.

.. __:
.. figure:: figures/workflow.*
    :align: center

    A Basic publication workflow represented as a directed graph.

The code below defines the workflow represented by `the figure`__::

    from itools.workflow import Workflow

    # Workflow definition
    workflow = Workflow()
    # Specify the workflow states
    workflow.add_state('private')
    workflow.add_state('pending')
    workflow.add_state('public')
    # Specify the workflow transitions
    workflow.add_trans('publish', 'private', 'public')
    workflow.add_trans('request', 'private', 'pending')
    workflow.add_trans('reject', 'pending', 'private')
    workflow.add_trans('accept', 'pending', 'public')
    workflow.add_trans('retire', 'public', 'private')
    workflow.set_initstate('private')

The class :class:`Workflow` is used to define the workflow system:

.. class:: Workflow

  .. method:: add_state(name, \*\*kw)

        This method defines a state.

  .. method:: add_trans(name, state_from, state_to, \*\*kw)

        This method defines a transition from one state to another.

  .. method:: set_initstate(name)

        To define the initial state.

Both states and transitions are identified by a name. It is possible to have
two or more transitions with the same name, if they start from different
states. A transition may start and end in the same state.


Workflow Aware objects
======================

.. class:: WorkflowAware

    A *Workflow Aware* object is one that inherits from the
    :class:`WorkflowAware` class::

        from itools.workflow import WorkflowAware

        class Document(WorkflowAware):
            pass


.. method:: WorkflowAware.enter_workflow(workflow=None, initstate=None, \*args, \*\*kw)
.. method:: WorkflowAware.do_trans(transname, \*args, \*\*kw)

    To make use of the workflow system we must initialize our workflow aware
    objects with a call to :meth:`enter_workflow`; then we will be able to
    move the object from one state to another with :meth:`do_trans`::

        >>> document = Document()
        >>> document.enter_workflow(workflow)
        >>> document.do_trans('request')
        >>> document.do_trans('accept')
        >>> print document.get_statename()
        public

.. method:: WorkflowAware.get_statename

    This method will return the name of the state the object is in.


Metadata & Introspection
========================

It is possible to add arbitrary metadata to the states and transitions
definition::

    workflow.add_state('private', title=u'Private')
    workflow.add_state('pending', title=u'Pending')
    workflow.add_state('public', title=u'Public')

    workflow.add_trans('publish', 'private', 'public',
        title=u'Publish')
    workflow.add_trans('request', 'private', 'pending',
        title=u'Request')
    workflow.add_trans('reject', 'pending', 'private',
        title=u'Reject')
    workflow.add_trans('accept', 'pending', 'public',
        title=u'Accept')
    workflow.add_trans('retire', 'public', 'private',
        title=u'Retire')

In this example we have added a title to every state and transition, but we
could have added anything else, like a description or access control
information.

To get the metadata for an state we use the method :meth:`get_state`::

    >>> state = document.get_state()
    >>> print state['title']
    Public

The method :meth:`get_state` returns the *State* object for the current
workflow state. Then we can access its metadata with the mapping interface.

Something else we can do is to find out the transitions that leave from that
state::

    >>> for name, transition in state.transitions.items():
    ...    print '->', transition['title']
    -> Retire


Actions
=======

We can associate actions to different events. Every time a transition is done,
if we have defined these actions, they will be automatically triggered. Here
they are, in the order they are called:

* **onleave_**\ *statename* Called at the beginning of the transition, where
  *statename* is the starting state.
* **ontrans_**\ *transname* Called in the middle of the transition, where
  *transname* is the transition being executed.
* **onenter_**\ *statename* Called at the end of the transition, where
  *statename* is the ending state.

And here the example, this is the way we define the actions::

    class Document(WorkflowAware):

        def onleave_private(self):
            print 'LEAVE PRIVATE'

        def ontrans_request(self):
            print 'REQUEST'

        def onenter_pending(self):
            print 'ENTER PENDING'

And here we test the code::

    >>> document = Document()
    >>> document.enter_workflow(workflow)
    >>> document.do_trans('request')
    LEAVE PRIVATE
    REQUEST
    ENTER PENDING

A much useful action would be, for example, to send an email to the reviewer
every time the publication of a document is requested.

