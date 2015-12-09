from django.contrib import admin
from django import forms
from django.forms import TextInput

import models


class UploaderSettingInlineForm(forms.ModelForm):

    class Meta:
        fields = '__all__'
        model = models.UploaderSetting
        widgets = {
            'key': TextInput(attrs={'size': 40}),
            'value': TextInput(attrs={'size': 80})
        }


class UploaderSettingInline(admin.TabularInline):
    model = models.UploaderSetting
    extra = 0
    form = UploaderSettingInlineForm


class UploaderForm(forms.ModelForm):

    class Meta:
        fields = '__all__'
        model = models.Uploader


class UploaderAdmin(admin.ModelAdmin):
    inlines = [UploaderSettingInline]
    form = UploaderForm


admin.site.register(models.Uploader, UploaderAdmin)
admin.site.register(models.UploaderRegistrationRequest)
admin.site.register(models.UploaderSetting)
