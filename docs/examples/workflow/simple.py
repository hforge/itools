
# Import from itools
from itools.workflow import Workflow, WorkflowAware


# Workflow definition
workflow = Workflow()
# Specify the workflow states
workflow.add_state('private', title=u'Private')
workflow.add_state('pending', title=u'Pending')
workflow.add_state('public', title=u'Public')
# Specify the workflow transitions
workflow.add_trans('publish', 'private', 'public', title=u'Publish')
workflow.add_trans('request', 'private', 'pending', title=u'Request')
workflow.add_trans('reject', 'pending', 'private', title=u'Reject')
workflow.add_trans('accept', 'pending', 'public', title=u'Accept')
workflow.add_trans('retire', 'public', 'private', title=u'Retire')
workflow.set_initstate('private')


class Document(WorkflowAware):

    def onleave_private(self):
        print 'LEAVE PRIVATE'


    def ontrans_request(self):
        print 'REQUEST'


    def onenter_pending(self):
        print 'ENTER PENDING'



if __name__ == '__main__':
    document = Document()
    document.enter_workflow(workflow)
    document.do_trans('request')
    document.do_trans('accept')
    state = document.get_state()
    print state['title']

    for name, transition in state.transitions.items():
        print '->', transition['title']

