# -*- coding: utf-8 -*-
from __future__ import print_function
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest

import qq0196 as qq
import qu0196 as qu
import uq0196 as uq
import uu0196 as uu
import mix
from pyxb.utils.domutils import BindingDOMSupport
from pyxb.utils import six

BindingDOMSupport.DeclareNamespace(qq.Namespace, 'qq')
BindingDOMSupport.DeclareNamespace(qu.Namespace, 'qu')
BindingDOMSupport.DeclareNamespace(uq.Namespace, 'uq')
BindingDOMSupport.DeclareNamespace(uu.Namespace, 'uu')
BindingDOMSupport.DeclareNamespace(mix.Namespace, 'mix')

qq_bds = BindingDOMSupport(default_namespace=qq.Namespace)


elt_kw = {
    'te' : 'te',
    'teq' : 'teq',
    'teu' : 'teu',
    'e' : 'e',
    'eq' : 'eq',
    'eu' : 'eu',
    'a' : 'a',
    'aq' : 'aq',
    'au' : 'au',
    'ta' : 'ta',
    'taq' : 'taq',
    'tau' : 'tau' }

qq_i = qq.elt(**elt_kw)
qu_i = qu.elt(**elt_kw)
uq_i = uq.elt(**elt_kw)
uu_i = uu.elt(**elt_kw)

i = mix.elt(qq_i, qu_i, uq_i, uu_i)
try:
    print(i.toDOM().toprettyxml())
except pyxb.ValidationError as e:
    print(e.details())
    raise

i = mix.uue(a='a')
print(i.toxml('utf-8'))

class TestTrac0196 (unittest.TestCase):

    module_map = { qq : ( qq.Namespace, qq.Namespace ),
                   qu : ( qu.Namespace, None ),
                   uq : ( None, uq.Namespace ),
                   uu : ( None, None ) }
    global_a = ( 'a', 'aq', 'au' )
    global_e = ('e', 'eq', 'eu' )
    local_a = ( 'ta', 'taq', 'tau' )
    local_e = ('te', 'teq', 'teu' )

    def testQualified (self):
        # Top-level declarations are qualified regardless of presence/absence of form attribute.
        # Internal declarations follow form attribute or schema default
        for (m, ( efd, afd )) in six.iteritems(self.module_map):
            for (n, d) in six.iteritems(m.t._AttributeMap):
                if n.localName() in ('a', 'au', 'aq'):
                    self.assertEqual(n.namespace(), m.Namespace)
                elif 'taq' == n.localName():
                    self.assertEqual(n.namespace(), m.Namespace)
                elif 'tau' == n.localName():
                    self.assertEqual(n.namespace(), None)
                elif 'ta' == n.localName():
                    self.assertEqual(n.namespace(), afd)
                else:
                    self.assertFalse()
            for (n, d) in six.iteritems(m.t._ElementMap):
                if n.localName() in ('e', 'eu', 'eq'):
                    self.assertEqual(n.namespace(), m.Namespace)
                elif 'teq' == n.localName():
                    self.assertEqual(n.namespace(), m.Namespace)
                elif 'teu' == n.localName():
                    self.assertEqual(n.namespace(), None)
                elif 'te' == n.localName():
                    self.assertEqual(n.namespace(), efd)
                else:
                    self.assertFalse()

if __name__ == '__main__':
    unittest.main()
