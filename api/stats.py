import logging

from django.conf.urls import url
from django.db.models import Sum, Max
from django.http import JsonResponse
from tastypie.utils import trailing_slash

import tardis.tardis_portal.api

from tardis.tardis_portal.models.dataset import Dataset
from tardis.tardis_portal.models.datafile import DataFile
from tardis.tardis_portal.models.datafile import DataFileObject
from tardis.tardis_portal.models.storage import StorageBox

from .auth import ACLAuthorization


logger = logging.getLogger(__name__)


class DatasetStatsAppResource(tardis.tardis_portal.api.MyTardisModelResource):

    class Meta(tardis.tardis_portal.api.MyTardisModelResource.Meta):
        resource_name = "dataset_stats"
        allowed_methods = ["get"]
        authorization = ACLAuthorization()
        queryset = Dataset.objects.all()
        filtering = {
            "dataset_id": ["exact"]
        }
        always_return_data = True

    def prepend_urls(self):
        return [
            url(
                r"^(?P<resource_name>%s)/(?P<dataset_id>\d+)%s$" % (
                    self._meta.resource_name,
                    trailing_slash()
                ),
                self.wrap_view("get_dataset_stats"),
                name="api_mydata_get_dataset_stats"
            )
        ]

    def get_dataset_stats(self, request, **kwargs):
        self.method_check(request, allowed=["get"])
        self.is_authenticated(request)

        data = {
            "success": False
        }

        try:
            dataset = Dataset.objects.get(id=kwargs["dataset_id"])
            total_size = DataFile.objects.filter(
                dataset=dataset
            ).aggregate(Sum("size"))["size__sum"]
            files_total = DataFile.objects.filter(dataset=dataset).count()
            files_verified = DataFile.objects.filter(dataset=dataset).filter(
                file_objects__verified=True
            ).count()
            storage_boxes = DataFileObject.objects.filter(
                datafile__dataset=dataset
            ).values("storage_box_id").distinct()
            storage_boxes = [sb["storage_box_id"] for sb in storage_boxes]
            storage_boxes = ",".join([
                sb.name for sb in
                StorageBox.objects.filter(id__in=storage_boxes)
            ])
            last_verified = DataFileObject.objects.filter(
                datafile__dataset=dataset
            ).aggregate(Max("last_verified_time"))["last_verified_time__max"]
            data = {
                "success": True,
                "files": {
                    "total": files_total,
                    "verified": files_verified
                },
                "verified": files_total > 0 and files_verified == files_total,
                "size": total_size,
                "location": storage_boxes,
                "last_verified": last_verified
            }
        except Exception as err:
            logger.error(str(err))

        return JsonResponse(data, status=200)
