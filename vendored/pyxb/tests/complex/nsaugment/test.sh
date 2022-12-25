PYXB_ARCHIVE_PATH=.
export PYXB_ARCHIVE_PATH

test_name=${0}

fail () {
  echo 1>&2 "${test_name} FAILED: ${@}"
  exit 1
}

rm -f *.wxs *.wxs- *.pyc common.py _common.py app.py

pyxbgen \
  --schema-location=common.xsd --module=common \
  --archive-to-file=common.wxs || fail cannot generate common schema

#pyxbdump common.wxs

python tst-common.py || fail common binding test

echo '**************************'

pyxbgen \
  --schema-location=app.xsd --module=app > bad.log 2>&1 \
  && fail unexpected success processing unaugmented import
grep -q 'Unable to locate element referenced by {urn:common}app' bad.log || fail missing diagnostic for bad unaugmented import

pyxbgen \
  --import-augmentable-namespace=urn:common \
  --schema-location=app.xsd --module=app > bad.log 2>&1 \
  || fail unable to generate app-augmented bindings

python tst-app.py || fail app-augmented bindings test

echo "nsaugment TESTS PASSED"
