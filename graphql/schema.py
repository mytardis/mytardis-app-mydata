import graphene
from graphene_django.filter import DjangoFilterConnectionField

from ..models.uploader import (
    Uploader as UploaderModel,
    UploaderRegistrationRequest as UploaderRegistrationRequestModel,
    UploaderSetting as UploaderSettingModel
)

from .uploader import (
    UploaderType, UploaderTypeFilter,
    CreateUploader, UpdateUploader
)
from .uploaderregistrationrequest import (
    CreateUploaderRegistrationRequest, UpdateUploaderRegistrationRequest
)
from .uploadersetting import (
    CreateUploaderSetting, UpdateUploaderSetting
)

class tardisQuery(graphene.ObjectType):

    uploaders = DjangoFilterConnectionField(
        UploaderType,
        filterset_class=UploaderTypeFilter
    )
    def resolve_uploaders(self, info, **kwargs):
        user = info.context.user
        if user.is_authenticated:
            if user.is_superuser:
                return UploaderModel.objects.all()
        return None


class tardisMutation(graphene.ObjectType):

    create_uploader = CreateUploader.Field()
    update_uploader = UpdateUploader.Field()

    create_uploaderregistrationrequest = CreateUploaderRegistrationRequest.Field()
    update_uploaderregistrationrequest = UpdateUploaderRegistrationRequest.Field()

    create_uploadersetting = CreateUploaderSetting.Field()
    update_uploadersetting = UpdateUploaderSetting.Field()
