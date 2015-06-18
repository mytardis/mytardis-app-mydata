from django.db import models
from django.contrib.contenttypes.models import ContentType

from tardis.tardis_portal.models.storage import StorageBox

class Uploader(models.Model):
    '''
    Represents a PC whose user(s) have expressed interest in
    uploading to this MyTardis instance - either a PC attached to
    a data-collection instrument, or an end-user's machine.  The
    upload method (once approved) could be RSYNC over SSH to a
    staging area.  See also the UploaderRegistrationRequest model.

    To be more accurate, an uploader represents a MyTardis-upload
    program instance which is installed on a PC.  Previously, a
    single PC running MyData could generate multiple uploader
    records, one for each network interface, because the PC's
    MAC address was used as the unique identifier.  Now, MyData
    generates a UUID the first time it runs, and if the user
    switches network interfaces, then the same uploader record
    will be used (and updated if necessary), instead of creating
    a second uploader record for the second network interface.

    Some field values within each uploader record (e.g. IP address)
    may change after this uploader has been approved.  The MyTardis
    admin who does the approving needs to determine whether the
    Uploader's IP range needs to be added to a hosts.allow file or
    to a firewall rule, or whether an SSH key-pair is sufficient.
    '''

    uuid = models.CharField(max_length=36, unique=True, blank=False)

    name = models.CharField(max_length=64)
    contact_name = models.CharField(max_length=64)
    contact_email = models.CharField(max_length=64)

    '''
    The uploader-instrument many-to-many relationship below deserves
    some explanation.  In the first instance, the Uploader model is
    designed to represent a MyTardis-upload program running on an
    instrument computer.  In that case, each uploader record created
    from an instrument computer should be associated with exactly one
    instrument record.  However it is envisaged that MyTardis-upload
    programs could also be run from PCs which manage data from
    multiple instruments.  Conversely, one instrument could be
    associated with multiple uploaders such as multiple network
    interfaces (Ethernet and WiFi) on the same instrument PC or a
    cluster of upload PCs sharing the task of uploading data from a
    single instrument.
    '''
    instruments = \
        models.ManyToManyField("tardis_portal.Instrument", 
                               related_name="uploaders",
                               blank=True, null=True)

    user_agent_name = models.CharField(max_length=64, null=True)
    user_agent_version = models.CharField(max_length=32, null=True)
    user_agent_install_location = models.CharField(max_length=256, null=True)

    os_platform = models.CharField(max_length=64, null=True)
    os_system = models.CharField(max_length=64, null=True)
    os_release = models.CharField(max_length=32, null=True)
    os_version = models.CharField(max_length=128, null=True)
    os_username = models.CharField(max_length=64, null=True)

    machine = models.CharField(max_length=64, null=True)
    architecture = models.CharField(max_length=64, null=True)
    processor = models.CharField(max_length=64, null=True)
    memory = models.CharField(max_length=32, null=True)
    cpus = models.IntegerField(null=True)

    disk_usage = models.TextField(null=True)
    data_path = models.CharField(max_length=256, null=True)
    default_user = models.CharField(max_length=64, null=True)

    interface = models.CharField(max_length=64, default="", blank=False)
    mac_address = models.CharField(max_length=64, blank=False)
    ipv4_address = models.CharField(max_length=16, null=True)
    ipv6_address = models.CharField(max_length=64, null=True)
    subnet_mask = models.CharField(max_length=16, null=True)

    hostname = models.CharField(max_length=64, null=True)

    # The wan_ip_address is populated in TastyPie by looking in request.META
    # It could be IPv4 or IPv6
    wan_ip_address = models.CharField(max_length=64, null=True)

    created_time = models.DateTimeField(null=True)
    updated_time = models.DateTimeField(null=True)

    class Meta:
        app_label = 'mydata'
        verbose_name_plural = 'Uploaders'

    def __unicode__(self):
        return self.name + " | " + self.uuid

    def get_ct(self):
        return ContentType.objects.get_for_model(self)


class UploaderRegistrationRequest(models.Model):
    '''
    Represents a request to register a new instrument PC with this
    MyTardis instance and allow it to act as an "uploader".
    The upload method could be RSYNC over SSH to a staging area for example.

    We could constrain these requests to be unique per uploader record,
    but we allow an uploader to make requests using multiple key pairs,
    which could represent different user accounts on the uploader PC,
    each having its own ~/.ssh/MyData private key.
    '''

    uploader = models.ForeignKey(Uploader)

    requester_name = models.CharField(max_length=64)
    requester_email = models.CharField(max_length=64)
    requester_public_key = models.TextField()
    requester_key_fingerprint = models.CharField(max_length=64)
    request_time = models.DateTimeField(null=True, blank=True)

    approved = models.BooleanField(default=False)
    approved_storage_box = models.ForeignKey(StorageBox,
                                              null=True, blank=True,
                                              default=None)
    approver_comments = models.TextField(null=True, blank=True, default=None)
    approval_expiry = models.DateField(null=True, blank=True, default=None)
    approval_time = models.DateTimeField(null=True, blank=True, default=None)

    class Meta:
        app_label = 'mydata'
        verbose_name_plural = 'UploaderRegistrationRequests'
        unique_together = ['uploader', 'requester_key_fingerprint']

    def __unicode__(self):
        return self.uploader.name + " | " + \
            self.uploader.interface + " | " + \
            self.requester_key_fingerprint + " | " + \
            self.requester_name + " | " + \
            str(self.request_time) + " | " + \
            ("Approved" if self.approved else "Not approved")
