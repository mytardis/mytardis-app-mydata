'''
Testing the tastypie-based mytardis api

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
'''
import uuid

from tastypie.test import ResourceTestCaseMixin

from django.contrib.auth.models import User, Group, Permission

from django.test import TestCase

from tardis.tardis_portal.auth.authservice import AuthService
from tardis.tardis_portal.auth.localdb_auth import django_user
from tardis.tardis_portal.models.access_control import ObjectACL
from tardis.tardis_portal.models.facility import Facility
from tardis.tardis_portal.models.instrument import Instrument
from tardis.tardis_portal.models.experiment import Experiment
from tardis.tardis_portal.models.dataset import Dataset
from tardis.tardis_portal.models.parameters import Schema
from tardis.tardis_portal.models.storage import StorageBox

from ...models.uploader import Uploader, UploaderRegistrationRequest


class MyTardisResourceTestCase(ResourceTestCaseMixin, TestCase):
    '''
    abstract class without tests to combine common settings in one place
    '''
    def setUp(self):
        super(MyTardisResourceTestCase, self).setUp()

        self.username = 'mytardis'
        self.password = 'mytardis'
        self.user = User.objects.create_user(username=self.username,
                                             password=self.password)

        test_auth_service = AuthService()
        test_auth_service._set_user_from_dict(
            self.user,
            user_dict={'first_name': 'Testing',
                       'last_name': 'MyTardis API',
                       'email': 'api_test@mytardis.org'},
            auth_method="None")

        for perm in ["change_dataset",
                     "add_datafile", "add_datafileobject",
                     "add_datafileparameter", "add_datafileparameterset"]:
            self.user.user_permissions.add(
                Permission.objects.get(codename=perm))

        self.testgroup = Group(name="Test Group")
        self.testgroup.save()
        self.testgroup.user_set.add(self.user)

        self.testfacility = Facility(name="Test Facility",
                                     manager_group=self.testgroup)
        self.testfacility.save()

        self.testinstrument = Instrument(name="Test Instrument",
                                         facility=self.testfacility)
        self.testinstrument.save()

        self.testexp = Experiment(title="Test Experiment",
                                  approved=True,
                                  created_by=self.user,
                                  locked=False)
        self.testexp.save()

        testacl = ObjectACL(
            content_type=self.testexp.get_ct(),
            object_id=self.testexp.id,
            pluginId=django_user,
            entityId=str(self.user.id),
            canRead=True,
            canWrite=True,
            canDelete=True,
            isOwner=True,
            aclOwnershipType=ObjectACL.OWNER_OWNED)
        testacl.save()

        self.uploader_uuid = str(uuid.uuid4())
        self.uploader = Uploader(name="Test Uploader", uuid=self.uploader_uuid)
        self.uploader.save()
        self.uploader.instruments.add(self.testinstrument)

        self.requester_key_fingerprint = "71:5a:6b:f0:81:f9:fe:ba:7a:e5:2d:00:a7:6a:cd:4a"
        self.uploader_request = UploaderRegistrationRequest(
            uploader=self.uploader,
            requester_key_fingerprint=self.requester_key_fingerprint,
            approved=True,
            approved_storage_box=StorageBox.get_default_storage()
        )
        self.uploader_request.save()

        self.schema = Schema.objects.create(
            namespace="http://schema.namespace/dataset/1",
            type=Schema.DATASET
        )

        self.dataset = Dataset.objects.create(description="Test Dataset")
        self.dataset.experiments.add(self.testexp)

    def tearDown(self):
        self.schema.delete()
        self.dataset.delete()
        self.uploader_request.delete()
        self.uploader.delete()
        self.testexp.delete()
        self.testinstrument.delete()
        self.testfacility.delete()
        self.testgroup.delete()
        self.user.delete()

    def get_credentials(self):
        return self.create_basic(username=self.username,
                                 password=self.password)

    def get_apikey_credentials(self):
        return self.create_apikey(username=self.username,
                                  api_key=self.user.api_key.key)
