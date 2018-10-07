from django.core.management.base import BaseCommand
from ...models import UploaderRegistrationRequest


class Command(BaseCommand):
    help = ('Exports the public keys for approved '
            'uploader registration requests')

    def handle(self, *args, **options):
        urrs = UploaderRegistrationRequest.objects.filter(approved=True)
        for urr in urrs:
            public_key = urr.requester_public_key.strip()
            public_key = public_key.replace('MyData Key', urr.uploader.name)
            self.stdout.write("%s\n" % public_key)
