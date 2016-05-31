import django_tables2 as tables
from django_tables2.utils import A
from django.utils.html import format_html
from datetime import date
from .models import Transfer,Experiment,Frog,Permit, Notes

class ExperimentTable(tables.Table):
    #selection = tables.CheckBoxColumn(accessor="pk", orderable=False)
    id = tables.LinkColumn('frogs:experiment_detail', text='View', args=[A('pk')], verbose_name='')
    transfer_date = tables.DateColumn(verbose_name='Date Received',
                                      accessor=A('transferid.transfer_date'), format='d-M-Y')
    expt_from = tables.DateColumn(verbose_name='Expt from', format='d-M-Y')
    expt_to = tables.DateColumn(verbose_name='Expt To', format='d-M-Y')
    frogid = tables.Column(verbose_name='Frog ID', accessor=A('transferid.operationid.frogid.frogid'))
    species = tables.Column(verbose_name = 'Species',
                            accessor = A('transferid.operationid.frogid.species'))
    received = tables.Column(verbose_name='Received (ml)')
    transferred = tables.Column(verbose_name='Transferred (ml)')
    used = tables.Column(verbose_name='Used (ml)')

    class Meta:
        model = Experiment
        attrs = {"class": "ui-responsive table table-hover"}
        fields = ['expt_location','transfer_date','frogid','species','received','transferred','used','expt_from','expt_to','expt_disposed','id']


class DisposalTable(tables.Table):
    id = tables.LinkColumn('frogs:experiment_detail', text='View', args=[A('pk')], verbose_name='')
    frogid = tables.Column(verbose_name='Frog ID', accessor=A('transferid.operationid.frogid.frogid'))
    qen = tables.Column(verbose_name='QEN', accessor=A('transferid.operationid.frogid.qen'))
    disposal_date = tables.DateColumn(verbose_name="Disposal Date", format='d-M-Y')
    
    class Meta:
        model = Experiment
        attrs = {"class": "ui-responsive table table-hover"}
        fields = ['expt_location','disposal_date','qen','frogid','waste_type','waste_content','waste_qty','autoclave_indicator','autoclave_complete','disposal_sentby','id']


class TransferTable(tables.Table):
    id = tables.LinkColumn('frogs:transfer_detail', text='View', args=[A('pk')], verbose_name='')
    frogid = tables.LinkColumn('frogs:frog_detail', accessor=A('operationid.frogid.frogid'), args=[A('operationid.frogid.pk')],verbose_name='Frog ID')
    species = tables.Column(verbose_name='Species', accessor=A('operationid.frogid.species'))
    qen = tables.Column(verbose_name='QEN', accessor=A('operationid.frogid.qen'))
    sop = tables.Column(verbose_name='Transfer Approval', accessor=A('transferapproval.sop'))
    transfer_date = tables.DateColumn(verbose_name="Transfer Date", format='d-M-Y')

    class Meta:
        model = Transfer
        attrs = {"class": "ui-responsive table table-hover"}
        fields = ['frogid','species','qen','volume','transporter','method','transfer_date','transferapproval', 'sop','id']

class FrogTable(tables.Table):
    #selectfrog = tables.CheckBoxColumn(accessor='pk')
    frogid = tables.LinkColumn('frogs:frog_detail', args=[A('pk')])
    class Meta:
        model = Frog
        attrs = {"class": "ui-responsive table table-hover"}
        fields = ['frogid','tankid','gender','species','current_location','condition','remarks','qen','aec','death','disposed']
        order_by_field = 'frogid'
        sortable = True

#Generic filtered table
class FilteredSingleTableView(tables.SingleTableView):
    filter_class = None

    def get_table_data(self):
        data = super(FilteredSingleTableView, self).get_table_data()
        self.filter = self.filter_class(self.request.GET, queryset=data)
        return self.filter

    def get_context_data(self, **kwargs):
        context = super(FilteredSingleTableView, self).get_context_data(**kwargs)
        context['filter'] = self.filter
        return context



class PermitTable(tables.Table):
    id = tables.LinkColumn('frogs:permit_detail', text='View', args=[A('pk')], verbose_name='' )


    class Meta:
        model = Permit
        attrs = {"class": "ui-responsive table table-hover"}
        fields = ['aqis','qen','females','males', 'arrival_date','species','supplier','country','id']

        order_by_field = 'arrival_date'
        sortable = True


## Used in Frog Log Report
class SummingColumn(tables.Column):
    def render_footer(self, bound_column, table):
        return sum(bound_column.accessor.resolve(row) for row in table.data)

class PermitReportTable(tables.Table):
    aqis = tables.LinkColumn('frogs:permit_detail', accessor=A('aqis'),  args=[A('pk')], verbose_name='AQIS Permit #' )
    qen = tables.Column(footer="Total Frogs:")
    get_totalfrogs = SummingColumn(verbose_name="Shipped/Born")
    frogs_disposed = SummingColumn(verbose_name="Disposed")
    get_frogs_remaining = SummingColumn(verbose_name="Remaining")
    get_frogs_transferred = SummingColumn(verbose_name="Transferred")


    class Meta:
        model = Permit
        attrs = {"class": "ui-responsive table table-hover"}
        fields = ['aqis','qen','arrival_date','get_totalfrogs','frogs_disposed', 'get_frogs_transferred','get_frogs_remaining',]

        order_by_field = 'arrival_date'
        sortable = True

class OperationTable(tables.Table):
    frogid = tables.LinkColumn('frogs:frog_detail', accessor=A('frogid'), args=[A('pk')],verbose_name='Frog ID')
    num_operations = tables.Column(verbose_name="Num Ops", accessor=A('num_operations'), orderable=False)
    last_operation = tables.DateColumn(verbose_name="Last Op", format='d-M-Y', accessor=A('last_operation'), orderable=False)
   # next_operation = tables.DateColumn(verbose_name="Next Op not before", format='d-M-Y', accessor=A('next_operation'), orderable=False)
    next_operation = tables.Column(verbose_name="Next Op", accessor=A('next_operation'), orderable=False)

    def render_next_operation(self, value):
        #print('DEBUG: next_op=', value)
        delta = value - date.today()

        if delta.days == 0:
            return format_html('<span style="color:green">Today</span>')
        elif delta.days < 1:
            return format_html('<span style="color:blue">%s %s ago</span>' % (abs(delta.days),
                                   ("day" if abs(delta.days) == 1 else "days")))
        elif delta.days == 1:
            return format_html('<span style="color:red">Tomorrow</span>')
        elif delta.days > 1:
            return format_html('<span style="color:red">In %s days</span>' % delta.days)

    class Meta:
        model = Frog
        attrs = {"class": "ui-responsive table table-hover"}
        fields = ['frogid', 'num_operations', 'last_operation', 'next_operation', 'condition', 'remarks', 'tankid']

        order_by_field = '-next_operation'
        sortable = True


class NotesTable(tables.Table):
    note_date = tables.LinkColumn('frogs:notes_detail', accessor=A('note_date'), args=[A('pk')], verbose_name='Date' )
    class Meta:
        model = Notes
        attrs = {"class": "ui-responsive table table-hover"}
        fields = ['note_date','notes','initials']

        order_by_field = '-note_date'
        sortable = True