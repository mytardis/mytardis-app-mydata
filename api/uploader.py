import logging
import traceback
from datetime import datetime

from django.contrib.sites.models import Site
from django.core import mail
from django.core.mail import get_connection

from tastypie import fields
from tastypie.constants import ALL_WITH_RELATIONS
from ipware import get_client_ip

import tardis.tardis_portal.api
from ..models.uploader import (
    Uploader,
    UploaderRegistrationRequest,
    UploaderSetting
)

from .auth import ACLAuthorization


logger = logging.getLogger(__name__)


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

        return super().hydrate_m2m(bundle)

    def obj_create(self, bundle, **kwargs):
        bundle.data['created_time'] = datetime.now()
        bundle.data['updated_time'] = datetime.now()
        ip, _ = get_client_ip(bundle.request)
        if ip is not None:
            bundle.data['wan_ip_address'] = ip
        bundle = super().obj_create(bundle, **kwargs)
        return bundle

    def obj_update(self, bundle, **kwargs):
        # Workaround for
        # https://github.com/toastdriven/django-tastypie/issues/390 :
        if hasattr(bundle, "obj_update_done"):
            return bundle
        bundle.data['updated_time'] = datetime.now()
        ip, _ = get_client_ip(bundle.request)
        if ip is not None:
            bundle.data['wan_ip_address'] = ip
        bundle = super().obj_update(bundle, **kwargs)
        bundle.obj_update_done = True
        return bundle


class UploaderRegistrationRequestAppResource(
    tardis.tardis_portal.api.MyTardisModelResource
):
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
        bundle = super().obj_create(bundle, **kwargs)
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
            logger.info('Informing managers of a new '
                        'uploader registraion request.')
            mail.mail_managers(
                subject,
                message,
                connection=get_connection(fail_silently=True)
            )
        except Exception:
            logger.error(traceback.format_exc())

        return bundle

    def hydrate(self, bundle):
        bundle = super().hydrate(bundle)
        bundle.data['request_time'] = datetime.now()
        return bundle

    def save_related(self, bundle):
        if not hasattr(bundle.obj, 'approved_storage_box'):
            bundle.obj.approved_storage_box = None
        super().save_related(bundle)


class UploaderSettingAppResource(
    tardis.tardis_portal.api.MyTardisModelResource
):
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
