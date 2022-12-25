test_name=trac/184

fail () {
  echo 1>&2 "${test_name} FAILED: ${@}"
  exit 1
}

rm -rf bindings
mkdir bindings

PYXB_ARCHIVE_PATH='bindings'
export PYXB_ARCHIVE_PATH

pyxbgen \
  --schema-location="s1core.xsd" --module=s1 \
  --module-prefix=bindings \
  --archive-to-file=bindings/s1.wxs \
|| fail s1 generation
pyxbgen \
  --schema-location="s0add.xsd" --module=s0 \
  --module-prefix=bindings \
  --archive-path=.:+ \
|| fail s0 generation
python check.py || fail validation
echo ${test_name} passed
