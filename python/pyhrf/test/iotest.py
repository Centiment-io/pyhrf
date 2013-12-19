

import unittest
import numpy as _np
import tempfile

import pyhrf
from pyhrf import get_data_file_name
from pyhrf.tools.io import *
from pyhrf.ndarray import MRI3Daxes, MRI4Daxes

import os
import numpy as np

import shutil

from pyhrf.tools.io import *


class NiftiTest(unittest.TestCase):

    def setUp(self):
        tmpDir = tempfile.mkdtemp(prefix='pyhrf_tests',
                                  dir=pyhrf.cfg['global']['tmp_path'])
        self.tmp_dir = tmpDir

    def tearDown(self):
        if 1:
            shutil.rmtree(self.tmp_dir)


    def test_process_history_extension(self):
        nii_fn = pyhrf.get_data_file_name('real_data_vol_4_regions_mask.nii.gz')

        nii_fn_out = op.join(self.tmp_dir, 'proc_ext_test.nii')
        #print 'nii_fn_out:', nii_fn_out
        input_pname = 'dummy_proc_test'
        input_pparams = {'my_param' : 5.5, 'input_file':'/home/blh'}

        append_process_info(nii_fn, input_pname, input_pparams,
                            img_output_fn=nii_fn_out)

        i2,(aff,header) = read_volume(nii_fn_out)
        #print 'Loaded extensions:', header.extensions

        reloaded_pinfo = get_process_info(nii_fn_out)
        self.assertNotEqual(reloaded_pinfo, None)
        self.assertEqual(reloaded_pinfo[0]['process_name'], input_pname)
        self.assertEqual(reloaded_pinfo[0]['process_inputs'], input_pparams)
        self.assertEqual(reloaded_pinfo[0]['process_version'], None)
        self.assertEqual(reloaded_pinfo[0]['process_id'], None)

class DataLoadTest(unittest.TestCase):

    def test_paradigm_csv(self):
        pfn = get_data_file_name('paradigm_loc_av.csv')
        o,d = load_paradigm_from_csv(pfn)
        if 0:
            print 'onsets:'
            print o
            print 'durations:'
            print d


    def test_paradigm_csv2(self):
        pfn = get_data_file_name('paradigm_loc_av.csv')
        o,d = load_paradigm_from_csv(pfn)
        if 0:
            print 'onsets:'
            print o
            print 'durations:'
            print d


    def test_frmi_vol(self):
        """ Test volumic data loading
        """
        boldFn = get_data_file_name('subj0_bold_session0.nii.gz')
        roiMaskFn = get_data_file_name('subj0_parcellation.nii.gz')
        g, b, ss, m, h = load_fmri_vol_data([boldFn, boldFn], roiMaskFn)
        if 0:
            print len(g), g[1]
            print b[1].shape
            print ss
            print m.shape, _np.unique(m)
            print h




class xndarrayIOTest(unittest.TestCase):

    def setUp(self):
        self.cub0 = xndarray(_np.random.rand(10,10))
        self.cub3DVol = xndarray(_np.random.rand(10,10,10),
                               axes_names=MRI3Daxes)
        d4D = _np.zeros((2,2,2,3))
        for c in xrange(3):
            d4D[:,:,:,c] = _np.ones((2,2,2))*(c-2)

        self.cub4DVol = xndarray(d4D, axes_names=['condition']+MRI3Daxes)

        self.cub4DTimeVol = xndarray(_np.random.rand(100,10,10,10),
                               axes_names=['time']+MRI3Daxes)
        self.cubNDVol = xndarray(_np.random.rand(10,2,2,2,3),
                               axes_names=['time']+MRI3Daxes+['condition'],
                               axes_domains={'condition':['audio','video','na']})

        self.tmp_dir = tempfile.mkdtemp(prefix='pyhrf_tests',
                                        dir=pyhrf.cfg['global']['tmp_path'])



    def tearDown(self):
        shutil.rmtree(self.tmp_dir)


    def test_save_nii_3D(self):
        fn = op.join(self.tmp_dir, 'test3D.nii')
        self.cub3DVol.save(fn)

    def test_save_nii_4D(self):
        fn = op.join(self.tmp_dir, 'test4D.nii')
        self.cub4DTimeVol.save(fn)

    def test_save_nii_multi(self):
        c = self.cubNDVol.reorient(MRI4Daxes + ['condition'])
        c.save(op.join(self.tmp_dir, './testND.nii'))

    # def test_cuboid_save_xml(self):
    #     cxml = xndarrayXml.fromxndarray(self.cubNDVol, 'mydata1')
    #     #print pyhrf.xmlio.toXML(cxml,NumpyXMLHandler(),pretty=True)
    #     cxml.cleanFiles()

    # def test_cuboid_load_xml(self):
    #     cxml = xndarrayXml.fromxndarray(self.cub4DVol, 'mydata2')
    #     sxml = pyhrf.xmlio.toXML(cxml, NumpyXMLHandler(),pretty=True)
    #     #print sxml
    #     #print 'loading from xml ...'
    #     c = pyhrf.xmlio.fromXML(sxml, NumpyXMLHandler())
    #     #print 'loaded cuboid:'
    #     #print c.cuboid.descrip()
    #     #print c.cuboid.data
    #     #print 'original cuboid:'
    #     #print self.cub4DVol.descrip()
    #     #print self.cub4DVol.data
    #     cxml.cleanFiles()

    # def test_cuboidND_load_xml(self):
    #     #print 'Creating xmlable cuboid ...'
    #     cxml = xndarrayXml.fromxndarray(self.cubNDVol, 'mydata3')
    #     import cPickle
    #     #cPickle.dump(self.cubNDVol, open('./cubNDVol.pck','w'))
    #     #print 'Converting to XML & dumping data ...'
    #     sxml = pyhrf.xmlio.toXML(cxml, NumpyXMLHandler(),pretty=True)
    #     #print sxml
    #     #print 'loading from xml ...'
    #     c = pyhrf.xmlio.fromXML(sxml, NumpyXMLHandler())
    #     #print 'loaded cuboid:'
    #     #print c.cuboid.descrip()
    #     #cPickle.dump(c.cuboid,open('./cubfromxml.pck','w'))
    #     #print c.cuboid.data
    #     #print 'original cuboid:'
    #     #print self.cubNDVol.descrip()
    #     c.cleanFiles()
    #     #print self.cubNDVol.data

    #     #from ndview import stack_cuboids
    #     #comparxndarray = stack_cuboids([self.cubNDVol,c.cuboid],'case',['orig','xml'])
    #     #cPickle.dump(comparxndarray,open('./cubFromXml.pck','w'))


class FileHandlingTest(unittest.TestCase):

    def setUp(self):

        self.tmp_dir = pyhrf.get_tmp_path()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_split_ext(self):
        bfn = pyhrf.get_data_file_name('subj0_bold_session0.nii.gz')
        split_ext_safe(bfn)
        #print 's:', s

    def test_split4DVol(self):
        s = 'subj0_bold_session0.nii.gz'
        bfn = pyhrf.get_data_file_name(s)
        bold_files = split4DVol(bfn, output_dir=self.tmp_dir)
        #print bold_files
        i,meta = read_volume(bold_files[0])

        if 0:
            affine, header = meta
            print ''
            print 'one vol shape:'
            print i.shape
            print 'header:'
            pprint.pprint(dict(header))

        for bf in bold_files:
            os.remove(bf)


class GiftiTest(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix='pyhrf_tests',
                                        dir=pyhrf.cfg['global']['tmp_path'])

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_read_tex_gii_label(self):
        tex_fn = 'real_data_surf_tiny_parcellation.gii'
        tex_fn = pyhrf.get_data_file_name(tex_fn)
        t,tgii = read_texture(tex_fn)

    def test_read_default_real_data_tiny(self):
        mesh_file = pyhrf.get_data_file_name('real_data_surf_tiny_mesh.gii')
        bold_file = pyhrf.get_data_file_name('real_data_surf_tiny_bold.gii')
        fn = 'real_data_surf_tiny_parcellation.gii'
        parcel_file = pyhrf.get_data_file_name(fn)

        cor, tri, mesh_gii = read_mesh(mesh_file)
        bold, bold_gii = read_texture(bold_file)
        parcellation, parcel_gii = read_texture(parcel_file)

        if 0:
            print 'cor:', cor.shape, cor.dtype
            print 'tri:', tri.shape, tri.dtype
            print 'bold:', bold.shape, bold.dtype
            print 'parcellation:', parcellation.shape, parcellation.dtype


    def test_load_fmri_surf_data(self):
        """ Test surfacic data loading
        """
        mesh_file = pyhrf.get_data_file_name('real_data_surf_tiny_mesh.gii')
        bold_file = pyhrf.get_data_file_name('real_data_surf_tiny_bold.gii')
        fn = 'real_data_surf_tiny_parcellation.gii'
        parcel_file = pyhrf.get_data_file_name(fn)

        # boldFn = pyhrf.get_data_file_name('localizer_surface_bold.tex')
        # roiMaskFn = pyhrf.get_data_file_name('roimask_gyrii.tex')
        # meshFn = pyhrf.get_data_file_name('right_hemisphere.mesh')
        #g, b, ss, m, h = load_fmri_surf_data([boldFn, boldFn],  meshFn,
        #                                     roiMaskFn)


        # graph, bold, session_scans, mask, edge lengthes
        #pyhrf.verbose.set_verbosity(3)
        g, b, ss, m, el = load_fmri_surf_data([bold_file, bold_file],
                                              mesh_file,
                                              parcel_file)
        assert len(g) == len(np.unique(m))

        if 0:
            first_parcel = g.keys()[0]
            print len(g), 'g[%d]:'%first_parcel, len(g[first_parcel])
            print 'edge lengthes of roi %d:' %first_parcel
            print el[first_parcel]
            print b[first_parcel].shape
            print ss[0][0],'-',ss[0][-1],',',ss[1][0],'-',ss[1][-1]
            print m.shape, _np.unique(m)


    def test_write_tex_gii_labels(self):
        labels = np.random.randint(0,2,10)
        # print 'labels:', labels.dtype
        # print labels
        tex_fn = op.join(self.tmp_dir, 'labels.gii')
        write_texture(labels, tex_fn)
        t,tgii = read_texture(tex_fn)
        assert t.dtype == labels.dtype
        assert (t == labels).all()
        # print 'labels loaded:', labels.dtype
        # print t

    def test_write_tex_gii_float(self):
        values = np.random.randn(10)
        # print 'values:', values.dtype
        # print values
        tex_fn = op.join(self.tmp_dir, 'float_values.gii')
        write_texture(values, tex_fn)
        t,tgii = read_texture(tex_fn)
        assert t.dtype == values.dtype
        assert np.allclose(t,values)
        # print 'loaded values:', t.dtype
        # print t


    def test_write_tex_gii_time_series(self):
        values = np.random.randn(120,10).astype(np.float32)
        # print 'values:', values.dtype
        # print values
        tex_fn = op.join(self.tmp_dir, 'time_series.gii')
        write_texture(values, tex_fn, intent='time series')
        t,tgii = read_texture(tex_fn)
        assert t.dtype == values.dtype
        assert np.allclose(t,values)
        # print 'loaded values:', t.dtype
        # print t


    def test_write_tex_gii_2D_float(self):
        values = np.random.randn(2,10).astype(np.float32)
        # print 'values:', values.dtype
        # print values
        tex_fn = op.join(self.tmp_dir, 'floats_2d.gii')
        write_texture(values, tex_fn)
        t,tgii = read_texture(tex_fn)
        assert t.dtype == values.dtype
        assert np.allclose(t,values)
        # print 'loaded values:', t.dtype
        # print t


class SPMIOTest(unittest.TestCase):

    def setUp(self):
        pass

    # def test_set_contrasts(self):

    #     spm_mat_fn = "/home/tom/Projects/PyHRF/ShippedData/SPM.mat"
    #     if not op.exists(spm_mat_fn):
    #         return

    #     try:
    #         from scipy.io.mio import loadmat
    #     except:
    #         from scipy.io.matlab import loadmat
    #     from pprint import pprint

    #     d = loadmat(spm_mat_fn)
    #     if 0:
    #         print 'd:'
    #         pprint(d)
    #         print ''

    #     spm = d['SPM']


    #     if isinstance(spm, np.ndarray):
    #         spm = spm[0]
    #     if isinstance(spm, np.ndarray):
    #         spm = spm[0]

    #     if isinstance(spm, np.void):
    #         if len(spm['xCon']) > 0:
    #             cons = spm['xCon'][0]
    #             print [ (c['name'], c['c'].squeeze(), c['STAT']) for c in cons ]
    #         else:
    #             print []
    #     elif isinstance(spm, np.ndarray):
    #         cons = spm.xCon[0]
    #         return [ (c.name, c.c.squeeze(), c.STAT) for c in cons ]
    #     else:
    #         raise Exception("Type of input (%s) is unsupported" \
    #                             %str(spm.__class__))




