import os
import uuid

from django.conf import settings
from django.core.files.storage import FileSystemStorage

from tardis.tardis_portal.storage import MyTardisLocalFileSystemStorage


class MyDataStagingFileSystemStorage(MyTardisLocalFileSystemStorage):
    '''
    Simply changes the FileSystemStorage default store location to the MyTardis
    file store location. Makes it easier to migrate 2.5 installations.
    '''

    def __init__(self, location=None, base_url=None):
        if location is None:
            location = getattr(settings, "DEFAULT_STORAGE_BASE_DIR",
                               '/var/lib/mytardis/store')
        super(MyDataStagingFileSystemStorage, self).__init__(
            location, base_url)

    def build_save_location(self, dfo):
        prefix = "%d-" % dfo.datafile.dataset.id

        def get_candidate_path():
            return os.path.join(self.location, 'mydata',
                                prefix + str(uuid.uuid4()))
        path = (p for p in iter(get_candidate_path, '')
                if not os.path.exists(p)).next()
        oldmask = os.umask(0o007)
        os.makedirs(path)
        os.umask(oldmask)
        os.chmod(path, 0o2770)
        return os.path.join(path, dfo.datafile.filename)
