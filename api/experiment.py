from django.contrib.auth.models import User

import tardis.tardis_portal.api
from tardis.tardis_portal.models.parameters import Schema
from tardis.tardis_portal.models.experiment import Experiment
from tardis.tardis_portal.models.parameters import ExperimentParameter
from tardis.tardis_portal.models.parameters import ExperimentParameterSet


class ExperimentAppResource(tardis.tardis_portal.api.ExperimentResource):
    '''Extends MyTardis's API for Experiments
    to allow querying of metadata relevant to MyData
    '''

    class Meta(tardis.tardis_portal.api.ExperimentResource.Meta):
        # This will be mapped to mydata_experiment by MyTardis's urls.py:
        resource_name = 'experiment'

    def obj_get_list(self, bundle, **kwargs):
        '''
        Used by MyData to determine whether an appropriate default experiment
        exists to add a dataset to.
        '''

        '''
        For backwards compatibility with older MyData versions, let's
        try to guess the folder structure if it wasn't provided:
        '''
        folder_structure = None
        if hasattr(bundle.request, 'GET') and \
                'folder_structure' not in bundle.request.GET:
            if 'group_folder_name' in bundle.request.GET and \
                    bundle.request.GET['group_folder_name'].strip() != '':
                folder_structure = 'User Group / ...'
            elif 'user_folder_name' in bundle.request.GET:
                if '@' in bundle.request.GET['user_folder_name']:
                    folder_structure = 'Email / ...'
                else:
                    folder_structure = 'Username / ...'
            else:
                folder_structure = 'Username / ...'

        class UnknownUser(object):
            def __init__(self, username='UNKNOWN', email='UNKNOWN'):
                self.username = username
                self.email = email

        '''
        Responds to title/folder_structure/[user_folder_name|group_folder_name]
        query for MyData.  This can be used by MyData to retrieve an experiment
        which can be used to collect datasets from multiple MyData instances.
        '''
        if hasattr(bundle.request, 'GET') and \
                'title' in bundle.request.GET and \
                ('user_folder_name' in bundle.request.GET or
                 'group_folder_name' in bundle.request.GET):

            title = bundle.request.GET['title']
            if 'folder_structure' in bundle.request.GET:
                folder_structure = bundle.request.GET['folder_structure']
            need_to_match_user = (folder_structure.startswith('Username /') or
                                  folder_structure.startswith('Email /'))
            need_to_match_group = folder_structure.startswith('User Group /')

            if need_to_match_user:
                user_folder_name = bundle.request.GET['user_folder_name']
                if folder_structure.startswith('Username /'):
                    try:
                        user_to_match = User.objects.get(
                            username=user_folder_name, is_active=True)
                    except User.DoesNotExist:
                        user_to_match = UnknownUser(username=user_folder_name)
                elif folder_structure.startswith('Email /'):
                    try:
                        user_to_match = User.objects.get(
                            email__iexact=user_folder_name, is_active=True)
                    except User.DoesNotExist:
                        user_to_match = UnknownUser(email=user_folder_name)

            if need_to_match_group:
                group_folder_name = bundle.request.GET['group_folder_name']

            mydata_default_exp_schema = Schema.objects.get(
                namespace='http://mytardis.org'
                '/schemas/mydata/defaultexperiment')

            exp_psets = ExperimentParameterSet.objects\
                .filter(experiment__title=title,
                        schema=mydata_default_exp_schema)
            for exp_pset in exp_psets:
                exp_params = ExperimentParameter.objects\
                    .filter(parameterset=exp_pset)
                matched_user = False
                matched_group = False
                for exp_param in exp_params:
                    if need_to_match_user and \
                            exp_param.name.name == 'user_folder_name' and \
                            (exp_param.string_value.lower() ==
                             user_to_match.username.lower() or
                             exp_param.string_value.lower() ==
                             user_to_match.email.lower()):
                        matched_user = True
                    if need_to_match_group and \
                            exp_param.name.name == 'group_folder_name' and \
                            exp_param.string_value == group_folder_name:
                        matched_group = True
                is_mu = need_to_match_user and matched_user
                is_mg = need_to_match_group and matched_group
                is_nah = not need_to_match_user and not need_to_match_group
                if is_mu or is_mg or is_nah:
                    experiment_id = exp_pset.experiment.id
                    exp_list = Experiment.objects.filter(pk=experiment_id)
                    if exp_list[0] in Experiment.safe.all(bundle.request.user):
                        return exp_list

            return []

        '''
        Responds to
        uploader/folder_structure/[user_folder_name|group_folder_name]
        query for MyData.  Each MyData instance generates a UUID the first time
        it runs on each upload PC. The UUID together with the user folder name
        (or group folder name) can be used to uniquely identify one particular
        user (or group) who has saved data on an instrument PC running a MyData
        instance identified by the UUID.
        '''
        if hasattr(bundle.request, 'GET') and \
                'uploader' in bundle.request.GET and \
                ('user_folder_name' in bundle.request.GET or
                 'group_folder_name' in bundle.request.GET):

            uploader_uuid = bundle.request.GET['uploader']
            if 'folder_structure' in bundle.request.GET:
                folder_structure = bundle.request.GET['folder_structure']
            need_to_match_user = (folder_structure.startswith('Username /') or
                                  folder_structure.startswith('Email /'))
            need_to_match_group = folder_structure.startswith('User Group /')

            if need_to_match_user:
                user_folder_name = bundle.request.GET['user_folder_name']
                if folder_structure.startswith('Username /'):
                    try:
                        user_to_match = User.objects.get(
                            username=user_folder_name, is_active=True)
                    except User.DoesNotExist:
                        user_to_match = UnknownUser(username=user_folder_name)
                elif folder_structure.startswith('Email /'):
                    try:
                        user_to_match = User.objects.get(
                            email__iexact=user_folder_name, is_active=True)
                    except User.DoesNotExist:
                        user_to_match = UnknownUser(email=user_folder_name)

            if need_to_match_group:
                group_folder_name = bundle.request.GET['group_folder_name']

            mydata_default_exp_schema = Schema.objects.get(
                namespace='http://mytardis.org'
                '/schemas/mydata/defaultexperiment')

            exp_psets = ExperimentParameterSet.objects\
                .filter(schema=mydata_default_exp_schema)
            for exp_pset in exp_psets:
                exp_params = ExperimentParameter.objects\
                    .filter(parameterset=exp_pset)
                matched_uploader_uuid = False
                matched_user = False
                matched_group = False
                for exp_param in exp_params:
                    if exp_param.name.name == 'uploader' and \
                            exp_param.string_value == uploader_uuid:
                        matched_uploader_uuid = True
                    if need_to_match_user and \
                            exp_param.name.name == 'user_folder_name' and \
                            (exp_param.string_value.lower() ==
                             user_to_match.username.lower() or
                             exp_param.string_value.lower() ==
                             user_to_match.email.lower()):
                        matched_user = True
                    if exp_param.name.name == 'group_folder_name' and \
                            exp_param.string_value == group_folder_name:
                        matched_group = True
                if matched_uploader_uuid and \
                        (need_to_match_user and matched_user or
                         need_to_match_group and matched_group):
                    experiment_id = exp_pset.experiment.id
                    exp_list = Experiment.objects.filter(pk=experiment_id)
                    if exp_list[0] in Experiment.safe.all(bundle.request.user):
                        return exp_list

            return []

        return super().obj_get_list(bundle, **kwargs)
