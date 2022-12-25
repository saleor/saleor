pyxbgen \
   -u base.xsd -m base \
   -u absent.xsd -m absent
python check.py
