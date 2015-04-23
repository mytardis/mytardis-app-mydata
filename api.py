# api.py
"""
Additions to MyTardis's REST API
"""
from tastypie import fields
from tastypie.constants import ALL_WITH_RELATIONS

import tardis.tardis_portal.api
from tardis.tardis_portal.models.facility import facilities_managed_by

from models.uploader import Uploader
from models.uploader import UploaderStagingHost
from models.uploader import UploaderRegistrationRequest


class ACLAuthorization(tardis.tardis_portal.api.ACLAuthorization):
    '''Authorisation class for Tastypie.
    '''
    def read_list(self, object_list, bundle):  # noqa # too complex
        authuser = bundle.request.user
        authenticated = authuser.is_authenticated()
        is_facility_manager = authenticated and \
            len(facilities_managed_by(authuser)) > 0
        if isinstance(bundle.obj, Uploader):
            if is_facility_manager:
                return object_list
            return []
        elif isinstance(bundle.obj, UploaderStagingHost):
            '''
            The uploader staging host is currently designed to be viewed
            only in the Django admin interface, not via the API.
            '''
            raise NotImplementedError(type(bundle.obj))
        elif isinstance(bundle.obj, UploaderRegistrationRequest):
            if is_facility_manager:
                return object_list
            return []
        else:
            super(ACLAuthorization, self).read_list(object_list, bundle)

    def read_detail(self, object_list, bundle):  # noqa # too complex
        authuser = bundle.request.user
        authenticated = authuser.is_authenticated()
        is_facility_manager = authenticated and \
            len(facilities_managed_by(authuser)) > 0
        if isinstance(bundle.obj, Uploader):
            return is_facility_manager
        elif isinstance(bundle.obj, UploaderStagingHost):
            return False
        elif isinstance(bundle.obj, UploaderRegistrationRequest):
            return is_facility_manager
        else:
            super(ACLAuthorization, self).read_detail(object_list, bundle)

    def create_list(self, object_list, bundle):
        super(ACLAuthorization, self).create_list(object_list, bundle)

    def create_detail(self, object_list, bundle):  # noqa # too complex
        super(ACLAuthorization, self).create_detail(object_list, bundle)

    def update_list(self, object_list, bundle):
        super(ACLAuthorization, self).update_list(object_list, bundle)

    def update_detail(self, object_list, bundle):  # noqa # too complex
        super(ACLAuthorization, self).update_detail(object_list, bundle)

    def delete_list(self, object_list, bundle):
        super(ACLAuthorization, self).delete_list(object_list, bundle)

    def delete_detail(self, object_list, bundle):  # noqa # too complex
        super(ACLAuthorization, self).delete_detail(object_list, bundle)


class UploaderAppResource(tardis.tardis_portal.api.MyTardisModelResource):
    instruments = \
        fields.ManyToManyField(tardis.tardis_portal.api.InstrumentResource,
                               'instruments',
                                         null=True, full=True)

    class Meta(tardis.tardis_portal.api.MyTardisModelResource.Meta):
        resource_name = 'uploader'
        authentication = tardis.tardis_portal.api.default_authentication
        authorization = ACLAuthorization()
        queryset = Uploader.objects.all()
        filtering = {
            'mac_address': ('exact', ),
            'name': ('exact', ),
            'id': ('exact', ),
        }
        always_return_data = True

    def obj_create(self, bundle, **kwargs):
        bundle.data['created_time'] = datetime.now()
        bundle.data['updated_time'] = datetime.now()
        ip = get_ip(bundle.request)
        if ip is not None:
            bundle.data['wan_ip_address'] = ip
        bundle = super(UploaderResource, self).obj_create(bundle, **kwargs)
        return bundle

    def obj_update(self, bundle, **kwargs):
        # Workaround for
        # https://github.com/toastdriven/django-tastypie/issues/390 :
        if hasattr(bundle, "obj_update_done"):
            return
        bundle.data['updated_time'] = datetime.now()
        ip = get_ip(bundle.request)
        if ip is not None:
            bundle.data['wan_ip_address'] = ip
        bundle = super(UploaderResource, self).obj_update(bundle, **kwargs)
        bundle.obj_update_done = True
        return bundle


class UploaderStagingHostAppResource(tardis.tardis_portal.api.MyTardisModelResource):
    class Meta(tardis.tardis_portal.api.MyTardisModelResource.Meta):
        resource_name = 'uploaderstaginghost'
        authentication = tardis.tardis_portal.api.default_authentication
        authorization = ACLAuthorization()
        queryset = UploaderStagingHost.objects.all()


class UploaderRegistrationRequestAppResource(tardis.tardis_portal.api.MyTardisModelResource):
    uploader = fields.ForeignKey(
        'tardis.tardis_portal.api.UploaderResource', 'uploader')
    approved_staging_host = fields.ForeignKey(
        'tardis.tardis_portal.api.UploaderStagingHostResource',
        'approved_staging_host',
        full=True, null=True, blank=True, default=None)

    class Meta(tardis.tardis_portal.api.MyTardisModelResource.Meta):
        resource_name = 'uploaderregistrationrequest'
        authentication = tardis.tardis_portal.api.default_authentication
        authorization = ACLAuthorization()
        queryset = UploaderRegistrationRequest.objects.all()
        filtering = {
            'id': ('exact', ),
            'approved': ('exact', ),
            'requester_key_fingerprint': ('exact', ),
            'uploader': ALL_WITH_RELATIONS,
            'requester_key_fingerprint': ('exact', ),
        }
        always_return_data = True
    def obj_create(self, bundle, **kwargs):
        bundle = super(UploaderRegistrationRequestResource, self)\
            .obj_create(bundle, **kwargs)

        protocol = ""

        try:
            if hasattr(settings, "IS_SECURE") and settings.IS_SECURE:
                protocol = "s"

            current_site_complete = "http%s://%s" % \
                (protocol, Site.objects.get_current().domain)

            context = Context({
                'current_site': current_site_complete,
                'request_id': bundle.obj.id
            })

            subject = '[MyTardis] Uploader Registration Request Created'

            staff_users = User.objects.filter(is_staff=True)

            for staff in staff_users:
                if staff.email:
                    logger.info('email task dispatched to staff %s'
                                % staff.username)
                    email_user_task\
                        .delay(subject,
                               'uploader_registration_request_created',
                               context, staff)
        except:
            logger.error(traceback.format_exc())

        return bundle

    def hydrate(self, bundle):
        bundle = super(UploaderRegistrationRequestResource, self)\
            .hydrate(bundle)
        bundle.data['request_time'] = datetime.now()
        return bundle

    def save_related(self, bundle):
        if not hasattr(bundle.obj, 'approved_staging_host'):
            bundle.obj.approved_staging_host = None
        super(UploaderRegistrationRequestResource, self).save_related(bundle)
