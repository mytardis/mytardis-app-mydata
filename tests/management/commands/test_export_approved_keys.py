import sys
import textwrap
from io import StringIO

from django.test import TestCase
from django.core.management import call_command

from ....models.uploader import Uploader, UploaderRegistrationRequest


class ExportApprovedKeysTestCase(TestCase):

    def setUp(self):
        '''
        Create mock Uploader and UploaderRegistrationRequest records
        for testing
        '''

        self.uploader = Uploader.objects.create(name="Test Instrument PC", uuid="001")
        self.urr = UploaderRegistrationRequest.objects.create(
            uploader=self.uploader,
            approved=True,
            requester_public_key="ssh-rsa MOCK_PUBLIC_KEY MOCK_KEY_COMMENT"
        )
        self.uploader2 = Uploader.objects.create(name="Uploader2", uuid="002")
        self.urr2 = UploaderRegistrationRequest.objects.create(
            uploader=self.uploader2,
            approved=True,
            requester_public_key="ssh-rsa ANOTHER_MOCK_PUBLIC_KEY"
        )

    def test_without_any_approved_keys(self):
        '''
        ./manage.py export_approved_keys
        without any runtime exceptions
        '''
        self.assertEqual(
            UploaderRegistrationRequest.objects.filter(approved=True).count(), 2)
        mock_stdout = StringIO()
        args = []
        opts = dict(stdout=mock_stdout)
        call_command('export_approved_keys', *args, **opts)    
        self.assertEqual(mock_stdout.getvalue().strip(), textwrap.dedent("""
            ssh-rsa MOCK_PUBLIC_KEY MOCK_KEY_COMMENT
            ssh-rsa ANOTHER_MOCK_PUBLIC_KEY
            """).strip())

    def tearDown(self):
        '''
        Clean up
        '''
        self.uploader.delete()
