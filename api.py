# api.py
"""
Additions to MyTardis's REST API
"""
import json
import logging
import os
import traceback
from datetime import datetime
import pytz

from django.conf import settings
from django.conf.urls import url
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail
from django.core.files.storage import FileSystemStorage, get_storage_class
from django.core.mail import get_connection
from django.db.utils import DatabaseError
from django.db import IntegrityError
from django.http import HttpResponse
from django.urls import resolve
from django.utils.timezone import is_aware, make_aware
from tastypie import fields
from tastypie.constants import ALL_WITH_RELATIONS
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.utils import trailing_slash
from ipware.ip import get_ip
from dateutil.parser import parse

import tardis.tardis_portal.api
from tardis.tardis_portal.auth.decorators import has_datafile_access
from tardis.tardis_portal.models.facility import facilities_managed_by
from tardis.tardis_portal.models.experiment import Experiment
from tardis.tardis_portal.models.parameters import Schema
from tardis.tardis_portal.models.parameters import ExperimentParameter
from tardis.tardis_portal.models.parameters import ExperimentParameterSet
from tardis.tardis_portal.models.datafile import DataFile
from tardis.tardis_portal.models.datafile import DataFileObject
from tardis.tardis_portal.models.datafile import compute_checksums

from .models.uploader import Uploader
from .models.uploader import UploaderRegistrationRequest
from .models.uploader import UploaderSetting

logger = logging.getLogger(__name__)


class ACLAuthorization(tardis.tardis_portal.api.ACLAuthorization):
    '''Authorisation class for Tastypie.
    '''
    def read_list(self, object_list, bundle):  # noqa # too complex
        authuser = bundle.request.user
        authenticated = authuser.is_authenticated
        is_facility_manager = authenticated and \
            len(facilities_managed_by(authuser)) > 0
        if isinstance(bundle.obj, Uploader):
            if is_facility_manager:
                return object_list
            return []
        if isinstance(bundle.obj, UploaderSetting):
            if is_facility_manager:
                return object_list
            return []
        if isinstance(bundle.obj, UploaderRegistrationRequest):
            if is_facility_manager:
                return object_list
            return []
        return super(ACLAuthorization, self).read_list(object_list, bundle)

    def read_detail(self, object_list, bundle):  # noqa # too complex
        if bundle.request.user.is_authenticated and \
           bundle.request.user.is_superuser:
            return True
        authuser = bundle.request.user
        authenticated = authuser.is_authenticated
        is_facility_manager = authenticated and \
            len(facilities_managed_by(authuser)) > 0
        if isinstance(bundle.obj, Uploader):
            return is_facility_manager
        if isinstance(bundle.obj, UploaderRegistrationRequest):
            return is_facility_manager
        if isinstance(bundle.obj, DataFileObject):
            return has_datafile_access(bundle.request, bundle.obj.datafile.id)
        return super(ACLAuthorization, self).read_detail(object_list, bundle)

    def create_detail(self, object_list, bundle):
        authuser = bundle.request.user
        authenticated = authuser.is_authenticated
        is_facility_manager = authenticated and \
            len(facilities_managed_by(authuser)) > 0
        if isinstance(bundle.obj, Uploader):
            return is_facility_manager
        if isinstance(bundle.obj, UploaderRegistrationRequest):
            return is_facility_manager
        if isinstance(bundle.obj, UploaderSetting):
            return is_facility_manager
        return super(ACLAuthorization, self).create_detail(object_list, bundle)

    def update_detail(self, object_list, bundle):
        '''
        Uploaders should only be able to update the uploader record whose
        UUID matches theirs (if it exists).
        '''
        authuser = bundle.request.user
        authenticated = authuser.is_authenticated
        is_facility_manager = authenticated and \
            len(facilities_managed_by(authuser)) > 0
        if isinstance(bundle.obj, Uploader):
            return is_facility_manager and \
                bundle.data['uuid'] == bundle.obj.uuid
        if isinstance(bundle.obj, UploaderSetting):
            return is_facility_manager
        return super(ACLAuthorization, self).update_detail(object_list, bundle)


class UploaderAppResource(tardis.tardis_portal.api.MyTardisModelResource):
    instruments = \
        fields.ManyToManyField(tardis.tardis_portal.api.InstrumentResource,
                               'instruments', null=True, full=True)
    settings = fields.ToManyField(
        'tardis.apps.mydata.api.UploaderSettingAppResource',
        'settings',
        related_name='uploader',
        full=True, null=True)

    class Meta(tardis.tardis_portal.api.MyTardisModelResource.Meta):
        object_class = Uploader
        resource_name = 'uploader'
        authentication = tardis.tardis_portal.api.default_authentication
        authorization = ACLAuthorization()
        queryset = Uploader.objects.all()
        filtering = {
            'uuid': ('exact', ),
            'name': ('exact', ),
        }
        always_return_data = True

    def dehydrate(self, bundle):
        '''
        We want to be able to upload some fields to give MyTardis sys admins
        info about the client machine MyData is running on, but we don't
        want those fields to be available for download, so we remove them
        here.
        '''
        accessible_keys = ['id', 'resource_uri', 'name', 'settings',
                           'settings_updated', 'settings_downloaded']
        for key in list(bundle.data.keys()):
            if key not in accessible_keys:
                del(bundle.data[key])
        return bundle

    def hydrate_m2m(self, bundle):
        '''
        Allow updating multiple UploaderSettings simultaneously.
        '''
        if getattr(bundle.obj, 'id', False) and 'settings' in bundle.data:
            uploader = bundle.obj
            for setting in bundle.data['settings']:
                try:
                    uploader_setting = \
                        UploaderSetting.objects.get(uploader=uploader,
                                                    key=setting['key'])
                    uploader_setting.value = setting['value']
                except UploaderSetting.DoesNotExist:
                    uploader_setting = UploaderSetting(uploader=uploader,
                                                       key=setting['key'],
                                                       value=setting['value'])
                uploader_setting.save()
            del(bundle.data['settings'])
            bundle.obj.settings_updated = datetime.now()
            bundle.obj.save()

        return super(UploaderAppResource, self).hydrate_m2m(bundle)

    def obj_create(self, bundle, **kwargs):
        bundle.data['created_time'] = datetime.now()
        bundle.data['updated_time'] = datetime.now()
        ip = get_ip(bundle.request)
        if ip is not None:
            bundle.data['wan_ip_address'] = ip
        bundle = super(UploaderAppResource, self).obj_create(bundle, **kwargs)
        return bundle

    def obj_update(self, bundle, **kwargs):
        # Workaround for
        # https://github.com/toastdriven/django-tastypie/issues/390 :
        if hasattr(bundle, "obj_update_done"):
            return bundle
        bundle.data['updated_time'] = datetime.now()
        ip = get_ip(bundle.request)
        if ip is not None:
            bundle.data['wan_ip_address'] = ip
        bundle = super(UploaderAppResource, self).obj_update(bundle, **kwargs)
        bundle.obj_update_done = True
        return bundle


class UploaderRegistrationRequestAppResource(tardis.tardis_portal.api
                                             .MyTardisModelResource):
    uploader = fields.ForeignKey(UploaderAppResource, 'uploader')
    approved_storage_box = fields.ForeignKey(
        tardis.tardis_portal.api.StorageBoxResource,
        'approved_storage_box', null=True, full=True)

    class Meta(tardis.tardis_portal.api.MyTardisModelResource.Meta):
        object_class = UploaderRegistrationRequest
        resource_name = 'uploaderregistrationrequest'
        authentication = tardis.tardis_portal.api.default_authentication
        authorization = ACLAuthorization()
        queryset = UploaderRegistrationRequest.objects.all()
        filtering = {
            'id': ('exact', ),
            'approved': ('exact', ),
            'requester_key_fingerprint': ('exact', ),
            'uploader': ALL_WITH_RELATIONS,
            'approved_storage_box': ALL_WITH_RELATIONS,
        }
        always_return_data = True

    def obj_create(self, bundle, **kwargs):
        bundle = super(UploaderRegistrationRequestAppResource, self)\
            .obj_create(bundle, **kwargs)
        try:
            site = Site.objects.get_current().domain
            subject = '[MyTardis] Uploader Registration Request Created'
            message = \
                "Hi, this message is for MyTardis Admins.\n\n" \
                "An uploader registration request has just been created:\n\n" \
                "%s/admin/mydata/uploaderregistrationrequest/%d\n\n" \
                "Thanks,\n" \
                "MyTardis\n" \
                % (site, bundle.obj.id)
            logger.info('Informing admins of a new '
                        'uploader registraion request.')
            mail.mail_admins(subject, message,
                             connection=get_connection(fail_silently=True))
        except:
            logger.error(traceback.format_exc())

        return bundle

    def hydrate(self, bundle):
        bundle = super(UploaderRegistrationRequestAppResource, self)\
            .hydrate(bundle)
        bundle.data['request_time'] = datetime.now()
        return bundle

    def save_related(self, bundle):
        if not hasattr(bundle.obj, 'approved_storage_box'):
            bundle.obj.approved_storage_box = None
        super(UploaderRegistrationRequestAppResource,
              self).save_related(bundle)


class UploaderSettingAppResource(tardis.tardis_portal.api.MyTardisModelResource):
    uploader = fields.ForeignKey(
        UploaderAppResource,
        'uploader',
        related_name='settings',
        full=False)

    class Meta(tardis.tardis_portal.api.MyTardisModelResource.Meta):
        object_class = UploaderSetting
        resource_name = 'uploadersetting'
        authentication = tardis.tardis_portal.api.default_authentication
        authorization = ACLAuthorization()
        queryset = UploaderSetting.objects.all()
        always_return_data = True


class ExperimentAppResource(tardis.tardis_portal.api.ExperimentResource):
    '''Extends MyTardis's API for Experiments
    to allow querying of metadata relevant to MyData
    '''

    class Meta(tardis.tardis_portal.api.ExperimentResource.Meta):
        # This will be mapped to mydata_experiment by MyTardis's urls.py:
        resource_name = 'experiment'

    def obj_get_list(self, bundle, **kwargs):
        '''
        Used by MyData to determine whether an appropriate default experiment
        exists to add a dataset to.
        '''

        '''
        For backwards compatibility with older MyData versions, let's
        try to guess the folder structure if it wasn't provided:
        '''
        folder_structure = None
        if hasattr(bundle.request, 'GET') and \
                'folder_structure' not in bundle.request.GET:
            if 'group_folder_name' in bundle.request.GET and \
                    bundle.request.GET['group_folder_name'].strip() != '':
                folder_structure = 'User Group / ...'
            elif 'user_folder_name' in bundle.request.GET:
                if '@' in bundle.request.GET['user_folder_name']:
                    folder_structure = 'Email / ...'
                else:
                    folder_structure = 'Username / ...'
            else:
                folder_structure = 'Username / ...'

        class UnknownUser(object):
            def __init__(self, username='UNKNOWN', email='UNKNOWN'):
                self.username = username
                self.email = email

        '''
        Responds to title/folder_structure/[user_folder_name|group_folder_name]
        query for MyData.  This can be used by MyData to retrieve an experiment
        which can be used to collect datasets from multiple MyData instances.
        '''
        if hasattr(bundle.request, 'GET') and \
                'title' in bundle.request.GET and \
                ('user_folder_name' in bundle.request.GET or
                 'group_folder_name' in bundle.request.GET):

            title = bundle.request.GET['title']
            if 'folder_structure' in bundle.request.GET:
                folder_structure = bundle.request.GET['folder_structure']
            need_to_match_user = (folder_structure.startswith('Username /') or
                                  folder_structure.startswith('Email /'))
            need_to_match_group = folder_structure.startswith('User Group /')

            if need_to_match_user:
                user_folder_name = bundle.request.GET['user_folder_name']
                if folder_structure.startswith('Username /'):
                    try:
                        user_to_match = \
                            User.objects.get(username=user_folder_name, is_active=True)
                    except User.DoesNotExist:
                        user_to_match = UnknownUser(username=user_folder_name)
                elif folder_structure.startswith('Email /'):
                    try:
                        user_to_match = \
                            User.objects.get(email__iexact=user_folder_name, is_active=True)
                    except User.DoesNotExist:
                        user_to_match = UnknownUser(email=user_folder_name)

            if need_to_match_group:
                group_folder_name = bundle.request.GET['group_folder_name']

            mydata_default_exp_schema = Schema.objects.get(
                namespace='http://mytardis.org'
                '/schemas/mydata/defaultexperiment')

            exp_psets = ExperimentParameterSet.objects\
                .filter(experiment__title=title,
                        schema=mydata_default_exp_schema)
            for exp_pset in exp_psets:
                exp_params = ExperimentParameter.objects\
                    .filter(parameterset=exp_pset)
                matched_user = False
                matched_group = False
                for exp_param in exp_params:
                    if need_to_match_user and \
                            exp_param.name.name == 'user_folder_name' and \
                            (exp_param.string_value.lower() ==
                             user_to_match.username.lower() or
                             exp_param.string_value.lower() ==
                             user_to_match.email.lower()):
                        matched_user = True
                    if need_to_match_group and \
                            exp_param.name.name == 'group_folder_name' and \
                            exp_param.string_value == group_folder_name:
                        matched_group = True
                is_mu = need_to_match_user and matched_user
                is_mg = need_to_match_group and matched_group
                is_nah = not need_to_match_user and not need_to_match_group
                if is_mu or is_mg or is_nah:
                    experiment_id = exp_pset.experiment.id
                    exp_list = Experiment.objects.filter(pk=experiment_id)
                    if exp_list[0] in Experiment.safe.all(bundle.request.user):
                        return exp_list

            return []

        '''
        Responds to
        uploader/folder_structure/[user_folder_name|group_folder_name]
        query for MyData.  Each MyData instance generates a UUID the first time
        it runs on each upload PC. The UUID together with the user folder name
        (or group folder name) can be used to uniquely identify one particular
        user (or group) who has saved data on an instrument PC running a MyData
        instance identified by the UUID.
        '''
        if hasattr(bundle.request, 'GET') and \
                'uploader' in bundle.request.GET and \
                ('user_folder_name' in bundle.request.GET or
                 'group_folder_name' in bundle.request.GET):

            uploader_uuid = bundle.request.GET['uploader']
            if 'folder_structure' in bundle.request.GET:
                folder_structure = bundle.request.GET['folder_structure']
            need_to_match_user = (folder_structure.startswith('Username /') or
                                  folder_structure.startswith('Email /'))
            need_to_match_group = folder_structure.startswith('User Group /')

            if need_to_match_user:
                user_folder_name = bundle.request.GET['user_folder_name']
                if folder_structure.startswith('Username /'):
                    try:
                        user_to_match = \
                            User.objects.get(username=user_folder_name, is_active=True)
                    except User.DoesNotExist:
                        user_to_match = UnknownUser(username=user_folder_name)
                elif folder_structure.startswith('Email /'):
                    try:
                        user_to_match = \
                            User.objects.get(email__iexact=user_folder_name, is_active=True)
                    except User.DoesNotExist:
                        user_to_match = UnknownUser(email=user_folder_name)

            if need_to_match_group:
                group_folder_name = bundle.request.GET['group_folder_name']

            mydata_default_exp_schema = Schema.objects.get(
                namespace='http://mytardis.org'
                '/schemas/mydata/defaultexperiment')

            exp_psets = ExperimentParameterSet.objects\
                .filter(schema=mydata_default_exp_schema)
            for exp_pset in exp_psets:
                exp_params = ExperimentParameter.objects\
                    .filter(parameterset=exp_pset)
                matched_uploader_uuid = False
                matched_user = False
                matched_group = False
                for exp_param in exp_params:
                    if exp_param.name.name == 'uploader' and \
                            exp_param.string_value == uploader_uuid:
                        matched_uploader_uuid = True
                    if need_to_match_user and \
                            exp_param.name.name == 'user_folder_name' and \
                            (exp_param.string_value.lower() ==
                             user_to_match.username.lower() or
                             exp_param.string_value.lower() ==
                             user_to_match.email.lower()):
                        matched_user = True
                    if exp_param.name.name == 'group_folder_name' and \
                            exp_param.string_value == group_folder_name:
                        matched_group = True
                if matched_uploader_uuid and \
                        (need_to_match_user and matched_user or
                         need_to_match_group and matched_group):
                    experiment_id = exp_pset.experiment.id
                    exp_list = Experiment.objects.filter(pk=experiment_id)
                    if exp_list[0] in Experiment.safe.all(bundle.request.user):
                        return exp_list

            return []

        return super(ExperimentAppResource, self).obj_get_list(bundle,
                                                               **kwargs)


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
    dataset = fields.ForeignKey(tardis.tardis_portal.api.DatasetResource, 'dataset')
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
                ip = get_ip(bundle.request)
                instrument_id = datafile.dataset.instrument.id
                uploader = Uploader.objects\
                    .filter(wan_ip_address=ip,
                            instruments__id=instrument_id)\
                    .first()
                uploader_registration_request = \
                    UploaderRegistrationRequest.objects\
                    .get(uploader=uploader)
                sbox = uploader_registration_request.approved_storage_box
        except:
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
            retval = super(DataFileAppResource, self).obj_create(bundle, **kwargs)
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
            # If the duplicate has zero DataFileObjects, delete it and replace it:
            if duplicate and DataFileObject.objects.filter(datafile=duplicate).count() == 0:
                duplicate.delete()
                retval = super(DataFileAppResource, self).obj_create(bundle, **kwargs)
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

                # Delete DataFile record, because DataFileObject creation failed:
                bundle.obj.delete()

                # The deletion above could fail with a subsequent database error,
                # in which case an exception will be raised and the Tastypie API
                # will return a 500 error *without* successfully rolling back the
                # DataFile creation.  This try/except was implemented in response
                # to intermittent database connection errors, in which case it
                # seems likely that the DataFile deletion will succeed.
                raise
        return retval

    def post_list(self, request, **kwargs):
        response = super(DataFileAppResource, self).post_list(request, **kwargs)
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
        return super(DataFileAppResource, self).deserialize(request, data, format)

    def put_detail(self, request, **kwargs):
        '''
        from https://github.com/toastdriven/django-tastypie/issues/42
        '''
        if request.META.get('CONTENT_TYPE').startswith('multipart') and \
                not hasattr(request, '_body'):
            request._body = ''

        return super(DataFileAppResource, self).put_detail(request, **kwargs)

    def obj_get_list(self, bundle, **kwargs):
        '''
        Ensure that DataFile queries (filtering by filename,
        directory and dataset ID) don't return duplicate results,
        even if the dataset belongs to multiple experiments.
        '''
        obj_list = super(DataFileAppResource, self).obj_get_list(
            bundle, **kwargs)
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
