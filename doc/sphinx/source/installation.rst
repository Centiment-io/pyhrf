.. _installation:

.. format of titles:

   =====
   lvl 1
   =====

   lvl2
   ####

   lvl3
   ****

   lvl4
   ====

   lvl5
   ----


==============
 Installation
==============

Instructions are given for linux and python2.6. The package is mainly developed and tested under ubuntu (>10.04), we then recommend this distribution.

For **windows users**, a linux distribution can be installed easely inside a virtual machine such as Virtual Box. This wiki page explains `how to install ubuntu from scratch in Virtual Box <http://www.wikihow.com/Install-Ubuntu-on-VirtualBox>`_ or you can get some `free VirtualBox images <http://virtualboxes.org/images/ubuntu/>`_.

**Requirements / Dependencies**
###############################

Dependencies are:
    - `python <http://www.python.org>`_ 2.5, 2.6 or 2.7 **with development headers**
    - `numpy <http://docs.scipy.org/doc/numpy/user/install.html>`_ >= 1.0
    - `scipy <http://www.scipy.org/install.html>`_ >= 0.7
    - `PyXML <http://pyxml.sourceforge.net/topics/index.html>`_ >= 0.8.4
    - `nibabel <http://nipy.sourceforge.net/nibabel/>`_
    - `nipy <http://nipy.sourceforge.net/nipy/stable/users/installation.html>`_
    - `matplotlib <http://matplotlib.org/users/installing.html>`_ 

Optional dependencies:
    - PyQt4 (viewer)


It is advised to install python (with development headers) and all above-mentioned dependencies through distribution tools such as apt-get or urpmi. Eg, for a Debian-based linux::

    sudo apt-get install python-dev python-numpy python-scipy python-matplotlib python-nibabel python-nipy

The pyhrf installation process relies on distribute (overlay of distutils), 
therefore all python dependencies (numpy, scipy, PyXML, matplotlib,
PyQt, nipy, nibabel) should be "egg installed". 
Python packages installed by the
linux distribution might not compatible with the setuptools egg system. Special installation locations can be added to the ``'setup.cfg'`` file at the root directory of the pyhrf decompressed tarball. Simply append a line such as:
``site-dirs=/path/to/installed/package``

If dependencies are not found on the system, the installation process tries to download (therefore needing an internet connection), compile and install them
automatically. For the compilation step, the following dependencies are
required:

     - gcc
     - fortran 95 compiler

**PyHRF download**
##################

PyHRF is distributed in two parts:

     `pyhrf-free <http://www.pyhrf.org/dist/pyhrf-0.2.tar.gz>`_
                  This part is under the CeCILL v2 licence and contains the core algorithms and
                  commands. Note that this part is independent from the other.
     
     `pyhrf-gpl <http://www.pyhrf.org/dist/pyhrf-gpl-0.2.tar.gz>`_
                  This part depends on pyhrf-free and is under the GPL licence. It mainly
                  provides GUIs: PyHRF's viewer and XML editor.                  


Source repository
*****************

The indev version of pyhrf is available via SVN with the following login: *brainvisa* and password: *Soma2009*. In the same way as the package distribution, it comes in two parts, which can be retrieved with following commands:
    
     pyhrf-free::

         svn co https://bioproj.extra.cea.fr/neurosvn/brainvisa/pyhrf/pyhrf-free/trunk pyhrf-free_trunk

     pyhrf-gpl::
         
         svn co https://bioproj.extra.cea.fr/neurosvn/brainvisa/pyhrf/pyhrf-gpl/trunk pyhrf-gpl_trunk
     

                  
.. _Pyhrf installation:

**PyHRF Installation**
######################

In the directory where the pyhrf tarball has been decompressed, you can install it globally or locally:

- global installation::

     $python setup.py install 
    
 This will attempt to write in the Python site-packages directory and will fail if you don't have the appropriate permissions (you usually need root privilege).
    
- local installation::

     $python setup.py install --prefix=/local/installation/path/

 Note: /local/installation/path/lib/python2.x/site-packages must exist and be in your ``PYTHONPATH`` environment variable. Pyhrf executables will be installed in /local/installation/bin/ and the latter should then be in the ``PATH`` environment variable.


*** Run tests to check installation**::

    pyhrf_maketests

*** Develop mode:**

Installation in development mode (only links to the source files are installed)::

        $python setup.py develop --prefix=/local/installation/path/

*** Install all in-dev features  (maybe unstable) ***

If one wants to install all in-dev features::

        $PYHRF_DEV=1 python setup.py develop --prefix=/local/installation/path/


**Configuration**
#################

Package options are stored in $HOME/.pyhrf/config.cfg, which is created after the installation. It handles global package options and the setup of parallel processing. Here is the default content of this file (section order may change)::

    [parallel-cluster]
    server_id = None
    server = None
    user = None
    remote_path = None
    
    [parallel-local]
    niceness = 10
    nb_procs = 1
    
    [global]
    write_texture_minf = False
    tmp_prefix = pyhrftmp
    verbosity = 0
    tmp_path = /tmp/
    use_mode = enduser
    spm_path = None
    
    [parallel-LAN]
    remote_host = None
    niceness = 10
    hosts = /home/tom/.pyhrf/hosts_LAN
    user = None
    remote_path = None
    

In the **global** section, parameters are used for:

   * *tmp_path*: path where to store temporary data
   * *tmp_prefix*: label used for temporary folders
   * *use_mode* (enduser/devel): define the user level. 'enduser' implies simpler and ready-to-use default configuration steps. 'devel' enables all in-dev features and provides default configurations mainly used for testing. 
   * *write_texture_minf* (True/False): enables writing extra header information in a minf file for texture output (Brainvisa format).

All **parallel-XXX** sections concern an in-dev feature which enables distributed analyses across machines in a local network or on a multi-cores cluster. This is not yet documented (but soon will be ...).

.. see :ref:`Parallel Computation <manual_parallel>`

.. 
   ** Installation from source
   
   
   bashrc : 
   export PYTHONPATH=/local/lib/site-pacakges ...
   export PATH=$HOMELOCAL/bin/:$PATH
   mkdir -p /local/lib/site ...
   
   grab nibabel
   easy-install --prefix=~/local nibabel
   
   sympy (dep of nipy): issue easy_install installs ver python3.2 rather than py2.7
   -> grab a tarball
   untargz
   python setup.py install --prefix=~/local
   
   easy_install --prefix=~/local nipy
   is direcoty issue -> grab tarball, uncompress, python setup.py install ...
   install may not work, try develop
   
   
   Grab sources of pyhrf:
   
   login: brainvisa
   password: Soma2009
   svn co https://bioproj.extra.cea.fr/neurosvn/brainvisa/pyhrf/pyhrf-free/trunk pyhrf-free_trunk
   
   svn co https://bioproj.extra.cea.fr/neurosvn/brainvisa/pyhrf/pyhrf-free/trunk pyhrf-gpl_trunk
   
   
   cd pyhrf-free_trunk
   python setup.py develop --prefix ...
   #TODO: remove import of pyhrf at the end or remove creating tmp path at import
