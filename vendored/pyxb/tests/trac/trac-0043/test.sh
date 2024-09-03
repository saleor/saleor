pyxbgen \
  --schema-location=a.xsd --module=A \
  --schema-location=b.xsd --module=B \
|| exit 1

python tst-1.py || exit 1

python tst-2.py || exit 1

echo Trac32 tests passed
