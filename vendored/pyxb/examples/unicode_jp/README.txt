This directory contains an example of processing Unicode XML, where both the
schemas and the documents are in various encodings.  It derives from the
PyXB ticket: http://sourceforge.net/p/pyxb/tickets/139

The files in the data subdirectory include a schema and a sample document,
in each of the encodings shift_jis, euc-jp, iso-2022-jp, and utf-8.  The
original format is shift_jis, and is available from
http://fgd.gsi.go.jp/download/.  The other formats were converted from the
shift_jis version by Hiroaki Itoh.

The domain appears to be Japanese extensions to the OpenGIS GML
infrastructure.  Two issues are addressed in the example:

* The inability of expat-based parsers to properly process documents using
  the iso-2022-jp encoding; and

* The desire to not strip out all non-identifier characters in the schema,
  which would result in every element/type/attribute being named
  "emptyString_#" for different values of #.

PyXB has features to work around both of these issues, but the pyxbgen
wrapper script does not provide a way to enable the features.  This example
shows a modified pyxbgen, with irrelevant WSDL code removed, which enables
the use of LibXML2 as an XML reader and implements a solution to
transliterate Kanji/Katakana/Hiragana Unicode characters into romaji.

Note that this transliteration requires installation of:

* the Python bindings for libxml2, which should be available for Linux systems
  from your vendor: e.g., on Fedora 16, the packages are:

  libxml2-2.7.8-6.fc16.x86_64
  libxml2-python-2.7.8-6.fc16.x86_64

  For Ubuntu you need:

  sudo apt-get install python-libxml2

* the Python bindings for MeCab and the corresponding UTF-8 encoding of
  IPADIC, which should be available for Linux systems from your vendor:
  e.g., on Fedora 16, the packages are:

  mecab-jumandic-5.1.20070304-5.fc15.x86_64
  mecab-jumandic-EUCJP-5.1.20070304-5.fc15.x86_64
  mecab-ipadic-2.7.0.20070801-4.fc15.1.x86_64
  mecab-0.98-1.fc15.x86_64
  python-mecab-0.98-2.fc15.x86_64
  mecab-ipadic-EUCJP-2.7.0.20070801-4.fc15.1.x86_64

  For Ubuntu you need:

  sudo apt-get install python-mecab mecab-ipadic-utf8

* The Python port of the Ruby/RomKan utility, available through
  http://lilyx.net/python-romkan/

If the latter two of these are missing, the generator will emit a warning
and proceed without transliteration.  If libxml2 is not available to python,
the test will abort.

The check.py program is a standard unit test which verifies that the
generated bindings can process documents in all four encodings, and shows
how Python code which itself uses the Shift_JIS encoding can interact with
the bindings.

Many thanks to Hiroaki Itoh for providing the schemas, example document, and
romanization code.

Note: Because the package depends on OpenGIS, and OpenGIS bindings are no
longer provided in the PyXB distribution, you should generate these bindings
first.  If they are missing, the test script will emit a warning and PyXB
will download and build them for you, but that is the wrong way to use
OpenGIS.  See the README.txt in the pyxb/bundles/opengis directory.
