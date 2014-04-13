# Launch all unit tests and doc test in this script with code coverage:
# nosetests indev.py --with-coverage --cover-html --with-doctest --cover-package indev --cover-branches --cover-erase -v
"""
"""
import os
import unittest
import os.path as op
#import numpy as np

#import matplotlib.pyplot as plt
import shutil

import pyhrf

rx_py_identifier = '[^\d\W]\w*'

class Test(unittest.TestCase):

    def setUp(self,):
        self.tmp_dir = pyhrf.get_tmp_path()

    def tearDown(self):
       shutil.rmtree(self.tmp_dir)

    def _create_tmp_files(self, fns):
        for fn in [op.join(self.tmp_dir,fn) for fn in fns]:
            d = op.dirname(fn)
            if not op.exists(d):
                os.makedirs(d)
            open(fn, 'a').close()

    def assert_file_exists(self, fn):
        if not op.exists(fn):
            raise Exception('File %s does not exist' %fn)


if __name__ == '__main__':
    unittest.main()       
