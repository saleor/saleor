Coding Style
============


Python
------

Always follow `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_ but keep in mind that consistency is important.

String Literals
~~~~~~~~~~~~~~~

Prefer single quotes to double quotes unless the string itself contains single quotes that would need to be needlessly escaped.

Wrapping Code
~~~~~~~~~~~~~

When wrapping code follow the "hanging grid" format:

.. code-block:: python

   some_dict = {
       'one': 1,
       'two': 2,
       'three': 3}

.. code-block:: python

   some_list = [
       'foo', 'bar', 'baz']

Python is an indent-based language and we believe that beautiful, readable code is more important than saving a single line of ``git diff``. Please avoid dangling parentheses, brackets, square brackets or hanging commas even if the Django project seems to encourage this programming style:

.. code-block:: python

   this_is_wrong = {
      'one': 1,
      'two': 2,
      'three': 3,
   }

Please break multi-line code immediately after the parenthesis and avoid relying on a precise number of spaces for alignment:

.. code-block:: python

   also_wrong('this is hard',
              'to maintain',
              'as it often needs to be realigned')

Linters
~~~~~~~

Use `isort <https://github.com/timothycrosley/isort>`_ to maintain consistent imports.

Use `pylint <https://www.pylint.org/>`_ with the ``pylint-django`` plugin to catch errors in your code.

Use `pycodestyle <http://pycodestyle.pycqa.org/en/latest/>`_ to make sure your code adheres to PEP 8.

Use `pydocstyle <http://pydocstyle.pycqa.org/en/latest/>`_ to check that your docstrings are properly formatted.
