'''
Testing the /api/v1/mydata_experiment/ endpoint

.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
'''
import json

from tardis.tardis_portal.models.experiment import Experiment
from tardis.tardis_portal.models.parameters import (
    ParameterName,
    Schema)

from . import MyTardisResourceTestCase


class ExperimentResourceTest(MyTardisResourceTestCase):
    fixtures = ['tardis/apps/mydata/fixtures/default_experiment_schema.json',]

    def setUp(self):
        super().setUp()
        df_schema_name = "http://experi-mental.com/"
        self.test_schema = Schema(namespace=df_schema_name,
                                  type=Schema.EXPERIMENT)
        self.test_schema.save()
        self.test_parname1 = ParameterName(schema=self.test_schema,
                                           name="expparameter1",
                                           data_type=ParameterName.STRING)
        self.test_parname1.save()
        self.test_parname2 = ParameterName(schema=self.test_schema,
                                           name="expparameter2",
                                           data_type=ParameterName.NUMERIC)
        self.test_parname2.save()

    def test_find_exp_for_uploader_user_folder_email_dataset_structure(self):
        uploader = "TEST_UPLOADER_UUID"
        user_folder_name = "testuser1@example.com"
        folder_structure = "Email / Dataset"
        output = self.api_client.get("/api/v1/mydata_experiment/?uploader=%s&user_folder_name=%s&folder_structure=%s"
                                     % (uploader, user_folder_name, folder_structure),
                                     authentication=self.get_credentials())
        returned_data = json.loads(output.content.decode())
        self.assertEqual(returned_data["meta"]["total_count"], 0)

        Experiment.objects.create(title="Test Instrument - Test User1")

    def test_find_exp_for_uploader_user_folder_username_dataset_structure(self):
        uploader = "TEST_UPLOADER_UUID"
        user_folder_name = "testuser1"
        folder_structure = "Username / Dataset"
        output = self.api_client.get("/api/v1/mydata_experiment/?uploader=%s&user_folder_name=%s&folder_structure=%s"
                                     % (uploader, user_folder_name, folder_structure),
                                     authentication=self.get_credentials())
        returned_data = json.loads(output.content.decode())
        self.assertEqual(returned_data["meta"]["total_count"], 0)

    def test_find_exp_for_uploader_group_folder_group_dataset_structure(self):
        uploader = "TEST_UPLOADER_UUID"
        group_folder_name = "TestGroup1"
        folder_structure = "User Group / Dataset"
        output = self.api_client.get("/api/v1/mydata_experiment/?uploader=%s&group_folder_name=%s&folder_structure=%s"
                                     % (uploader, group_folder_name, folder_structure),
                                     authentication=self.get_credentials())
        returned_data = json.loads(output.content.decode())
        self.assertEqual(returned_data["meta"]["total_count"], 0)

    def test_find_exp_for_title_user_folder_email_dataset_structure(self):
        title = "Experiment1"
        user_folder_name = "testuser1@example.com"
        folder_structure = "Email / Dataset"
        output = self.api_client.get("/api/v1/mydata_experiment/?title=%s&user_folder_name=%s&folder_structure=%s"
                                     % (title, user_folder_name, folder_structure),
                                     authentication=self.get_credentials())
        returned_data = json.loads(output.content.decode())
        self.assertEqual(returned_data["meta"]["total_count"], 0)

    def test_find_exp_for_title_group_folder_group_dataset_structure(self):
        title = "Experiment1"
        group_folder_name = "TestGroup1"
        folder_structure = "User Group / Dataset"
        output = self.api_client.get("/api/v1/mydata_experiment/?title=%s&group_folder_name=%s&folder_structure=%s"
                                     % (title, group_folder_name, folder_structure),
                                     authentication=self.get_credentials())
        returned_data = json.loads(output.content.decode())
        self.assertEqual(returned_data["meta"]["total_count"], 0)
