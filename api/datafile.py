import logging
import traceback
import os
import json
import pytz

from django.conf import settings
from django.conf.urls import url
from django.core.files.storage import FileSystemStorage, get_storage_class
from django.db.utils import DatabaseError
from django.db import IntegrityError
from django.http import HttpResponse
from django.urls import resolve
from django.utils.timezone import is_aware, make_aware

from tastypie import fields
from tastypie.constants import ALL_WITH_RELATIONS
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.utils import trailing_slash
from ipware import get_client_ip
from dateutil.parser import parse

import tardis.tardis_portal.api
from tardis.tardis_portal.models.datafile import (
    DataFile,
    DataFileObject,
    compute_checksums
)
from ..models.uploader import (
    Uploader,
    UploaderRegistrationRequest
)

from .auth import ACLAuthorization


logger = logging.getLogger(__name__)


class DataFileAppResource(tardis.tardis_portal.api.MyTardisModelResource):
    '''
    Replaces MyTardis's API for DataFiles to make use of the
    Uploader model's approved_storage_box in staging uploads
    (e.g. from MyData)

    This class used to extend (inherit from) the MyTardis API's
    DataFileResource class, but the metadata included in the bundle is
    not needed for MyData's DataFile lookups, so now we're replacing
    that class, rather than extending it.
    '''
    dataset = fields.ForeignKey(
        tardis.tardis_portal.api.DatasetResource, 'dataset')
    datafile = fields.FileField()
    replicas = fields.ToManyField(
        tardis.tardis_portal.api.ReplicaResource,
        'file_objects',
        related_name='datafile', full=True, null=True)
    temp_url = None

    class Meta(tardis.tardis_portal.api.MyTardisModelResource.Meta):
        object_class = DataFile
        queryset = DataFile.objects.all()
        filtering = {
            'directory': ('exact', 'startswith'),
            'dataset': ALL_WITH_RELATIONS,
            'filename': ('exact', ),
        }
        ordering = [
            'filename',
            'modification_time'
        ]
        # This will be mapped to mydata_dataset_file by MyTardis's urls.py:
        resource_name = 'dataset_file'

    def hydrate(self, bundle):
        if 'attached_file' in bundle.data:
            # have POSTed file
            newfile = bundle.data['attached_file'][0]
            compute_md5 = getattr(settings, 'COMPUTE_MD5', True)
            compute_sha512 = getattr(settings, 'COMPUTE_SHA512', True)
            if (compute_md5 and 'md5sum' not in bundle.data) or \
                    (compute_sha512 and 'sha512sum' not in bundle.data):
                checksums = compute_checksums(newfile, close_file=False)
                if compute_md5:
                    bundle.data['md5sum'] = checksums['md5sum']
                if compute_sha512:
                    bundle.data['sha512sum'] = checksums['sha512sum']

            if 'replicas' in bundle.data:
                for replica in bundle.data['replicas']:
                    replica.update({'file_object': newfile})
            else:
                bundle.data['replicas'] = [{'file_object': newfile}]

            del(bundle.data['attached_file'])
        return bundle

    def _create_dfo(self, bundle):
        '''
        Called by the obj_create method, this method creates a DataFileObject
        when the POST body submitted to create a DataFile record doesn't
        include any replicas.
        '''
        datafile = bundle.obj
        try:
            if 'uploader_uuid' in bundle.data and \
                    'requester_key_fingerprint' in bundle.data:
                uploader_uuid = bundle.data['uploader_uuid']
                fingerprint = bundle.data['requester_key_fingerprint']
                uploader = Uploader.objects.get(uuid=uploader_uuid)
                uploader_registration_request = \
                    UploaderRegistrationRequest.objects.get(
                        uploader=uploader,
                        requester_key_fingerprint=fingerprint)
                sbox = uploader_registration_request.approved_storage_box
            else:
                ip, _ = get_client_ip(bundle.request)
                instrument_id = datafile.dataset.instrument.id
                uploader = Uploader.objects\
                    .filter(wan_ip_address=ip,
                            instruments__id=instrument_id)\
                    .first()
                uploader_registration_request = \
                    UploaderRegistrationRequest.objects\
                    .get(uploader=uploader)
                sbox = uploader_registration_request.approved_storage_box
        except Exception:
            logger.warning(traceback.format_exc())
            sbox = datafile.get_receiving_storage_box()
        if sbox is None:
            raise NotImplementedError
        dfo = DataFileObject(
            datafile=datafile,
            storage_box=sbox)
        dfo.create_set_uri()
        dfo.save()
        storage_class = get_storage_class(dfo.storage_box.django_storage_class)
        if getattr(settings, 'MYDATA_CREATE_DIRS', False) and \
                issubclass(storage_class, FileSystemStorage):
            # Try to ensure that the directory will exist for the client
            # (MyData) to upload to.  If creating the directory fails, log
            # an error, but don't raise an exception, because the client
            # can still create the directory if necessary.
            dfo_dir = os.path.dirname(dfo.get_full_path())
            try:
                os.makedirs(dfo_dir, mode=0o770, exist_ok=True)
                os.chmod(dfo_dir, 0o770)
            except OSError:
                logger.exception('Failed to make dirs for %s' % dfo_dir)
        self.temp_url = dfo.get_full_path()

    def obj_create(self, bundle, **kwargs):
        '''
        Creates a new DataFile object from the provided bundle.data dict.

        If a duplicate key error occurs, responds with HTTP Error 409: CONFLICT
        '''
        if settings.USE_TZ:
            tz = pytz.timezone(settings.TIME_ZONE)
            dst = getattr(settings, 'IS_DST', True)
            for k in ["created_time", "modification_time"]:
                time_str = bundle.data.get(k)
                if not time_str:
                    continue
                v = parse(time_str)
                if not is_aware(v):
                    bundle.data[k] = make_aware(v, tz, dst).isoformat()
        try:
            retval = super().obj_create(bundle, **kwargs)
        except IntegrityError as err:
            if "duplicate key" not in str(err) and \
                    "UNIQUE constraint failed" not in str(err) and \
                    "Duplicate entry" not in str(err):
                raise
            # Before returning a conflict error (409), let's check whether
            # the conflicting record is empty, in which case it can be deleted:
            filename = bundle.data.get("filename", "")
            directory = bundle.data.get("directory", "")
            version = bundle.data.get("version", 1)
            _, _, kwargs = resolve(bundle.data.get("dataset"))
            dataset_id = kwargs["pk"]
            duplicate = DataFile.objects.filter(
                dataset__id=dataset_id, filename=filename, directory=directory,
                version=version).first()
            # If the duplicate has zero DataFileObjects,
            # delete it and replace it:
            total = DataFileObject.objects.filter(datafile=duplicate).count()
            if duplicate and total == 0:
                duplicate.delete()
                retval = super().obj_create(bundle, **kwargs)
            else:
                raise ImmediateHttpResponse(HttpResponse(status=409))
        if 'replicas' not in bundle.data or not bundle.data['replicas']:
            # no replica specified: return upload path and create dfo for
            # new path
            try:
                self._create_dfo(bundle)
            except DatabaseError:
                # Instead of catching a DatabaseError, we could decorate the
                # obj_create method with @transaction.atomic, but this can
                # affect API performance, given the high frequency of DataFile
                # creation requests.

                # Delete DataFile record,
                # because DataFileObject creation failed:
                bundle.obj.delete()

                # The deletion above could fail with a subsequent database
                # error, in which case an exception will be raised and the
                # Tastypie API will return a 500 error *without* successfully
                # rolling back the DataFile creation. This try/except was
                # implemented in response to intermittent database connection
                # errors, in which case it seems likely that the DataFile
                # deletion will succeed.
                raise
        return retval

    def post_list(self, request, **kwargs):
        response = super().post_list(request, **kwargs)
        if self.temp_url is not None:
            response.content = self.temp_url
            self.temp_url = None
        return response

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/download%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('download_file'), name="api_download_file"),
            url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/verify%s$" %
                (self._meta.resource_name, trailing_slash()),
                self.wrap_view('verify_file'), name="api_verify_file"),
        ]

    def deserialize(self, request, data, format=None):
        '''
        from https://github.com/toastdriven/django-tastypie/issues/42
        modified to deserialize json sent via POST. Would fail if data is sent
        in a different format.
        uses a hack to get back pure json from request.POST
        '''
        if not format:
            format = request.META.get('CONTENT_TYPE', 'application/json')
        if format == 'application/x-www-form-urlencoded':
            return request.POST
        if format.startswith('multipart'):
            jsondata = request.POST['json_data']
            data = json.loads(jsondata)
            data.update(request.FILES)
            return data
        return super().deserialize(request, data, format)

    def put_detail(self, request, **kwargs):
        '''
        from https://github.com/toastdriven/django-tastypie/issues/42
        '''
        if request.META.get('CONTENT_TYPE').startswith('multipart') and \
                not hasattr(request, '_body'):
            request._body = ''

        return super().put_detail(request, **kwargs)

    def obj_get_list(self, bundle, **kwargs):
        '''
        Ensure that DataFile queries (filtering by filename,
        directory and dataset ID) don't return duplicate results,
        even if the dataset belongs to multiple experiments.
        '''
        obj_list = super().obj_get_list(bundle, **kwargs)
        return obj_list.order_by('id').distinct()


class ReplicaAppResource(tardis.tardis_portal.api.ReplicaResource):
    '''Extends MyTardis's API for DFOs, adding in the size as measured
    by file_object.size
    '''
    class Meta(tardis.tardis_portal.api.ReplicaResource.Meta):
        # This will be mapped to mydata_replica by MyTardis's urls.py:
        resource_name = 'replica'
        authorization = ACLAuthorization()
        queryset = DataFileObject.objects.all()
        filtering = {
            'verified': ('exact',),
            'url': ('exact', 'startswith'),
        }

    def dehydrate(self, bundle):
        dfo = bundle.obj
        bundle.data['location'] = dfo.storage_box.name
        try:
            file_object_size = getattr(
                getattr(dfo, 'file_object', None), 'size', None)
        except AttributeError:
            file_object_size = None
        except IOError:
            file_object_size = None
        bundle.data['size'] = file_object_size
        return bundle
