rm -rf bindings
mkdir bindings

PYXB_ARCHIVE_PATH='bindings'
export PYXB_ARCHIVE_PATH

pyxbgen \
  --schema-location=../schemas/shared-types.xsd --module=st \
  --module-prefix=bindings \
  --archive-to-file=bindings/st.wxs \
 && pyxbgen \
  --schema-location=../schemas/test-external.xsd --module=te \
  --module-prefix=bindings \
  --archive-to-file=bindings/te.wxs \
 && python tst-stored.py \
 && echo "test-stored TESTS PASSED" \
|| ( echo "test-stored FAILED" ; exit 1 )
