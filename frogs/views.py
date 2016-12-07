import trml2pdf
import datetime
from axes.utils import reset
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME, login, logout
from django.contrib.auth import views
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse_lazy, reverse
from django.db import IntegrityError
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect, resolve_url, render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views import generic
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import FormView, RedirectView
from django_tables2 import RequestConfig
from django.db.models import Sum
from ipware.ip import get_ip

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
try:
    import urlparse
except ImportError:
    from urllib import parse as urlparse # python3 support
### Local imports ###############################################################################
from .models import Permit, Frog, Operation, Transfer, Experiment, FrogAttachment, Notes, Location, Species, Deathtype, SiteConfiguration, Qap, PermitAttachment, Document
from .forms import PermitForm, FrogForm, FrogDeathForm, FrogDisposalForm, OperationForm, TransferForm, ExperimentForm, FrogAttachmentForm, BulkFrogForm, BulkFrogDeleteForm, ExperimentDisposalForm, ExperimentAutoclaveForm, BulkFrogDisposalForm, BulkExptDisposalForm, NotesForm, AxesCaptchaForm, BulkExptAutoclaveForm, PermitAttachmentForm, DocumentForm
from .tables import ExperimentTable,PermitTable,FrogTable,TransferTable, OperationTable,DisposalTable, FilteredSingleTableView, NotesTable, PermitReportTable, DocumentTable
from .filters import FrogFilter, PermitFilter, TransferFilter, ExperimentFilter, OperationFilter
###AUTHORIZATION CLASS ##########################################################################
#from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
# import the logging library
import logging


# Get an instance of a logger
logger = logging.getLogger(__name__)

   
## Index page
class IndexView(generic.ListView):
    template_name ='frogs/index.html'
    context_object_name = 'datalist'


    def get_shipment_count(self):
        return Permit.objects.count()

    def get_frog_count(self):
        return Frog.objects.count()

    def get_transfer_count(self):
        return Transfer.objects.count()

    def get_operations_ready_count(self):
        alive = Frog.objects.filter(death__alive=True) \
            .filter(gender='female').exclude(condition=True)
        #print("DEBUG: Alive=", alive.count())
        ready = []
        for f in alive:
            if (f.next_operation_OK()):
                ready.append(f)

        #print("DEBUG: Ready=", len(ready))
        return len(ready)

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['shipment_list']= self.get_shipment_count()
        context['frog_list'] = self.get_frog_count()
        context['op_list']= self.get_operations_ready_count()
        context['species'] = Species.objects.all()
        return context

    def get_queryset(self):
        """Return the all shipments"""
        return Permit.objects.all()

## Login
class LoginView(FormView):
    """
    Provides the ability to login as a user with a username and password
    """
    template_name = 'frogs/index.html'
    success_url = '/frogs'
    form_class = AuthenticationForm
    redirect_field_name = REDIRECT_FIELD_NAME

    @method_decorator(sensitive_post_parameters('password'))
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        # Sets a test cookie to make sure the user has cookies enabled
        request.session.set_test_cookie()

        return super(LoginView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        if user is not None:
            msg = 'User: %s' % user
            if user.is_active:
                login(self.request, user)
                msg = '% has logged in' % msg
                logger.info(msg)
            else:
                # Return a 'disabled account' error message
                form.add_error = 'Your account has been disabled. Please contact admin.'
                msg = '% has disabled account' % msg
                logger.warning(msg)

        else:
            # Return an 'invalid login' error message.
            form.add_error = 'Login credentials are invalid. Please try again'
            msg = 'Login failed with invalid credentials'
            logger.error(msg)

        # If the test cookie worked, go ahead and
        # delete it since its no longer needed
        self.check_and_delete_test_cookie()
        return super(LoginView, self).form_valid(form)

    def form_invalid(self, form):
        """
        The user has provided invalid credentials (this was checked in AuthenticationForm.is_valid()). So now we
        set the test cookie again and re-render the form with errors.
        """
        self.set_test_cookie()
        return super(LoginView, self).form_invalid(form)

    def set_test_cookie(self):
        self.request.session.set_test_cookie()

    def check_and_delete_test_cookie(self):
        if self.request.session.test_cookie_worked():
            self.request.session.delete_test_cookie()
            return True
        return False

    def get_success_url(self):
        if self.success_url:
            redirect_to = self.success_url
        else:
            redirect_to = self.request.POST.get(
                self.redirect_field_name,
                self.request.GET.get(self.redirect_field_name, ''))

        netloc = urlparse.urlparse(redirect_to)[1]
        if not redirect_to:
            redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)
        # Security check -- don't allow redirection to a different host.
        elif netloc and netloc != self.request.get_host():
            redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)
        return redirect_to
        #return reverse(redirect_to)


class LogoutView(RedirectView):
    """
    Provides users the ability to logout
    """
    #template_name = 'frogs/index.html'
    successurl = '/frogs'

    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect(self.successurl)

def locked_out(request):
    if request.POST:
        form = AxesCaptchaForm(request.POST)
        if form.is_valid():
            ip = get_ip(request)
            if ip is not None:
                msg = "User locked out with IP address=%s" % ip
                logger.warning(msg)
                reset(ip=ip)

            return HttpResponseRedirect(reverse_lazy('frogs:index'))
    else:
        form = AxesCaptchaForm()

    return render_to_response('frogs/locked.html', dict(form=form), context_instance=RequestContext(request))

def change_password(request):
    template_response = views.password_change(request)
    # Do something with `template_response`
    return template_response

def csrf_failure(request, reason=""):
    ctx = {'title': 'CSRF Failure', 'message': 'Your browser does not accept cookies and this can be a problem in ensuring a secure connection.'}
    template_name= 'admin/csrf_failure.html'
    return render_to_response(template_name, ctx)
###########################################################################################
#### PERMITS/SHIPMENTS

class PermitList(LoginRequiredMixin, generic.ListView):
    template_name = 'frogs/shipment/shipment_list.html'
    context_object_name = 'shipment_list'
    raise_exception = True

    def get_queryset(self):
        table = PermitTable(Permit.objects.order_by('-arrival_date'))
        RequestConfig(self.request, paginate={"per_page": 10}).configure(table)
        return table

class PermitDetail(LoginRequiredMixin, generic.DetailView):
    model = Permit
    context_object_name = 'shipment'
    template_name = 'frogs/shipment/shipment_view.html'
    raise_exception = True

class PermitFilterView(FilteredSingleTableView):
    model = Permit
    table_class = PermitTable
    filter_class = PermitFilter

class PermitCreate(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    model = Permit
    template_name = 'frogs/shipment/shipment_create.html'
    form_class = PermitForm
    raise_exception = True
    success_url = reverse_lazy('frogs:permit_list')
    permission_required = 'frogs.permit.can_add_permit'

class PermitUpdate(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = Permit
    form_class = PermitForm
    template_name = 'frogs/shipment/shipment_create.html'
    success_url = reverse_lazy('frogs:permit_list')
    raise_exception = True
    permission_required = 'frogs.permit.can_change_permit'

class PermitDelete(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    model = Permit
    success_url = reverse_lazy("frogs:permit_list")
    raise_exception = True
    template_name = 'frogs/shipment/permit_confirm_delete.html'
    permission_required = 'frogs.permit.can_delete_permit'


class PermitAttachmentView(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    model = PermitAttachment
    form_class = PermitAttachmentForm
    context_object_name = 'permit'
    template_name = 'frogs/shipment/shipment_upload.html'
    raise_exception = True
    permission_required = 'frogs.permit_attachment.can_add_permit_attachment'

    def get_success_url(self):
        return reverse('frogs:permit_detail', args=[self.object.permitid.pk])

    def get_initial(self):
        fid = self.kwargs.get('permitid')
        permit = Permit.objects.get(pk=fid)
        return {'permitid': permit}

class PermitAttachmentDelete(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    model = PermitAttachment
    raise_exception = True
    template_name = 'frogs/shipment/permitattachment_confirm_delete.html'
    permission_required = 'frogs.permit_attachment.can_delete_permit_attachment'

    def get_success_url(self):
        return reverse('frogs:permit_detail', args=[self.object.permitid.pk])


# def download(request, permitattachmentid):
#     f = PermitAttachment.objects.get(pk=permitattachmentid)
#     print("DEBUG: download=", f.docfile)
#     #f.write(p.body)
#     fname = os.path.basename(f.docfile.name)
#     print("DEBUG: filename=", fname)
#     docname = os.path.join(settings.MEDIA_ROOT, fname)
#     print("DEBUG: pathname=", docname)
#     print("DEBUG: file exists=", os.path.exists(docname))
#     size = os.path.getsize(docname)
#     print("DEBUG: file size=",size)
#     fw = FileWrapper(open(docname))
#     print("DEBUG: fw=", fw)
#     response = HttpResponse(fw, content_type='text/plain')
#     response['Content-Disposition'] = 'attachment; filename=%s' % fname
#     response['Content-Length'] = size
#     response['X-SendFile-Encoding: url'] = docname
#
#     return response


############################################################################
# Frog Log Quarantine Report
class ReportTableView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'frogs/shipment/report_froglog.html'
    raise_exception = True

    def get_queryset(self, **kwargs):
        species = self.kwargs.get('species')
        if (species == None):
            qs = Permit.objects.all()
        else:
            qs = Permit.objects.filter(species__name=species)
        qs.order_by('arrival_date')
        return qs

    def get_context_data(self, **kwargs):
        context = super(ReportTableView, self).get_context_data(**kwargs)
        table = PermitReportTable(self.get_queryset())
        RequestConfig(self.request).configure(table)
        species = self.kwargs.get('species')
        sp = Species.objects.get(name=species)
        config = SiteConfiguration.objects.get()
        limit = config.notes_limit
        notes_qs = Notes.objects.filter(notes_species__name=species).order_by('-note_date')[:limit]
        locations = []
        for loc in Location.objects.all():
            if (Frog.objects.filter(species__name=species).filter(current_location=loc).count() > 0):
                locations.append(loc)

        context['species'] = species
        context['frognotes_table'] = notes_qs
        context['generalnotes'] = sp.generalnotes
        context['table'] = table
        context['locations'] = locations
        context['genders'] =['female','male']
        context['frogs_table']= Frog.objects.filter(species__name=species).order_by('frogid')
        return context

    # def pdfview(self, request):
    #     resp = HttpResponse(content_type='application/pdf')
    #     context = self.get_context_data()
    #     result = generate_pdf(self.template_name, file_object=resp, context=context)
    #     return result



########## FROGS ############################################
class FrogList(LoginRequiredMixin, generic.ListView):
    template_name = 'frogs/frog/frog_minilist.html'
    context_object_name = 'table'
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super(FrogList, self).get_context_data(**kwargs)
        list_title="Frogs List"
        if (self.kwargs.get('shipmentid')):
            sid = self.kwargs.get('shipmentid')
            shipment = Permit.objects.get(pk=sid)
            list_title = "Frogs for QEN %s" % shipment.qen
        context['list_title'] = list_title
        return context

    def get_queryset(self):
        #print('DEBUG:kwargs', self.kwargs)
        qs = Frog.objects.all().order_by('frogid')
        if (self.kwargs.get('shipmentid')):
            sid = self.kwargs.get('shipmentid')
            shipment = Permit.objects.get(pk=sid)
            qs = qs.filter(qen=shipment)
            #print('DEBUG:frogs per shipment=', qs.count())
        table = FrogTable(qs)
        RequestConfig(self.request, paginate={"per_page": 20}).configure(table)
        return table

class FrogFilterView(LoginRequiredMixin, FilteredSingleTableView):
    template_name = 'frogs/frog/frog_list.html'
    model = Frog
    table_class = FrogTable
    filter_class = FrogFilter
    raise_exception = True


class FrogDetail(LoginRequiredMixin, generic.DetailView):
    model = Frog
    context_object_name = 'frog'
    template_name = 'frogs/frog/frog_view.html'
    raise_exception = True

class FrogCreate(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    model = Frog
    template_name = 'frogs/frog/frog_create.html'
    form_class = FrogForm
    raise_exception = True
    permission_required = 'frogs.add_frog'

    def form_valid(self, form):
        try:
            return super(FrogCreate, self).form_valid(form)
        except IntegrityError as e:
            msg = 'Database Error: Unable to create Frog - see Administrator'
            form.add_error('frogid',msg)
            logger.warning(msg)
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('frogs:frog_detail', args=[self.object.id])

class FrogUpdate(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = Frog
    form_class = FrogForm
    template_name = 'frogs/frog/frog_create.html'
    raise_exception = True
    permission_required = 'frogs.change_frog'

    def get_success_url(self):
        return reverse('frogs:frog_detail', args=[self.object.id])

class FrogDelete(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    model = Frog
    success_url = reverse_lazy("frogs:frog_list")
    template_name = 'frogs/frog/frog_confirm_delete.html'
    raise_exception = True
    permission_required = 'frogs.delete_frog'

class FrogDeath(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = Frog
    form_class = FrogDeathForm
    context_object_name = 'frog'
    template_name = 'frogs/frog/frog_death.html'
    raise_exception = True
    permission_required = 'frogs.change_frog'

    def get_success_url(self):
        return reverse('frogs:frog_detail', args=[self.object.id])

class FrogDisposal(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = Frog
    form_class = FrogDisposalForm
    context_object_name = 'frog'
    template_name = 'frogs/frog/frog_disposal.html'
    raise_exception = True
    permission_required = 'frogs.change_frog'

    def get_success_url(self):
        return reverse('frogs:frog_detail', args=[self.object.id])

class FrogAttachment(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    model = FrogAttachment
    form_class = FrogAttachmentForm
    context_object_name = 'frog'
    template_name = 'frogs/frog/frog_upload.html'
    raise_exception = True
    permission_required = 'frogs.add_frogattachment'

    def get_success_url(self):
        return reverse('frogs:frog_detail', args=[self.object.frogid.pk])

    def get_initial(self):
        fid = self.kwargs.get('frogid')
        frog = Frog.objects.get(pk=fid)
        return {'frogid': frog}

class FrogBulkCreate(LoginRequiredMixin, PermissionRequiredMixin, generic.FormView):
    model = Frog
    form_class = BulkFrogForm
    template_name = "frogs/frog/bulkfrog_create.html"
    success_url = reverse_lazy("frogs:frog_list")
    fid = None
    raise_exception = True
    permission_required = 'frogs.add_frog'

    def form_valid(self, form):
        #Get shipment: number female/male
        self.fid = self.kwargs.get('shipmentid')
        shipment = Permit.objects.get(pk=self.fid)
        females = shipment.females
        males = shipment.males
        prefix = form.cleaned_data['prefix']
        startid = int(form.cleaned_data['startid'])
        qen = form.cleaned_data['qen']
        tankid = int(form.cleaned_data['tankid'])
        species = form.cleaned_data['species']
        location = form.cleaned_data['current_location']
       # aec = form.cleaned_data['aec']
        deathtype = Deathtype.objects.filter(name='Alive')[0]
        bulk_list=[]
        #Check initial prefix unique
        #firstfrogid = "%s%d" % (prefix, startid)
        msg = 'BulkFrog: generating records from QEN=%s' % shipment.qen
        logger.info(msg)
        #Generate Frog objects
        for i in range(startid,(startid + females + males)):
            gender = 'female'
            if (i > (startid + females)):
                gender = 'male'
            frogid = "%s%d" % (prefix, i)
            frog = Frog()
            frog.frogid=frogid
            frog.qen=qen
            frog.tankid=tankid
            frog.species=species
            frog.gender=gender
            frog.current_location=location
            frog.condition= ''
            frog.remarks='auto-generated'
            if (deathtype is not None):
                frog.death=deathtype
           # frog.aec=aec
            #print('DEBUG: Generated:Frog=',frog.frogid)
            bulk_list.append(frog)

        try:
            Frog.objects.bulk_create(bulk_list)
            msg = 'BulkFrog: frogs generated=%d from QEN=%s' % (len(bulk_list), shipment.qen)
            logger.info(msg)
            return super(FrogBulkCreate, self).form_valid(form)
        except IntegrityError:
            return super(FrogBulkCreate, self).form_invalid(form)

    def get_initial(self):
        fid = self.kwargs.get('shipmentid')
        shipment = Permit.objects.get(pk=fid)
        #print('DEBUG: Shipment qen:', shipment.qen)
        return {'qen': shipment, 'species': shipment.species, 'prefix': shipment.prefix}

    def get_success_url(self):
        return reverse('frogs:frog_list_byshipment',kwargs={'shipmentid': self.fid})


#Delete frogs from a shipment
class FrogBulkDelete(LoginRequiredMixin, PermissionRequiredMixin, generic.FormView):
    template_name = 'frogs/frog/bulkfrog_confirm_delete.html'
    form_class=BulkFrogDeleteForm
    raise_exception = True
    permission_required = 'frogs.delete_frog'


    def post(self, request, *args, **kwargs):
        froglist = self.get_queryset()
        r = froglist.delete()
        message = 'Successfully deleted ' + str(r[0]) + ' frogs'
        #print('DELETED: ', message, ' r=', r)
        logger.info(message)
        return render(request, self.template_name, {'msg': message})

    def get_context_data(self, **kwargs):
        context = super(FrogBulkDelete, self).get_context_data(**kwargs)
        fid = self.kwargs.get('shipmentid')
        shipment = Permit.objects.get(pk=fid)
        froglist = self.get_queryset()
        context.update({
            'qen': shipment.qen,
            'species' : shipment.species,
            'pk': shipment
        })
        if (len(froglist) > 0):
            context['frogs'] = len(froglist)
        else:
            context['msg'] = 'There are NO frogs to delete for this shipment (QEN=%s)' % shipment.qen
        return context

    def get_queryset(self):
        fid = self.kwargs.get('shipmentid')
        shipment = Permit.objects.get(pk=fid)
        return Frog.objects.filter(qen=shipment)

    def get_success_url(self):
        return reverse('frogs:frog_list')

# Bulk entry for disposal of frogs
class FrogBulkDisposal(LoginRequiredMixin, PermissionRequiredMixin, generic.FormView):
    template_name = 'frogs/frog/frog_bulkdisposal.html'
    form_class = BulkFrogDisposalForm
    model = Frog
    raise_exception = True
    permission_required = 'frogs.change_frog'

    def form_valid(self, form):
        bulkfrogs = form.cleaned_data['frogs']
        msg = 'BulkFrog: updating frog records=%d' % len(bulkfrogs)
        logger.info(msg)
        # Generate Frog objects
        for pk in bulkfrogs:
            #print('Updating frog:', pk)
            frog = pk #Frog.objects.get(pk=pk)
            frog.disposed = form.cleaned_data['disposed']
            frog.autoclave_date = form.cleaned_data['autoclave_date']
            frog.autoclave_run = form.cleaned_data['autoclave_run']
            frog.incineration_date = form.cleaned_data['incineration_date']
            #print('Updated:Frog=', frog.frogid)
            frog.save()

        return super(FrogBulkDisposal, self).form_valid(form)


    def get_success_url(self):
        return reverse('frogs:frog_list')

########## PDF REPORTS IN RML ############################################
class FrogReport(LoginRequiredMixin, generic.DetailView):
    model = Frog
    context_object_name = 'frog'
    template_name = 'frogs/reports/frogreport.rml'
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super(FrogReport, self).get_context_data(**kwargs)
        fid = self.kwargs.get('pk')
        frog = Frog.objects.get(pk=fid)
        context['hostname'] = 'http://%s' % self.request.get_host()
        context['name'] = frog.frogid
        context['pdfname'] = 'FrogReport_%s.pdf' % frog.frogid.rstrip()
        context['printdatetime'] = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
        return context


    def render_to_response(self, context, **response_kwargs):
        """Returns PDF as a binary stream."""
        rml = render_to_string(self.get_template_names(),
                               self.get_context_data())
        rml = rml.encode('utf8')
        #print("DEBUG: rml=",rml)

        # send the response
        response = HttpResponse(content_type='application/pdf')
        response.write(trml2pdf.parseString(rml))
        response['Content-Disposition'] = 'attachment; filename=%s' % context['pdfname']
        return response

###RML Parser helper - hack unfortunately to handle embedded html TODO: Another method to reformat html
def rml_html_clean(para):
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(para, 'html.parser')
    print("text:", soup.get_text())
    parts = [text.replace('\xa0', '') for text in soup.stripped_strings]
    p = []
    t0 =0
    for i,t in enumerate(parts):
        #print('DEBUG: SEARCH: ', t)
        if t[-1] =='(':
            t0 = 1 #append next
        elif t0:
            #print('DEBUG: matched: ', t)
            t = parts[i-1] + t + parts[i+1]
            p.append(t)
            t0 = 0
        elif t != ')':
            p.append(t)
            t0 = 0
    #print("DEBUG:", p)
    return p;



class SpeciesReport(LoginRequiredMixin, generic.TemplateView):
    model = Species
    context_object_name = 'species'
    template_name = 'frogs/reports/speciesreport.rml'
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super(SpeciesReport, self).get_context_data(**kwargs)
        species = self.kwargs.get('species')
        sp = Species.objects.get(name=species)
        config = SiteConfiguration.objects.get()
        limit = config.notes_limit
        notes_qs = Notes.objects.filter(notes_species=sp).order_by('-note_date')[:limit]
        locations = []
        for loc in Location.objects.all():
            if (Frog.objects.filter(species=sp).filter(current_location=loc).count() > 0):
                locations.append(loc)
        context['pdfname'] = 'QBIXenopusRegister_%s.pdf' % species.rstrip()
        context['printdatetime'] = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
        permits = Permit.objects.filter(species=sp)
        totals = Permit.objects.filter(species=sp).aggregate(Sum('females'), Sum('males'))
        totals['total'] = totals['females__sum'] + totals['males__sum']
        totals['females_remain'] =0
        totals['males_remain'] = 0
        totals['disposed'] = 0
        for p in permits:
            totals['females_remain'] += p.get_females_remaining()
            totals['males_remain'] += p.get_males_remaining()
            totals['disposed'] += p.frogs_disposed()

        context['hostname'] = 'http://%s' % self.request.get_host()
        context['species'] = species
        context['config'] = config
        context['contacts'] = rml_html_clean(config.report_contact_details)
        context['frognotes_table'] = notes_qs
        context['generalnotes'] = sp.generalnotes
        context['permits'] = permits
        context['totals'] = totals
        context['locations'] = locations
        context['genders'] =['female','male']
        context['frogs_table']= Frog.objects.filter(species=sp).order_by('frogid')
        return context

    def render_to_response(self, context, **response_kwargs):
        """Returns PDF as a binary stream."""
        rml = render_to_string(self.get_template_names(),
                               self.get_context_data())
        rml = rml.encode('utf8')
        # print("DEBUG: rml=",rml)

        # send the response
        response = HttpResponse(content_type='application/pdf')
        response.write(trml2pdf.parseString(rml))
        response['Content-Disposition'] = 'attachment; filename=%s' % context['pdfname']
        return response


########## OPERATIONS ############################################

# Filtered listing

class OperationFilterView(LoginRequiredMixin, FilteredSingleTableView):
    template_name = 'frogs/operation/operation_summary.html'
    model = Frog
    table_class = OperationTable
    filter_class = OperationFilter
    raise_exception = True

    def get_context_data(self, **kwargs):
        spp = self.kwargs.get('sp')
        if (spp is None):
            spp = 'all'
        #print("DEBUG: sp=", spp)
        context = super(OperationFilterView, self).get_context_data(**kwargs)
        spnames={'all':'All'}
        #ALL
        qs = Frog.objects.filter(gender='female') \
            .filter(death__name='Alive').order_by('frogid')

        #SPP
        frogspecies = Species.objects.values_list('name', flat=True)
        for s in frogspecies:
            spnames[s.split('.')[1]]= s

        fsp = "X.%s" % spp
        if (fsp in frogspecies):
            qs = qs.filter(species__name=fsp)

        table = OperationTable(qs)
        RequestConfig(self.request, paginate={"per_page": 20}).configure(table)

        context['species'] = spp
        context['summaries'] = table
        context['splist'] = sorted(spnames.items()) #speciestables
        return context


class OperationStatsView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'frogs/operation/operation_statistics.html'
    raise_exception = True

    def get_queryset(self, **kwargs):
        qs = Frog.objects.filter(gender='female').filter(death__alive=True)
        return qs

    def get_context_data(self, **kwargs):
        context = super(OperationStatsView, self).get_context_data(**kwargs)
        config = SiteConfiguration.objects.get()
        qs = self.get_queryset()
        frogspecies = Species.objects.all()
        totals = []
        operative=[]
        isolation=[]
        observation=[]
        condition=[]
        actualoperative=[]
        sp_left = []
        sp_opstates=[]
        for sp in frogspecies:
            keys = range(0,config.max_ops+2)

            opstates = {k:0 for k in keys}
            num = 0
            #print("DEBUG:Ops=", opstates)
            qs_sp = qs.filter(species=sp)
            totals.append(qs_sp.count())
            #Get number operative
            num_none = qs_sp.filter(operation__isnull=True).count()
            qs_ops = qs_sp.filter(operation__gt=0).distinct()
            #print("DEBUG: 0=", num_none, "haveops=", qs_ops.count())
            opstates[0]=num_none
            for f in qs_ops:
                if f.next_operation_OK:
                    num += 1
                #Get opstates
                #print("DEBUG:fid=", f.frogid, "numops=",f.num_operations())
                opstates[f.num_operations()]+= 1
            #print("DEBUG:Ops=", opstates)
            operative.append(num_none+num)
            #Get numbers
            num_isolation = qs_sp.filter(remarks__icontains='isolation').count()
            isolation.append(num_isolation)
            num_observation = qs_sp.filter(remarks__icontains='observation').count()
            observation.append(num_observation)
            num_condition = qs_sp.filter(condition=True).count()
            condition.append(num_condition)
            actualoperative.append(num_none + num - num_isolation - num_observation - num_condition)
            #Calculate total left
            t = 0
            for key, val in opstates.items():
                t += (config.max_ops - key) * val
            #print("DEBUG: left=", t)
            opstates[config.max_ops+1]=t
            sp_opstates.append(opstates)
            print("DEBUG:Ops=", sp_opstates)

        context['species'] = frogspecies
        context['total'] = totals
        context['operative'] = operative
        context['isolation'] = isolation
        context['observation']= observation
        context['condition']= condition
        context['actualoperative']=actualoperative
        context['operationstate']= sp_opstates

        return context


## 1. Set frogid then 2. Increment opnum
## Limits: 6 operations and 6 mths apart - in Model
class OperationCreate(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    model = Operation
    template_name = 'frogs/operation/operation_create.html'
    form_class = OperationForm
    raise_exception = True
    permission_required = 'frogs.add_operation'


    def get_success_url(self):
        frog = Frog.objects.filter(frogid=self.object.frogid)
        return reverse('frogs:frog_detail', args=[frog[0].id])

    def get_initial(self):
        fid = self.kwargs.get('frogid')
        frog = Frog.objects.get(pk=fid)
        ## next opnum
        config = SiteConfiguration.objects.get()
        max = config.max_ops
        opnum = 1 #default
        if (frog.operation_set.all()):
            opnum = frog.operation_set.count() + 1
        return {'frogid': frog, 'opnum': opnum}


class OperationUpdate(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = Operation
    form_class = OperationForm
    template_name = 'frogs/operation/operation_create.html'
    raise_exception = True
    permission_required = 'frogs.change_operation'

    def get_success_url(self):
        frogid = self.object.frogid
        frog = Frog.objects.filter(frogid=frogid)
        fid = frog[0].id
        return reverse('frogs:frog_detail', args=[fid])


class OperationDelete(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    model = Operation
    template_name = 'frogs/operation/operation_confirm_delete.html'
    raise_exception = True
    permission_required = 'frogs.delete_operation'

    def get_success_url(self):
        frog = Frog.objects.filter(frogid=self.object.frogid)
        return reverse('frogs:frog_detail', args=[frog[0].id])

########## TRANSFERS ############################################
class TransferList(LoginRequiredMixin, generic.ListView):
    template_name = 'frogs/transfer/transfer_list.html'
    context_object_name = 'table'
    raise_exception = True
    filter_class = TransferFilter

    def get_queryset(self):
        qs = Transfer.objects.order_by('-transfer_date')
       # print("DEBUG: All Transfers=", qs.count())
        if (self.kwargs.get('operationid')):
            qs = qs.filter(operationid=self.kwargs.get('operationid'))
            table = TransferTable(qs)
            #print("DEBUG: Op Transfers=", qs.count())
        else:
            table = TransferTable(qs)
        RequestConfig(self.request, paginate={"per_page": 20}).configure(table)
        return table
        
    def get_context_data(self, **kwargs):
        context = super(TransferList, self).get_context_data(**kwargs)
        context['hide_filter']=True
        return context

class TransferFilterView(LoginRequiredMixin, FilteredSingleTableView):
    template_name = 'frogs/transfer/transfer_list.html'
    context_object_name = 'table'
    model = Transfer
    table_class = TransferTable
    filter_class = TransferFilter
    raise_exception = True

class TransferDetail(LoginRequiredMixin, generic.DetailView):
    model = Transfer
    template_name = 'frogs/transfer/transfer_detail.html'
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super(TransferDetail, self).get_context_data(**kwargs)
        return context

class TransferCreate(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    model = Transfer
    template_name = 'frogs/transfer/transfer_create.html'
    form_class = TransferForm
    raise_exception = True
    permission_required = 'frogs.add_transfer'

    def get_initial(self):
        opid = self.kwargs.get('operationid')
        op = Operation.objects.get(pk=opid)
        return {'operationid': op, 'volume': op.volume}

    def get_success_url(self):
        return reverse('frogs:transfer_detail', args=[self.object.id])

class TransferUpdate(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = Transfer
    form_class = TransferForm
    template_name = 'frogs/transfer/transfer_create.html'
    raise_exception = True
    permission_required = 'frogs.change_transfer'

    def get_success_url(self):
        return reverse('frogs:transfer_detail', args=[self.object.id])

class TransferDelete(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    model = Transfer
    template_name = 'frogs/transfer/transfer_confirm_delete.html'
    success_url = reverse_lazy("frogs:transfer_list")
    raise_exception = True
    permission_required = 'frogs.delete_transfer'

########## EXPERIMENTS ############################################
class ExperimentList(LoginRequiredMixin, generic.ListView):
    template_name = 'frogs/experiment/experiment_list_transfer.html'
    context_object_name = 'expt_list'
    raise_exception = True

    def get_queryset(self):
        mylist = Experiment.objects.order_by('-transferid')
        if (self.kwargs.get('transferid')):
            mylist = mylist.filter(transferid=self.kwargs.get('transferid'))

        table = ExperimentTable(mylist)
        RequestConfig(self.request, paginate={"per_page": 20}).configure(table)
        return table

    def get_context_data(self, **kwargs):
        context = super(ExperimentList, self).get_context_data(**kwargs)
        #print('DEBUG:GET INITIAL')
        tid = self.kwargs.get('transferid')
        transfer = Transfer.objects.get(pk=tid)
        context['frogid']= transfer.operationid.frogid
        context['transfer_date']= transfer.transfer_date
        context['transfer_from_to']= transfer.transferapproval
        return context

class ExperimentFilterView(LoginRequiredMixin, FilteredSingleTableView):
    template_name = 'frogs/experiment/experiment_list.html'
    context_object_name = 'table'
    model = Experiment
    table_class = ExperimentTable
    filter_class = ExperimentFilter
    raise_exception = True

class ExperimentTracking(LoginRequiredMixin, generic.ListView):
    template_name = 'frogs/experiment/experiment_list.html'
    context_object_name = 'expt_list'
    raise_exception = True

    def get_queryset(self):
        table = Experiment.objects.order_by('-transferid')
        return table
    
    def get_context_data(self, **kwargs):
        loc = self.kwargs.get('loc')
        if (loc is None):
            loc = 'aaall' #ensure comes first
        context = super(ExperimentTracking, self).get_context_data(**kwargs)
        qs = self.get_queryset()

        qaps = Qap.objects.values_list('building', flat=True).order_by('building')
        buildings ={'aaall': 'All'}
        for q in qaps:
            buildings[q.lower()] = q
        #print("DEBUG: loc=", loc)
        #print("DEBUG: buildings=", buildings)
        #print("DEBUG: qaps=", qaps)
        if (loc != 'aaall'):
            qs = qs.filter(expt_location__building__iexact=loc)
        table = ExperimentTable(qs)
        RequestConfig(self.request, paginate={"per_page": 20}).configure(table)
        context['location'] = loc
        context['loclist'] = sorted(buildings.items())
        context['expts'] = table
        return context


class ExperimentDetail(LoginRequiredMixin, generic.DetailView):
    model = Experiment
    context_object_name = 'expt'
    template_name = 'frogs/experiment/experiment_detail.html'
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super(ExperimentDetail, self).get_context_data(**kwargs)
        return context

class ExperimentCreate(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    model = Experiment
    template_name = 'frogs/experiment/experiment_create.html'
    form_class = ExperimentForm
    raise_exception = True
    permission_required = 'frogs.add_experiment'

    def get_initial(self):
        opid = self.kwargs.get('transferid')
        op = Transfer.objects.get(pk=opid)
        location = op.transferapproval.tfr_to
        return {'transferid': op, 'expt_location': location}

    def get_success_url(self):
        return reverse('frogs:experiment_detail', args=[self.object.id])

class ExperimentUpdate(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = Experiment
    form_class = ExperimentForm
    template_name = 'frogs/experiment/experiment_create.html'
    raise_exception = True
    permission_required = 'frogs.change_experiment'

    def get_success_url(self):
        return reverse('frogs:experiment_detail', args=[self.object.id])

class ExperimentDelete(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    model = Experiment
    template_name = 'frogs/experiment/experiment_confirm_delete.html'
    success_url = reverse_lazy("frogs:experiment_list_location")
    raise_exception = True
    permission_required = 'frogs.delete_experiment'

class ExperimentDisposal(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = Experiment
    form_class = ExperimentDisposalForm
    context_object_name = 'experiment'
    template_name = 'frogs/experiment/experiment_create.html'
    raise_exception = True
    permission_required = 'frogs.change_experiment'

    def get_success_url(self):
        return reverse('frogs:experiment_detail', args=[self.object.id])


class ExperimentAutoclave(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = Experiment
    form_class = ExperimentAutoclaveForm
    context_object_name = 'experiment'
    template_name = 'frogs/experiment/experiment_create.html'
    raise_exception = True
    permission_required = 'frogs.change_experiment'

    def get_success_url(self):
        return reverse('frogs:experiment_detail', args=[self.object.id])

class DisposalList(LoginRequiredMixin, generic.ListView):
    template_name = 'frogs/experiment/disposal_list.html'
    context_object_name = 'expt_list'
    raise_exception = True

    def get_queryset(self):
        table = Experiment.objects.filter(expt_disposed=True).order_by('-disposal_date')
        #table = DisposalTable(Experiment.objects.order_by('disposal_date'))
        #RequestConfig(self.request, paginate={"per_page": 20}).configure(table)
        return table
    
    def get_context_data(self, **kwargs):
        loc = self.kwargs.get('location')
        if (loc is None):
            loc = 'aaall'  # ensure comes first
        context = super(DisposalList, self).get_context_data(**kwargs)
        qs = self.get_queryset()
        qaps = Qap.objects.values_list('building', flat=True).order_by('building')
        buildings = {'aaall': 'All'}
        for q in qaps:
            buildings[q.lower()] = q
        if (loc != 'aaall'):
            qs = qs.filter(expt_location__building__iexact=loc)
        table = DisposalTable(qs)
        RequestConfig(self.request, paginate={"per_page": 20}).configure(table)
        context['location'] = loc
        context['loclist'] = sorted(buildings.items())
        context['expts'] = table
       # context['tablelist'] =tablelist
        return context


class BulkDisposal(LoginRequiredMixin, PermissionRequiredMixin, generic.FormView):
    template_name = 'frogs/experiment/bulkdisposal.html'
    form_class = BulkExptDisposalForm
    model = Experiment
    raise_exception = True
    location = 'aaall'
    permission_required = 'frogs.change_experiment'

    def get_form_kwargs(self, **kwargs):
        #print("DEBUG:getformkwargs:", kwargs)
        kwargs = super(BulkDisposal, self).get_form_kwargs(**kwargs)
        kwargs['location'] = self.location
        return kwargs

    def get_initial(self):
        #print("DEBUG:getinitial:", self.kwargs)
        if self.kwargs.get('location'):
            self.location = self.kwargs.get('location')

    def form_valid(self, form):
        #print('DEBUG: form_valid', self.request.POST)
        bulklist = form.cleaned_data['expts']
        msg = 'BULKDISPOSAL: updating records=%d' % len(bulklist)
        logger.info(msg)
        
        for pk in bulklist:
            #print('Updating expt:', pk)
            expt = pk  # Frog.objects.get(pk=pk)
            expt.expt_disposed = form.cleaned_data['expt_disposed']
            expt.disposal_sentby = form.cleaned_data['disposal_sentby']
            expt.disposal_date = form.cleaned_data['disposal_date']
            expt.waste_type = form.cleaned_data['waste_type']
            expt.waste_content = form.cleaned_data['waste_content']
            expt.waste_qty = form.cleaned_data['waste_qty']
            expt.save()

        return super(BulkDisposal, self).form_valid(form)

    def get_queryset(self):
        mylist = Experiment.objects.order_by('-disposal_date')
        if self.kwargs.get('location'):
            location = self.kwargs.get('location')
            #print("DEBUG:location:", location)
            if (location != 'aaall'):
                mylist = mylist.filter(expt_location__building=location)

        table = ExperimentTable(mylist)
        RequestConfig(self.request, paginate={"per_page": 20}).configure(table)
        return table

    def get_success_url(self):
        return reverse('frogs:experiment_list_location')


class BulkAutoclave(LoginRequiredMixin, PermissionRequiredMixin, generic.FormView):
    template_name = 'frogs/experiment/bulkautoclave.html'
    location = 'aaall' #'All'
    form_class = BulkExptAutoclaveForm
    model = Experiment
    raise_exception = True
    permission_required = 'frogs.change_experiment'

    def get_form_kwargs(self, **kwargs):
        #print("DEBUG:getformkwargs:", kwargs)
        kwargs = super(BulkAutoclave, self).get_form_kwargs(**kwargs)
        kwargs['location'] = self.location
        return kwargs

    def get_initial(self):
        #print("DEBUG:getinitial:", self.kwargs)
        if self.kwargs.get('location'):
            self.location = self.kwargs.get('location')

    def form_valid(self, form):
        bulklist = form.cleaned_data['expts']
        msg = 'BULKAUTOCLAVE: updating records=%d' % len(bulklist)
        logger.info(msg)
        
        for pk in bulklist:
            #print('Updating expt:', pk)
            expt = pk  # Frog.objects.get(pk=pk)
            expt.autoclave_indicator = form.cleaned_data['autoclave_indicator']
            expt.autoclave_complete = form.cleaned_data['autoclave_complete']
            expt.autoclave_machine = form.cleaned_data['autoclave_machine']
            expt.autoclave_run = form.cleaned_data['autoclave_run']
            expt.autoclave_comments = form.cleaned_data['autoclave_comments']
            #print('Updated:Expt=', expt.id)
            expt.save()

        return super(BulkAutoclave, self).form_valid(form)
    

    def get_success_url(self):
        return reverse('frogs:disposal_list')

# FROG NOTES
class NotesList(LoginRequiredMixin, generic.ListView):
    template_name = 'frogs/notes/notes_list.html'
    context_object_name = 'notes_list'
    raise_exception = True

    def get_queryset(self):
        table = NotesTable(Notes.objects.order_by('-note_date'))
        RequestConfig(self.request, paginate={"per_page": 20}).configure(table)
        return table

class NotesDetail(LoginRequiredMixin, generic.DetailView):
    model = Notes
    context_object_name = 'notes'
    template_name = 'frogs/notes/notes_view.html'
    raise_exception = True

# class NotesFilterView(FilteredSingleTableView):
#     model = Notes
#     table_class = NotesTable
#     filter_class = NotesFilter

class NotesCreate(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    model = Notes
    template_name = 'frogs/notes/notes_create.html'
    form_class = NotesForm
    success_url = reverse_lazy('frogs:notes_list')
    raise_exception = True
    permission_required = 'frogs.add_notes'

class NotesUpdate(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = Notes
    form_class = NotesForm
    template_name = 'frogs/notes/notes_create.html'
    success_url = reverse_lazy('frogs:notes_list')
    raise_exception = True
    permission_required = 'frogs.change_notes'

class NotesDelete(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    model = Notes
    success_url = reverse_lazy("frogs:notes_list")
    template_name = 'frogs/notes/notes_confirm_delete.html'
    raise_exception = True
    permission_required = 'frogs.delete_notes'

# DOCUMENTS
class DocumentList(LoginRequiredMixin, generic.ListView):
    template_name = 'frogs/document/document_list.html'
    context_object_name = 'docs_list'
    raise_exception = True

    def get_queryset(self):
        table = DocumentTable(Document.objects.order_by('pk'))
        RequestConfig(self.request, paginate={"per_page": 10}).configure(table)
        return table

class DocumentDetail(LoginRequiredMixin, generic.DetailView):
    model = Document
    context_object_name = 'document'
    template_name = 'frogs/document/document_view.html'
    raise_exception = True

class DocumentCreate(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    model = Document
    template_name = 'frogs/document/document_create.html'
    form_class = DocumentForm
    success_url = reverse_lazy('frogs:documents_list')
    raise_exception = True
    permission_required = 'frogs.add_document'

    def get_success_url(self):
        return reverse('frogs:documents_detail', args=[self.object.pk])


class DocumentUpdate(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = 'frogs/document/document_create.html'
    success_url = reverse_lazy('frogs:documents_list')
    raise_exception = True
    permission_required = 'frogs.change_document'

class DocumentDelete(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    model = Document
    success_url = reverse_lazy("frogs:documents_list")
    template_name = 'frogs/document/document_confirm_delete.html'
    raise_exception = True
    permission_required = 'frogs.delete_document'