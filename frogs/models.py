from datetime import date, datetime, timedelta
from django.db import models
from django.db.models import Count
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
#from .models import SiteConfiguration
from solo.models import SingletonModel
#######################################################################
##  SITE CONFIG - Managed in Admin
#######################################################################
class SiteConfiguration(SingletonModel):
    site_name = models.CharField(max_length=255, default='Site Name')
    report_location = models.CharField(max_length=1000, default='Location')
    report_contact_details = models.CharField(max_length=2000, default='Contact Details')
    report_general_notes = models.CharField(max_length=5000, default='General Notes')
    maintenance_mode = models.BooleanField(default=False)
    max_ops = models.SmallIntegerField(_("Max operations"), default=6)
    op_interval= models.SmallIntegerField(_("Operation interval (days)"), default=180)

    def __unicode__(self):
        return u"Site Configuration"

    class Meta:
        verbose_name = "Site Configuration"

#######################################################################
##  DB LISTS - Managed in Admin
#######################################################################
GENDERS=(('female','Female'),('male','Male'), ('unknown', 'Unknown'))
class Qap(models.Model):
    qap = models.CharField(_("QAP"), max_length=80, primary_key=True)
    building = models.CharField(_("Building"), max_length=60, null=False)

    def __str__(self):
        return self.building

class Supplier(models.Model):
    name = models.CharField(_("Name"), max_length=100)

    def __str__(self):
        return self.name

class Country(models.Model):
    name = models.CharField(_("Name"), max_length=60)
    code = models.CharField(_("Code"), max_length=5)

    def __str__(self):
        return self.name

class Species(models.Model):
    name = models.CharField(_("Species"), unique=True, max_length=100)

    def __str__(self):
        return self.name

class Imagetype(models.Model):
    name = models.CharField(_("Image Type"), max_length=100)

    def __str__(self):
        return self.name

class Wastetype(models.Model):
    name = models.CharField(_("Waste Type"), max_length=100)

    def __str__(self):
        return self.name

class Location(models.Model):
    name = models.CharField(_("Current Location"), max_length=100)
    brief = models.CharField(_("Abbreviation"), max_length=20)

    def __str__(self):
        return self.name

class Deathtype(models.Model):
    name = models.CharField(_("Death Type"), max_length=100)

    def __str__(self):
        return self.name


#######################################################################
##  DB models
#######################################################################
class Permit(models.Model):
    aqis = models.CharField(_("AQIS"), max_length=20)
    qen = models.CharField(_("QEN"), max_length=20, unique=True)
    females = models.PositiveSmallIntegerField(_("Females"), default=0)
    males = models.PositiveSmallIntegerField(_("Males"), default=0)
    arrival_date = models.DateField(_("Arrival date"))
    species = models.ForeignKey(Species, verbose_name="Species")
    supplier = models.ForeignKey(Supplier, verbose_name="Supplier")
    country = models.ForeignKey(Country, verbose_name="Country")
    color = models.CharField(_("Colour"), max_length=20, unique=True, null=True, blank=True)


    def __str__(self):
        return self.qen

    def get_absolute_url(self):
        return reverse('permit_detail', args=[str(self.pk)])

    def arrived_recently(self):
        delta = date.today() - datetime.strptime(self.arrival_date, "%Y-%m-%d").date()
        return delta.days >=0 and delta.days <= 30

    def get_totalfrogs(self):
        return (self.females + self.males)

    def frogs_disposed(self):
        qs = Frog.objects.filter(qen=self).filter(disposed=True)
        #print('DEBUG: frogs_disposed=', qs.count())
        return qs.count()

    def get_frogs_remaining(self):
        return self.get_totalfrogs() - self.frogs_disposed() - self.get_frogs_transferred('AIBN')

    def get_frogs_transferred(self, transferfrom='AIBN'):
        frogs = Frog.objects.filter(qen=self)\
            .filter(disposed=False)\
            .filter(operation__transfer__transferapproval__tfr_from__building=transferfrom)
        #print('DEBUG: transferred frogs=', frogs)
        return frogs.count()


class Frog(models.Model):

    frogid = models.CharField(_("Frog ID"), max_length=30, unique=True)
    tankid = models.PositiveSmallIntegerField(_("Tank ID"), default=0)
    gender = models.CharField(_("Gender"), max_length=10, choices=GENDERS)
    current_location = models.ForeignKey(Location, verbose_name="Current Location", null=False)
    species = models.ForeignKey(Species, verbose_name="Species", null=False)
    condition = models.CharField(_("Oocyte Health Condition"), max_length=100, null=True, blank=True)
    remarks = models.TextField(_("General Remarks"),null=True, blank=True)
    qen = models.ForeignKey(Permit, verbose_name="QEN", on_delete=models.CASCADE, null=False)
    aec = models.CharField(_("AEC"), max_length=80,null=True, blank=True)
    death = models.ForeignKey(Deathtype, verbose_name="Death",null=True, blank=True)
    death_date = models.DateField("Date of Death", null=True, blank=True)
    death_initials = models.CharField(_("Initials"), max_length=10, null=True, blank=True)
    disposed = models.BooleanField(_("Disposed"), default=False)
    autoclave_date = models.DateField("Autoclave Date", null=True, blank=True)
    autoclave_run = models.PositiveIntegerField(_("Autoclave Run"), default=0, null=True, blank=True)
    incineration_date = models.DateField(_("Incineration Date"), null=True, blank=True)

    def __str__(self):
        return self.frogid

    def get_absolute_url(self):
        return reverse('frog_detail', args=[str(self.pk)])

    def died_recently(self):
        if self.death_date:
            delta = date.today() - datetime.strptime(self.death_date, "%Y-%m-%d").date()
            return delta.days >= 0 and delta.days <= 30
        else:
            return False

    # derived fields
    def get_operations(self):
        return self.operation_set.order_by('opnum')

    def last_operation(self):
        totalops = self.operation_set.count()
        lastop = None
        if (totalops > 0):
            lastop = self.operation_set.order_by('opnum')[totalops - 1]
            return lastop.opdate
        else:
            return lastop

    def num_operations(self):
         return self.operation_set.count()

    def next_operation(self):
        config = SiteConfiguration.objects.get()
        operation_interval = config.op_interval
        if operation_interval is None:
            operation_interval = 180 #hardcoded default in days
        lastop = self.last_operation()
        d = timedelta(days=operation_interval)
        if lastop is not None:
            nextop = lastop + d
            return nextop
        else:
            return None

    def dorsalimage(self):
        return self.get_image('Dorsal')

    def ventralimage(self):
        return self.get_image('Ventral')

    def get_image(self,type):
        img = None
        itype = Imagetype.objects.get(name=type)
        if (self.frogattachment_set.count() > 0):
            imgs = self.frogattachment_set.filter(imagetype=itype)
            if imgs.count() > 0:
                img = imgs[0]
        return img

    #Validation
    def clean(self):
        if self.death_date is not None:
            #print("DEBUG: Validating death_date:", self.death_date)
            deathdate = self.death_date #datetime.strptime(self.death_date, "%Y-%m-%d").date()
            delta = date.today() - self.death_date #datetime.strptime(self.death_date, "%Y-%m-%d").date()
            #print("DEBUG: Validating death_date:deltadays=", delta.days)
            #print("DEBUG: Validating death_date:arrival=", self.qen.arrival_date)
            #print("DEBUG: Validating death_date:lastop=", self.last_operation())
            if delta.days < 0:
                raise ValidationError("Date of death selected is in the future")
            if deathdate < self.qen.arrival_date:
                raise ValidationError("Date of death is before arrival")
            if self.last_operation() != None and deathdate < self.last_operation():
                raise ValidationError("Date of death is before last operation")




class FrogAttachment(models.Model):
    frogid = models.ForeignKey(Frog, on_delete=models.CASCADE)
    imgfile = models.ImageField(verbose_name="Image")
    imagetype = models.ForeignKey(Imagetype, verbose_name="Dorsal/Ventral")
    description = models.CharField(_("Description"), max_length=200, null=True, blank=True)

    def __str__(self):
        return self.imagetype

    def clean(self):
        #Check if replacing an image or new
        #Get frog - get images - get type
        frog = Frog.objects.get(pk=self.frogid.pk)
        dorsal = frog.dorsalimage()
        ventral = frog.ventralimage()
        if dorsal is not None and self.imagetype.name =='Dorsal':
            dorsal.delete()
        elif ventral is not None and self.imagetype.name =='Ventral':
            ventral.delete()



class Operation(models.Model):
    frogid = models.ForeignKey(Frog, on_delete=models.CASCADE)
    opnum = models.PositiveSmallIntegerField(_("Operation Number"), default=1)
    opdate = models.DateField("Operation Date")
    anesthetic = models.CharField(_("Anesthetic"), max_length=30)
    volume = models.PositiveSmallIntegerField("Volume (ml)")
    comments = models.TextField("Comments")
    initials = models.CharField(_("Operated by"), max_length=10)

    def __str__(self):
        opref = "Frog %s Operation %d" % (self.frogid, self.opnum)
        return opref

    def clean_opnum(self):
        config = SiteConfiguration.objects.get()
        max = config.max_ops
        if self.opnum > max:
            raise ValidationError("Can only create %d operations per frog" % max)
        nums = []
        for n in self.frogid.operation_set:
            nums.append(n.opnum)
        if self.opnum in nums:
            raise ValidationError("An operation %d already exists for this frog" % self.opnum)

    def clean_opdate(self):
        config = SiteConfiguration.objects.get()
        operation_interval = config.op_interval
        if (self.opdate < self.frogid.qen.arrival_date):
            raise ValidationError("This operation is earlier than the shipment arrival date")
        delta = self.opdate - self.frogid.last_operation()
        if delta < (operation_interval):
            raise ValidationError("This operation is only %d days since the last operation (require an interval of %d days)" % delta, SiteConfiguration.op_interval)

    def get_number_expts(self):
        total = 0
        if (self.transfer_set.count() > 0):
            #print('DEBUG: get_number_expts: transfers=', self.transfer_set.count())
            for t in self.transfer_set.all():
                if t.experiment_set.count() > 0:
                    #print('DEBUG: get_number_expts: expt=', t.experiment_set.count())
                    total += t.experiment_set.count()

        return total

    def get_expts_disposaldate_range(self):
        exptfrom = exptto = None #datetime.date.today()
        rtn = " - "
        if (self.transfer_set.count() > 0):
            for t in self.transfer_set.all():
                for e in t.experiment_set.all():
                    if (exptfrom == None):
                        exptfrom = e.expt_from
                        exptto = e.expt_to
                    else:
                        if e.expt_from < exptfrom:
                            exptfrom = e.expt_from
                        if e.expt_to > exptto:
                            exptto = e.expt_to

            rtn = str(exptfrom) + " to " + str(exptto)
        return rtn

    def get_expts_number_disposals(self):
        total = 0
        if (self.transfer_set.count() > 0):
            for t in self.transfer_set.all():
                for e in t.experiment_set.all():
                    if e.expt_disposed:
                        total += 1
        return total

    def get_number_autoclaved(self):
        total = 0
        if (self.transfer_set.count() > 0):
            for t in self.transfer_set.all():
                for e in t.experiment_set.all():
                    if e.autoclave_complete:
                        total += 1
        return total

class TransferApproval(models.Model):
    tfr_from = models.ForeignKey(Qap, verbose_name="Transfer from", related_name="tfr_from")
    tfr_to = models.ForeignKey(Qap, verbose_name="Transfer to", related_name="tfr_to")
    sop = models.CharField(_("SOP details"), max_length=100)

    def __str__(self):
        return self.get_fromto()

    # Return string with from-to
    def get_fromto(self):
        fromto = "%s to %s" % (self.tfr_from.building, self.tfr_to.building)
        return fromto

    def get_sop(self):
        return self.sop


class Transfer(models.Model):
    transferapproval = models.ForeignKey(TransferApproval, verbose_name="Transfer from/to")
    operationid = models.ForeignKey(Operation, verbose_name="Operation", on_delete=models.CASCADE)
    volume = models.PositiveSmallIntegerField("Volume carried (ml)")
    transfer_date = models.DateField("Transfer date")
    #transporter = models.CharField(_("Transporter Name or Initials"), max_length=120)
    transporter = models.ForeignKey(User, verbose_name="Transporter Name", related_name="transporter")
    method = models.CharField(_("Method"), max_length=120)

    def __str__(self):
        return str(self.get_verbose())

    def maxvol(self):
        return self.operationid.volume

    # Return string with from-to
    def get_verbose(self):
        verbose = "Frog %s: from operation %d on %s (total %d ml)" % (self.operationid.frogid, self.operationid.opnum, self.operationid.opdate, self.operationid.volume)
        return verbose

    def clean(self):
        max = self.maxvol()
        if self.volume > max:
            raise ValidationError("Can only transfer maximum %d ml" % max)

class Experiment(models.Model):
    transferid = models.ForeignKey(Transfer, on_delete=models.CASCADE, verbose_name="Oocyte source")
    received = models.PositiveSmallIntegerField("Oocytes received (ml)")
    transferred = models.PositiveSmallIntegerField("Oocytes transferred (ml)")
    used = models.PositiveSmallIntegerField("Oocytes used (ml)")
    expt_from = models.DateField("Experiments from")
    expt_to = models.DateField("Experiments to")
    expt_location = models.ForeignKey(Qap, verbose_name="Experiment Location", related_name="expt_location")
    expt_disposed = models.BooleanField(_("Disposed"), default=False)
    disposal_sentby = models.ForeignKey(User, verbose_name="Disposal sent by",blank=True,null=True)
    disposal_date = models.DateField("Disposal date", blank=True,null=True)
    waste_type = models.ForeignKey(Wastetype, verbose_name="Type of waste", blank=True,null=True)
    waste_content = models.CharField(_("Waste content"), max_length=30, blank=True,null=True)
    waste_qty = models.PositiveSmallIntegerField(_("Waste quantity"), blank=True, null=True)
    autoclave_indicator = models.BooleanField("Autoclave indicator", default=False)
    autoclave_complete = models.BooleanField("Autoclave complete", default=False)

    def __str__(self):
        verbose = "Frog %s [op %d] expt %s (%d of %d ml)" % (
        self.transferid.operationid.frogid, self.transferid.operationid.opnum, self.expt_to, self.used, self.received)
        return verbose

class Notes(models.Model):
    note_date = models.DateField("Notes date")
    notes = models.CharField(_("Notes"), max_length=500, blank=True, null=True)
    initials = models.CharField(_("Initials"), max_length=10, blank=True, null=True)

    def __str__(self):
        return self.notes