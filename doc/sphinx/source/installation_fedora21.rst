.. _installation_fedora21:


============================
 Installation for Fedora 21
============================

These instructions are specific to Fedora 21.

Required dependencies
#####################

First, be sure that your system is up-to-date:

.. code:: bash

    $ sudo yum update

Then install the following packages:

.. code:: bash

    $ sudo yum install python-devel numpy scipy python-matplotlib python-pip sympy gcc

These dependencies are not available as system packages, they have to be installed
by hand ::

    $ pip install --user nibabel
    $ pip install --user nipy

Optional dependencies
#####################

Install the following packages:

.. code:: bash

    $ sudo yum install graphviz-python python-sphinx python-scikit-learn python-pillow python-joblib python-paramiko
    $ pip install --user munkres

If you plan to use our specific viewer (pyhrf_viewer), run:

.. code:: bash

    $ sudo yum install PyQt4 python-matplotlib-qt4 

.. include:: pyhrf_installation.rst
