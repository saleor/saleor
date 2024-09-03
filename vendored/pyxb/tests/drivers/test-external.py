# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
from pyxb.utils import six
from xml.dom import Node
import pyxb.namespace
import sys
import imp

import os.path

te_generator = pyxb.binding.generate.Generator(allow_absent_module=True, generate_to_files=False)
te_generator.setSchemaRoot(os.path.realpath('%s/../schemas' % (os.path.dirname(__file__),)))
te_generator.addSchemaLocation('test-external.xsd')

# Create a module into which we'll stick the shared types bindings.
# Put it into the sys modules so the import directive in subsequent
# code is resolved.
st = imp.new_module('st')
sys.modules['st'] = st

# Now get the code for the shared types bindings, and evaluate it
# within the new module.

st_generator = pyxb.binding.generate.Generator(allow_absent_module=True, generate_to_files=False)
st_generator.setSchemaRoot(os.path.realpath('%s/../schemas' % (os.path.dirname(__file__),)))
st_generator.addSchemaLocation('shared-types.xsd')

st_modules = st_generator.bindingModules()
assert 1 == len(st_modules)
code = st_modules.pop().moduleContents()
open('st.py', 'w').write(code)
rv = compile(code, 'shared-types', 'exec')
six.exec_(code, st.__dict__)

# Set the path by which we expect to reference the module
stns = pyxb.namespace.NamespaceForURI('URN:shared-types', create_if_missing=True)
module_record = stns.lookupModuleRecordByUID(st_generator.generationUID())
assert module_record is not None, 'Unable to find %s in ns %s' % (st_generator.generationUID(), stns)
module_record.setModulePath('st')

# Now get and build a module that refers to that module.

modules = te_generator.bindingModules()
assert 1 == len(modules)
m = modules.pop()
assert m.namespace() != stns
code = m.moduleContents()
open('te.py', 'w').write(code)
rv = compile(code, 'test-external', 'exec')
eval(rv)

from pyxb.exceptions_ import *

from pyxb.utils import domutils
def ToDOM (instance):
    return instance.toDOM().documentElement

import unittest

class TestExternal (unittest.TestCase):
    def setUp (self):
        self.__basis_log = logging.getLogger('pyxb.binding.basis')
        self.__basis_loglevel = self.__basis_log.level

    def tearDown (self):
        self.__basis_log.level = self.__basis_loglevel

    def testSharedTypes (self):
        self.assertEqual(word.typeDefinition()._ElementMap['from'].elementBinding().typeDefinition(), st.english)
        self.assertEqual(word.typeDefinition()._ElementMap['to'].elementBinding().typeDefinition(), st.welsh)
        one = st.english('one')
        self.assertRaises(SimpleTypeValueError, st.english, 'five')
        # Element constructor without content is error
        self.assertRaises(SimpleTypeValueError, english)
        self.assertEqual('one', english('one'))
        # Element constructor with out-of-range content is error
        self.assertRaises(SimpleTypeValueError, english, 'five')

        xmlt = six.u('<ns1:english xmlns:ns1="URN:test-external">one</ns1:english>')
        xmld = xmlt.encode('utf-8')
        instance = st.CreateFromDocument(xmlt)
        self.assertEqual('one', instance)
        self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)

    def testWords (self):
        xmlt = six.u('<ns1:word xmlns:ns1="URN:test-external"><from>one</from><to>un</to></ns1:word>')
        xmld = xmlt.encode('utf-8')
        instance = CreateFromDocument(xmld)
        self.assertEqual('one', instance.from_)
        self.assertEqual('un', instance.to)
        self.assertEqual(ToDOM(instance).toxml("utf-8"), xmld)

    def testBadWords (self):
        xmlt = six.u('<ns1:word xmlns:ns1="URN:test-external"><from>five</from><to>pump</to></ns1:word>')
        xmld = xmlt.encode('utf-8')
        self.assertRaises(SimpleTypeValueError, CreateFromDocument, xmlt)
        self.assertRaises(SimpleTypeValueError, CreateFromDocument, xmld)

    def testComplexShared (self):
        xmlt = six.u('<ns1:lwords language="english" newlanguage="welsh" xmlns:ns1="URN:test-external">un</ns1:lwords>')
        instance = CreateFromDocument(xmlt)
        self.assertEqual(instance._element(), lwords)
        self.assertTrue(isinstance(instance.value(), st.welsh))
        self.assertEqual('english', instance.language)
        self.assertEqual('welsh', instance.newlanguage)

    def testCrossedRestriction (self):
        # Content model elements that are consistent with parent
        # should share its fields; those that change something should
        # override it.
        self.assertEqual(st.extendedName._ElementMap['title'], restExtName._ElementMap['title'])
        self.assertEqual(st.extendedName._ElementMap['forename'], restExtName._ElementMap['forename'])
        self.assertEqual(st.extendedName._ElementMap['surname'], restExtName._ElementMap['surname'])
        self.assertEqual(st.extendedName._ElementMap['generation'], restExtName._ElementMap['generation'])

        xmlt = six.u('<personName><surname>Smith</surname></personName>')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = st.personName.Factory(_dom_node=dom.documentElement)
        xmlt = six.u('<personName><surname>Smith</surname><generation>Jr.</generation></personName>')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        self.__basis_log.setLevel(logging.ERROR)
        self.assertRaises(UnrecognizedContentError, st.personName.Factory, _dom_node=dom.documentElement)
        self.__basis_log.level = self.__basis_loglevel
        xmlt = xmlt.replace('personName', 'extendedName')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = st.extendedName.Factory(_dom_node=dom.documentElement)
        xmlt = xmlt.replace('extendedName', 'restExtName')
        dom = pyxb.utils.domutils.StringToDOM(xmlt)
        instance = restExtName.Factory(_dom_node=dom.documentElement)

    def testUnionExtension (self):
        e = morewords('one')
        self.assertTrue(isinstance(e, st.english))
        self.assertTrue(uMorewords._IsValidValue(e))
        self.assertEqual(e, st.english.one)
        self.assertEqual(e, uMorewords.one)
        w = morewords('un')
        self.assertTrue(isinstance(w, st.welsh))
        self.assertTrue(uMorewords._IsValidValue(w))
        self.assertEqual(w, st.welsh.un)
        self.assertEqual(w, uMorewords.un)
        n = morewords('ichi')
        self.assertTrue(uMorewords._IsValidValue(n))
        self.assertEqual(n, uMorewords.ichi)

if __name__ == '__main__':
    unittest.main()

import os
try:
    os.unlink('st.py')
    os.unlink('te.py')
except:
    pass
