import mimetypes
import os
import warnings
from datetime import datetime
from gzip import GzipFile
from tempfile import SpooledTemporaryFile

from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.core.files.base import File
from django.core.files.storage import Storage
from django.utils import timezone as tz
from django.utils.deconstruct import deconstructible
from django.utils.encoding import (
    filepath_to_uri, force_bytes, force_text, smart_str,
)
from django.utils.six import BytesIO

from storages.utils import (
    check_location, clean_name, get_available_overwrite_name, lookup_env,
    safe_join, setting,
)

try:
    from boto import __version__ as boto_version
    from boto.s3.connection import S3Connection, SubdomainCallingFormat, Location
    from boto.exception import S3ResponseError
    from boto.s3.key import Key as S3Key
    from boto.utils import parse_ts, ISO8601
except ImportError:
    raise ImproperlyConfigured("Could not load Boto's S3 bindings.\n"
                               "See https://github.com/boto/boto")


boto_version_info = tuple([int(i) for i in boto_version.split('-')[0].split('.')])

if boto_version_info[:2] < (2, 32):
    raise ImproperlyConfigured("The installed Boto library must be 2.32 or "
                               "higher.\nSee https://github.com/boto/boto")

warnings.warn(
    "The S3BotoStorage backend is deprecated in favor of the S3Boto3Storage backend "
    "and will be removed in django-storages 1.8. This backend is mostly in bugfix only "
    "mode and has been for quite a while (in much the same way as its underlying "
    "library 'boto'). For performance, security and new feature reasons it is _strongly_ "
    "recommended that you update to the S3Boto3Storage backend. Please see the migration docs "
    "https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#migrating-boto-to-boto3.",
    DeprecationWarning
)


@deconstructible
class S3BotoStorageFile(File):
    """
    The default file object used by the S3BotoStorage backend.

    This file implements file streaming using boto's multipart
    uploading functionality. The file can be opened in read or
    write mode.

    This class extends Django's File class. However, the contained
    data is only the data contained in the current buffer. So you
    should not access the contained file object directly. You should
    access the data via this class.

    Warning: This file *must* be closed using the close() method in
    order to properly write the file to S3. Be sure to close the file
    in your application.
    """
    # TODO: Read/Write (rw) mode may be a bit undefined at the moment. Needs testing.
    # TODO: When Django drops support for Python 2.5, rewrite to use the
    #       BufferedIO streams in the Python 2.6 io module.
    buffer_size = setting('AWS_S3_FILE_BUFFER_SIZE', 5242880)

    def __init__(self, name, mode, storage, buffer_size=None):
        self._storage = storage
        self.name = name[len(self._storage.location):].lstrip('/')
        self._mode = mode
        self.key = storage.bucket.get_key(self._storage._encode_name(name))
        if not self.key and 'w' in mode:
            self.key = storage.bucket.new_key(storage._encode_name(name))
        self._is_dirty = False
        self._file = None
        self._multipart = None
        # 5 MB is the minimum part size (if there is more than one part).
        # Amazon allows up to 10,000 parts.  The default supports uploads
        # up to roughly 50 GB.  Increase the part size to accommodate
        # for files larger than this.
        if buffer_size is not None:
            self.buffer_size = buffer_size
        self._write_counter = 0

        if not hasattr(django_settings, 'AWS_DEFAULT_ACL'):
            warnings.warn(
                "The default behavior of S3BotoStorage is insecure. By default files "
                "and new buckets are saved with an ACL of 'public-read' (globally "
                "publicly readable). To change to using the bucket's default ACL "
                "set AWS_DEFAULT_ACL = None, otherwise to silence this warning "
                "explicitly set AWS_DEFAULT_ACL."
            )

    @property
    def size(self):
        return self.key.size

    def _get_file(self):
        if self._file is None:
            self._file = SpooledTemporaryFile(
                max_size=self._storage.max_memory_size,
                suffix='.S3BotoStorageFile',
                dir=setting('FILE_UPLOAD_TEMP_DIR')
            )
            if 'r' in self._mode:
                self._is_dirty = False
                self.key.get_contents_to_file(self._file)
                self._file.seek(0)
            if self._storage.gzip and self.key.content_encoding == 'gzip':
                self._file = GzipFile(mode=self._mode, fileobj=self._file)
        return self._file

    def _set_file(self, value):
        self._file = value

    file = property(_get_file, _set_file)

    def read(self, *args, **kwargs):
        if 'r' not in self._mode:
            raise AttributeError('File was not opened in read mode.')
        return super(S3BotoStorageFile, self).read(*args, **kwargs)

    def write(self, content, *args, **kwargs):
        if 'w' not in self._mode:
            raise AttributeError('File was not opened in write mode.')
        self._is_dirty = True
        if self._multipart is None:
            provider = self.key.bucket.connection.provider
            upload_headers = {}
            if self._storage.default_acl:
                upload_headers[provider.acl_header] = self._storage.default_acl
            upload_headers.update({
                'Content-Type': mimetypes.guess_type(self.key.name)[0] or self._storage.key_class.DefaultContentType
            })
            upload_headers.update(self._storage.headers)
            self._multipart = self._storage.bucket.initiate_multipart_upload(
                self.key.name,
                headers=upload_headers,
                reduced_redundancy=self._storage.reduced_redundancy,
                encrypt_key=self._storage.encryption,
            )
        if self.buffer_size <= self._buffer_file_size:
            self._flush_write_buffer()
        return super(S3BotoStorageFile, self).write(force_bytes(content), *args, **kwargs)

    @property
    def _buffer_file_size(self):
        pos = self.file.tell()
        self.file.seek(0, os.SEEK_END)
        length = self.file.tell()
        self.file.seek(pos)
        return length

    def _flush_write_buffer(self):
        if self._buffer_file_size:
            self._write_counter += 1
            self.file.seek(0)
            headers = self._storage.headers.copy()
            self._multipart.upload_part_from_file(
                self.file, self._write_counter, headers=headers)
            self.file.seek(0)
            self.file.truncate()

    def close(self):
        if self._is_dirty:
            self._flush_write_buffer()
            self._multipart.complete_upload()
        else:
            if self._multipart is not None:
                self._multipart.cancel_upload()
        self.key.close()
        if self._file is not None:
            self._file.close()
            self._file = None


@deconstructible
class S3BotoStorage(Storage):
    """
    Amazon Simple Storage Service using Boto

    This storage backend supports opening files in read or write
    mode and supports streaming(buffering) data in chunks to S3
    when writing.
    """
    connection_class = S3Connection
    connection_response_error = S3ResponseError
    file_class = S3BotoStorageFile
    key_class = S3Key

    # used for looking up the access and secret key from env vars
    access_key_names = ['AWS_S3_ACCESS_KEY_ID', 'AWS_ACCESS_KEY_ID']
    secret_key_names = ['AWS_S3_SECRET_ACCESS_KEY', 'AWS_SECRET_ACCESS_KEY']
    security_token_names = ['AWS_SESSION_TOKEN', 'AWS_SECURITY_TOKEN']
    security_token = None

    access_key = setting('AWS_S3_ACCESS_KEY_ID', setting('AWS_ACCESS_KEY_ID'))
    secret_key = setting('AWS_S3_SECRET_ACCESS_KEY', setting('AWS_SECRET_ACCESS_KEY'))
    file_overwrite = setting('AWS_S3_FILE_OVERWRITE', True)
    headers = setting('AWS_HEADERS', {})
    bucket_name = setting('AWS_STORAGE_BUCKET_NAME')
    auto_create_bucket = setting('AWS_AUTO_CREATE_BUCKET', False)
    default_acl = setting('AWS_DEFAULT_ACL', 'public-read')
    bucket_acl = setting('AWS_BUCKET_ACL', default_acl)
    querystring_auth = setting('AWS_QUERYSTRING_AUTH', True)
    querystring_expire = setting('AWS_QUERYSTRING_EXPIRE', 3600)
    reduced_redundancy = setting('AWS_REDUCED_REDUNDANCY', False)
    location = setting('AWS_LOCATION', '')
    origin = setting('AWS_ORIGIN', Location.DEFAULT)
    encryption = setting('AWS_S3_ENCRYPTION', False)
    custom_domain = setting('AWS_S3_CUSTOM_DOMAIN')
    calling_format = setting('AWS_S3_CALLING_FORMAT', SubdomainCallingFormat())
    secure_urls = setting('AWS_S3_SECURE_URLS', True)
    file_name_charset = setting('AWS_S3_FILE_NAME_CHARSET', 'utf-8')
    gzip = setting('AWS_IS_GZIPPED', False)
    preload_metadata = setting('AWS_PRELOAD_METADATA', False)
    gzip_content_types = setting('GZIP_CONTENT_TYPES', (
        'text/css',
        'text/javascript',
        'application/javascript',
        'application/x-javascript',
        'image/svg+xml',
    ))
    url_protocol = setting('AWS_S3_URL_PROTOCOL', 'http:')
    host = setting('AWS_S3_HOST', S3Connection.DefaultHost)
    use_ssl = setting('AWS_S3_USE_SSL', True)
    port = setting('AWS_S3_PORT')
    proxy = setting('AWS_S3_PROXY_HOST')
    proxy_port = setting('AWS_S3_PROXY_PORT')
    max_memory_size = setting('AWS_S3_MAX_MEMORY_SIZE', 0)

    def __init__(self, acl=None, bucket=None, **settings):
        # check if some of the settings we've provided as class attributes
        # need to be overwritten with values passed in here
        for name, value in settings.items():
            if hasattr(self, name):
                setattr(self, name, value)

        # For backward-compatibility of old differing parameter names
        if acl is not None:
            self.default_acl = acl
        if bucket is not None:
            self.bucket_name = bucket

        check_location(self)

        # Backward-compatibility: given the anteriority of the SECURE_URL setting
        # we fall back to https if specified in order to avoid the construction
        # of unsecure urls.
        if self.secure_urls:
            self.url_protocol = 'https:'

        self._entries = {}
        self._bucket = None
        self._connection = None
        self._loaded_meta = False

        self.access_key, self.secret_key = self._get_access_keys()
        self.security_token = self._get_security_token()

    @property
    def connection(self):
        if self._connection is None:
            kwargs = self._get_connection_kwargs()

            self._connection = self.connection_class(
                self.access_key,
                self.secret_key,
                **kwargs
            )
        return self._connection

    def _get_connection_kwargs(self):
        return dict(
            security_token=self.security_token,
            is_secure=self.use_ssl,
            calling_format=self.calling_format,
            host=self.host,
            port=self.port,
            proxy=self.proxy,
            proxy_port=self.proxy_port
        )

    @property
    def bucket(self):
        """
        Get the current bucket. If there is no current bucket object
        create it.
        """
        if self._bucket is None:
            self._bucket = self._get_or_create_bucket(self.bucket_name)
        return self._bucket

    @property
    def entries(self):
        """
        Get the locally cached files for the bucket.
        """
        if self.preload_metadata and not self._loaded_meta:
            self._entries.update({
                self._decode_name(entry.key): entry
                for entry in self.bucket.list(prefix=self.location)
            })
            self._loaded_meta = True
        return self._entries

    def _get_access_keys(self):
        """
        Gets the access keys to use when accessing S3. If none is
        provided in the settings then get them from the environment
        variables.
        """
        access_key = self.access_key or lookup_env(S3BotoStorage.access_key_names)
        secret_key = self.secret_key or lookup_env(S3BotoStorage.secret_key_names)
        return access_key, secret_key

    def _get_security_token(self):
        """
        Gets the security token to use when accessing S3. Get it from
        the environment variables.
        """
        security_token = self.security_token or lookup_env(S3BotoStorage.security_token_names)
        return security_token

    def _get_or_create_bucket(self, name):
        """
        Retrieves a bucket if it exists, otherwise creates it.
        """
        try:
            return self.connection.get_bucket(name, validate=self.auto_create_bucket)
        except self.connection_response_error:
            if self.auto_create_bucket:
                bucket = self.connection.create_bucket(name, location=self.origin)
                if not hasattr(django_settings, 'AWS_BUCKET_ACL'):
                    warnings.warn(
                        "The default behavior of S3BotoStorage is insecure. By default new buckets "
                        "are saved with an ACL of 'public-read' (globally publicly readable). To change "
                        "to using Amazon's default of the bucket owner set AWS_DEFAULT_ACL = None, "
                        "otherwise to silence this warning explicitly set AWS_DEFAULT_ACL."
                    )
                if self.bucket_acl:
                    bucket.set_acl(self.bucket_acl)
                return bucket
            raise ImproperlyConfigured('Bucket %s does not exist. Buckets '
                                       'can be automatically created by '
                                       'setting AWS_AUTO_CREATE_BUCKET to '
                                       '``True``.' % name)

    def _clean_name(self, name):
        """
        Cleans the name so that Windows style paths work
        """
        return clean_name(name)

    def _normalize_name(self, name):
        """
        Normalizes the name so that paths like /path/to/ignored/../something.txt
        work. We check to make sure that the path pointed to is not outside
        the directory specified by the LOCATION setting.
        """
        try:
            return safe_join(self.location, name)
        except ValueError:
            raise SuspiciousOperation("Attempted access to '%s' denied." %
                                      name)

    def _encode_name(self, name):
        return smart_str(name, encoding=self.file_name_charset)

    def _decode_name(self, name):
        return force_text(name, encoding=self.file_name_charset)

    def _compress_content(self, content):
        """Gzip a given string content."""
        zbuf = BytesIO()
        #  The GZIP header has a modification time attribute (see http://www.zlib.org/rfc-gzip.html)
        #  This means each time a file is compressed it changes even if the other contents don't change
        #  For S3 this defeats detection of changes using MD5 sums on gzipped files
        #  Fixing the mtime at 0.0 at compression time avoids this problem
        zfile = GzipFile(mode='wb', fileobj=zbuf, mtime=0.0)
        try:
            zfile.write(force_bytes(content.read()))
        finally:
            zfile.close()
        zbuf.seek(0)
        content.file = zbuf
        content.seek(0)
        return content

    def _open(self, name, mode='rb'):
        name = self._normalize_name(self._clean_name(name))
        f = self.file_class(name, mode, self)
        if not f.key:
            raise IOError('File does not exist: %s' % name)
        return f

    def _save(self, name, content):
        cleaned_name = self._clean_name(name)
        name = self._normalize_name(cleaned_name)
        headers = self.headers.copy()
        _type, encoding = mimetypes.guess_type(name)
        content_type = getattr(content, 'content_type', None)
        content_type = content_type or _type or self.key_class.DefaultContentType

        # setting the content_type in the key object is not enough.
        headers.update({'Content-Type': content_type})

        if self.gzip and content_type in self.gzip_content_types:
            content = self._compress_content(content)
            headers.update({'Content-Encoding': 'gzip'})
        elif encoding:
            # If the content already has a particular encoding, set it
            headers.update({'Content-Encoding': encoding})

        content.name = cleaned_name
        encoded_name = self._encode_name(name)
        key = self.bucket.get_key(encoded_name)
        if not key:
            key = self.bucket.new_key(encoded_name)
        if self.preload_metadata:
            self._entries[encoded_name] = key
            key.last_modified = datetime.utcnow().strftime(ISO8601)

        key.set_metadata('Content-Type', content_type)
        self._save_content(key, content, headers=headers)
        return cleaned_name

    def _save_content(self, key, content, headers):
        # only pass backwards incompatible arguments if they vary from the default
        kwargs = {}
        if self.encryption:
            kwargs['encrypt_key'] = self.encryption
        key.set_contents_from_file(content, headers=headers,
                                   policy=self.default_acl,
                                   reduced_redundancy=self.reduced_redundancy,
                                   rewind=True, **kwargs)

    def _get_key(self, name):
        name = self._normalize_name(self._clean_name(name))
        if self.entries:
            return self.entries.get(name)
        return self.bucket.get_key(self._encode_name(name))

    def delete(self, name):
        name = self._normalize_name(self._clean_name(name))
        self.bucket.delete_key(self._encode_name(name))

    def exists(self, name):
        if not name:  # root element aka the bucket
            try:
                self.bucket
                return True
            except ImproperlyConfigured:
                return False

        return self._get_key(name) is not None

    def listdir(self, name):
        name = self._normalize_name(self._clean_name(name))
        # for the bucket.list and logic below name needs to end in /
        # But for the root path "" we leave it as an empty string
        if name and not name.endswith('/'):
            name += '/'

        dirlist = self.bucket.list(self._encode_name(name))
        files = []
        dirs = set()
        base_parts = name.split('/')[:-1]
        for item in dirlist:
            parts = item.name.split('/')
            parts = parts[len(base_parts):]
            if len(parts) == 1:
                # File
                files.append(parts[0])
            elif len(parts) > 1:
                # Directory
                dirs.add(parts[0])
        return list(dirs), files

    def size(self, name):
        return self._get_key(name).size

    def get_modified_time(self, name):
        dt = tz.make_aware(parse_ts(self._get_key(name).last_modified), tz.utc)
        return dt if setting('USE_TZ') else tz.make_naive(dt)

    def modified_time(self, name):
        dt = tz.make_aware(parse_ts(self._get_key(name).last_modified), tz.utc)
        return tz.make_naive(dt)

    def url(self, name, headers=None, response_headers=None, expire=None):
        # Preserve the trailing slash after normalizing the path.
        name = self._normalize_name(self._clean_name(name))
        if self.custom_domain:
            return '%s//%s/%s' % (self.url_protocol,
                                  self.custom_domain, filepath_to_uri(name))

        if expire is None:
            expire = self.querystring_expire

        return self.connection.generate_url(
            expire,
            method='GET',
            bucket=self.bucket.name,
            key=self._encode_name(name),
            headers=headers,
            query_auth=self.querystring_auth,
            force_http=not self.secure_urls,
            response_headers=response_headers,
        )

    def get_available_name(self, name, max_length=None):
        """ Overwrite existing file with the same name. """
        name = self._clean_name(name)
        if self.file_overwrite:
            return get_available_overwrite_name(name, max_length)
        return super(S3BotoStorage, self).get_available_name(name, max_length)
