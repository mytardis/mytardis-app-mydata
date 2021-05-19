import json
import uuid
from random import randint

from django.test.client import Client

from tardis.tardis_portal.models.storage import StorageBox
from tardis.tardis_portal.models.datafile import DataFile, DataFileObject

from . import MyTardisResourceTestCase


class DatasetStatsAppResourceTest(MyTardisResourceTestCase):

    def setUp(self):
        super().setUp()
        self.num = randint(10, 20)
        self.size = 0
        for i in range(self.num):
            id = str(uuid.uuid4())
            size = randint(100, 1000)
            self.size += size
            df = DataFile(
                dataset=self.dataset,
                filename="%s-%s.txt" % (str(i), id),
                md5sum="c858d6319609d6db3c091b09783c479c",
                size=size)
            df.save()
            dfo = DataFileObject(
                datafile=df,
                storage_box=StorageBox.get_default_storage())
            dfo.create_set_uri()
            dfo.save()
        self.client = Client()
        self.client.login(
            username=self.username,
            password=self.password)

    def test_dataset_stats(self):
        response = self.client.get(
            "/api/v1/mydata_dataset_stats/%s/" % self.dataset.id
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("success", data)
        self.assertTrue(data["success"])
        self.assertIn("files", data)
        self.assertIn("total", data["files"])
        self.assertEqual(data["files"]["total"], self.num)
        self.assertEqual(data["files"]["verified"], 0)
        self.assertIn("size", data)
        self.assertEqual(data["size"], self.size)
        self.assertIn("verified", data)
        self.assertFalse(data["verified"])
