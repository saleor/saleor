# Download a mirror of the W3C technical archive
#  --backup-converted

wget \
  --recursive \
  --timestamping \
  --level 1 \
  --no-remove-listing \
  --convert-links \
  --html-extension \
  http://www.w3.org/Addressing \
  http://www.w3.org/TR/xmlschema-0 \
  http://www.w3.org/TR/xmlschema-1 \
  http://www.w3.org/TR/xmlschema-2 \
  http://www.w3.org/TR/xmlbase \
  http://www.w3.org/TR/xml-names \
  http://www.w3.org/TR/xml-infoset \
  http://www.w3.org/TR/xml-id \
  http://www.w3.org/TR/XML/Core \
  http://www.w3.org/TR/sawsdl \
  http://www.w3.org/TR/soap \
  http://www.w3.org/TR/ws-addr-core \
  http://www.w3.org/TR/ws-addr-metadata \
  http://www.w3.org/TR/ws-addr-soap \
  http://www.w3.org/TR/wsdl20-primer \
  http://www.w3.org/TR/wsdl20 \
  http://www.w3.org/TR/wsdl20-adjuncts \
  http://www.w3.org/TR/ws-policy \
  http://www.w3.org/TR/ws-policy-attach \
