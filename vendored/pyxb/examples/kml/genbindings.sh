PYTHONPATH=../..
export PYTHONPATH

URI='http://schemas.opengis.net/kml/2.2.0/ogckml22.xsd'
PREFIX='ogckml'

rm -rf raw
mkdir -p raw
touch raw/__init__.py

# Hack until we get relative URI handling into the import routine
../../scripts/pyxbgen \
   -u 'http://schemas.opengis.net/kml/2.2.0/atom-author-link.xsd' \
   -m atom \
   -r -C
../../scripts/pyxbgen \
   -u 'http://docs.oasis-open.org/election/external/xAL.xsd' \
   -m xAL \
   -r -C

PYXB_ARCHIVE_PATH='raw:+'
export PYXB_ARCHIVE_PATH

# NB: If you add -C to this, Python will blow up from the bug about
# pickling heavily recursive structures.  Fortunately, we don't need
# the content model.
../../scripts/pyxbgen \
   -u "${URI}" \
   -m "${PREFIX}" \
   -r

# Except that we do need the content model for Google's extensions.
# So this one has to be disabled.
#../../scripts/pyxbgen \
#   -u 'http://code.google.com/apis/kml/schema/kml22gx' \
#   -p gx \
#   -r

for f in atom xAL ${PREFIX} gx ; do
  if [ ! -f ${f}.py ] ; then
    echo "from raw.${f} import *" > ${f}.py
  fi
done
