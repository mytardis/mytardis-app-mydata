from django.contrib import admin
from django import forms
from django.forms import TextInput

from .models import Uploader
from .models import UploaderRegistrationRequest
from .models import UploaderSetting


class UploaderSettingInlineForm(forms.ModelForm):

    class Meta:
        fields = '__all__'
        model = UploaderSetting
        widgets = {
            'key': TextInput(attrs={'size': 40}),
            'value': TextInput(attrs={'size': 80})
        }


class UploaderSettingInline(admin.TabularInline):
    model = UploaderSetting
    extra = 0
    form = UploaderSettingInlineForm


class UploaderForm(forms.ModelForm):

    class Meta:
        fields = '__all__'
        model = Uploader


class UploaderAdmin(admin.ModelAdmin):
    inlines = [UploaderSettingInline]
    form = UploaderForm


admin.site.register(Uploader, UploaderAdmin)
admin.site.register(UploaderRegistrationRequest)
admin.site.register(UploaderSetting)
