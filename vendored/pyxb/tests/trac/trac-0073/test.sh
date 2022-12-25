pyxbgen \
  --archive-to-file base.wxs \
  --schema-location base.xsd --module base

pyxbgen \
  --archive-path '.:+' \
  --schema-location profile.xsd --module profile

python check.py
