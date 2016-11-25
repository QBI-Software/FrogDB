import django_filters

from .models import Permit, Frog, Transfer, Experiment


class PermitFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='iexact')
    arrival_date = django_filters.DateFromToRangeFilter(label="Arrival Date (from-to)",
                                                        widget=django_filters.widgets.RangeWidget(
                                                            attrs={'class': 'myDateClass', 'type': 'date',
                                                                   'placeholder': 'Select a date'}), )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    class Meta:
        model = Permit
        fields = ['aqis', 'qen', 'arrival_date']


class FrogFilter(django_filters.FilterSet):
    condition = django_filters.CharFilter(lookup_expr=['exact', 'iexact', 'contains'])
    remarks = django_filters.CharFilter(lookup_expr=['exact', 'iexact', 'contains'])
    gender = django_filters.ChoiceFilter(choices=[('', '---------'),
                                                  ('female', 'Female'),
                                                  ('male', 'Male')])
    death = django_filters.BooleanFilter(label="Alive", name='death', lookup_expr='alive')

    death_date = django_filters.DateFromToRangeFilter(label="Death Date (from-to)",
                                                      widget=django_filters.widgets.RangeWidget(
                                                          attrs={'class': 'myDateClass', 'type': 'date',
                                                                 'placeholder': 'Select a date'}), )
    autoclave_date = django_filters.DateFromToRangeFilter(label="Autoclave Date (from-to)",
                                                          widget=django_filters.widgets.RangeWidget(
                                                              attrs={'class': 'myDateClass', 'type': 'date',
                                                                     'placeholder': 'Select a date'}), )
    incineration_date = django_filters.DateFromToRangeFilter(label="Incineration Date (from-to)",
                                                             widget=django_filters.widgets.RangeWidget(
                                                                 attrs={'class': 'myDateClass', 'type': 'date',
                                                                        'placeholder': 'Select a date'}), )

    class Meta:
        model = Frog
        fields = '__all__'


class TransferFilter(django_filters.FilterSet):
    transfer_date = django_filters.DateFromToRangeFilter(label="Transfer Date (from-to)",
                                                         widget=django_filters.widgets.RangeWidget(
                                                             attrs={'class': 'myDateClass', 'type': 'date',
                                                                    'placeholder': 'Select a date'}), )
    frogid = django_filters.CharFilter(label="Frog ID", name='operationid', lookup_expr='frogid__frogid')
    transporter = django_filters.CharFilter(label="Transporter Name", name='transporter', lookup_expr='username')
   # transporter = django_filters.ChoiceFilter(label="Transporter Name", name='transporter',
   #    widget=django_filters.widgets.LinkWidget(
   #         choices=User.objects.filter(groups__name__in=['GeneralStaff', 'AdminStaff'])))


    class Meta:
        model = Transfer
        fields = '__all__'



class ExperimentFilter(django_filters.FilterSet):
    transfer_date = django_filters.DateFromToRangeFilter(label="Transfer Date (from-to)",
                                                         widget=django_filters.widgets.RangeWidget(
                                                             attrs={'class': 'myDateClass', 'type': 'date',
                                                                    'placeholder': 'Select a date'}), )

    class Meta:
        model = Experiment
        fields = '__all__'


##TODO Custom fields based on calculated fields
class OperationFilter(django_filters.FilterSet):
    opdate = django_filters.DateFromToRangeFilter(label="Operation Date (from-to)",
                                                  widget=django_filters.widgets.RangeWidget(
                                                      attrs={'class': 'myDateClass', 'type': 'date',
                                                             'placeholder': 'Select a date'}), )

    #  numops = django_filters.NumericRangeFilter(label="Total ops (from-to)")


    class Meta:
        model = Frog
        fields = '__all__'
        # fields = ['frogid']
        # ,'num_operations','last_operation','next_operation']
