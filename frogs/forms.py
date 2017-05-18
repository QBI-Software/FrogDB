# -*- coding: UTF-8 -*-
from django.contrib.auth.forms import AuthenticationForm
from django import forms
from django.forms import Form, ModelForm, DateInput
from suit_ckeditor.widgets import CKEditorWidget
from suit.widgets import HTML5Input
from captcha.fields import CaptchaField
from .models import Permit, Frog, Operation, Transfer, Experiment, FrogAttachment, Notes, SiteConfiguration, Species, PermitAttachment, Document
from django.contrib.auth.models import User


class LoginForm(AuthenticationForm):
    class Meta:
        fields = ('username', 'password')
        widgets = {'username': forms.TextInput(attrs={'class': 'form-control', 'name': 'username'}),
                   'password': forms.PasswordInput(attrs={'class': 'form-control', 'name': 'password'})
                   }


class AxesCaptchaForm(Form):
    captcha = CaptchaField()


class PermitForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    class Meta:
        model = Permit

        fields = ('aqis',
                  'qen',
                  'arrival_date',
                  'species',
                  'females',
                  'males',
                  'supplier',
                  'country',
                  'prefix',
                  'color')
        widgets = {
            'arrival_date': DateInput(format=('%Y-%m-%d'),
                                      attrs={'class': 'myDateClass',
                                             'type': 'date',
                                             'placeholder': 'Select a date'}
                                      ),
            'color': HTML5Input(input_type='color'),
        }


class FrogForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    class Meta:
        model = Frog
        fields = ('frogid',
                  'qen',
                  'tankid',
                  'species',
                  'gender',
                  'current_location',
                  'condition',
                  'remarks',
                  'death'
                  )


class BulkFrogForm(ModelForm):
    prefix = forms.CharField(max_length=20, label="Prefix")
    startid = forms.IntegerField(label="Start ID", min_value=1, max_value=1000)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    class Meta:
        model = Frog

        fields = (
            'prefix',
            'startid',
            'qen',
            'tankid',
            'species',
            'current_location',
        )


class BulkFrogDeleteForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    class Meta:
        model = Permit
        fields = ('qen',
                  'species')


class FrogDeathForm(ModelForm):
    qs = User.objects.filter(groups__name__in=['GeneralStaff', 'AdminStaff'])
    death_recorded_by = forms.ModelChoiceField(label='Recorded By', queryset=qs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    class Meta:
        model = Frog

        fields = ('frogid',
                  'death',
                  'death_date',
                  'death_recorded_by',
                  'current_location'
                  )
        widgets = {
            'death_date': DateInput(format=('%Y-%m-%d'),
                                    attrs={'class': 'myDateClass',
                                           'type': 'date',
                                           'placeholder': 'Select a date'}
                                    ),
        }


class FrogDisposalForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    class Meta:
        model = Frog
        fields = ('frogid',
                  'disposed',
                  'autoclave_date',
                  'autoclave_run',
                  'incineration_date',
                  'current_location'
                  )
        widgets = {
            'autoclave_date': DateInput(format=('%Y-%m-%d'),
                                        attrs={'class': 'myDateClass',
                                               'type': 'date',
                                               'placeholder': 'Select a date'}
                                        ),
            'incineration_date': DateInput(format=('%Y-%m-%d'),
                                           attrs={'class': 'myDateClass',
                                                  'type': 'date',
                                                  'placeholder': 'Select a date'}
                                           ),
        }


class BulkFrogDisposalForm(ModelForm):
    qs = Frog.objects.filter(disposed=False).filter(death__isnull=False).exclude(
        death__name__contains='Alive').order_by('frogid')
    frogs = forms.ModelMultipleChoiceField(label='', queryset=qs,
                                           widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    class Meta:
        model = Frog
        fields = (
            'frogs',
            'disposed',
            'autoclave_date',
            'autoclave_run',
            'incineration_date',
            'current_location'
        )

        widgets = {
            'autoclave_date': DateInput(format=('%Y-%m-%d'),
                                        attrs={'class': 'myDateClass',
                                               'type': 'date',
                                               'placeholder': 'Select a date'}
                                        ),
            'incineration_date': DateInput(format=('%Y-%m-%d'),
                                           attrs={'class': 'myDateClass',
                                                  'type': 'date',
                                                  'placeholder': 'Select a date'}
                                           ),
        }


class FrogAttachmentForm(ModelForm):
    imgfile = forms.ImageField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    class Meta:
        model = FrogAttachment
        fields = ('frogid',
                  'imagetype',
                  'imgfile',
                  'description'
                  )
        widgets = {
            'imgfile': forms.FileInput()
        }


class PermitAttachmentForm(ModelForm):
    docfile = forms.FileField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    class Meta:
        model = PermitAttachment
        fields = ('permitid',
                  'docfile',
                  'description'
                  )
        widgets = {
            'docfile': forms.FileInput()
        }


class DocumentForm(ModelForm):
    docfile = forms.FileField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    class Meta:
        model = Document
        fields = ('docfile', 'description','order','archive')
        widgets = {
            'docfile': forms.FileInput()
        }


class OperationForm(ModelForm):
    qs = User.objects.filter(groups__name__in=['GeneralStaff', 'AdminStaff'])
    operated_by = forms.ModelChoiceField(label='Operated By', queryset=qs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    class Meta:
        model = Operation
        fields = ('frogid',
                  'opnum',
                  'opdate',
                  'anesthetic',
                  'volume',
                  'comments',
                  'operated_by')
        widgets = {
            'opdate': DateInput(format=('%Y-%m-%d'),
                                attrs={'class': 'myDateClass',
                                       'type': 'date',
                                       'placeholder': 'Select a date'}
                                ),
        }


class TransferForm(ModelForm):
    qs = User.objects.filter(groups__name__in=['GeneralStaff', 'AdminStaff'])
    transporter = forms.ModelChoiceField(label='Transported By', queryset=qs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    class Meta:
        model = Transfer
        fields = ('operationid',
                  'volume',
                  'transfer_date',
                  'transporter',
                  'method',
                  'transferapproval')
        widgets = {
            'transfer_date': DateInput(format=('%Y-%m-%d'),
                                       attrs={'class': 'myDateClass',
                                              'type': 'date',
                                              'placeholder': 'Select a date'}
                                       ),
        }


class ExperimentForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['expt_location'].widget.attrs['readonly'] = True
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    class Meta:
        model = Experiment

        fields = ('transferid',
                  'received',
                  'transferred',
                  'used',
                  'expt_from',
                  'expt_to',
                  'expt_location'
                  )
        widgets = {
            'disposal_date': DateInput(format=('%Y-%m-%d'),
                                       attrs={'class': 'myDateClass',
                                              'type': 'date',
                                              'placeholder': 'Select a date'}
                                       ),

            'expt_from': DateInput(format=('%Y-%m-%d'),
                                   attrs={'class': 'myDateClass',
                                          'type': 'date',
                                          'placeholder': 'Select a date'}
                                   ),

            'expt_to': DateInput(format=('%Y-%m-%d'),
                                 attrs={'class': 'myDateClass',
                                        'type': 'date',
                                        'placeholder': 'Select a date'}
                                 )
        }


class ExperimentDisposalForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    class Meta:
        model = Experiment
        fields = ('id',
                  'expt_disposed',
                  'disposal_sentby',
                  'disposal_date',
                  'waste_type',
                  'waste_content',
                  'waste_qty')
        widgets = {
            'disposal_date': DateInput(format=('%Y-%m-%d'),
                                       attrs={'class': 'myDateClass',
                                              'type': 'date',
                                              'placeholder': 'Select a date'}
                                       )
        }


class ExperimentAutoclaveForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    class Meta:
        model = Experiment
        fields = ('id',
                  'autoclave_indicator',
                  'autoclave_complete',
                  'autoclave_machine',
                  'autoclave_run',
                  'autoclave_comments',
                  )




class BulkExptDisposalForm(ModelForm):
    qs = Experiment.objects.filter(expt_disposed=False)
    expts = forms.ModelMultipleChoiceField(label='Select Waste',
                                           queryset=qs, widget=forms.CheckboxSelectMultiple())
    qs = User.objects.filter(groups__name__in=['GeneralStaff', 'AdminStaff'])
    disposal_sentby = forms.ModelChoiceField(label='Disposed By', queryset=qs)

    def __init__(self, *args, **kwargs):
        location = kwargs.pop('location', None)
        super(BulkExptDisposalForm, self).__init__(*args, **kwargs)
        if (location.lower() != 'aaall'):
            qs = Experiment.objects.filter(expt_disposed=False).filter(
                expt_location__building=location.upper())
            self.fields['expts'].queryset = qs
            self.fields['expts'].label = 'Select Waste stored at %s' % location.upper()
        # Adds a bootstrap class
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    class Meta:
        model = Experiment
        fields = ('expts',
                  'expt_disposed',
                  'disposal_sentby',
                  'disposal_date',
                  'waste_type',
                  'waste_content',
                  'waste_qty')

        widgets = {
            'disposal_date': DateInput(format=('%Y-%m-%d'),
                                       attrs={'class': 'myDateClass',
                                              'type': 'date',
                                              'placeholder': 'Select a date'}
                                       ),

        }


class BulkExptAutoclaveForm(ModelForm):
    qs = Experiment.objects.filter(expt_disposed=True).exclude(autoclave_complete=True)
    expts = forms.ModelMultipleChoiceField(label='Select Waste',
                                           queryset=qs, widget=forms.CheckboxSelectMultiple())

    def __init__(self, *args, **kwargs):
        location = kwargs.pop('location', None)
        super(BulkExptAutoclaveForm, self).__init__(*args, **kwargs)
        qs = Experiment.objects.filter(expt_disposed=True).exclude(autoclave_complete=True)
        label = 'Select Waste stored at ALL locations'
        if (location.lower() != 'aaall'):
            qs = qs.filter(expt_location__building=location.upper())
            label = 'Select Waste stored at %s' % location.upper()
        self.fields['expts'].queryset = qs
        self.fields['expts'].label = label
        # Adds a bootstrap class
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    class Meta:
        model = Experiment
        fields = ('expts',
                  'autoclave_indicator',
                  'autoclave_complete',
                  'autoclave_machine',
                  'autoclave_run',
                  'autoclave_comments',
                  )



class NotesForm(ModelForm):
    qs = User.objects.filter(groups__name__in=['GeneralStaff', 'AdminStaff'])
    notes_by = forms.ModelChoiceField(label='Notes By', queryset=qs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    class Meta:
        model = Notes

        fields = ('note_date',
                  'notes_species',
                  'notes',
                  'notes_by',
                  )
        widgets = {
            'note_date': DateInput(format=('%Y-%m-%d'),
                                   attrs={'class': 'myDateClass',
                                          'type': 'date',
                                          'placeholder': 'Select a date'}
                                   ),
        }


class SiteConfigurationForm(forms.ModelForm):
    class Meta:
        model = SiteConfiguration
        fields = '__all__'
        # ('site_name','report_location','report_contact_details', 'aec','maintenance_mode')
        widgets = {
            'report_contact_details': CKEditorWidget(editor_options={'startupFocus': True}),
        }


class SpeciesForm(forms.ModelForm):
    class Meta:
        model = Species
        fields = '__all__'

        widgets = {
            'generalnotes': CKEditorWidget(editor_options={'startupFocus': True}),
        }
