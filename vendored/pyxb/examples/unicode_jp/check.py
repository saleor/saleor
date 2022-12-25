# -*- coding: shift_jis -*-
#
# Validate the Japanese GML bindings

from __future__ import print_function, unicode_literals
import os.path
import pyxb.utils.saxutils
import fgd_gml
import unittest

# Need this to override parse from default expat, which can't handle
# Japanese encodings.  libxml2 can.  It is not necessary to explicitly
# reference libxml2 anywhere else, although this test does so to ensure
# the test doesn't fail just because libxml2 is not installed.
pyxb.utils.saxutils.SetCreateParserModules(['drv_libxml2'])

class ExampleUnicode_JP (unittest.TestCase):

    def tryit (self, path):
        # Make sure we find the files, for tests where we are not
        # in the examples/unicode_jp directory
        path = os.path.join(os.path.dirname(__file__), path)
        xmls = open(path).read()
        instance = fgd_gml.CreateFromDocument(xmls)
        for name in instance.name:
            return name.value()
        return None

    shortPass = False
    def setUp (self):
        try:
            import drv_libxml2
        except ImportError:
            print('WARNING: libxml2 not installed, test not valid')
            self.shortPass = True
            return
        self.shift_jis = self.tryit('data/shift_jis/FG-GML-13-RailCL25000-20080331-0001.xml')

    def testISO_2022_JP (self):
        if not self.shortPass:
            name = self.tryit('data/iso-2022-jp/FG-GML-13-RailCL25000-20080331-0001.xml')
            self.assertEqual(self.shift_jis, name)

    def testEUC_JP (self):
        if not self.shortPass:
            name = self.tryit('data/euc-jp/FG-GML-13-RailCL25000-20080331-0001.xml')
            self.assertEqual(self.shift_jis, name)

    def testUTF_8 (self):
        if not self.shortPass:
            name = self.tryit('data/utf-8/FG-GML-13-RailCL25000-20080331-0001.xml')
            self.assertEqual(self.shift_jis, name)

    def testTransliteration (self):
        instance = fgd_gml.hyouji_kubun_rekkyo_gata('表示')
        self.assertEqual(instance, fgd_gml.hyouji_kubun_rekkyo_gata.hyouji)

if __name__ == '__main__':
    unittest.main()
