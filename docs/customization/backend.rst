Working with Python Code
========================

Managing Dependencies
---------------------

To guarantee repeatable installations all project dependencies are managed using `pip-tools <https://github.com/nvie/pip-tools>`_.
Project's direct dependencies are listed in ``requirements.in`` and running :code:`pip-compile` generates ``requirements.txt`` that has all versions pinned.

We recommend you use this workflow and keep ``requirements.txt`` under version control to make sure all computers and environments run exactly the same code.


