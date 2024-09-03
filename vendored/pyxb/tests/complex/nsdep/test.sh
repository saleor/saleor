PYXB_ARCHIVE_PATH=bindings
rm -rf bindings
mkdir -p bindings
touch bindings/__init__.py

pyxbgen \
  --module-prefix=bindings \
  --schema-location=d_c.xsd --module=D \
  --archive-to-file=bindings/D.wxs \
 || exit 1

python tst-a.py || exit 1

python tst-b.py || exit 1

echo nsdep tests passed
