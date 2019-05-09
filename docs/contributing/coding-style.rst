Coding Style
============


Python
------

Always follow `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_ but keep in mind that consistency is important.

The only difference with ``PEP 8`` is that we use a 88 characters line limit instead of 79.

String Literals
~~~~~~~~~~~~~~~

Prefer double quotes to single quotes.

Wrapping Code
~~~~~~~~~~~~~

When wrapping code follow the "vertical hanging indent" format:

.. code-block:: python

   some_dict = {
       'one': 1,
       'two': 2,
       'three': 3,
   }

.. code-block:: python

   some_list = [
       'foo',
       'bar',
       'baz',
   ]

.. code-block:: python

   this_is_wrong = {
      'one': 1,
      'two': 2,
      'three': 3}

Please break multi-line code immediately after the parenthesis and avoid relying on a precise number of spaces for alignment:

.. code-block:: python

   also_wrong('this is hard',
              'to maintain',
              'as it often needs to be realigned')

Linters
~~~~~~~

Use `black <https://github.com/python/black/>`_ to make sure your code is correctly formatted.

Use `isort <https://github.com/timothycrosley/isort>`_ to maintain consistent imports.

Use `pylint <https://www.pylint.org/>`_ with the ``pylint-django`` plugin to catch errors in your code.

Use `pycodestyle <http://pycodestyle.pycqa.org/en/latest/>`_ to make sure your code adheres to PEP 8.

Use `pydocstyle <http://pydocstyle.pycqa.org/en/latest/>`_ to check that your docstrings are properly formatted.

Saleor uses various tools to maintain a common coding style and help with development. To install all the development tools do:

.. code-block:: console

  $ python -m pip install -r requirements_dev.txt``

or if using ``pipenv``:

.. code-block:: console

  $ pipenv install --dev

Saleor uses the `pre-commit <https://pre-commit.com/#install>`_ tool to check and
automatically fix any formatting issue before creating a git commit.

Run the following command to install pre-commit into your git hooks and have it run on every commit:

.. code-block:: console

  $ pre-commit install

If you want more information on how it works, you can refer to the ``.pre-commit-config.yaml``
configuration file.
