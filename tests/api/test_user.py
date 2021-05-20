import json

from django.contrib.auth.models import User
from django.test.client import Client

from tardis.apps.openid_migration.models import OpenidUserMigration

from . import MyTardisResourceTestCase


class UserAppResourceTest(MyTardisResourceTestCase):

    def setUp(self):
        super().setUp()
        self.old_username = "jsmith01"
        self.new_username = "John.Smith@monash.edu"
        self.user_old = User.objects.create_user(
            username=self.old_username + "_ldap",
            password="boo",
            is_active=False)
        self.user_new = User.objects.create_user(
            username=self.new_username,
            password="foo")
        self.migration = OpenidUserMigration(
            old_user=self.user_old,
            new_user=self.user_new)
        self.migration.save()
        self.client = Client()
        self.client.login(
            username=self.username,
            password=self.password)

    def tearDown(self):
        self.migration.delete()
        self.user_old.delete()
        self.user_new.delete()
        super().tearDown()

    def test_get_user(self):
        response = self.client.get(
            "/api/v1/mydata_user/?username=%s" % self.old_username
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("success", data)
        self.assertTrue(data["success"])
        self.assertIn("username", data)
        self.assertEqual(data["username"], self.new_username)
