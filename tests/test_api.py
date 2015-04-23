'''
Testing the tastypie-based mytardis api

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
'''
import json
import os
import tempfile
import urllib

from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.contrib.auth.models import Group

from django.test.client import Client
from django.test import TestCase

from tastypie.test import ResourceTestCase

from tardis.tardis_portal.auth.authservice import AuthService
from tardis.tardis_portal.auth.localdb_auth import django_user
from tardis.tardis_portal.models import UserProfile
from tardis.tardis_portal.models import Facility
from tardis.tardis_portal.models import Instrument

from tardis.apps.mydata.models import Uploader
from tardis.apps.mydata.models import UploaderStagingHost
from tardis.apps.mydata.models import UploaderRegistrationRequest


class MyTardisResourceTestCase(ResourceTestCase):
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
        self.user_profile = UserProfile(user=self.user).save()
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
        self.uploader = Uploader(interface='Ethernet', mac_address='ABCDEFG')
        self.uploader.save()
        self.uploader.instruments.add(self.testinstrument)

    def test_get_uploader_by_id(self):
        expected_output = {
            "id": 1,
            "interface": "Ethernet",
            "mac_address": "ABCDEFG!",
        }
        output = self.api_client.get('/api/v1/uploader/1/',
                                     authentication=self.get_credentials())
        returned_data = json.loads(output.content)
        for key, value in expected_output.iteritems():
            self.assertTrue(key in returned_data)
            self.assertEqual(returned_data[key], value)
