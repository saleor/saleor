# This module is sourced by genbind scripts in bundle directories to
# initialize a bundle area and provide a function to translate schema.

set -e

if [ ! "${PYXB_ROOT}" ] ; then
  echo 1>&2 "ERROR: Must set PYXB_ROOT environment variable"
  exit 1
fi

# Try to validate PYXB_ROOT as being the real thing
if [ ! -x "${PYXB_ROOT}/scripts/pyxbgen" ] ; then
  echo 1>&2 "ERROR: PYXB_ROOT (=${PYXB_ROOT}) does not appear to have pyxbgen"
  exit 1
fi

if [ ! "${BUNDLE_TAG}" ] ; then
  echo 1>&2 "ERROR: Must set BUNDLE_TAG environment variable"
  exit 1
fi

failure () {
  echo "Failed: ${@}"
  exit 1
}

PYXB_ROOT=${PYXB_ROOT}

BUNDLE_TAG=${BUNDLE_TAG:-core}

MODULE_PREFIX=pyxb.bundles.${BUNDLE_TAG}
BUNDLE_ROOT=${PYXB_ROOT}/pyxb/bundles/${BUNDLE_TAG}
SCHEMA_DIR=${BUNDLE_ROOT}/schemas
RAW_DIR=${BUNDLE_ROOT}/raw
ARCHIVE_DIR=${RAW_DIR}

rm -rf ${RAW_DIR}
mkdir -p ${RAW_DIR}
touch ${RAW_DIR}/__init__.py

if ! test -d ${SCHEMA_DIR} && \
   test -n "${PYXB_SCHEMA_REPO:+available}" && \
    ( cd ${PYXB_SCHEMA_REPO} && test -d .git && git log -1 schemas/bundles/${BUNDLE_TAG} ) ; then
  ( cd ${BUNDLE_ROOT} &&
    git clone -b schemas/bundles/${BUNDLE_TAG} ${PYXB_SCHEMA_REPO} schemas )
fi

mkdir -p ${SCHEMA_DIR}

# We use this to keep local copies of schema we had to retrieve from a
# remote system.  Normally, any such means a namespace dependency; the
# retrieved schema should have been translated first, and read from an
# archive.
CONTENT_COPY_DIR=${BUNDLE_ROOT}/remote

PYTHONPATH=${PYXB_ROOT}
PATH=${PYXB_ROOT}/scripts:${PATH}
export PATH PYTHONPATH

generateBindings () {
  AUX_PYXBGEN_FLAGS="${@}"
  sed -e '/^#/d' \
    | while read uri prefix auxflags ; do
    echo
    original_uri="${uri}"
    if ( echo ${uri} | grep -q ':/' ) ; then
       original_uri=${uri}
       cached_schema=${SCHEMA_DIR}/${prefix}.xsd
       if [ ! -f ${cached_schema} ] ; then
          echo "Retrieving ${prefix} from ${uri}"
          wget -O ${cached_schema} ${uri}
       fi
       echo "Using local cache ${cached_schema} for ${uri}"
       uri=${cached_schema}
    fi
    echo "Generating bindings ${prefix} from ${uri}"
    set -x
    pyxbgen \
      ${auxflags} \
      --schema-location ${uri} \
      --module=${prefix} \
      --module-prefix=${MODULE_PREFIX} \
      --write-for-customization \
      --archive-path=${RAW_DIR}:+ \
      --archive-to-file=${ARCHIVE_DIR}/${prefix}.wxs \
      --uri-content-archive-directory=${CONTENT_COPY_DIR} \
      ${AUX_PYXBGEN_FLAGS} \
    || failure ${prefix} ${original_uri}
    set +x
  done
}


