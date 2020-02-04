'''
Testing the tastypie-based mytardis api

.. moduleauthor:: Grischa Meyer <grischa@gmail.com>
.. moduleauthor:: James Wettenhall <james.wettenhall@monash.edu>
'''
import json

from . import MyTardisResourceTestCase


class UploaderAppResourceTest(MyTardisResourceTestCase):
    def test_get_uploader_by_id(self):
        response = self.api_client.get(
            "/api/v1/mydata_uploader/%s/" % self.uploader.id,
            authentication=self.get_credentials())
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        for k in ["id", "name"]:
            self.assertIn(k, data)
            self.assertEqual(data[k], getattr(self.uploader, k))

    def test_ambiguous_time_error(self):
        '''
        Test for ticket https://jira.apps.monash.edu/browse/SDM-411
        '''
        payload = {
            "uploader_uuid": self.uploader_uuid,
            "requester_key_fingerprint": self.requester_key_fingerprint,
            "dataset": "/api/v1/dataset/%s/" % self.dataset.id,
            "schema": "/api/v1/schema/%s/" % self.schema.id,
            "directory": "",
            "filename": "mytestfile.txt",
            "md5sum": "c858d6319609d6db3c091b09783c479c",
            "size": 339597188,
            "mimetype": "text/plain",
            "created_time": "2019-04-07T01:24:07.692530",
            "modification_time": "2019-04-07T02:46:42.739467"
        }
        response = self.api_client.post(
            "/api/v1/mydata_dataset_file/",
            data=payload,
            authentication=self.get_credentials())

        self.assertEqual(response.status_code, 201) # HTTP 201 Created
