# Prosolia

**speech features extraction pipeline for prosody analysis**

## Usage

Once installed, prosolia is available as a command-line tool. To get
in, simply have a ``prosolia --help``.

## Installation

* Using the [Anaconda][http://continuum.io/downloads] distribution of
  Python 3 (conda is also available independently of Anaconda with
  ``pip install conda; conda init``):

.. code:: bash

    conda install cffi numpy scipy matplotlib
    python setup.py build
    python setup.py install

* Prosalia relies on the system library ``libsndfile``. On Windows and
  OS X, it is installed automatically. On Linux, you need to install
  libsndfile using your distribution's package manager, for example
  ``sudo apt-get install libsndfile1``.

* Install Kaldi by following the instructions from
  [here](http://kaldi-asr.org/doc/install.html). Basically, you have
  to do (from the `kaldi` directory):

        cd tools
        ./extras/check_dependancies.sh
        make -j 4  # -j N do a parallel build on N CPUs
        cd ../src
        ./configure
        make depend -j 4
        make -j 4

## Licence

**Copyright 2016 Mathieu Bernard**

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
