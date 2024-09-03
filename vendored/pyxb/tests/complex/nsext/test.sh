PYXB_ARCHIVE_PATH=.
export PYXB_ARCHIVE_PATH

test_name=${0}

fail () {
  echo 1>&2 "${test_name} FAILED: ${@}"
  exit 1
}

# cat >/dev/null <<EOT

rm -f *.wxs *.wxs- *.pyc common.py common4app.py app.py

pyxbgen \
  --schema-location=base.xsd --module=common \
  --archive-to-file=common.wxs || fail cannot generate base schema

#pyxbdump common.wxs
python tst-base.py || fail base binding test

echo '**************************'

pyxbgen \
  --schema-location=extend.xsd --module=common4app \
  --archive-to-file=common4app.wxs || fail bindings for extended

# pyxbdump common4app.wxs
python tst-extend.py || exit 1

# Use this to verify dependency checking
mv common.wxs common.wxs-
pyxbgen \
  --schema-location=app.xsd --module=app > bad.log 2>&1 \
  && ( echo "Succeeded bad conversion" ; exit 1 )
grep -q 'common4app.wxs: archive depends on unavailable archive' bad.log || exit 1

mv common.wxs- common.wxs
pyxbgen \
  --schema-location=app.xsd --module=app \
  || ( echo "Failed application schema" ; exit 1 )

python tst-app.py || exit 1

echo "nsext TESTS PASSED"
