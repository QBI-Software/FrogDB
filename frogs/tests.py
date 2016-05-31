from django.test import TestCase
import datetime

from django.utils import timezone
from django.test import TestCase
from django.core.urlresolvers import reverse
from .models import *

def create_permit(aqis,qen,females,males,arrival_date,species,supplier,country,countrycode,color):
    """
    Creates Permit with lookup values
    :param aqis:
    :param qen:
    :param females:
    :param males:
    :param arrival_date:
    :param species:
    :param supplier:
    :param country:
    :param countrycode:
    :param color:
    :return:
    """
    speciesobj = Species.objects.create(name=species)
    supplierobj = Supplier.objects.create(name=supplier)
    countryobj = Country.objects.create(name=country, code=countrycode)
    return Permit.objects.create(aqis=aqis,qen=qen,females=females,males=males,arrival_date=arrival_date,species=speciesobj,supplier=supplierobj,country=countryobj,color=color)

def create_frog(frogid,tankid,gender,current_location,species,condition,remarks,qen,aec):
    """
    Creates Frog with Permit (mandatory values only)
    :param frogid:
    :param tankid:
    :param gender:
    :param current_location:
    :param species:
    :param condition:
    :param remarks:
    :param qen:
    :param aec:
    :return:
    """
    permit = create_permit(aqis="T123", qen=qen, females=4, males=2,
                                    arrival_date="2000-10-04", species=species,
                                    supplier="TestSupplies", country="Australia",
                                    countrycode="AU", color="#666666")
    locationobj = Location.objects.create(name=current_location, brief="here")
    return Frog.objects.create(frogid=frogid,tankid=tankid,gender=gender,current_location=locationobj,species=permit.species,condition=condition,remarks=remarks,qen=permit,aec=aec)

def create_operation(frogid,opnum, opdate,anesthetic,volume,comments,initials):
    """
    Creates Operation after creating Frog which creates Permit
    :param frogid:
    :param opnum:
    :param opdate:
    :param anesthetic:
    :param volume:
    :param comments:
    :param initials:
    :return:
    """
    frog = create_frog(frogid=frogid, tankid=10, gender='female', current_location="Stored here",
                                species="X.test", condition="OK", remarks="Good", qen="Q345", aec="1234")
    return Operation.objects.create(frogid=frog, opnum=opnum, opdate=opdate,anesthetic=anesthetic,volume=volume,comments=comments,initials=initials)

class PermitMethodTests(TestCase):
    def test_permit_arrived_recently(self):
        """
        tests permit method
        """
        test_permit = create_permit(aqis="T123", qen="Q123", females=4, males=2,
                                    arrival_date="2000-10-04", species="X.test",
                                    supplier="TestSupplies", country="Australia",
                                    countrycode="AU", color="#666666")

        self.assertEqual(test_permit.arrived_recently(), False)

    def test_frogs_remaining_none(self):
        test_permit = create_permit(aqis="T123", qen="Q123", females=4, males=2,
                                    arrival_date="2000-10-04", species="X.test",
                                    supplier="TestSupplies", country="Australia",
                                    countrycode="AU", color="#666666")
        self.assertEqual(test_permit.get_frogs_remaining(), 0)
        self.assertEqual(test_permit.get_frogs_remaining('female'), 0)
        self.assertEqual(test_permit.get_frogs_remaining('male'), 0)

class FrogMethodTests(TestCase):
    def test_frog_died_recently(self):
        test_frog = create_frog(frogid="V1",tankid=10,gender='female',current_location="Stored here",species="X.test",condition="OK",remarks="Good",qen="Q345",aec="1234")
        #No death date
        self.assertEquals(test_frog.died_recently(), False)
        #With death date
        test_frog.death_date = "2003-10-04"
        test_frog.save()
        self.assertEquals(test_frog.died_recently(), False)
        # With recent death date
        test_frog.death_date = "2016-05-04"
        test_frog.save()
        self.assertEquals(test_frog.died_recently(), True)

    def test_frog_valid_death_date(self):
        test_operation = create_operation(frogid="V2",opnum=1, opdate="2012-10-03",anesthetic="Strong",volume=5,comments="OK",initials="JFK")
        test_frog = test_operation.frogid
        #Valid death date
        test_frog.death_date = "2016-05-04"
        test_frog.save()
        self.assertRaises(ValidationError, test_frog.clean_death_date)
        #Not valid - after today
        test_frog.death_date = "2016-08-04"
        test_frog.save()
        self.assertRaises(ValidationError, test_frog.clean_death_date)
        #Not valid - before op date
        test_frog.death_date = "2012-08-04"
        test_frog.save()
        self.assertRaises(ValidationError, test_frog.clean_death_date)
