# -*- coding: utf-8 -*-

import pyxb.bundles.reqif.driver
import pyxb.bundles.reqif.ReqIF as ReqIF

xml = open('in.xml').read();
doc = ReqIF.CreateFromDocument(xml)
print(doc.THE_HEADER.REQ_IF_HEADER.COMMENT)
