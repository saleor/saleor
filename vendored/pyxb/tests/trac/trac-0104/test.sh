#!/bin/sh

rm -rf modules

pyxbgen \
  --module-prefix=com.example.pyxb \
  --binding-root=modules --schema-root=XSD \
  --schema-location=ModelA/AA.xsd --module=ModelA.AA \
  --schema-location=ModelB/BB.xsd --module=ModelB.BB \
&& python tryload.py \
&& echo "trac104 passed" \
|| ( echo "trac104 FAILED" ; exit 1)
