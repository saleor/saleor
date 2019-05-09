import mimetypes
import os
import posixpath
import threading
import warnings
from gzip import GzipFile
from tempfile import SpooledTemporaryFile

from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.core.files.base import File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from django.utils.encoding import (
    filepath_to_uri, force_bytes, force_text, smart_text,
)
from django.utils.six import BytesIO
from django.utils.six.moves.urllib import parse as urlparse
from django.utils.timezone import is_naive, localtime

from storages.utils import (
    check_location, get_available_overwrite_name, lookup_env, safe_join,
    setting,
)

try:
    import boto3.session
    from boto3 import __version__ as boto3_version
    from botocore.client import Config
    from botocore.exceptions import ClientError
except ImportError:
    raise ImproperlyConfigured("Could not load Boto3's S3 bindings.\n"
                               "See https://github.com/boto/boto3")


boto3_version_info = tuple([int(i) for i in boto3_version.split('.')])


@deconstructible
class S3Boto3StorageFile(File):

    """
    The default file object used by the S3Boto3Storage backend.

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
        if 'r' in mode and 'w' in mode:
            raise ValueError("Can't combine 'r' and 'w' in mode.")
        self._storage = storage
        self.name = name[len(self._storage.location):].lstrip('/')
        self._mode = mode
        self.obj = storage.bucket.Object(storage._encode_name(name))
        if 'w' not in mode:
            # Force early RAII-style exception if object does not exist
            self.obj.load()
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

    @property
    def size(self):
        return self.obj.content_length

    def _get_file(self):
        if self._file is None:
            self._file = SpooledTemporaryFile(
                max_size=self._storage.max_memory_size,
                suffix=".S3Boto3StorageFile",
                dir=setting("FILE_UPLOAD_TEMP_DIR")
            )
            if 'r' in self._mode:
                self._is_dirty = False
                self.obj.download_fileobj(self._file)
                self._file.seek(0)
            if self._storage.gzip and self.obj.content_encoding == 'gzip':
                self._file = GzipFile(mode=self._mode, fileobj=self._file, mtime=0.0)
        return self._file

    def _set_file(self, value):
        self._file = value

    file = property(_get_file, _set_file)

    def read(self, *args, **kwargs):
        if 'r' not in self._mode:
            raise AttributeError("File was not opened in read mode.")
        return super(S3Boto3StorageFile, self).read(*args, **kwargs)

    def write(self, content):
        if 'w' not in self._mode:
            raise AttributeError("File was not opened in write mode.")
        self._is_dirty = True
        if self._multipart is None:
            parameters = self._storage.object_parameters.copy()
            if self._storage.default_acl:
                parameters['ACL'] = self._storage.default_acl
            parameters['ContentType'] = (mimetypes.guess_type(self.obj.key)[0] or
                                         self._storage.default_content_type)
            if self._storage.reduced_redundancy:
                parameters['StorageClass'] = 'REDUCED_REDUNDANCY'
            if self._storage.encryption:
                parameters['ServerSideEncryption'] = 'AES256'
            self._multipart = self.obj.initiate_multipart_upload(**parameters)
        if self.buffer_size <= self._buffer_file_size:
            self._flush_write_buffer()
        return super(S3Boto3StorageFile, self).write(force_bytes(content))

    @property
    def _buffer_file_size(self):
        pos = self.file.tell()
        self.file.seek(0, os.SEEK_END)
        length = self.file.tell()
        self.file.seek(pos)
        return length

    def _flush_write_buffer(self):
        """
        Flushes the write buffer.
        """
        if self._buffer_file_size:
            self._write_counter += 1
            self.file.seek(0)
            part = self._multipart.Part(self._write_counter)
            part.upload(Body=self.file.read())
            self.file.seek(0)
            self.file.truncate()

    def close(self):
        if self._is_dirty:
            self._flush_write_buffer()
            # TODO: Possibly cache the part ids as they're being uploaded
            # instead of requesting parts from server. For now, emulating
            # s3boto's behavior.
            parts = [{'ETag': part.e_tag, 'PartNumber': part.part_number}
                     for part in self._multipart.parts.all()]
            self._multipart.complete(
                MultipartUpload={'Parts': parts})
        else:
            if self._multipart is not None:
                self._multipart.abort()
        if self._file is not None:
            self._file.close()
            self._file = None


@deconstructible
class S3Boto3Storage(Storage):
    """
    Amazon Simple Storage Service using Boto3

    This storage backend supports opening files in read or write
    mode and supports streaming(buffering) data in chunks to S3
    when writing.
    """
    default_content_type = 'application/octet-stream'
    # If config provided in init, signature_version and addressing_style settings/args are ignored.
    config = None

    # used for looking up the access and secret key from env vars
    access_key_names = ['AWS_S3_ACCESS_KEY_ID', 'AWS_ACCESS_KEY_ID']
    secret_key_names = ['AWS_S3_SECRET_ACCESS_KEY', 'AWS_SECRET_ACCESS_KEY']
    security_token_names = ['AWS_SESSION_TOKEN', 'AWS_SECURITY_TOKEN']
    security_token = None

    access_key = setting('AWS_S3_ACCESS_KEY_ID', setting('AWS_ACCESS_KEY_ID'))
    secret_key = setting('AWS_S3_SECRET_ACCESS_KEY', setting('AWS_SECRET_ACCESS_KEY'))
    file_overwrite = setting('AWS_S3_FILE_OVERWRITE', True)
    object_parameters = setting('AWS_S3_OBJECT_PARAMETERS', {})
    bucket_name = setting('AWS_STORAGE_BUCKET_NAME')
    auto_create_bucket = setting('AWS_AUTO_CREATE_BUCKET', False)
    default_acl = setting('AWS_DEFAULT_ACL', 'public-read')
    bucket_acl = setting('AWS_BUCKET_ACL', default_acl)
    querystring_auth = setting('AWS_QUERYSTRING_AUTH', True)
    querystring_expire = setting('AWS_QUERYSTRING_EXPIRE', 3600)
    signature_version = setting('AWS_S3_SIGNATURE_VERSION')
    reduced_redundancy = setting('AWS_REDUCED_REDUNDANCY', False)
    location = setting('AWS_LOCATION', '')
    encryption = setting('AWS_S3_ENCRYPTION', False)
    custom_domain = setting('AWS_S3_CUSTOM_DOMAIN')
    addressing_style = setting('AWS_S3_ADDRESSING_STYLE')
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
    endpoint_url = setting('AWS_S3_ENDPOINT_URL')
    proxies = setting('AWS_S3_PROXIES')
    region_name = setting('AWS_S3_REGION_NAME')
    use_ssl = setting('AWS_S3_USE_SSL', True)
    verify = setting('AWS_S3_VERIFY', None)
    max_memory_size = setting('AWS_S3_MAX_MEMORY_SIZE', 0)

    def __init__(self, acl=None, bucket=None, **settings):
        # check if some of the settings we've provided as class attributes
        # need to be overwritten with values passed in here
        for name, value in settings.items():
            if hasattr(self, name):
                setattr(self, name, value)

        # For backward-compatibility of old differing parameter names
        if acl is not None:
            warnings.warn(
                "The acl argument of S3Boto3Storage is deprecated. Use "
                "argument default_acl or setting AWS_DEFAULT_ACL instead. The "
                "acl argument will be removed in version 2.0.",
                DeprecationWarning,
            )
            self.default_acl = acl
        if bucket is not None:
            warnings.warn(
                "The bucket argument of S3Boto3Storage is deprecated. Use "
                "argument bucket_name or setting AWS_STORAGE_BUCKET_NAME "
                "instead. The bucket argument will be removed in version 2.0.",
                DeprecationWarning,
            )
            self.bucket_name = bucket

        check_location(self)

        # Backward-compatibility: given the anteriority of the SECURE_URL setting
        # we fall back to https if specified in order to avoid the construction
        # of unsecure urls.
        if self.secure_urls:
            self.url_protocol = 'https:'

        self._entries = {}
        self._bucket = None
        self._connections = threading.local()

        self.access_key, self.secret_key = self._get_access_keys()
        self.security_token = self._get_security_token()

        if not self.config:
            kwargs = dict(
                s3={'addressing_style': self.addressing_style},
                signature_version=self.signature_version,
            )

            if boto3_version_info >= (1, 4, 4):
                kwargs['proxies'] = self.proxies
            else:
                warnings.warn(
                    "In version 2.0 of django-storages the minimum required version of "
                    "boto3 will be 1.4.4. You have %s " % boto3_version_info
                )
            self.config = Config(**kwargs)

        # warn about upcoming change in default AWS_DEFAULT_ACL setting
        if not hasattr(django_settings, 'AWS_DEFAULT_ACL'):
            warnings.warn(
                "The default behavior of S3Boto3Storage is insecure and will change "
                "in django-storages 2.0. By default files and new buckets are saved "
                "with an ACL of 'public-read' (globally publicly readable). Version 2.0 will "
                "default to using the bucket's ACL. To opt into the new behavior set "
                "AWS_DEFAULT_ACL = None, otherwise to silence this warning explicitly "
                "set AWS_DEFAULT_ACL."
            )

    def __getstate__(self):
        state = self.__dict__.copy()
        state.pop('_connections', None)
        state.pop('_bucket', None)
        return state

    def __setstate__(self, state):
        state['_connections'] = threading.local()
        state['_bucket'] = None
        self.__dict__ = state

    @property
    def connection(self):
        connection = getattr(self._connections, 'connection', None)
        if connection is None:
            session = boto3.session.Session()
            self._connections.connection = session.resource(
                's3',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                aws_session_token=self.security_token,
                region_name=self.region_name,
                use_ssl=self.use_ssl,
                endpoint_url=self.endpoint_url,
                config=self.config,
                verify=self.verify,
            )
        return self._connections.connection

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
        if self.preload_metadata and not self._entries:
            self._entries = {
                self._decode_name(entry.key): entry
                for entry in self.bucket.objects.filter(Prefix=self.location)
            }
        return self._entries

    def _get_access_keys(self):
        """
        Gets the access keys to use when accessing S3. If none is
        provided in the settings then get them from the environment
        variables.
        """
        access_key = self.access_key or lookup_env(S3Boto3Storage.access_key_names)
        secret_key = self.secret_key or lookup_env(S3Boto3Storage.secret_key_names)
        return access_key, secret_key

    def _get_security_token(self):
        """
        Gets the security token to use when accessing S3. Get it from
        the environment variables.
        """
        security_token = self.security_token or lookup_env(S3Boto3Storage.security_token_names)
        return security_token

    def _get_or_create_bucket(self, name):
        """
        Retrieves a bucket if it exists, otherwise creates it.
        """
        bucket = self.connection.Bucket(name)
        if self.auto_create_bucket:
            try:
                # Directly call head_bucket instead of bucket.load() because head_bucket()
                # fails on wrong region, while bucket.load() does not.
                bucket.meta.client.head_bucket(Bucket=name)
            except ClientError as err:
                if err.response['ResponseMetadata']['HTTPStatusCode'] == 301:
                    raise ImproperlyConfigured("Bucket %s exists, but in a different "
                                               "region than we are connecting to. Set "
                                               "the region to connect to by setting "
                                               "AWS_S3_REGION_NAME to the correct region." % name)

                elif err.response['ResponseMetadata']['HTTPStatusCode'] == 404:
                    # Notes: When using the us-east-1 Standard endpoint, you can create
                    # buckets in other regions. The same is not true when hitting region specific
                    # endpoints. However, when you create the bucket not in the same region, the
                    # connection will fail all future requests to the Bucket after the creation
                    # (301 Moved Permanently).
                    #
                    # For simplicity, we enforce in S3Boto3Storage that any auto-created
                    # bucket must match the region that the connection is for.
                    #
                    # Also note that Amazon specifically disallows "us-east-1" when passing bucket
                    # region names; LocationConstraint *must* be blank to create in US Standard.
                    if not hasattr(django_settings, 'AWS_BUCKET_ACL'):
                        warnings.warn(
                            "The default behavior of S3Boto3Storage is insecure and will change "
                            "in django-storages 2.0. By default new buckets are saved with an ACL of "
                            "'public-read' (globally publicly readable). Version 2.0 will default to "
                            "Amazon's default of the bucket owner. To opt into this behavior this warning "
                            "set AWS_BUCKET_ACL = None, otherwise to silence this warning explicitly set "
                            "AWS_BUCKET_ACL."
                        )
                    if self.bucket_acl:
                        bucket_params = {'ACL': self.bucket_acl}
                    else:
                        bucket_params = {}
                    region_name = self.connection.meta.client.meta.region_name
                    if region_name != 'us-east-1':
                        bucket_params['CreateBucketConfiguration'] = {
                            'LocationConstraint': region_name}
                    bucket.create(**bucket_params)
                else:
                    raise
        return bucket

    def _clean_name(self, name):
        """
        Cleans the name so that Windows style paths work
        """
        # Normalize Windows style paths
        clean_name = posixpath.normpath(name).replace('\\', '/')

        # os.path.normpath() can strip trailing slashes so we implement
        # a workaround here.
        if name.endswith('/') and not clean_name.endswith('/'):
            # Add a trailing slash as it was stripped.
            clean_name += '/'
        return clean_name

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
        return smart_text(name, encoding=self.file_name_charset)

    def _decode_name(self, name):
        return force_text(name, encoding=self.file_name_charset)

    def _compress_content(self, content):
        """Gzip a given string content."""
        content.seek(0)
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
        # Boto 2 returned the InMemoryUploadedFile with the file pointer replaced,
        # but Boto 3 seems to have issues with that. No need for fp.name in Boto3
        # so just returning the BytesIO directly
        return zbuf

    def _open(self, name, mode='rb'):
        name = self._normalize_name(self._clean_name(name))
        try:
            f = S3Boto3StorageFile(name, mode, self)
        except ClientError as err:
            if err.response['ResponseMetadata']['HTTPStatusCode'] == 404:
                raise IOError('File does not exist: %s' % name)
            raise  # Let it bubble up if it was some other error
        return f

    def _save(self, name, content):
        cleaned_name = self._clean_name(name)
        name = self._normalize_name(cleaned_name)
        parameters = self.object_parameters.copy()
        _type, encoding = mimetypes.guess_type(name)
        content_type = getattr(content, 'content_type', None)
        content_type = content_type or _type or self.default_content_type

        # setting the content_type in the key object is not enough.
        parameters.update({'ContentType': content_type})

        if self.gzip and content_type in self.gzip_content_types:
            content = self._compress_content(content)
            parameters.update({'ContentEncoding': 'gzip'})
        elif encoding:
            # If the content already has a particular encoding, set it
            parameters.update({'ContentEncoding': encoding})

        encoded_name = self._encode_name(name)
        obj = self.bucket.Object(encoded_name)
        if self.preload_metadata:
            self._entries[encoded_name] = obj

        # If both `name` and `content.name` are empty or None, your request
        # can be rejected with `XAmzContentSHA256Mismatch` error, because in
        # `django.core.files.storage.Storage.save` method your file-like object
        # will be wrapped in `django.core.files.File` if no `chunks` method
        # provided. `File.__bool__`  method is Django-specific and depends on
        # file name, for this reason`botocore.handlers.calculate_md5` can fail
        # even if wrapped file-like object exists. To avoid Django-specific
        # logic, pass internal file-like object if `content` is `File`
        # class instance.
        if isinstance(content, File):
            content = content.file

        self._save_content(obj, content, parameters=parameters)
        # Note: In boto3, after a put, last_modified is automatically reloaded
        # the next time it is accessed; no need to specifically reload it.
        return cleaned_name

    def _save_content(self, obj, content, parameters):
        # only pass backwards incompatible arguments if they vary from the default
        put_parameters = parameters.copy() if parameters else {}
        if self.encryption:
            put_parameters['ServerSideEncryption'] = 'AES256'
        if self.reduced_redundancy:
            put_parameters['StorageClass'] = 'REDUCED_REDUNDANCY'
        if self.default_acl:
            put_parameters['ACL'] = self.default_acl
        content.seek(0, os.SEEK_SET)
        obj.upload_fileobj(content, ExtraArgs=put_parameters)

    def delete(self, name):
        name = self._normalize_name(self._clean_name(name))
        self.bucket.Object(self._encode_name(name)).delete()

    def exists(self, name):
        name = self._normalize_name(self._clean_name(name))
        if self.entries:
            return name in self.entries
        try:
            self.connection.meta.client.head_object(Bucket=self.bucket_name, Key=name)
            return True
        except ClientError:
            return False

    def listdir(self, name):
        path = self._normalize_name(self._clean_name(name))
        # The path needs to end with a slash, but if the root is empty, leave
        # it.
        if path and not path.endswith('/'):
            path += '/'

        directories = []
        files = []
        paginator = self.connection.meta.client.get_paginator('list_objects')
        pages = paginator.paginate(Bucket=self.bucket_name, Delimiter='/', Prefix=path)
        for page in pages:
            for entry in page.get('CommonPrefixes', ()):
                directories.append(posixpath.relpath(entry['Prefix'], path))
            for entry in page.get('Contents', ()):
                files.append(posixpath.relpath(entry['Key'], path))
        return directories, files

    def size(self, name):
        name = self._normalize_name(self._clean_name(name))
        if self.entries:
            entry = self.entries.get(name)
            if entry:
                return entry.size if hasattr(entry, 'size') else entry.content_length
            return 0
        return self.bucket.Object(self._encode_name(name)).content_length

    def get_modified_time(self, name):
        """
        Returns an (aware) datetime object containing the last modified time if
        USE_TZ is True, otherwise returns a naive datetime in the local timezone.
        """
        name = self._normalize_name(self._clean_name(name))
        entry = self.entries.get(name)
        # only call self.bucket.Object() if the key is not found
        # in the preloaded metadata.
        if entry is None:
            entry = self.bucket.Object(self._encode_name(name))
        if setting('USE_TZ'):
            # boto3 returns TZ aware timestamps
            return entry.last_modified
        else:
            return localtime(entry.last_modified).replace(tzinfo=None)

    def modified_time(self, name):
        """Returns a naive datetime object containing the last modified time."""
        # If USE_TZ=False then get_modified_time will return a naive datetime
        # so we just return that, else we have to localize and strip the tz
        mtime = self.get_modified_time(name)
        return mtime if is_naive(mtime) else localtime(mtime).replace(tzinfo=None)

    def _strip_signing_parameters(self, url):
        # Boto3 does not currently support generating URLs that are unsigned. Instead we
        # take the signed URLs and strip any querystring params related to signing and expiration.
        # Note that this may end up with URLs that are still invalid, especially if params are
        # passed in that only work with signed URLs, e.g. response header params.
        # The code attempts to strip all query parameters that match names of known parameters
        # from v2 and v4 signatures, regardless of the actual signature version used.
        split_url = urlparse.urlsplit(url)
        qs = urlparse.parse_qsl(split_url.query, keep_blank_values=True)
        blacklist = {
            'x-amz-algorithm', 'x-amz-credential', 'x-amz-date',
            'x-amz-expires', 'x-amz-signedheaders', 'x-amz-signature',
            'x-amz-security-token', 'awsaccesskeyid', 'expires', 'signature',
        }
        filtered_qs = ((key, val) for key, val in qs if key.lower() not in blacklist)
        # Note: Parameters that did not have a value in the original query string will have
        # an '=' sign appended to it, e.g ?foo&bar becomes ?foo=&bar=
        joined_qs = ('='.join(keyval) for keyval in filtered_qs)
        split_url = split_url._replace(query="&".join(joined_qs))
        return split_url.geturl()

    def url(self, name, parameters=None, expire=None):
        # Preserve the trailing slash after normalizing the path.
        # TODO: Handle force_http=not self.secure_urls like in s3boto
        name = self._normalize_name(self._clean_name(name))
        if self.custom_domain:
            return "%s//%s/%s" % (self.url_protocol,
                                  self.custom_domain, filepath_to_uri(name))
        if expire is None:
            expire = self.querystring_expire

        params = parameters.copy() if parameters else {}
        params['Bucket'] = self.bucket.name
        params['Key'] = self._encode_name(name)
        url = self.bucket.meta.client.generate_presigned_url('get_object', Params=params,
                                                             ExpiresIn=expire)
        if self.querystring_auth:
            return url
        return self._strip_signing_parameters(url)

    def get_available_name(self, name, max_length=None):
        """Overwrite existing file with the same name."""
        name = self._clean_name(name)
        if self.file_overwrite:
            return get_available_overwrite_name(name, max_length)
        return super(S3Boto3Storage, self).get_available_name(name, max_length)
