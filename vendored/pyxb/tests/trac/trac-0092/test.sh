rm -rf bindings
mkdir bindings

XSD_DIR=../../schemas
PYXB_ARCHIVE_PATH='bindings'
export PYXB_ARCHIVE_PATH
export PYTHONPATH=${PYTHONPATH:+${PYTHONPATH}:}.

pyxbgen \
  --schema-location=${XSD_DIR}/shared-types.xsd --module=st \
  --module-prefix=bindings \
  --archive-to-file=bindings/st.wxs \
&& pyxbgen \
  --schema-location=${XSD_DIR}/test-external.xsd --module=te \
  --module-prefix=bindings \
  --archive-path=.:+ \
&& python ../../drivers/tst-stored.py \
&& echo "trac92 passed" \
|| ( echo "trac92 FAILED" ; exit 1 )
