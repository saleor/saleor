Customizing CSS and JavaScript
==============================

All static assets live in subdirectories of ``/saleor/static/``.

Stylesheets are written in `Sass <http://sass-lang.com/>`_ and rely on `postcss <http://postcss.org/>`_ and `autoprefixer <https://autoprefixer.github.io/>`_ for cross-browser compatibility.

JavaScript code is written according to the ES2015 standard and relies on `Babel <https://babeljs.io/>`_ for transpilation and browser-specific polyfills.

Everything is compiled together using `webpack module bundler <https://webpack.github.io/>`_.

The resulting files are written to ``/saleor/static/assets/`` and should not be edited manually.

During development it's very convenient to have webpack automatically track changes made locally.
This will also enable *source maps* that are extremely helpful when debugging.

To run webpack in *watch* mode run:

.. code-block:: bash

    $ npm start

.. warning::

    Files produced this way are not ready for production use.
    To prepare static assets for deployment run:

    .. code-block:: bash

        $ npm run build-assets --production
