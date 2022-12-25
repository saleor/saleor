#!/bin/sh

fail () {
  echo 1>&2 "${test_name} FAILED: ${@}"
  exit 1
}

# Because this is an OpenGIS application, the OpenGIS bundle must be
# made available during binding generation.  OpenGIS also depends
# on XLink which is in the common bundle.
export PYXB_ARCHIVE_PATH='&pyxb/bundles/opengis//:&pyxb/bundles/common//:+'

# Attempt to get romkan.py if not already available
[ -f romkan.py ] || wget https://raw.githubusercontent.com/mhagiwara/nltk/master/jpbook/romkan.py

python -c 'import drv_libxml2' || fail python-libxml2 not installed

if python -c 'import pyxb.bundles.opengis.gml_3_2' ; then
  echo 1>&2 "OpenGIS bundle present and will be used"
else
  cat 1>&2 <<EOText

Warning: The PyXB OpenGIS bundle is not available.  PyXB will attempt to
dynamically retrieve the referenced schemas and build them, but if you
intend to work with this example, please follow the directions in the
opengis bundle directory.
EOText
fi

# This allows this script to run under the autotest environment, where
# output is sent to a file.
export PYTHONIOENCODING='utf-8'

rm fgd_gml.*
# A customized pyxbgen is required to do the translation
./pyxbgen_jp \
   --schema-location=data/shift_jis/FGD_GMLSchema.xsd --module=fgd_gml

# Make sure it worked
python check.py
