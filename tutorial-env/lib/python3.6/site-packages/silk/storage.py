from django.core.files.storage import FileSystemStorage

from silk.config import SilkyConfig


class ProfilerResultStorage(FileSystemStorage):
    # the default storage will only store under MEDIA_ROOT, so we must define our own.
    def __init__(self):
        super(ProfilerResultStorage, self).__init__(
            location=SilkyConfig().SILKY_PYTHON_PROFILER_RESULT_PATH,
            base_url=''
        )
        self.base_url = None
