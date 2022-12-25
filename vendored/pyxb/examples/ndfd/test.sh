PYXB_ARCHIVE_PATH="&pyxb/bundles/wssplat//"
export PYXB_ARCHIVE_PATH
sh genbindings.sh \
  && python showreq.py \
  && python forecast.py
