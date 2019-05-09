Text-Unidecode
==============

.. image:: https://travis-ci.org/kmike/text-unidecode.svg?branch=master
    :target: https://travis-ci.org/kmike/text-unidecode
    :alt: Build Status

text-unidecode is the most basic port of the
`Text::Unidecode <http://search.cpan.org/~sburke/Text-Unidecode-0.04/lib/Text/Unidecode.pm>`_
Perl library.

There are other Python ports of Text::Unidecode (unidecode_
and isounidecode_). unidecode_ is GPL; isounidecode_ uses too much memory,
and it didn't support Python 3 when this package was created.

This port is licensed under `Artistic License`_ and supports Python 2.7 and
3.3+. If you're OK with GPL, use unidecode_ (it has better memory usage and
better transliteration quality).

.. _unidecode: https://pypi.python.org/pypi/Unidecode/
.. _isounidecode: https://pypi.python.org/pypi/isounidecode/
.. _Artistic License: https://opensource.org/licenses/Artistic-Perl-1.0

Installation
------------

::

    pip install text-unidecode

Usage
-----

::

    >>> from text_unidecode import unidecode
    >>> unidecode(u'какой-то текст')
    u'kakoi-to tekst'


