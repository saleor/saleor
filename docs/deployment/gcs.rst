.. _amazon-s3:

Storing Files on Google Cloud Storage (GCS) 
===========================================

If you're using containers for deployment (including Docker and Heroku) you'll want to avoid storing files in the container's volatile filesystem. This integration allows you to delegate storing such files to `Google Cloud Storage (GCS)  <https://django-storages.readthedocs.io/en/latest/backends/gcloud.html>`_ service.

Base configuration
------------------

``GOOGLE_APPLICATION_CREDENTIALS``
  Set an environment variable to path of the json file.

``GS_CREDENTIALS`` (optional)
  The OAuth 2 credentials to use for the connection. 
  If unset, falls back to the default inferred from the environment (i.e. GOOGLE_APPLICATION_CREDENTIALS)

Serving media files with a GCS bucket
-------------------------------------

If you want to store and serve media files, set the following environment
variable to use GCS as media bucket:

``GS_MEDIA_BUCKET_NAME``
  The GCS bucket name to use for media files.

If you are intending into using a custom domain for your media GCS bucket,
you can set this environment variable to your custom GCS media domain:

``GS_MEDIA_CUSTOM_DOMAIN``
  The GCS custom domain to use for the media bucket.


.. note::
 The media files are every data uploaded through the dashboard
 (product images, category images, etc.)


Serving static files with a GCS bucket
--------------------------------------

By default static files (such as CSS and JS files required to display your pages) will be served by the application server.

If you intend to use GCS for your static files as well, set an additional environment variable:

``GS_STORAGE_BUCKET_NAME``
  The GCS bucket name to use for static files.

If you are intending into using a custom domain for your static GCS bucket,
you can set this environment variable to your custom GCS domain:

``GS_STATIC_CUSTOM_DOMAIN``
  The GCS custom domain to use for the static bucket.


.. note::
  You will need to configure your GCS bucket to allow cross origin requests for
  some files to be properly served (SVG files, Javascript files, etc.).
  For that, you have to set below instructions in your
  GCS Bucket's permissions tab under the `CORS section <https://cloud.google.com/storage/docs/xml-api/put-bucket-cors>`_.

  .. code-block:: xml
  
    <?xml version="1.0" encoding="UTF-8"?>
    <CorsConfig>
    <Cors>
        <Origins>
            <Origin>http://origin1.example.com</Origin>
            <Origin>http://origin2.example.com</Origin>
         </Origins>
         <Methods>
             <Method>GET</Method>
             <Method>HEAD</Method>
             <Method>PUT</Method>
             <Method>POST</Method>
             <Method>DELETE</Method>
          </Methods>
          <ResponseHeaders>
              <ResponseHeader>x-goog-meta-foo1</ResponseHeader>
              <ResponseHeader>x-goog-meta-foo2</ResponseHeader>
          </ResponseHeaders>
          <MaxAgeSec>1800</MaxAgeSec>
     </Cors>
     </CorsConfig>
