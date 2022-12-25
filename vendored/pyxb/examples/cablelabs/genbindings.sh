# Note: Module order is in increasing dependency order so schema are
# downloaded and saved only once.
[ -f cablelabs.wxs ] \
 || pyxbgen \
   --module-prefix=cablelabs \
   --archive-to-file=cablelabs.wxs \
   --uri-content-archive-directory=schemas \
   -m core -u http://www.cablelabs.com/projects/metadata/specifications/xml_schemas/MD-SP-CORE-I01.xsd \
   -m content -u http://www.cablelabs.com/projects/metadata/specifications/xml_schemas/MD-SP-CONTENT-I01.xsd \
   -m offer -u http://www.cablelabs.com/projects/metadata/specifications/xml_schemas/MD-SP-OFFER-I01.xsd \
   -m terms -u http://www.cablelabs.com/projects/metadata/specifications/xml_schemas/MD-SP-TERMS-I01.xsd \
   -m title -u http://www.cablelabs.com/projects/metadata/specifications/xml_schemas/MD-SP-TITLE-I01.xsd \
   -m vod30 -u http://www.cablelabs.com/projects/metadata/specifications/xml_schemas/MD-SP-VODContainer-I01.xsd

# Generate the custom bindings for the extension capability
pyxbgen \
  --archive-path=.:+ \
  -u custom.xsd -m custom
