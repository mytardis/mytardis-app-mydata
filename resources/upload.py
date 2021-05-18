import logging
import os
import re
import math

from django.conf import settings
from django.conf.urls import url
from django.http import JsonResponse
from tastypie.utils import trailing_slash

import tardis.tardis_portal.api

from tardis.tardis_portal.models.datafile import DataFileObject

from .auth import ACLAuthorization

from ..models.chunk import Chunk

from .. import utils
from .. import tasks


logger = logging.getLogger(__name__)


class UploadAppResource(tardis.tardis_portal.api.MyTardisModelResource):
    """
    Provide chunked upload for data file
    https://docs.google.com/document/d/1wZDwReW8LyplHJiUuH3QTzNguODX6mU2-8J6XN7PzZk/edit
    """

    class Meta(tardis.tardis_portal.api.MyTardisModelResource.Meta):
        resource_name = "upload"
        allowed_methods = ["get", "put", "post"]
        authorization = ACLAuthorization()
        queryset = Chunk.objects.all()
        filtering = {
            "dfo_id": ["exact"]
        }
        always_return_data = True

    def prepend_urls(self):
        return [
            url(
                r"^(?P<resource_name>%s)/(?P<dfo_id>\d+)%s$" % (
                self._meta.resource_name, trailing_slash()),
                self.wrap_view("get_chunks"),
                name="api_mydata_get_chunks"
            ),
            url(
                r"^(?P<resource_name>%s)/(?P<dfo_id>\d+)/upload%s$" % (
                self._meta.resource_name, trailing_slash()),
                self.wrap_view("upload_chunk"),
                name="api_mydata_upload_chunk"
            ),
            url(
                r"^(?P<resource_name>%s)/(?P<dfo_id>\d+)/complete%s$" % (
                self._meta.resource_name, trailing_slash()),
                self.wrap_view("complete_upload"),
                name="api_mydata_complete_upload"
            ),
        ]

    def check_dfo(self, request, dfo_id):
        try:
            dfo = DataFileObject.objects.get(id=dfo_id)
            return any(
                request.user.has_perm("tardis_acls.change_experiment", experiment)
                for experiment in dfo.datafile.dataset.experiments.all())
        except:
            pass

        return None

    def handle_error(self, message):
        """
        Return error message in JSON format
        """
        data = {
            "success": False,
            "error": message
        }

        return JsonResponse(data, status=200)

    def get_chunk_size(self, file_size):
        """
        Calculate chunk size based on data file size
        """
        chunk_size = settings.CHUNK_MIN_SIZE
        while True:
            count_chunks = math.ceil(file_size/chunk_size)
            if count_chunks < 100:
                return chunk_size
            chunk_size += settings.CHUNK_MIN_SIZE
            if chunk_size > settings.CHUNK_MAX_SIZE:
                return settings.CHUNK_MAX_SIZE

    def get_chunks(self, request, **kwargs):
        """
        Get status of data file upload
        """
        self.method_check(request, allowed=["get"])
        self.is_authenticated(request)

        if not self.check_dfo(request, kwargs["dfo_id"]):
            return self.handle_error("Invalid object or access denied.")

        dfo = DataFileObject.objects.get(id=kwargs["dfo_id"])
        file_size = dfo.datafile.size

        data = {
            "success": True,
            "completed": True
        }

        if not dfo.verified:

            try:
                # Check for uploaded chunks
                last_chunk = Chunk.objects.filter(dfo_id=kwargs["dfo_id"]).order_by("-offset")[0]
                offset = min(last_chunk.offset + last_chunk.size, file_size)
            except:
                offset = 0

            if offset != file_size:
                data["completed"] = False
                data["offset"] = offset
                data["size"] = self.get_chunk_size(file_size)
                data["checksum"] = settings.CHUNK_CHECKSUM

        return JsonResponse(data, status=200)

    def upload_chunk(self, request, **kwargs):
        """
        Upload chunk of data file
        """
        import uuid

        self.method_check(request, allowed=["post"])
        self.is_authenticated(request)

        if not self.check_dfo(request, kwargs["dfo_id"]):
            return self.handle_error("Invalid object or access denied.")

        checksum = request.headers.get("Checksum", None)
        if checksum is None:
            checksum = request.META.get("Checksum", None)
            if checksum is None:
                return self.handle_error("Missing 'Checksum' in header.")

        content_range = request.headers.get("Content-Range", None)
        if content_range is None:
            content_range = request.META.get("Content-Range", None)
            if content_range is None:
                return self.handle_error("Missing 'Content-Range' in header.")

        m = re.search(r"^(\d+)\-(\d+)\/(\d+)$", content_range).groups()
        content_start = int(m[0])
        content_end = int(m[1])
        content_length = content_end-content_start
        if content_length > settings.CHUNK_MAX_SIZE:
            return self.handle_error("Chunk size is larger than max allowed.")

        check = Chunk.objects.filter(
            dfo_id=kwargs["dfo_id"],
            offset=content_start
        )
        if len(check) != 0:
            return self.handle_error("Chunk already uploaded.")

        content_checksum = utils.calc_checksum(settings.CHUNK_CHECKSUM, request.body)
        if content_checksum is None or content_checksum != checksum:
            return self.handle_error(
                "Checksum does not match. {}:{}".format(settings.CHUNK_CHECKSUM, content_checksum))

        if not os.path.exists(settings.CHUNK_STORAGE):
            try:
                os.mkdir(settings.CHUNK_STORAGE)
            except Exception as e:
                return self.handle_error(str(e))

        data_path = os.path.join(settings.CHUNK_STORAGE, kwargs["dfo_id"])
        if not os.path.exists(data_path):
            try:
                os.makedirs(data_path, mode=0o770, exist_ok=True)
                os.chmod(data_path, 0o770)
            except Exception as e:
                return self.handle_error(str(e))

        chunk_id = str(uuid.uuid4())
        file_path = os.path.join(data_path, chunk_id)

        try:
            with open(file_path, "wb") as file:
                file.write(request.body)
                file.close()
        except Exception as e:
            return self.handle_error(str(e))

        dfo = DataFileObject.objects.get(id=kwargs["dfo_id"])

        instrument = dfo.datafile.dataset.instrument
        if instrument is not None:
            instrument_id = instrument.id
        else:
            instrument_id = None

        try:
            chunk = Chunk.objects.create(
                chunk_id=chunk_id,
                dfo_id=kwargs["dfo_id"],
                offset=content_start,
                size=content_length,
                instrument_id=instrument_id,
                user_id=request.user.id
            )
        except Exception as e:
            try:
                os.remove(file_path)
            except Exception as e:
                pass
            return self.handle_error(str(e))

        data = {
            "success": True,
            "id": chunk.id
        }

        return JsonResponse(data, status=200)

    def complete_upload(self, request, **kwargs):
        """
        Complete upload and create full file
        """

        self.method_check(request, allowed=["get"])
        self.is_authenticated(request)

        if not self.check_dfo(request, kwargs["dfo_id"]):
            return self.handle_error("Invalid object or access denied.")

        dfo = DataFileObject.objects.get(id=kwargs["dfo_id"])

        if not dfo.verified:
            # Async task as we can't wait until file is ready
            tasks.complete_chunked_upload.apply_async(args=[dfo.id])

        data = {
            "success": True,
            "verified": dfo.verified
        }

        return JsonResponse(data, status=200)
