#!/bin/sh

failure () {
  echo "Failed: ${@}"
  exit 1
}

python demo.py || exit 1

SCHEMAS_OPENGIS_NET=${SCHEMAS_OPENGIS_NET:-${PYXB_ROOT}/pyxb/bundles/opengis/schemas}

if test -d "${SCHEMAS_OPENGIS_NET}" ; then
  echo "testing nothingness"
  # sosRegisterSensor.xml uses tml:tcfTrigger, but the element is really named tml:cfTrigger
  # Skip testing it since it will fail to validate thereby confusing the viewer.
  ls ${SCHEMAS_OPENGIS_NET}/sos/1.0.0/examples/*.xml \
    | grep -v sosRegisterSensor \
    | xargs python check_sos.py \
  || exit 1
  # The SOAP versions are irrelevant for this purpose;
  # 53_wpsExecute_request_ComplexValue references a custom binding
  # that hasn't been built because it isn't in OpenGIS.
  ls ${SCHEMAS_OPENGIS_NET}/wps/1.0.0/examples/*.xml \
    | sed -e '/SOAP/d' -e '/^53_/d' \
    | xargs python check_wps.py \
  || exit 1
  ls ${SCHEMAS_OPENGIS_NET}/oseo/1.0/SampleMessages/*.xml \
    | xargs python check_oseo.py \
  || exit 1

else
  echo 1>&2 "WARNING: Need SCHEMAS_OPENGIS_NET defined to test example documents"
fi

rm -f gmlapp.py* raw/gmlapp.py*
PYXB_ARCHIVE_PATH='&pyxb/bundles/opengis//:&pyxb/bundles/common//'
export PYXB_ARCHIVE_PATH
pyxbgen \
  --schema-location=gmlapp.xsd --module=gmlapp \
  --write-for-customization
python testgml.py || exit 1
