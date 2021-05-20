import logging

from django.conf.urls import url
from django.http import JsonResponse
from django.contrib.auth.models import User
from tastypie.utils import trailing_slash

import tardis.tardis_portal.api

from tardis.apps.openid_migration.models import OpenidUserMigration

from .auth import ACLAuthorization


logger = logging.getLogger(__name__)


class UserAppResource(tardis.tardis_portal.api.MyTardisModelResource):

    class Meta(tardis.tardis_portal.api.MyTardisModelResource.Meta):
        resource_name = "user"
        allowed_methods = ["get"]
        authorization = ACLAuthorization()
        filtering = {
            "username": "exact"
        }
        always_return_data = True

    def prepend_urls(self):
        return [
            url(
                r"^(?P<resource_name>%s)%s$" % (
                    self._meta.resource_name,
                    trailing_slash()
                ),
                self.wrap_view("get_user"),
                name="api_mydata_get_user"
            )
        ]

    def get_user(self, request, **kwargs):
        self.method_check(request, allowed=["get"])
        self.is_authenticated(request)

        data = {
            "success": False
        }

        username = request.GET.get("username", "")
        if len(username) != 0:
            users = User.objects.filter(username=username + "_ldap",
                                        is_active=False)
            if len(users) == 1:
                migrations = OpenidUserMigration.objects.filter(
                    old_user=users[0])
                if len(migrations) == 1:
                    data["success"] = True
                    data["id"] = migrations[0].new_user.id
                    data["username"] = migrations[0].new_user.username

        return JsonResponse(data, status=200)
