<h1 align='center'>SRAM Platform</h1>

<h3 align='center'>Platform for Acquisition of SRAM-based 
PUFs from Micro-Controllers</h3>

[![License: GPL v2](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)

## Introduction


## Usage

First, download the repository

```console
$ git clone http://servinagrero/SRAM-Platform.git && cd SRAM-Platform
```

After that, copy the cofiguration template file and edit it.

```
$ cp config_template.toml config.toml
```

Now the station can be deployed with
```
$ python3 src/main.py
```


This platform has only been tested on linux, but it should work on both Windows and Mac. If you find any error, feel free to open an issue.

## Requirements

To run this project, python-3.X needs to be installed. The list of dependencies for the project can be found in the file `requirements.txt` and installed in the following manner. It is recommended to install the dependencies in a virtual environment.

```console
$ python3 -m venv platform-env
```

To activate the virtual environment

```console
$ source platform-env/bin/activate
```

And lastly, to install the dependencies

```console
$ pip -r install requirements.txt
```

## Documentation

The documentation for the project can be found in the `docs` folder. To build the documentation, sphinx should be installed.


