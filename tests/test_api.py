'''
Testing the tastypie-based mytardis api

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
'''
import json

from tastypie.test import ResourceTestCaseMixin

from django.contrib.auth.models import User
from django.contrib.auth.models import Group

from django.test import TestCase

from tardis.tardis_portal.auth.authservice import AuthService
from tardis.tardis_portal.models.facility import Facility
from tardis.tardis_portal.models.instrument import Instrument

from tardis.apps.mydata.models.uploader import Uploader


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
        self.testgroup = Group(name="Test Group")
        self.testgroup.save()
        self.testgroup.user_set.add(self.user)
        self.testfacility = Facility(name="Test Facility",
                                     manager_group=self.testgroup)
        self.testfacility.save()
        self.testinstrument = Instrument(name="Test Instrument",
                                         facility=self.testfacility)
        self.testinstrument.save()

    def get_credentials(self):
        return self.create_basic(username=self.username,
                                 password=self.password)

    def get_apikey_credentials(self):
        return self.create_apikey(username=self.username,
                                  api_key=self.user.api_key.key)


class UploaderAppResourceTest(MyTardisResourceTestCase):
    def setUp(self):
        super(UploaderAppResourceTest, self).setUp()
        self.uploader = Uploader(name='Test Uploader')
        self.uploader.save()
        self.uploader.instruments.add(self.testinstrument)

    def test_get_uploader_by_id(self):
        expected_output = {
            "id": 1,
            "name": "Test Uploader"
        }
        output = self.api_client.get('/api/v1/mydata_uploader/1/',
                                     authentication=self.get_credentials())
        returned_data = json.loads(output.content)
        for key, value in expected_output.items():
            self.assertIn(key, returned_data)
            self.assertEqual(returned_data[key], value)
