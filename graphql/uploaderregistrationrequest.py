import graphene
from graphene import relay
from django_filters import FilterSet, OrderingFilter

from graphene_django_plus.types import ModelType
from graphene_django_plus.mutations import (
    ModelCreateMutation,
    ModelUpdateMutation
)

from .utils import ExtendedConnection

from ..models.uploader import \
    UploaderRegistrationRequest as UploaderRegistrationRequestModel


class UploaderRegistrationRequestType(ModelType):
    class Meta:
        model = UploaderRegistrationRequestModel
        permissions = ['mydata.view_uploaderregistrationrequest']
        interfaces = [relay.Node]
        connection_class = ExtendedConnection

    pk = graphene.Int(source='pk')


class UploaderRegistrationRequestTypeFilter(FilterSet):
    class Meta:
        model = UploaderRegistrationRequestModel
        fields = {
            'uploader_id': ['exact']
        }

    order_by = OrderingFilter(
        # must contain strings or (field name, param name) pairs
        fields=()
    )


class CreateUploaderRegistrationRequest(ModelCreateMutation):
    class Meta:
        model = UploaderRegistrationRequestModel
        permissions = ['mydata.add_uploaderregistrationrequest']


class UpdateUploaderRegistrationRequest(ModelUpdateMutation):
    class Meta:
        model = UploaderRegistrationRequestModel
        permissions = ['mydata.change_uploaderregistrationrequest']
