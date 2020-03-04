'''
Testing the /api/v1/mydata_experiment/ endpoint

.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
'''
import json

from tardis.tardis_portal.models.access_control import ObjectACL
from tardis.tardis_portal.models.experiment import Experiment
from tardis.tardis_portal.models.parameters import (
    ExperimentParameterSet,
    ExperimentParameter,
    ParameterName,
    Schema)

from . import MyTardisResourceTestCase


def create_uploader_exp(user, uploader, user_folder_name=None, group_folder_name=None):
    """
    Create an experiment for testing API response

    This is for the case where the MyData doesn't use a folder structure
    including "Experiment", so MyData generates the experiment title
    for them automatically and associates the experiment with the
    MyData instance (uploader UUID).
    """
    title = "Test Instrument - Test User1"
    if group_folder_name:
        title = "Test Instrument - TestGroup1"
    exp = Experiment.objects.create(title=title, created_by=user)
    ObjectACL.objects.create(
        content_type=exp.get_ct(), object_id=exp.id, pluginId='django_user',
        entityId=str(user.id), canRead=True, canWrite=True,
        canDelete=True, isOwner=True, aclOwnershipType=ObjectACL.OWNER_OWNED)
    schema = Schema.objects.get(
        namespace="http://mytardis.org/schemas/mydata/defaultexperiment")
    pset = ExperimentParameterSet.objects.create(experiment=exp, schema=schema)
    pname = ParameterName.objects.get(schema=schema, name="uploader")
    ExperimentParameter.objects.create(
        parameterset=pset, name=pname, string_value=uploader)
    if user_folder_name:
        pname = ParameterName.objects.get(schema=schema, name="user_folder_name")
        ExperimentParameter.objects.create(
            parameterset=pset, name=pname, string_value=user_folder_name)
    if group_folder_name:
        pname = ParameterName.objects.get(schema=schema, name="group_folder_name")
        ExperimentParameter.objects.create(
            parameterset=pset, name=pname, string_value=group_folder_name)
    return exp


def create_title_exp(user, title, user_folder_name=None, group_folder_name=None):
    """
    Create an experiment for testing API response

    This is for the case where the MyData uses a folder structure
    including "Experiment", so the MyData user can name their
    experiment folder according to the experiment title they want
    MyData to create for them in MyTardis.
    """
    exp = Experiment.objects.create(title=title, created_by=user)
    ObjectACL.objects.create(
        content_type=exp.get_ct(), object_id=exp.id, pluginId='django_user',
        entityId=str(user.id), canRead=True, canWrite=True,
        canDelete=True, isOwner=True, aclOwnershipType=ObjectACL.OWNER_OWNED)
    schema = Schema.objects.get(
        namespace="http://mytardis.org/schemas/mydata/defaultexperiment")
    pset = ExperimentParameterSet.objects.create(experiment=exp, schema=schema)
    if user_folder_name:
        pname = ParameterName.objects.get(schema=schema, name="user_folder_name")
        ExperimentParameter.objects.create(
            parameterset=pset, name=pname, string_value=user_folder_name)
    if group_folder_name:
        pname = ParameterName.objects.get(schema=schema, name="group_folder_name")
        ExperimentParameter.objects.create(
            parameterset=pset, name=pname, string_value=group_folder_name)
    return exp


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
        response = self.api_client.get("/api/v1/mydata_experiment/?uploader=%s&user_folder_name=%s&folder_structure=%s"
                                     % (uploader, user_folder_name, folder_structure),
                                     authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        self.assertEqual(returned_data["meta"]["total_count"], 0)

        # Now let's create an experiment and ensure that the API returns 1 record:

        exp = create_uploader_exp(self.user, uploader, user_folder_name)
        response = self.api_client.get(
            "/api/v1/mydata_experiment/?uploader=%s&user_folder_name=%s&folder_structure=%s"
            % (uploader, user_folder_name, folder_structure),
            authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        self.assertEqual(returned_data["meta"]["total_count"], 1)
        exp.delete()

    def test_find_exp_for_uploader_user_folder_username_dataset_structure(self):
        uploader = "TEST_UPLOADER_UUID"
        user_folder_name = "testuser1"
        folder_structure = "Username / Dataset"
        response = self.api_client.get(
            "/api/v1/mydata_experiment/?uploader=%s&user_folder_name=%s&folder_structure=%s"
            % (uploader, user_folder_name, folder_structure),
            authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        self.assertEqual(returned_data["meta"]["total_count"], 0)

        # Now let's create an experiment and ensure that the API returns 1 record:

        exp = create_uploader_exp(self.user, uploader, user_folder_name)
        response = self.api_client.get(
            "/api/v1/mydata_experiment/?uploader=%s&user_folder_name=%s&folder_structure=%s"
            % (uploader, user_folder_name, folder_structure),
            authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        self.assertEqual(returned_data["meta"]["total_count"], 1)
        exp.delete()

    def test_find_exp_for_uploader_group_folder_group_dataset_structure(self):
        uploader = "TEST_UPLOADER_UUID"
        group_folder_name = "TestGroup1"
        folder_structure = "User Group / Dataset"
        output = self.api_client.get(
            "/api/v1/mydata_experiment/?uploader=%s&group_folder_name=%s&folder_structure=%s"
            % (uploader, group_folder_name, folder_structure),
            authentication=self.get_credentials())
        returned_data = json.loads(output.content.decode())
        self.assertEqual(returned_data["meta"]["total_count"], 0)

        # Now let's create an experiment and ensure that the API returns 1 record:

        exp = create_uploader_exp(self.user, uploader, group_folder_name=group_folder_name)
        response = self.api_client.get(
            "/api/v1/mydata_experiment/?uploader=%s&group_folder_name=%s&folder_structure=%s"
            % (uploader, group_folder_name, folder_structure),
            authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        self.assertEqual(returned_data["meta"]["total_count"], 1)
        exp.delete()

    def test_find_exp_for_title_user_folder_email_dataset_structure(self):
        title = "Experiment1"
        user_folder_name = "testuser1@example.com"
        folder_structure = "Email / Dataset"
        output = self.api_client.get(
            "/api/v1/mydata_experiment/?title=%s&user_folder_name=%s&folder_structure=%s"
            % (title, user_folder_name, folder_structure),
            authentication=self.get_credentials())
        returned_data = json.loads(output.content.decode())
        self.assertEqual(returned_data["meta"]["total_count"], 0)

        # Now let's create an experiment and ensure that the API returns 1 record:

        exp = create_title_exp(self.user, title, user_folder_name)
        response = self.api_client.get(
            "/api/v1/mydata_experiment/?title=%s&user_folder_name=%s&folder_structure=%s"
            % (title, user_folder_name, folder_structure),
            authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        self.assertEqual(returned_data["meta"]["total_count"], 1)
        exp.delete()

    def test_find_exp_for_title_group_folder_group_dataset_structure(self):
        title = "Experiment1"
        group_folder_name = "TestGroup1"
        folder_structure = "User Group / Dataset"
        output = self.api_client.get(
            "/api/v1/mydata_experiment/?title=%s&group_folder_name=%s&folder_structure=%s"
            % (title, group_folder_name, folder_structure),
            authentication=self.get_credentials())
        returned_data = json.loads(output.content.decode())
        self.assertEqual(returned_data["meta"]["total_count"], 0)

        # Now let's create an experiment and ensure that the API returns 1 record:

        exp = create_title_exp(self.user, title, group_folder_name=group_folder_name)
        response = self.api_client.get(
            "/api/v1/mydata_experiment/?title=%s&group_folder_name=%s&folder_structure=%s"
            % (title, group_folder_name, folder_structure),
            authentication=self.get_credentials())
        returned_data = json.loads(response.content.decode())
        self.assertEqual(returned_data["meta"]["total_count"], 1)
        exp.delete()
