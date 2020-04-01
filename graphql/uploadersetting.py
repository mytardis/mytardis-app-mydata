import graphene
from graphene import relay
from django_filters import FilterSet, OrderingFilter

from graphene_django_plus.types import ModelType
from graphene_django_plus.mutations import (
    ModelCreateMutation,
    ModelUpdateMutation
)

from .utils import ExtendedConnection

from ..models.uploader import UploaderSetting as UploaderSettingModel


class UploaderSettingType(ModelType):
    class Meta:
        model = UploaderSettingModel
        permissions = ['mydata.view_uploadersetting']
        interfaces = [relay.Node]
        connection_class = ExtendedConnection

    pk = graphene.Int(source='pk')


class UploaderSettingTypeFilter(FilterSet):
    class Meta:
        model = UploaderSettingModel
        fields = {
            'uploader_id': ['exact']
        }

    order_by = OrderingFilter(
        # must contain strings or (field name, param name) pairs
        fields=(
            ('key', 'key')
        )
    )


class CreateUploaderSetting(ModelCreateMutation):
    class Meta:
        model = UploaderSettingModel
        permissions = ['mydata.add_uploadersetting']


class UpdateUploaderSetting(ModelUpdateMutation):
    class Meta:
        model = UploaderSettingModel
        permissions = ['mydata.change_uploadersetting']
