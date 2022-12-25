PYTHONPATH=../..
export PYTHONPATH
rm -rf raw
mkdir -p raw
touch raw/__init__.py
../../scripts/pyxbgen \
  -u ipo.xsd \
  -m ipo \
  -r


