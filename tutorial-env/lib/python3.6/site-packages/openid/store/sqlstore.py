"""
This module contains C{L{OpenIDStore}} implementations that use
various SQL databases to back them.

Example of how to initialize a store database::

python -c 'from openid.store import sqlstore; import pysqlite2.dbapi2;'
  'sqlstore.SQLiteStore(pysqlite2.dbapi2.connect("cstore.db")).createTables()'
"""
import re
import time

try:
    import psycopg2
except ImportError:
    from psycopg2cffi import compat
    compat.register()

from openid.association import Association
from openid.store.interface import OpenIDStore
from openid.store import nonce


def _inTxn(func):
    def wrapped(self, *args, **kwargs):
        return self._callInTransaction(func, self, *args, **kwargs)

    if hasattr(func, '__name__'):
        try:
            wrapped.__name__ = func.__name__[4:]
        except TypeError:
            pass

    if hasattr(func, '__doc__'):
        wrapped.__doc__ = func.__doc__

    return wrapped


class SQLStore(OpenIDStore):
    """
    This is the parent class for the SQL stores, which contains the
    logic common to all of the SQL stores.

    The table names used are determined by the class variables
    C{L{associations_table}} and
    C{L{nonces_table}}.  To change the name of the tables used, pass
    new table names into the constructor.

    To create the tables with the proper schema, see the
    C{L{createTables}} method.

    This class shouldn't be used directly.  Use one of its subclasses
    instead, as those contain the code necessary to use a specific
    database.

    All methods other than C{L{__init__}} and C{L{createTables}}
    should be considered implementation details.


    @cvar associations_table: This is the default name of the table to
        keep associations in

    @cvar nonces_table: This is the default name of the table to keep
        nonces in.


    @sort: __init__, createTables
    """

    associations_table = 'oid_associations'
    nonces_table = 'oid_nonces'

    def __init__(self, conn, associations_table=None, nonces_table=None):
        """
        This creates a new SQLStore instance.  It requires an
        established database connection be given to it, and it allows
        overriding the default table names.


        @param conn: This must be an established connection to a
            database of the correct type for the SQLStore subclass
            you're using.

        @type conn: A python database API compatible connection
            object.


        @param associations_table: This is an optional parameter to
            specify the name of the table used for storing
            associations.  The default value is specified in
            C{L{SQLStore.associations_table}}.

        @type associations_table: C{str}


        @param nonces_table: This is an optional parameter to specify
            the name of the table used for storing nonces.  The
            default value is specified in C{L{SQLStore.nonces_table}}.

        @type nonces_table: C{str}
        """
        self.conn = conn
        self.cur = None
        self._statement_cache = {}
        self._table_names = {
            'associations': associations_table or self.associations_table,
            'nonces': nonces_table or self.nonces_table,
        }
        self.max_nonce_age = 6 * 60 * 60  # Six hours, in seconds

        # DB API extension: search for "Connection Attributes .Error,
        # .ProgrammingError, etc." in
        # http://www.python.org/dev/peps/pep-0249/
        if (hasattr(self.conn, 'IntegrityError') and
                hasattr(self.conn, 'OperationalError')):
            self.exceptions = self.conn

        if not (hasattr(self.exceptions, 'IntegrityError') and
                hasattr(self.exceptions, 'OperationalError')):
            raise RuntimeError("Error using database connection module "
                               "(Maybe it can't be imported?)")

    def blobDecode(self, blob):
        """Convert a blob as returned by the SQL engine into a str object.

        str -> str"""
        return blob

    def blobEncode(self, s):
        """Convert a str object into the necessary object for storing
        in the database as a blob."""
        return s

    def _getSQL(self, sql_name):
        try:
            return self._statement_cache[sql_name]
        except KeyError:
            sql = getattr(self, sql_name)
            sql %= self._table_names
            self._statement_cache[sql_name] = sql
            return sql

    def _execSQL(self, sql_name, *args):
        sql = self._getSQL(sql_name)

        # Kludge because we have reports of postgresql not quoting
        # arguments if they are passed in as unicode instead of str.
        # Currently the strings in our tables just have ascii in them,
        # so this ought to be safe.
        def unicode_to_str(arg):
            if isinstance(arg, str):
                return str(arg)
            else:
                return arg

        str_args = list(map(unicode_to_str, args))
        self.cur.execute(sql, str_args)

    def __getattr__(self, attr):
        # if the attribute starts with db_, use a default
        # implementation that looks up the appropriate SQL statement
        # as an attribute of this object and executes it.
        if attr[:3] == 'db_':
            sql_name = attr[3:] + '_sql'

            def func(*args):
                return self._execSQL(sql_name, *args)

            setattr(self, attr, func)
            return func
        else:
            raise AttributeError('Attribute %r not found' % (attr, ))

    def _callInTransaction(self, func, *args, **kwargs):
        """Execute the given function inside of a transaction, with an
        open cursor. If no exception is raised, the transaction is
        comitted, otherwise it is rolled back."""
        # No nesting of transactions
        self.conn.rollback()

        try:
            self.cur = self.conn.cursor()
            try:
                ret = func(*args, **kwargs)
            finally:
                self.cur.close()
                self.cur = None
        except:
            self.conn.rollback()
            raise
        else:
            self.conn.commit()

        return ret

    def txn_createTables(self):
        """
        This method creates the database tables necessary for this
        store to work.  It should not be called if the tables already
        exist.
        """
        self.db_create_nonce()
        self.db_create_assoc()

    createTables = _inTxn(txn_createTables)

    def txn_storeAssociation(self, server_url, association):
        """Set the association for the server URL.

        Association -> NoneType
        """
        a = association
        self.db_set_assoc(server_url, a.handle,
                          self.blobEncode(a.secret), a.issued, a.lifetime,
                          a.assoc_type)

    storeAssociation = _inTxn(txn_storeAssociation)

    def txn_getAssociation(self, server_url, handle=None):
        """Get the most recent association that has been set for this
        server URL and handle.

        str -> NoneType or Association
        """
        if handle is not None:
            self.db_get_assoc(server_url, handle)
        else:
            self.db_get_assocs(server_url)

        rows = self.cur.fetchall()
        if len(rows) == 0:
            return None
        else:
            associations = []
            for values in rows:
                values = list(values)
                values[1] = self.blobDecode(values[1])
                assoc = Association(*values)
                if assoc.expiresIn == 0:
                    self.txn_removeAssociation(server_url, assoc.handle)
                else:
                    associations.append((assoc.issued, assoc))

            if associations:
                associations.sort()
                return associations[-1][1]
            else:
                return None

    getAssociation = _inTxn(txn_getAssociation)

    def txn_removeAssociation(self, server_url, handle):
        """Remove the association for the given server URL and handle,
        returning whether the association existed at all.

        (str, str) -> bool
        """
        self.db_remove_assoc(server_url, handle)
        return self.cur.rowcount > 0  # -1 is undefined

    removeAssociation = _inTxn(txn_removeAssociation)

    def txn_useNonce(self, server_url, timestamp, salt):
        """Return whether this nonce is present, and if it is, then
        remove it from the set.

        str -> bool"""
        if abs(timestamp - time.time()) > nonce.SKEW:
            return False

        try:
            self.db_add_nonce(server_url, timestamp, salt)
        except self.exceptions.IntegrityError:
            # The key uniqueness check failed
            return False
        else:
            # The nonce was successfully added
            return True

    useNonce = _inTxn(txn_useNonce)

    def txn_cleanupNonces(self):
        self.db_clean_nonce(int(time.time()) - nonce.SKEW)
        return self.cur.rowcount

    cleanupNonces = _inTxn(txn_cleanupNonces)

    def txn_cleanupAssociations(self):
        self.db_clean_assoc(int(time.time()))
        return self.cur.rowcount

    cleanupAssociations = _inTxn(txn_cleanupAssociations)


class SQLiteStore(SQLStore):
    """
    This is an SQLite-based specialization of C{L{SQLStore}}.

    To create an instance, see C{L{SQLStore.__init__}}.  To create the
    tables it will use, see C{L{SQLStore.createTables}}.

    All other methods are implementation details.
    """

    create_nonce_sql = """
    CREATE TABLE %(nonces)s (
        server_url VARCHAR,
        timestamp INTEGER,
        salt CHAR(40),
        UNIQUE(server_url, timestamp, salt)
    );
    """

    create_assoc_sql = """
    CREATE TABLE %(associations)s
    (
        server_url VARCHAR(2047),
        handle VARCHAR(255),
        secret BLOB(128),
        issued INTEGER,
        lifetime INTEGER,
        assoc_type VARCHAR(64),
        PRIMARY KEY (server_url, handle)
    );
    """

    set_assoc_sql = ('INSERT OR REPLACE INTO %(associations)s '
                     '(server_url, handle, secret, issued, '
                     'lifetime, assoc_type) '
                     'VALUES (?, ?, ?, ?, ?, ?);')
    get_assocs_sql = ('SELECT handle, secret, issued, lifetime, assoc_type '
                      'FROM %(associations)s WHERE server_url = ?;')
    get_assoc_sql = (
        'SELECT handle, secret, issued, lifetime, assoc_type '
        'FROM %(associations)s WHERE server_url = ? AND handle = ?;')

    get_expired_sql = ('SELECT server_url '
                       'FROM %(associations)s WHERE issued + lifetime < ?;')

    remove_assoc_sql = ('DELETE FROM %(associations)s '
                        'WHERE server_url = ? AND handle = ?;')

    clean_assoc_sql = 'DELETE FROM %(associations)s WHERE issued + lifetime < ?;'

    add_nonce_sql = 'INSERT INTO %(nonces)s VALUES (?, ?, ?);'

    clean_nonce_sql = 'DELETE FROM %(nonces)s WHERE timestamp < ?;'

    def blobEncode(self, s):
        return memoryview(s)

    def useNonce(self, *args, **kwargs):
        # Older versions of the sqlite wrapper do not raise
        # IntegrityError as they should, so we have to detect the
        # message from the OperationalError.
        try:
            return super(SQLiteStore, self).useNonce(*args, **kwargs)
        except self.exceptions.OperationalError as why:
            if re.match('^columns .* are not unique$', str(why)):
                return False
            else:
                raise


class MySQLStore(SQLStore):
    """
    This is a MySQL-based specialization of C{L{SQLStore}}.

    Uses InnoDB tables for transaction support.

    To create an instance, see C{L{SQLStore.__init__}}.  To create the
    tables it will use, see C{L{SQLStore.createTables}}.

    All other methods are implementation details.
    """

    try:
        import MySQLdb as exceptions
    except ImportError:
        exceptions = None

    create_nonce_sql = """
    CREATE TABLE %(nonces)s (
        server_url BLOB NOT NULL,
        timestamp INTEGER NOT NULL,
        salt CHAR(40) NOT NULL,
        PRIMARY KEY (server_url(255), timestamp, salt)
    )
    ENGINE=InnoDB;
    """

    create_assoc_sql = """
    CREATE TABLE %(associations)s
    (
        server_url BLOB NOT NULL,
        handle VARCHAR(255) NOT NULL,
        secret BLOB NOT NULL,
        issued INTEGER NOT NULL,
        lifetime INTEGER NOT NULL,
        assoc_type VARCHAR(64) NOT NULL,
        PRIMARY KEY (server_url(255), handle)
    )
    ENGINE=InnoDB;
    """

    set_assoc_sql = ('REPLACE INTO %(associations)s '
                     'VALUES (%%s, %%s, %%s, %%s, %%s, %%s);')
    get_assocs_sql = ('SELECT handle, secret, issued, lifetime, assoc_type'
                      ' FROM %(associations)s WHERE server_url = %%s;')
    get_expired_sql = ('SELECT server_url '
                       'FROM %(associations)s WHERE issued + lifetime < %%s;')

    get_assoc_sql = (
        'SELECT handle, secret, issued, lifetime, assoc_type'
        ' FROM %(associations)s WHERE server_url = %%s AND handle = %%s;')
    remove_assoc_sql = ('DELETE FROM %(associations)s '
                        'WHERE server_url = %%s AND handle = %%s;')

    clean_assoc_sql = 'DELETE FROM %(associations)s WHERE issued + lifetime < %%s;'

    add_nonce_sql = 'INSERT INTO %(nonces)s VALUES (%%s, %%s, %%s);'

    clean_nonce_sql = 'DELETE FROM %(nonces)s WHERE timestamp < %%s;'


class PostgreSQLStore(SQLStore):
    """
    This is a PostgreSQL-based specialization of C{L{SQLStore}}.

    To create an instance, see C{L{SQLStore.__init__}}.  To create the
    tables it will use, see C{L{SQLStore.createTables}}.

    All other methods are implementation details.
    """
    exceptions = None

    create_nonce_sql = """
    CREATE TABLE %(nonces)s (
        server_url VARCHAR(2047) NOT NULL,
        timestamp INTEGER NOT NULL,
        salt CHAR(40) NOT NULL,
        PRIMARY KEY (server_url, timestamp, salt)
    );
    """

    create_assoc_sql = """
    CREATE TABLE %(associations)s
    (
        server_url VARCHAR(2047) NOT NULL,
        handle VARCHAR(255) NOT NULL,
        secret BYTEA NOT NULL,
        issued INTEGER NOT NULL,
        lifetime INTEGER NOT NULL,
        assoc_type VARCHAR(64) NOT NULL,
        PRIMARY KEY (server_url, handle),
        CONSTRAINT secret_length_constraint CHECK (LENGTH(secret) <= 128)
    );
    """

    def db_set_assoc(self, server_url, handle, secret, issued, lifetime,
                     assoc_type):
        """
        Set an association.  This is implemented as a method because
        REPLACE INTO is not supported by PostgreSQL (and is not
        standard SQL).
        """
        result = self.db_get_assoc(server_url, handle)
        rows = self.cur.fetchall()
        if len(rows):
            # Update the table since this associations already exists.
            return self.db_update_assoc(secret, issued, lifetime, assoc_type,
                                        server_url, handle)
        else:
            # Insert a new record because this association wasn't
            # found.
            return self.db_new_assoc(server_url, handle, secret, issued,
                                     lifetime, assoc_type)

    new_assoc_sql = ('INSERT INTO %(associations)s '
                     'VALUES (%%s, %%s, %%s, %%s, %%s, %%s);')
    update_assoc_sql = ('UPDATE %(associations)s SET '
                        'secret = %%s, issued = %%s, '
                        'lifetime = %%s, assoc_type = %%s '
                        'WHERE server_url = %%s AND handle = %%s;')
    get_assocs_sql = ('SELECT handle, secret, issued, lifetime, assoc_type'
                      ' FROM %(associations)s WHERE server_url = %%s;')
    get_expired_sql = ('SELECT server_url '
                       'FROM %(associations)s WHERE issued + lifetime < %%s;')

    get_assoc_sql = (
        'SELECT handle, secret, issued, lifetime, assoc_type'
        ' FROM %(associations)s WHERE server_url = %%s AND handle = %%s;')
    remove_assoc_sql = ('DELETE FROM %(associations)s '
                        'WHERE server_url = %%s AND handle = %%s;')

    clean_assoc_sql = 'DELETE FROM %(associations)s WHERE issued + lifetime < %%s;'

    add_nonce_sql = 'INSERT INTO %(nonces)s VALUES (%%s, %%s, %%s);'

    clean_nonce_sql = 'DELETE FROM %(nonces)s WHERE timestamp < %%s;'

    def blobEncode(self, blob):
        from psycopg2 import Binary

        return Binary(blob)

    def blobDecode(self, blob):
        return blob.tobytes()
