========================
MaxMind DB Python Module
========================

Description
-----------

This is a Python module for reading MaxMind DB files. The module includes both
a pure Python reader and an optional C extension.

MaxMind DB is a binary file format that stores data indexed by IP address
subnets (IPv4 or IPv6).

Installation
------------

If you want to use the C extension, you must first install `libmaxminddb
<https://github.com/maxmind/libmaxminddb>`_ C library installed before
installing this extension. If the library is not available, the module will
fall-back to a pure Python implementation.

To install maxminddb, type:

.. code-block:: bash

    $ pip install maxminddb

If you are not able to use pip, you may also use easy_install from the
source directory:

.. code-block:: bash

    $ easy_install .

Usage
-----

To use this module, you must first download or create a MaxMind DB file. We
provide `free GeoLite2 databases
<http://dev.maxmind.com/geoip/geoip2/geolite2>`_. These files must be
decompressed with ``gunzip``.

After you have obtained a database and imported the module, call
``open_database`` with a path, or file descriptor (in the case of MODE_FD),
to the database as the first argument. Optionally, you may pass a mode as the
second argument. The modes are exported from ``maxminddb``. Valid modes are:

* MODE_MMAP_EXT - use the C extension with memory map.
* MODE_MMAP - read from memory map. Pure Python.
* MODE_FILE - read database as standard file. Pure Python.
* MODE_MEMORY - load database into memory. Pure Python.
* MODE_FD - load database into memory from a file descriptor. Pure Python.
* MODE_AUTO - try MODE_MMAP_EXT, MODE_MMAP, MODE_FILE in that order. Default.

**NOTE**: When using ``MODE_FD``, it is the *caller's* responsibility to be
sure that the file descriptor gets closed properly. The caller may close the
file descriptor immediately after the ``Reader`` object is created.

The ``open_database`` function returns a ``Reader`` object. To look up an IP
address, use the ``get`` method on this object. The method will return the
corresponding values for the IP address from the database (e.g., a dictionary
for GeoIP2/GeoLite2 databases). If the database does not contain a record for
that IP address, the method will return ``None``.

Example
-------

.. code-block:: pycon

    >>> import maxminddb
    >>>
    >>> reader = maxminddb.open_database('GeoLite2-City.mmdb')
    >>> reader.get('1.1.1.1')
    {'country': ... }
    >>>
    >>> reader.close()

Exceptions
----------

The module will return an ``InvalidDatabaseError`` if the database is corrupt
or otherwise invalid. A ``ValueError`` will be thrown if you look up an
invalid IP address or an IPv6 address in an IPv4 database.

Requirements
------------

This code requires Python 2.6+ or 3.3+. The C extension requires CPython. The
pure Python implementation has been tested with PyPy.

On Python 2, the `ipaddress module <https://pypi.python.org/pypi/ipaddress>`_ is
required.

Versioning
----------

The MaxMind DB Python module uses `Semantic Versioning <http://semver.org/>`_.

Support
-------

Please report all issues with this code using the `GitHub issue tracker
<https://github.com/maxmind/MaxMind-DB-Reader-python/issues>`_

If you are having an issue with a MaxMind service that is not specific to this
API, please contact `MaxMind support <http://www.maxmind.com/en/support>`_ for
assistance.


