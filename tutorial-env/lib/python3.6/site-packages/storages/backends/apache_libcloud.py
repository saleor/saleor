# Django storage using libcloud providers
# Aymeric Barantal (mric at chamal.fr) 2011
#
import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from django.utils.six import BytesIO, string_types
from django.utils.six.moves.urllib.parse import urljoin

try:
    from libcloud.storage.providers import get_driver
    from libcloud.storage.types import ObjectDoesNotExistError, Provider
except ImportError:
    raise ImproperlyConfigured("Could not load libcloud")


@deconstructible
class LibCloudStorage(Storage):
    """Django storage derived class using apache libcloud to operate
    on supported providers"""
    def __init__(self, provider_name=None, option=None):
        if provider_name is None:
            provider_name = getattr(settings, 'DEFAULT_LIBCLOUD_PROVIDER', 'default')

        self.provider = settings.LIBCLOUD_PROVIDERS.get(provider_name)
        if not self.provider:
            raise ImproperlyConfigured(
                'LIBCLOUD_PROVIDERS %s not defined or invalid' % provider_name)
        extra_kwargs = {}
        if 'region' in self.provider:
            extra_kwargs['region'] = self.provider['region']
        # Used by the GoogleStorageDriver
        if 'project' in self.provider:
            extra_kwargs['project'] = self.provider['project']
        try:
            provider_type = self.provider['type']
            if isinstance(provider_type, string_types):
                module_path, tag = provider_type.rsplit('.', 1)
                if module_path != 'libcloud.storage.types.Provider':
                    raise ValueError("Invalid module path")
                provider_type = getattr(Provider, tag)

            Driver = get_driver(provider_type)
            self.driver = Driver(
                self.provider['user'],
                self.provider['key'],
                **extra_kwargs
            )
        except Exception as e:
            raise ImproperlyConfigured(
                "Unable to create libcloud driver type %s: %s" %
                (self.provider.get('type'), e))
        self.bucket = self.provider['bucket']   # Limit to one container

    def _get_bucket(self):
        """Helper to get bucket object (libcloud container)"""
        return self.driver.get_container(self.bucket)

    def _clean_name(self, name):
        """Clean name (windows directories)"""
        return os.path.normpath(name).replace('\\', '/')

    def _get_object(self, name):
        """Get object by its name. Return None if object not found"""
        clean_name = self._clean_name(name)
        try:
            return self.driver.get_object(self.bucket, clean_name)
        except ObjectDoesNotExistError:
            return None

    def delete(self, name):
        """Delete object on remote"""
        obj = self._get_object(name)
        if obj:
            return self.driver.delete_object(obj)
        else:
            raise Exception('Object to delete does not exists')

    def exists(self, name):
        obj = self._get_object(name)
        return bool(obj)

    def listdir(self, path='/'):
        """Lists the contents of the specified path,
        returning a 2-tuple of lists; the first item being
        directories, the second item being files.
        """
        container = self._get_bucket()
        objects = self.driver.list_container_objects(container)
        path = self._clean_name(path)
        if not path.endswith('/'):
            path = "%s/" % path
        files = []
        dirs = []
        # TOFIX: better algorithm to filter correctly
        # (and not depend on google-storage empty folder naming)
        for o in objects:
            if path == '/':
                if o.name.count('/') == 0:
                    files.append(o.name)
                elif o.name.count('/') == 1:
                    dir_name = o.name[:o.name.index('/')]
                    if dir_name not in dirs:
                        dirs.append(dir_name)
            elif o.name.startswith(path):
                if o.name.count('/') <= path.count('/'):
                    # TOFIX : special case for google storage with empty dir
                    if o.name.endswith('_$folder$'):
                        name = o.name[:-9]
                        name = name[len(path):]
                        dirs.append(name)
                    else:
                        name = o.name[len(path):]
                        files.append(name)
        return (dirs, files)

    def size(self, name):
        obj = self._get_object(name)
        return obj.size if obj else -1

    def url(self, name):
        provider_type = self.provider['type'].lower()
        obj = self._get_object(name)
        if not obj:
            return None
        try:
            url = self.driver.get_object_cdn_url(obj)
        except NotImplementedError as e:
            object_path = '%s/%s' % (self.bucket, obj.name)
            if 's3' in provider_type:
                base_url = 'https://%s' % self.driver.connection.host
                url = urljoin(base_url, object_path)
            elif 'google' in provider_type:
                url = urljoin('https://storage.googleapis.com', object_path)
            elif 'azure' in provider_type:
                base_url = ('https://%s.blob.core.windows.net' %
                            self.provider['user'])
                url = urljoin(base_url, object_path)
            else:
                raise e
        return url

    def _open(self, name, mode='rb'):
        remote_file = LibCloudFile(name, self, mode=mode)
        return remote_file

    def _read(self, name):
        obj = self._get_object(name)
        # TOFIX : we should be able to read chunk by chunk
        return next(self.driver.download_object_as_stream(obj, obj.size))

    def _save(self, name, file):
        self.driver.upload_object_via_stream(iter(file), self._get_bucket(), name)
        return name


class LibCloudFile(File):
    """File inherited class for libcloud storage objects read and write"""
    def __init__(self, name, storage, mode):
        self.name = name
        self._storage = storage
        self._mode = mode
        self._is_dirty = False
        self._file = None

    def _get_file(self):
        if self._file is None:
            data = self._storage._read(self.name)
            self._file = BytesIO(data)
        return self._file

    def _set_file(self, value):
        self._file = value

    file = property(_get_file, _set_file)

    @property
    def size(self):
        if not hasattr(self, '_size'):
            self._size = self._storage.size(self.name)
        return self._size

    def read(self, num_bytes=None):
        return self.file.read(num_bytes)

    def write(self, content):
        if 'w' not in self._mode:
            raise AttributeError("File was opened for read-only access.")
        self.file = BytesIO(content)
        self._is_dirty = True

    def close(self):
        if self._is_dirty:
            self._storage._save(self.name, self.file)
        self.file.close()
