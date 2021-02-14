import os
import json

from django.test import override_settings
from django.test.client import Client

from tardis.tardis_portal.models.storage import StorageBox
from tardis.tardis_portal.models.datafile import DataFile, DataFileObject
from ...models.chunk import Chunk
from ...tasks import chunks_cleanup

from . import MyTardisResourceTestCase


class UploadAppResourceTest(MyTardisResourceTestCase):

    def setUp(self):
        super().setUp()
        self.fixtures_path = "tardis/apps/mydata/fixtures"
        self.chunks = [{
            "name": "xaa.bin",
            "range": "0-1000/1553",
            "md5sum": "1302ac5df76a7c3fb420cdf7f660049a"
        }, {
            "name": "xab.bin",
            "range": "1000-1553/1553",
            "md5sum": "6778a50e7d952264d0cadf8500e53559"
        }]
        self.df = DataFile(
            dataset=self.dataset,
            filename="passenger.txt",
            md5sum="3b87f155dbbbd3168c09be2500f43437",
            size=1553)
        self.df.save()
        self.dfo = DataFileObject(
            datafile=self.df,
            storage_box=StorageBox.get_default_storage())
        self.dfo.create_set_uri()
        self.dfo.save()
        self.client = Client()
        self.client.login(
            username=self.username,
            password=self.password)

    def tearDown(self):
        try:
            self.dfo.delete()
        except:
            pass
        try:
            self.df.delete()
        except:
            pass
        super().tearDown()

    def upload_chunk(self, pos):
        chunk = self.chunks[pos]
        fname = os.path.join(self.fixtures_path, chunk["name"])
        headers = {
            "Checksum": chunk["md5sum"],
            "Content-Range": chunk["range"]
        }
        with open(fname, "rb") as f:
            data = f.read()
        return self.client.post(
            "/api/v1/mydata_upload/%s/upload/" % self.dfo.id,
            content_type="application/octet-stream",
            data=data,
            **headers)

    def test_get_chunks_error(self):
        response = self.api_client.get(
            "/api/v1/mydata_upload/%s/" % str(self.dfo.id+1),
            authentication=self.get_credentials())
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        for k in ["success", "error"]:
            self.assertIn(k, data)
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "Invalid object or access denied.")

    @override_settings(CHUNK_MIN_SIZE=1000)
    @override_settings(CHUNK_MAX_SIZE=1000)
    @override_settings(CHUNK_CHECKSUM="md5")
    def test_get_chunks(self):
        response = self.api_client.get(
            "/api/v1/mydata_upload/%s/" % self.dfo.id,
            authentication=self.get_credentials())
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        for k in ["success", "offset", "size", "checksum"]:
            self.assertIn(k, data)
        self.assertTrue(data["success"])
        self.assertEqual(data["offset"], 0)
        self.assertEqual(data["size"], 1000)
        self.assertEqual(data["checksum"], "md5")

    @override_settings(CHUNK_MIN_SIZE=1000)
    @override_settings(CHUNK_MAX_SIZE=1000)
    @override_settings(CHUNK_CHECKSUM="md5")
    @override_settings(CHUNK_STORAGE="/tmp")
    def test_upload_chunk(self):
        response = self.upload_chunk(0)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        for k in ["success", "id"]:
            self.assertIn(k, data)
        self.assertTrue(data["success"])

    @override_settings(CHUNK_MIN_SIZE=1000)
    @override_settings(CHUNK_MAX_SIZE=1000)
    @override_settings(CHUNK_CHECKSUM="md5")
    @override_settings(CHUNK_STORAGE="/tmp")
    @override_settings(CHUNK_COPY_SIZE=250)
    def test_complete_upload(self):
        self.upload_chunk(0)
        self.upload_chunk(1)
        response = self.api_client.get(
            "/api/v1/mydata_upload/%s/complete/" % self.dfo.id,
            authentication=self.get_credentials())
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("success", data)
        self.assertTrue(data["success"])
        dfo = DataFileObject.objects.get(id=self.dfo.id)
        self.assertTrue(dfo.verify())


    @override_settings(CHUNK_MIN_SIZE=1000)
    @override_settings(CHUNK_MAX_SIZE=1000)
    @override_settings(CHUNK_CHECKSUM="md5")
    @override_settings(CHUNK_STORAGE="/tmp")
    @override_settings(CHUNK_COPY_SIZE=250)
    def test_cleanup_task(self):
        chunks_folder = os.path.join("/tmp", str(self.dfo.id))
        response = self.upload_chunk(0)
        data = json.loads(response.content)
        chunk_a = Chunk.objects.get(id=data["id"])
        fname_a = os.path.join("/tmp", str(self.dfo.id), str(chunk_a.chunk_id))
        response = self.upload_chunk(1)
        data = json.loads(response.content)
        chunk_b = Chunk.objects.get(id=data["id"])
        fname_b = os.path.join("/tmp", str(self.dfo.id), str(chunk_b.chunk_id))
        self.assertTrue(os.path.exists(fname_a))
        self.assertTrue(os.path.exists(fname_b))
        self.dfo.delete()
        self.assertTrue(os.path.exists(fname_a))
        self.assertTrue(os.path.exists(fname_b))
        chunks_cleanup.apply_async()
        self.assertFalse(os.path.exists(fname_a))
        self.assertFalse(os.path.exists(fname_b))
        self.assertFalse(os.path.exists(chunks_folder))
