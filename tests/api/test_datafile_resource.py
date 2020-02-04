'''
Testing the DataFile resource in MyTardis's Tastypie-based REST API

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
'''
import json
import tempfile

from django.test.client import Client

from tardis.tardis_portal.models.datafile import DataFile, DataFileObject
from tardis.tardis_portal.models.dataset import Dataset
from tardis.tardis_portal.models.parameters import ParameterName
from tardis.tardis_portal.models.parameters import Schema

from . import MyTardisResourceTestCase


class DataFileResourceTest(MyTardisResourceTestCase):
    def setUp(self):
        super(DataFileResourceTest, self).setUp()
        self.django_client = Client()
        self.django_client.login(username=self.username,
                                 password=self.password)
        self.testds = Dataset()
        self.testds.description = "test dataset"
        self.testds.save()
        self.testds.experiments.add(self.testexp)
        df_schema_name = "http://datafileshop.com/"
        self.test_schema = Schema(namespace=df_schema_name,
                                  type=Schema.DATAFILE)
        self.test_schema.save()
        self.test_parname1 = ParameterName(schema=self.test_schema,
                                           name="fileparameter1",
                                           data_type=ParameterName.STRING)
        self.test_parname1.save()
        self.test_parname2 = ParameterName(schema=self.test_schema,
                                           name="fileparameter2",
                                           data_type=ParameterName.NUMERIC)
        self.test_parname2.save()

        self.datafile = DataFile(dataset=self.testds,
                                 filename="testfile.txt",
                                 size="42", md5sum='bogus')
        self.datafile.save()

    def test_post_single_file(self):
        ds_id = Dataset.objects.first().id
        post_data = """{
    "dataset": "/api/v1/dataset/%d/",
    "filename": "mytestfile.txt",
    "md5sum": "930e419034038dfad994f0d2e602146c",
    "size": "8",
    "mimetype": "text/plain",
    "parameter_sets": [{
        "schema": "http://datafileshop.com/",
        "parameters": [{
            "name": "fileparameter1",
            "value": "123"
        },
        {
            "name": "fileparameter2",
            "value": "123"
        }]
    }]
}""" % ds_id

        post_file = tempfile.NamedTemporaryFile()
        file_content = b"123test\n"
        post_file.write(file_content)
        post_file.flush()
        post_file.seek(0)
        datafile_count = DataFile.objects.count()
        dfo_count = DataFileObject.objects.count()
        self.assertHttpCreated(self.django_client.post(
            '/api/v1/mydata_dataset_file/',
            data={"json_data": post_data, "attached_file": post_file}))
        self.assertEqual(datafile_count + 1, DataFile.objects.count())
        self.assertEqual(dfo_count + 1, DataFileObject.objects.count())
        new_file = DataFile.objects.order_by('-pk')[0]
        self.assertEqual(file_content, new_file.get_file().read())

    def test_create_df_for_staging(self):
        ds_id = Dataset.objects.first().id
        post_data = {
            "dataset": "/api/v1/dataset/%d/" % ds_id,
            "filename": "mytestfile.txt",
            "md5sum": "930e419034038dfad994f0d2e602146c",
            "size": "8",
            "mimetype": "text/plain",
            "parameter_sets": []
        }

        datafile_count = DataFile.objects.count()
        dfo_count = DataFileObject.objects.count()
        response = self.django_client.post(
            '/api/v1/mydata_dataset_file/',
            json.dumps(post_data),
            content_type='application/json')
        self.assertHttpCreated(response)
        self.assertEqual(datafile_count + 1, DataFile.objects.count())
        self.assertEqual(dfo_count + 1, DataFileObject.objects.count())
        new_datafile = DataFile.objects.order_by('-pk')[0]
        new_dfo = DataFileObject.objects.order_by('-pk')[0]
        self.assertEqual(response.content, new_dfo.get_full_path().encode())

        # Now check we can submit a verification request for that file:
        response = self.django_client.get(
            '/api/v1/dataset_file/%s/verify/'
            % new_datafile.id)
        self.assertHttpOK(response)
