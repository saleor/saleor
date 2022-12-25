# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import sys
import pyxb.binding.generate
import pyxb.utils.domutils


xmls = '''<?xml version="1.0"?>
<Signature xmlns="http://www.w3.org/2000/09/xmldsig#">
  <SignedInfo>
    <CanonicalizationMethod Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/>
    <SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1"/>
    <Reference URI="#_53cdd0e9-bd51-4a49-8519-f711860c5499">
      <Transforms>
        <Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/>
        <Transform Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#">
          <InclusiveNamespaces xmlns="http://www.w3.org/2001/10/xml-exc-c14n#" PrefixList="#default samlp saml ds xs xsi"/>
        </Transform>
      </Transforms>
      <DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"/>
      <DigestValue>4OXjC8LT68JYyCVbtKJims+qe4U=</DigestValue>
    </Reference>
  </SignedInfo>
  <SignatureValue>vG+UCB9C3T8k91yDP2zCvKNHJbp+P1aik9xckByr43y5V5BZktzOF9h4FC8C3mYklg/jTtzWiN4TvAd+wrznpOYDBv3/AseHM+LWG2Q/0t1o8owiliR1z8BqydQUXPuwTSTrPAzEmYFKnq+OQvtq8GiebfYHD2nTKc4M0B8//TuQ295WLwX06RXiuNxGN9C1YvMOL/hHKybPeiVbT7I0wnUMDjf4H/K+4hnCZY2wT+nOBf0fRVkFud/0/lIxCu8T3SMQeSzMRXcdK0FiElFNzh24DJerVwIIZTFXl5Qg42S2Is6kFs1KR0CYDXR/ZVNF5CdVY/xe62t8GUYbTHAoBw==</SignatureValue>
</Signature>'''

import unittest

class TestTrac0123 (unittest.TestCase):
    def testEmpty (self):
        try:
            import pyxb.bundles.wssplat.ds as dsig
        except ImportError as e:
            _log.warning('%s: skipping test, error importing dsig', __file__)
            return
        # The warning that InclusiveNamespaces could not be converted
        # is correct.  We don't have bindings for
        # http://www.w3.org/2001/10/xml-exc-c14n#.  We're going to
        # leave it that way for now, as evidence the warning is still
        # present.
        instance = dsig.CreateFromDocument(xmls)
        # Problem was the PrefixList attribute in InclusiveNamespaces,
        # which has no namespace; deepClone couldn't handle it.  Show
        # that it can.
        dom = instance.toDOM()

if __name__ == '__main__':
    unittest.main()
