from django.contrib import admin
import models

admin.site.register(Uploader)
admin.site.register(models.UploaderStagingHost)
admin.site.register(models.UploaderRegistrationRequest)
