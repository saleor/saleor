from __future__ import unicode_literals

import mimetypes
import re
from datetime import datetime, timedelta
from tempfile import SpooledTemporaryFile

from azure.common import AzureMissingResourceHttpError
from azure.storage.blob import BlobPermissions, ContentSettings
from azure.storage.common import CloudStorageAccount
from django.core.exceptions import SuspiciousOperation
from django.core.files.base import File
from django.core.files.storage import Storage
from django.utils import timezone
from django.utils.deconstruct import deconstructible
from django.utils.encoding import force_bytes, force_text

from storages.utils import (
    clean_name, get_available_overwrite_name, safe_join, setting,
)


@deconstructible
class AzureStorageFile(File):

    def __init__(self, name, mode, storage):
        self.name = name
        self._mode = mode
        self._storage = storage
        self._is_dirty = False
        self._file = None
        self._path = storage._get_valid_path(name)

    def _get_file(self):
        if self._file is not None:
            return self._file

        file = SpooledTemporaryFile(
            max_size=self._storage.max_memory_size,
            suffix=".AzureStorageFile",
            dir=setting("FILE_UPLOAD_TEMP_DIR", None))

        if 'r' in self._mode or 'a' in self._mode:
            # I set max connection to 1 since spooledtempfile is
            # not seekable which is required if we use max_connections > 1
            self._storage.service.get_blob_to_stream(
                container_name=self._storage.azure_container,
                blob_name=self._path,
                stream=file,
                max_connections=1,
                timeout=10)
        if 'r' in self._mode:
            file.seek(0)

        self._file = file
        return self._file

    def _set_file(self, value):
        self._file = value

    file = property(_get_file, _set_file)

    def read(self, *args, **kwargs):
        if 'r' not in self._mode and 'a' not in self._mode:
            raise AttributeError("File was not opened in read mode.")
        return super(AzureStorageFile, self).read(*args, **kwargs)

    def write(self, content):
        if len(content) > 100*1024*1024:
            raise ValueError("Max chunk size is 100MB")
        if ('w' not in self._mode and
                '+' not in self._mode and
                'a' not in self._mode):
            raise AttributeError("File was not opened in write mode.")
        self._is_dirty = True
        return super(AzureStorageFile, self).write(force_bytes(content))

    def close(self):
        if self._file is None:
            return
        if self._is_dirty:
            self._file.seek(0)
            self._storage._save(self.name, self._file)
            self._is_dirty = False
        self._file.close()
        self._file = None


def _content_type(content):
    try:
        return content.file.content_type
    except AttributeError:
        pass
    try:
        return content.content_type
    except AttributeError:
        pass
    return None


def _get_valid_path(s):
    # A blob name:
    #   * must not end with dot or slash
    #   * can contain any character
    #   * must escape URL reserved characters
    # We allow a subset of this to avoid
    # illegal file names. We must ensure it is idempotent.
    s = force_text(s).strip().replace(' ', '_')
    s = re.sub(r'(?u)[^-\w./]', '', s)
    s = s.strip('./')
    if len(s) > _AZURE_NAME_MAX_LEN:
        raise ValueError(
            "File name max len is %d" % _AZURE_NAME_MAX_LEN)
    if not len(s):
        raise ValueError(
            "File name must contain one or more "
            "printable characters")
    if s.count('/') > 256:
        raise ValueError(
            "File name must not contain "
            "more than 256 slashes")
    return s


def _clean_name_dance(name):
    # `get_valid_path` may return `foo/../bar`
    name = name.replace('\\', '/')
    return clean_name(_get_valid_path(clean_name(name)))


# Max len according to azure's docs
_AZURE_NAME_MAX_LEN = 1024


@deconstructible
class AzureStorage(Storage):

    account_name = setting("AZURE_ACCOUNT_NAME")
    account_key = setting("AZURE_ACCOUNT_KEY")
    azure_container = setting("AZURE_CONTAINER")
    azure_ssl = setting("AZURE_SSL", True)
    upload_max_conn = setting("AZURE_UPLOAD_MAX_CONN", 2)
    timeout = setting('AZURE_CONNECTION_TIMEOUT_SECS', 20)
    max_memory_size = setting('AZURE_BLOB_MAX_MEMORY_SIZE', 2*1024*1024)
    expiration_secs = setting('AZURE_URL_EXPIRATION_SECS')
    overwrite_files = setting('AZURE_OVERWRITE_FILES', False)
    location = setting('AZURE_LOCATION', '')
    default_content_type = 'application/octet-stream'
    is_emulated = setting('AZURE_EMULATED_MODE', False)

    def __init__(self):
        self._service = None

    @property
    def service(self):
        # This won't open a connection or anything,
        # it's akin to a client
        if self._service is None:
            account = CloudStorageAccount(
                self.account_name,
                self.account_key,
                is_emulated=self.is_emulated)
            self._service = account.create_block_blob_service()
        return self._service

    @property
    def azure_protocol(self):
        if self.azure_ssl:
            return 'https'
        else:
            return 'http'

    def _path(self, name):
        name = _clean_name_dance(name)
        try:
            return safe_join(self.location, name)
        except ValueError:
            raise SuspiciousOperation("Attempted access to '%s' denied." % name)

    def _get_valid_path(self, name):
        # Must be idempotent
        return _get_valid_path(self._path(name))

    def _open(self, name, mode="rb"):
        return AzureStorageFile(name, mode, self)

    def get_valid_name(self, name):
        return _clean_name_dance(name)

    def get_available_name(self, name, max_length=_AZURE_NAME_MAX_LEN):
        """
        Returns a filename that's free on the target storage system, and
        available for new content to be written to.
        """
        name = self.get_valid_name(name)
        if self.overwrite_files:
            return get_available_overwrite_name(name, max_length)
        return super(AzureStorage, self).get_available_name(name, max_length)

    def exists(self, name):
        return self.service.exists(
            self.azure_container,
            self._get_valid_path(name),
            timeout=self.timeout)

    def delete(self, name):
        try:
            self.service.delete_blob(
                container_name=self.azure_container,
                blob_name=self._get_valid_path(name),
                timeout=self.timeout)
        except AzureMissingResourceHttpError:
            pass

    def size(self, name):
        properties = self.service.get_blob_properties(
            self.azure_container,
            self._get_valid_path(name),
            timeout=self.timeout).properties
        return properties.content_length

    def _save(self, name, content):
        name_only = self.get_valid_name(name)
        name = self._get_valid_path(name)
        guessed_type, content_encoding = mimetypes.guess_type(name)
        content_type = (
            _content_type(content) or
            guessed_type or
            self.default_content_type)

        # Unwrap django file (wrapped by parent's save call)
        if isinstance(content, File):
            content = content.file

        content.seek(0)
        self.service.create_blob_from_stream(
            container_name=self.azure_container,
            blob_name=name,
            stream=content,
            content_settings=ContentSettings(
                content_type=content_type,
                content_encoding=content_encoding),
            max_connections=self.upload_max_conn,
            timeout=self.timeout)
        return name_only

    def _expire_at(self, expire):
        # azure expects time in UTC
        return datetime.utcnow() + timedelta(seconds=expire)

    def url(self, name, expire=None):
        name = self._get_valid_path(name)

        if expire is None:
            expire = self.expiration_secs

        make_blob_url_kwargs = {}
        if expire:
            sas_token = self.service.generate_blob_shared_access_signature(
                self.azure_container, name, BlobPermissions.READ, expiry=self._expire_at(expire))
            make_blob_url_kwargs['sas_token'] = sas_token

        if self.azure_protocol:
            make_blob_url_kwargs['protocol'] = self.azure_protocol
        return self.service.make_blob_url(
            container_name=self.azure_container,
            blob_name=name,
            **make_blob_url_kwargs)

    def get_modified_time(self, name):
        """
        Returns an (aware) datetime object containing the last modified time if
        USE_TZ is True, otherwise returns a naive datetime in the local timezone.
        """
        properties = self.service.get_blob_properties(
            self.azure_container,
            self._get_valid_path(name),
            timeout=self.timeout).properties
        if not setting('USE_TZ', False):
            return timezone.make_naive(properties.last_modified)

        tz = timezone.get_current_timezone()
        if timezone.is_naive(properties.last_modified):
            return timezone.make_aware(properties.last_modified, tz)

        # `last_modified` is in UTC time_zone, we
        # must convert it to settings time_zone
        return properties.last_modified.astimezone(tz)

    def modified_time(self, name):
        """Returns a naive datetime object containing the last modified time."""
        mtime = self.get_modified_time(name)
        if timezone.is_naive(mtime):
            return mtime
        return timezone.make_naive(mtime)

    def list_all(self, path=''):
        """Return all files for a given path"""
        if path:
            path = self._get_valid_path(path)
        if path and not path.endswith('/'):
            path += '/'
        # XXX make generator, add start, end
        return [
            blob.name
            for blob in self.service.list_blobs(
                self.azure_container,
                prefix=path,
                timeout=self.timeout)]

    def listdir(self, path=''):
        """
        Return directories and files for a given path.
        Leave the path empty to list the root.
        Order of dirs and files is undefined.
        """
        files = []
        dirs = set()
        for name in self.list_all(path):
            n = name[len(path):]
            if '/' in n:
                dirs.add(n.split('/', 1)[0])
            else:
                files.append(n)
        return list(dirs), files

    def get_name_max_len(self):
        max_len = _AZURE_NAME_MAX_LEN - len(self._get_valid_path('foo')) - len('foo')
        if not self.overwrite_files:
            max_len -= len('_1234567')
        return max_len
