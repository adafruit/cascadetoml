Introduction
============

[![Discord](https://img.shields.io/discord/327254708534116352.svg)](https://adafru.it/discord)
[![Build Status](https://github.com/adafruit/cascadetoml/workflows/Build%20CI/badge.svg)](https://github.com/adafruit/cascadetoml/actions)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Command for cascading toml "databases" into their full objects

TOML cascades are file trees that define generic configuration. Cascading allows
for shared setting to be set in one place.

The root of a cascade has two files that define it:

* `.cascade.toml` defines settings for `cascadetoml`. Settings are:
  * `paths` a list of strings where each string is a python format-style string. These strings are used to pull out setting defined by the path.
* `<type>.template.toml` defines the full structure of the resulting TOML object. `<type>` is used as the name for the array of tables output when a cascade results in multiple objects. The keys in the table are the only ones allowed in TOML files within the tree. The types of values must also be consistent.

Settings for a particular folder are in a TOML file with the folder name plus the `.toml` extension.

The first repo using this is the
[`nvm.toml`](https://github.com/adafruit/nvm.toml) repo. Its only path is `{technology}/{manufacturer}/{sku}.toml`. A file such as `flash/gigadevice/GD1.toml` will have the implicit values:

```toml
technology = "flash"
manufacturer = "gigadevice"
sku = "GD1"
```

All of the other values come from these files in order:

* `flash/flash.toml`
* `flash/gigadevice/gigadevice.toml`
* `flash/gigadevice/GD1.toml`

No key may exist at multiple levels.

`cascadetoml check` can be used to validate much of this.

Installing from PyPI
=====================

To install for current user:

```shell
pip3 install cascadetoml
```

To install system-wide (this may be required in some cases):

```shell
sudo pip3 install cascadetoml
```

To install in a virtual environment in your current project:

```shell
mkdir project-name && cd project-name
python3 -m venv .env
source .env/bin/activate
pip3 install cascadetoml
```

Installing for development
==========================

`cascadetoml` uses [flit]() for packaging. To install a development copy into your current venv do:

  flit install -s --deps develop

After install, you simply edit the files in place and the venv will use the source files directly.

Contributing
============

Contributions are welcome! Please read our [Code of Conduct](https://github.com/adafruit/Adafruit_CircuitPython_cascadetoml/blob/main/CODE_OF_CONDUCT.md)
before contributing to help this project stay welcoming.

Documentation
=============

For information on building library documentation, please check out
[this guide](https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/sharing-our-docs-on-readthedocs#sphinx-5-1).
