import logging

from django.contrib.auth.models import User

import tardis.tardis_portal.api

from tardis.tardis_portal.auth.decorators import has_datafile_access
from tardis.tardis_portal.models.facility import facilities_managed_by
from tardis.tardis_portal.models.datafile import DataFileObject

from ..models.uploader import Uploader
from ..models.uploader import UploaderRegistrationRequest
from ..models.uploader import UploaderSetting


logger = logging.getLogger(__name__)


class ACLAuthorization(tardis.tardis_portal.api.ACLAuthorization):
    """
    Authorisation class for Tastypie
    """
    def read_list(self, object_list, bundle):  # noqa # too complex
        authuser = bundle.request.user
        authenticated = authuser.is_authenticated
        is_facility_manager = authenticated and \
            len(facilities_managed_by(authuser)) > 0
        if isinstance(bundle.obj, (User, Uploader, UploaderSetting,
                                   UploaderRegistrationRequest)):
            if is_facility_manager:
                return object_list
            return []
        return super().read_list(object_list, bundle)

    def read_detail(self, object_list, bundle):  # noqa # too complex
        if bundle.request.user.is_authenticated and \
           bundle.request.user.is_superuser:
            return True
        authuser = bundle.request.user
        authenticated = authuser.is_authenticated
        is_facility_manager = authenticated and \
            len(facilities_managed_by(authuser)) > 0
        if isinstance(bundle.obj, (Uploader, UploaderRegistrationRequest)):
            return is_facility_manager
        if isinstance(bundle.obj, DataFileObject):
            return has_datafile_access(bundle.request, bundle.obj.datafile.id)
        return super().read_detail(object_list, bundle)

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
        return super().create_detail(object_list, bundle)

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
        return super().update_detail(object_list, bundle)
