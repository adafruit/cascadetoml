Introduction
============

.. image:: https://img.shields.io/discord/327254708534116352.svg
    :target: https://adafru.it/discord
    :alt: Discord


.. image:: https://github.com/adafruit/cascadetoml/workflows/Build%20CI/badge.svg
    :target: https://github.com/adafruit/cascadetoml/actions
    :alt: Build Status


.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: Code Style: Black

Command for cascading toml "databases" into their full objects

TOML cascades are file trees that define generic configuration. Cascading allows
for shared setting to be set in one place. The first repo using this is the
[`nvm.toml`]() repo.


Installing from PyPI
=====================

To install for current user:

.. code-block:: shell

    pip3 install cascadetoml

To install system-wide (this may be required in some cases):

.. code-block:: shell

    sudo pip3 install cascadetoml

To install in a virtual environment in your current project:

.. code-block:: shell

    mkdir project-name && cd project-name
    python3 -m venv .env
    source .env/bin/activate
    pip3 install cascadetoml

Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/adafruit/Adafruit_CircuitPython_cascadetoml/blob/main/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.

Documentation
=============

For information on building library documentation, please check out
`this guide <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/sharing-our-docs-on-readthedocs#sphinx-5-1>`_.
