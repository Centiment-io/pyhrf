# -*- coding: utf-8 -*-


from numpy import *
import numpy as np

from numpy.linalg import cholesky
from numpy.matlib import repmat

import pyhrf
import intensivecalc
from pyhrf import xmlio
from samplerbase import *
from numpy.matlib import *

class DriftSampler(xmlio.XmlInitable, GibbsSamplerVariable):
    """
    Gibbs sampler of the parameters modelling the low frequency drift in
    the fMRI time course, in the case of white noise.
    """

    def __init__(self, do_sampling=True, use_true_value=False,
                 val_ini=None):

        #TODO : comment
        xmlio.XmlInitable.__init__(self)

        an = ['order','voxel']
        GibbsSamplerVariable.__init__(self,'drift', valIni=val_ini,
                                      sampleFlag=do_sampling,
                                      useTrueValue=use_true_value,
                                      axes_names=an,
                                      value_label='PM LFD')

    def linkToData(self, dataInput):

        self.dataInput = dataInput
        self.nbSess = self.dataInput.nbSessions
        self.dimDrift = self.dataInput.colP
        self.nbVox = self.dataInput.nbVoxels
        self.P = self.dataInput.lfdMat[0] # 0 for 1st session

        if dataInput.simulData is not None and \
            isinstance(dataInput.simulData, BOLDModel):
            self.trueValue = dataInput.simulData.rdrift.lfd

    def checkAndSetInitValue(self, variables):
        smplVarDrift = variables[self.samplerEngine.I_ETA]
        smplVarDrift.checkAndSetInitValue(variables)
        varDrift = smplVarDrift.currentValue

        if self.useTrueValue :
            if self.trueValue is not None:
                self.currentValue = self.trueValue
            else:
                raise Exception('Needed a true value for drift init but '\
                                    'None defined')

        if 0 and self.currentValue is None :
            #if not self.sampleFlag and self.dataInput.simulData is None :
                #self.currentValue = self.dataInput.simulData.drift.lfd
                #pyhrf.verbose(6,'drift dimensions :' \
                              #+str(self.currentValue.shape))
                #pyhrf.verbose(6,'self.dimDrift :' \
                              #+str(self.dimDrift))
                #assert self.dimDrift == self.currentValue.shape[0]
            #else:
            self.currentValue = np.sqrt(varDrift) * \
                np.random.randn(self.dimDrift, self.nbVox)

        if self.currentValue is None:
            pyhrf.verbose(1,"Initialisation of Drift from the data")
            ptp = numpy.dot(self.P.transpose(),self.P)
            invptp = numpy.linalg.inv(ptp)
            invptppt = numpy.dot(invptp, self.P.transpose())
            self.currentValue = numpy.dot(invptppt,self.dataInput.varMBY)

        self.updateNorm()
        self.matPl = dot(self.P, self.currentValue)
        self.ones_Q_J = np.ones((self.dimDrift, self.nbVox))
        self.ones_Q   = np.ones((self.dimDrift))

    def updateNorm(self):
        self.norm = (self.currentValue * self.currentValue).sum()

        #if self.trueValue is not None:
            #print 'cur drift norm:', self.norm
            #print 'true drift norm:', (self.trueValue * self.trueValue).sum()

        #n2 = sum( diag( dot( self.currentValue.transpose(), self.currentValue ) ) )
        # if not np.allclose(self.norm,n2):
        #     print 'norm != n2'
        #     print self.norm
        #     print n2


    def sampleNextInternal(self, variables):
        reps = variables[self.samplerEngine.I_NOISE_VAR].currentValue
        snrls = variables[self.samplerEngine.I_NRLS]
        sHrf = variables[self.samplerEngine.I_HRF]
        eta =  variables[self.samplerEngine.I_ETA].currentValue

        for i in xrange(self.nbVox):
            # inv_sigma = np.eye(self.dimDrift) * (1/eta + 1/reps[i])
            # pty = np.dot(self.P.transpose(), snrls.varYtilde[:,i])
            # self.currentValue[:,i] = sampleDrift(inv_sigma, pty, self.dimDrift)

            v_lj = reps[i]*eta / (reps[i] + eta)
            #v_lj = ( 1/reps[i] + 1/eta )
            mu_lj = v_lj/reps[i] * np.dot(self.P.transpose(), snrls.varYtilde[:,i])
            #print 'ivox=%d, v_lj=%f, std_lj=%f mu_lj=' %(i,v_lj,v_lj**.5), mu_lj
            self.currentValue[:,i] = np.random.randn(self.dimDrift) * v_lj**.5 + mu_lj

        pyhrf.verbose(5, 'eta : %f' %eta)
        pyhrf.verbose(5, 'reps :' )
        pyhrf.verbose.printNdarray(5, reps)

        inv_vars_l = (1/reps + 1/eta) * self.ones_Q_J
        mu_l = 1/inv_vars_l * np.dot(self.P.transpose(), snrls.varYtilde)

        pyhrf.verbose(5, 'vars_l :')
        pyhrf.verbose.printNdarray(5, 1/inv_vars_l)

        pyhrf.verbose(5, 'mu_l :')
        pyhrf.verbose.printNdarray(5, mu_l)

        cur_val = np.random.normal(mu_l, 1/inv_vars_l)

        pyhrf.verbose(5, 'drift params :')
        pyhrf.verbose.printNdarray(5, self.currentValue)

        pyhrf.verbose(5, 'drift params (alt) :')
        pyhrf.verbose.printNdarray(5, cur_val)

        #assert np.allclose(cur_val, self.currentValue)

        self.updateNorm()
        self.matPl = dot(self.P, self.currentValue)

        # updating VarYTilde and VarYbar
        varXh = sHrf.varXh
        snrls.computeVarYTildeOpt(varXh)


    def getOutputs(self):
        outputs = GibbsSamplerVariable.getOutputs(self)
        drifts = np.dot(self.P, self.finalValue)
        an = ['time','voxel']
        ad = {'time' : arange(self.dataInput.ny)*self.dataInput.tr}
        outputs['drift_signal'] = xndarray(drifts, axes_names=an, axes_domains=ad,
                                         value_label='Delta BOLD')

        return outputs

class DriftSamplerWithRelVar(DriftSampler):
    """
    Gibbs sampler of the parameters modelling the low frequency drift in
    the fMRI time course, in the case of white noise.
    """

    def linkToData(self, dataInput):

        self.dataInput = dataInput
        self.nbSess = self.dataInput.nbSessions
        self.dimDrift = self.dataInput.colP
        self.nbVox = self.dataInput.nbVoxels
        self.P = self.dataInput.lfdMat[0] # 0 for 1st session

        if dataInput.simulData is not None and \
            isinstance(dataInput.simulData, BOLDModel):
            self.trueValue = dataInput.simulData.rdrift.lfd


    def checkAndSetInitValue(self, variables):
        smplVarDrift = variables[self.samplerEngine.I_ETA]
        smplVarDrift.checkAndSetInitValue(variables)
        varDrift = smplVarDrift.currentValue

        if self.useTrueValue :
            if self.trueValue is not None:
                self.currentValue = self.trueValue
            else:
                raise Exception('Needed a true value for drift init but '\
                                    'None defined')


        if 0 and self.currentValue is None :
            #if not self.sampleFlag and self.dataInput.simulData is None :
                #self.currentValue = self.dataInput.simulData.drift.lfd
                #pyhrf.verbose(6,'drift dimensions :' \
                              #+str(self.currentValue.shape))
                #pyhrf.verbose(6,'self.dimDrift :' \
                              #+str(self.dimDrift))
                #assert self.dimDrift == self.currentValue.shape[0]
            #else:
            self.currentValue = np.sqrt(varDrift) * \
                np.random.randn(self.dimDrift, self.nbVox)

        if self.currentValue is None:
            pyhrf.verbose(1,"Initialisation of Drift from the data")
            n = len(self.dataInput.varMBY)
            ptp = numpy.dot(self.P.transpose(),self.P)
            invptp = numpy.linalg.inv(ptp)
            invptppt = numpy.dot(invptp, self.P.transpose())
            self.currentValue = numpy.dot(invptppt,self.dataInput.varMBY)

        self.updateNorm()
        self.matPl = dot(self.P, self.currentValue)
        self.ones_Q_J = np.ones((self.dimDrift, self.nbVox))
        self.ones_Q   = np.ones((self.dimDrift))

    def updateNorm(self):
        self.norm = (self.currentValue * self.currentValue).sum()

        #if self.trueValue is not None:
            #print 'cur drift norm:', self.norm
            #print 'true drift norm:', (self.trueValue * self.trueValue).sum()

        #n2 = sum( diag( dot( self.currentValue.transpose(), self.currentValue ) ) )
        # if not np.allclose(self.norm,n2):
        #     print 'norm != n2'
        #     print self.norm
        #     print n2


    def sampleNextInternal(self, variables):

        #print 'Step 4 : Drift Sampling *****RelVar*****'

        reps = variables[self.samplerEngine.I_NOISE_VAR].currentValue
        snrls = variables[self.samplerEngine.I_NRLS]
        #print '         varYbar begin =',snrls.varYbar.sum()
        #print '         varYtilde begin =',snrls.varYtilde.sum()
        sHrf = variables[self.samplerEngine.I_HRF]
        eta =  variables[self.samplerEngine.I_ETA].currentValue
        w = variables[self.samplerEngine.I_W].currentValue

        for i in xrange(self.nbVox):
            # inv_sigma = np.eye(self.dimDrift) * (1/eta + 1/reps[i])
            # pty = np.dot(self.P.transpose(), snrls.varYtilde[:,i])
            # self.currentValue[:,i] = sampleDrift(inv_sigma, pty, self.dimDrift)

            v_lj = reps[i]*eta / (reps[i] + eta)
            #v_lj = ( 1/reps[i] + 1/eta )
            mu_lj = v_lj/reps[i] * np.dot(self.P.transpose(), snrls.varYtilde[:,i])
            #print 'ivox=%d, v_lj=%f, std_lj=%f mu_lj=' %(i,v_lj,v_lj**.5), mu_lj
            self.currentValue[:,i] = np.random.randn(self.dimDrift) * v_lj**.5 + mu_lj

        pyhrf.verbose(5, 'eta : %f' %eta)
        pyhrf.verbose(5, 'reps :' )
        pyhrf.verbose.printNdarray(5, reps)

        inv_vars_l = (1/reps + 1/eta) * self.ones_Q_J
        mu_l = 1/inv_vars_l * np.dot(self.P.transpose(), snrls.varYtilde)

        pyhrf.verbose(5, 'vars_l :')
        pyhrf.verbose.printNdarray(5, 1/inv_vars_l)

        pyhrf.verbose(5, 'mu_l :')
        pyhrf.verbose.printNdarray(5, mu_l)

        cur_val = np.random.normal(mu_l, 1/inv_vars_l)

        pyhrf.verbose(5, 'drift params :')
        pyhrf.verbose.printNdarray(5, self.currentValue)

        pyhrf.verbose(5, 'drift params (alt) :')
        pyhrf.verbose.printNdarray(5, cur_val)

        #assert np.allclose(cur_val, self.currentValue)

        self.updateNorm()
        self.matPl = dot(self.P, self.currentValue)

        # updating VarYTilde and VarYbar
        varXh = sHrf.varXh
        snrls.computeVarYTildeOptWithRelVar(varXh, w)
        #print '         varYbar end =',snrls.varYbar.sum()
        #print '         varYtilde end =',snrls.varYtilde.sum()


    def getOutputs(self):
        outputs = GibbsSamplerVariable.getOutputs(self)
        drifts = np.dot(self.P, self.finalValue)
        an = ['time','voxel']
        ad = {'time' : arange(self.dataInput.ny)*self.dataInput.tr}
        outputs['drift_signal'] = xndarray(drifts, axes_names=an, axes_domains=ad,
                                         value_label='Delta BOLD')

        return outputs
##################################################
#TODO : IMPORTANT : handle mutlisession inputs ! #
##################################################

# In case of multi-sessions

class Drift_MultiSess_Sampler(DriftSampler):

    def __init__(self, do_sampling=True, use_true_value=False,
                 val_ini=None):

        #TODO : comment
        xmlio.XmlInitable.__init__(self)

        an = ['session','order','voxel']
        GibbsSamplerVariable.__init__(self,'drift', valIni=val_ini,
                                      sampleFlag=do_sampling,
                                      useTrueValue=use_true_value,
                                      axes_names=an,
                                      value_label='PM LFD')

    def linkToData(self, dataInput):

        self.dataInput = dataInput
        self.ny = self.dataInput.ny
        self.dimDrift = self.dataInput.colP
        self.nbVox = self.dataInput.nbVoxels
        self.P = self.dataInput.lfdMat # : for all sessions
        self.nbSess = self.dataInput.nbSessions

        if dataInput.simulData is not None and \
           isinstance(dataInput.simulData[0], BOLDModel):
            self.trueValue = np.array([sd.rdrift.lfd for sd in dataInput.simulData])
        elif dataInput.simulData is not None and \
          isinstance(dataInput.simulData, list):
            self.trueValue = np.array([sd['drift_coeffs'] \
                                       for sd in dataInput.simulData])

    def checkAndSetInitValue(self, variables):
        smplVarDrift = variables[self.samplerEngine.I_ETA]
        smplVarDrift.checkAndSetInitValue(variables)
        varDrift = smplVarDrift.currentValue

        if self.useTrueValue :
            if self.trueValue is not None:
                self.currentValue = self.trueValue
            else:
                raise Exception('Needed a true value for drift init but '\
                                    'None defined')


        if self.currentValue is None :
            #if not self.sampleFlag and self.dataInput.simulData is None :
                #self.currentValue = self.dataInput.simulData.drift.lfd
                #pyhrf.verbose(6,'drift dimensions :' \
                              #+str(self.currentValue.shape))
                #pyhrf.verbose(6,'self.dimDrift :' \
                              #+str(self.dimDrift))
                #assert self.dimDrift == self.currentValue.shape[0]
            #else:
            #self.currentValue = np.sqrt(varDrift) * \
            #    np.random.randn(self.nbSess, self.dimDrift, self.nbVox)

            # Init as lsq fit:
            self.currentValue = np.zeros((self.nbSess, self.dimDrift, self.nbVox))
            for s in xrange(self.nbSess):
                self.currentValue[s,:,:] = np.dot(self.P[s].T, self.dataInput.varMBY[s])

        self.updateNorm()
        self.matPl = np.zeros((self.nbSess, self.ny, self.nbVox))
        for s in xrange(self.nbSess):
            self.matPl[s] = dot(self.P[s], self.currentValue[s])
        #self.ones_Q_J = np.ones((self.dimDrift, self.nbVox))
        self.ones_Q   = np.ones((self.dimDrift))

        #sHrf = variables[self.samplerEngine.I_HRF]
        #sHrf.checkAndSetInitValue(variables)
        #self.varXh = sHrf.varXh
        #nrlsmpl = variables[self.samplerEngine.I_NRLS_SESS]
        #nrlsmpl.checkAndSetInitValue(variables)
        #for s in xrange(self.nbSess):
            #nrlsmpl.computeVarYTildeSessionOpt(self.varXh[s], s)

    def updateNorm(self):
        #for s in xrange(self.nbSess):
            #norm = np.dot(self.currentValue[s].T, self.currentValue[s])

        self.norm = np.array([(self.currentValue[s] * self.currentValue[s]).sum() \
                              for s in xrange(self.nbSess)]).sum()


        #if self.trueValue is not None:
            #print 'cur drift norm:', self.norm
            #print 'true drift norm:', (self.trueValue * self.trueValue).sum()

    def sampleNextInternal(self, variables):
        eta =  variables[self.samplerEngine.I_ETA].currentValue

        for j in xrange(self.nbVox):
            for s in xrange(self.nbSess):
                reps = variables[self.samplerEngine.I_NOISE_VAR_SESS].currentValue[s,j]
                snrls = self.samplerEngine.getVariable('nrl_by_session')
                pyhrf.verbose(5, 'eta : %f' %eta)
                pyhrf.verbose(5, 'reps :' )
                pyhrf.verbose.printNdarray(5, reps)

                ##inv_vars_l = 1/eta * self.ones_Q + 1/reps * np.dot(self.P[s].transpose(), self.P[s])
                ##print 'PtP:', np.dot(self.P[s].transpose(), self.P[s])
                #inv_vars_l = (1./eta +1./reps)* self.ones_Q
                #mu_l = np.dot(1./inv_vars_l, np.dot(self.P[s].transpose(), snrls.varYtilde[s,:,j])) * 1./reps

                #pyhrf.verbose(5, 'vars_l_j_s :')
                #pyhrf.verbose.printNdarray(5, 1/inv_vars_l)
                #pyhrf.verbose(5, 'mu_l_j_s :')
                #pyhrf.verbose.printNdarray(5, mu_l)
                #print 'mu et invl:', mu_l, inv_vars_l
                #self.currentValue[s][:,j] = randn(self.dimDrift) * 1./inv_vars_l**.5 + mu_l
                ##self.currentValue[s][:,j] = np.random.multivariate_normal(mu_l, 1/inv_vars_l)
                #print j,s

                v_lj = reps*eta / (reps + eta)
                mu_lj = v_lj/reps * np.dot(self.P[s].transpose(),
                                           snrls.varYtilde[s,:,j])

                self.currentValue[s,:,j] = np.random.randn(self.dimDrift) * v_lj**.5 + mu_lj
                #print 'drifts coeffs:', self.currentValue[s][:,j]

        sHrf = variables[self.samplerEngine.I_HRF]
        self.varXh = sHrf.varXh
        nrlsmpl = variables[self.samplerEngine.I_NRLS_SESS]

        for s in xrange(self.nbSess):
            self.matPl[s] = dot(self.P[s], self.currentValue[s])
            nrlsmpl.computeVarYTildeSessionOpt(self.varXh[s], s)

        pyhrf.verbose(5, 'drift params :')
        pyhrf.verbose.printNdarray(5, self.currentValue)


    def sampleNextAlt(self, variables):
        self.updateNorm()


    #def checkAndSetInitValue(self, variables):
        #smplVarDrift = variables[self.samplerEngine.I_ETA]
        #smplVarDrift.checkAndSetInitValue(variables)
        #varDrift = smplVarDrift.currentValue

        #if self.useTrueValue :
            #if self.trueValue is not None:
                #self.currentValue = self.trueValue
            #else:
                #raise Exception('Needed a true value for drift init but '\
                                    #'None defined')


        #if self.currentValue is None :
            #if not self.sampleFlag and self.dataInput.simulData is None :
                #self.currentValue = self.dataInput.simulData.drift.lfd
                #pyhrf.verbose(6,'drift dimensions :' \
                              #+str(self.currentValue.shape))
                #pyhrf.verbose(6,'self.dimDrift :' \
                              #+str(self.dimDrift))
                #assert self.dimDrift == self.currentValue.shape[0]
            #else:
                #curV=[]
                #for s in xrange(self.nbSess):
                    #self.currentValue = np.sqrt(varDrift) * \
                            #np.random.randn(self.dimDrift, self.nbVox)
                    #curV.append(self.currentValue)
                #self.currentValue = np.array(curV)

        #self.updateNorm()
        #matPl=[]
        #for s in xrange(self.nbSess):
            #self.matPl = dot(self.P, self.currentValue)
            #matPl.append(self.matPl)
        #self.matPl = np.array(matPl)
        #self.ones_Q_J = np.ones((self.dimDrift, self.nbVox))
        #self.ones_Q   = np.ones((self.dimDrift))


    def compute_drift_signal(self, drift_coeffs=None):
        if drift_coeffs is None:
            if self.finalValue is not None:
                drift_coeffs = self.finalValue
            else:
                drift_coeffs = self.currentValue

        drifts = np.zeros((self.nbSess, self.ny, self.nbVox))
        for s in xrange(self.nbSess):
            drifts[s] = np.dot(self.P[s], drift_coeffs[s])

        return drifts

    def getOutputs(self):

        sn = self.dataInput.sNames
        outputs = GibbsSamplerVariable.getOutputs(self)
        drifts = self.compute_drift_signal()
        an = ['session', 'time','voxel']
        ad = {'time' : arange(self.ny)*self.dataInput.tr, 'session':sn}
        outputs['drift_signal'] = xndarray(drifts, axes_names=an, axes_domains=ad,
                                    value_label='Delta BOLD')

        return outputs

def sampleDrift( varInvSigma_drift, ptLambdaY, dim):

    mean_drift = np.linalg.solve(varInvSigma_drift, ptLambdaY )
    choleskyInvSigma_drift = cholesky(varInvSigma_drift).transpose()
    drift = np.linalg.solve(choleskyInvSigma_drift, random.randn(dim))
    drift += mean_drift
    return drift


class DriftARSampler(xmlio.XmlInitable, GibbsSamplerVariable):
    """
    Gibbs sampler of the parameters modelling the low frequency drift in the
    fMRI time course, in the case of AR noise
    """

    def __init__(self, do_sampling=True, use_true_value=False,
                 val_ini=None):

        #TODO : comment
        xmlio.XmlInitable.__init__(self)

        an = ['order','voxel']
        GibbsSamplerVariable.__init__(self,'drift', valIni=val_ini,
                                      sampleFlag=do_sampling,
                                      useTrueValue=use_true_value,
                                      axes_names=an,
                                      value_label='PM LFD')

#        self.functionBasis = self.parameters[self.P_FUNCTION_BASIS]
#        self.dimDrift = self.parameters[self.P_POLYORDER] +1

    def linkToData(self, dataInput):
        self.dataInput = dataInput
        self.nbConditions = self.dataInput.nbConditions
        self.nbVox = self.dataInput.nbVoxels
        self.ny = self.dataInput.ny
        self.nbColX = self.dataInput.nbColX
        self.dimDrift = self.dataInput.colP
        self.P = self.dataInput.lfdMat[0] #for 1st session
        self.varPtLambdaP =  zeros((self.dimDrift, self.dimDrift, self.nbVox),
                                      dtype=float)
        self.varPtLambdaYmP = zeros((self.dimDrift, self.nbVox), dtype=float)

    def updateNorm(self):
        self.norm = sum( diag( dot( self.currentValue.transpose(), self.currentValue ) ) )

    def updateVarYmDrift(self):
        self.matPl = dot(self.P, self.currentValue)
	#print matPl.shape, self.dataInput.varMBY.shape
        for v in range(self.nbVox):
            self.varMBYPl[:,v] = self.dataInput.varMBY[:,v] - self.matPl[:,v]

    def computeVarYTilde(self, varNrls, varXh):
        for v in xrange(self.nbVox):
            repNRLv = repmat(varNrls[:,v], self.ny, 1)
            avjXjh = repNRLv * varXh
            self.varYTilde[:,v] = self.varMBYPl[:,v] - avjXjh.sum(axis=1)

    def checkAndSetInitValue(self, variables):
        smplVarDrift = variables[self.samplerEngine.I_ETA]
        smplVarDrift.checkAndSetInitValue(variables)
        VarDrift = smplVarDrift.currentValue
	#print 'nbscans=', self.ny, 'nbvox=', self.nbVox
        if self.currentValue == None :
            if not self.sampleFlag and self.dataInput.simulData != None :
                self.currentValue = self.dataInput.simulData.drift.lfd
                pyhrf.verbose(6,'drift dimensions :' \
                              +str(self.currentValue.shape))
                pyhrf.verbose(6,'self.dimDrift :' \
                              +str(self.dimDrift))
                assert self.dimDrift == self.currentValue.shape[0]
            else:
                self.currentValue = sqrt(VarDrift)*random.randn( self.dimDrift, self.nbVox)

        self.updateNorm()
        self.varMBYPl = zeros((self.ny, self.nbVox), dtype=float)
#	invDelta = np.linalg.inv(self.dataInput.delta)
#	DetDelta = 1./np.linalg.det(invDelta)
#	print "Det Delta:", DetDelta
        self.updateVarYmDrift()

    def samplingWarmUp(self, variables):
        """
        #TODO : comment
        """
        ##print 'Drift warming up ...'
        # Precalculations and allocations :
        smplHRF = variables[self.samplerEngine.I_HRF]
        smplHRF.checkAndSetInitValue(variables)
        smplNRLs = variables[self.samplerEngine.I_NRLS]
        smplNRLs.checkAndSetInitValue(variables)
        self.varMBYPl = zeros((self.ny, self.nbVox), dtype=float)
        self.varYTilde = zeros((self.ny, self.nbVox), dtype=float)
        self.updateVarYmDrift()
        self.computeVarYTilde(smplNRLs.currentValue, smplHRF.varXh)

    def sampleNextAlt(self, variables):
        varXh = variables[self.samplerEngine.I_HRF].varXh
        varNRLs = variables[self.samplerEngine.I_NRLS].currentValue
        self.updateVarYmDrift()
        self.computeVarYTilde(varNRLs, varXh)

    def sampleNextInternal(self, variables):
        reps = variables[self.samplerEngine.I_NOISE_VAR].currentValue
        smplVarARp = variables[self.samplerEngine.I_NOISE_ARP]
        invAutoCorrNoise = smplVarARp.InvAutoCorrNoise
        varNrls = variables[self.samplerEngine.I_NRLS].currentValue
        smplVarh =  variables[self.samplerEngine.I_HRF]
        varXh = smplVarh.varXh
        eta =  variables[self.samplerEngine.I_ETA].currentValue
        invSigma= empty( ( self.dimDrift, self.dimDrift), dtype=float )
        datamPredict = empty(( self.ny), dtype=float)
        self.updateVarYmDrift()
        self.computeVarYTilde(varNrls, varXh)

        if 1:
            pyhrf.verbose(6, 'Computing PtDeltaP and PtDeltaY in C fashion')
            tSQSOptimIni = time.time()
#             print self.dataInput.varMBY.shape
#             print "dim VarXh", varXh.shape
#             print "dim VarNRLs", varNrls.shape
#             return
            intensivecalc.computePtLambdaARModel(self.P,
                                                 invAutoCorrNoise,
                                                 varNrls,
                                                 varXh,
                                                 self.dataInput.varMBY,
                                                 reps,
                                                 self.varPtLambdaP,
                                                 self.varPtLambdaYmP)
            pyhrf.verbose(6, 'Computing PtDeltaP and PtDeltaY in C fashion'+\
                          ' done in %1.3f sec' %(time.time()-tSQSOptimIni))
            for v in xrange(self.nbVox):
                invSigma =  eye(self.dimDrift,dtype=float)/eta + self.varPtLambdaP[:,:,v]
#                 pyhrf.verbose.printNdarray(6,  invSigma )
                self.currentValue[:,v] = sampleDrift( invSigma,
                                                      self.varPtLambdaYmP[:,v],
                                                      self.dimDrift )
            pyhrf.verbose(6, 'Sampling drift in C fashion'+\
                          ' done in %1.3f sec' %(time.time()-tSQSOptimIni))
        if 0:
            pyhrf.verbose(6, 'Computing PtDeltaP and PtDeltaY in Numpy fashion')
            tSQSOptimIni = time.time()
            for v in xrange(self.nbVox):
                projCovNoise= dot( self.P.transpose(), invAutoCorrNoise[:,:,v] )/reps[v]
    #            invSigma =  self.dataInput.varPtP/eta + dot( projCovNoise, self.P)
                invSigma =  dot( projCovNoise, self.P)
                assert numpy.allclose(invSigma, self.varPtLambdaP[:,:,v])
                invSigma += eye(self.dimDrift,dtype=float)/eta
#                 pyhrf.verbose.printNdarray(6,  invSigma )

#                self.updateDatamPredict(v, varNrls, varXh)
                repNRLv = repmat(varNrls[:,v], self.ny, 1)
                avjXjh = repNRLv * varXh
                datamPredict = self.dataInput.varMBY[:,v] - avjXjh.sum(axis=1)
                datamPredict = dot(projCovNoise, datamPredict)
                assert numpy.allclose(datamPredict, self.varPtLambdaYmP[:,v])
                self.currentValue[:,v] = sampleDrift(invSigma, datamPredict, self.dimDrift )
            pyhrf.verbose(6, 'Sampling drift in Numpy fashion'+\
                          ' done in %1.3f sec' %(time.time()-tSQSOptimIni))

        pyhrf.verbose(6, 'drift params :')
        pyhrf.verbose(6,
                      numpy.array2string(self.currentValue,precision=3))
        self.updateNorm()
        self.updateVarYmDrift()
        self.computeVarYTilde(varNrls, varXh)

    def initOutputs2(self, outputs, nbROI=-1):
        self.initOutputObservables(outputs, nbROI)
        nbd = self.dimDrift
        voxShape = self.dataInput.finalShape
        shape = (nbd,) + voxShape
        axes_names = ['LFDorder', 'axial', 'coronal', 'sagital']
        outputs['pmLFD'] = xndarray(zeros(shape,dtype=float),
                                  axes_names=axes_names,
                                  value_label="pm LFD")


    def fillOutputs2(self, outputs, iROI=-1):
        self.fillOutputObservables(outputs, iROI)
        d = outputs['pmLFD'].data
        vm = self.dataInput.voxelMapping
        m = vm.getNdArrayMask()
        d[:, m[0], m[1], m[2]] = self.mean
        dl[:,:,m[0], m[1], m[2]] = self.meanLabels.swapaxes(0,1)

    def finalizeSampling(self):
        # clean memory of temporary variables :
        del self.varPtLambdaP
        del self.varPtLambdaYmP
        del self.varMBYPl
        del self.varYTilde


class ETASampler(xmlio.XmlInitable, GibbsSamplerVariable):
    """
    Gibbs sampler of the variance of the Inverse Gamma prior used to
    regularise the estimation of the low frequency drift embedded
    in the fMRI time course
    """

    def __init__(self, do_sampling=True, use_true_value=False,
                 val_ini=np.array([1.0])):

        #TODO : comment
        xmlio.XmlInitable.__init__(self)

        GibbsSamplerVariable.__init__(self,'driftVar', valIni=val_ini,
                                      sampleFlag=do_sampling,
                                      useTrueValue=use_true_value)

    def linkToData(self, dataInput):
        self.dataInput = dataInput
        self.nbVox = self.dataInput.nbVoxels

        if dataInput.simulData is not None and \
                isinstance(dataInput.simulData, BOLDModel):
            self.trueValue = np.array([dataInput.simulData.rdrift.var])
        if dataInput.simulData is not None and \
            isinstance(dataInput.simulData, list): #multisession
            #self.trueValue = np.array([dataInput.simulData[0]['drift_var']])
            sd = dataInput.simulData
            # self.trueValue = np.array([np.array([ssd['drift_coeffs'] \
            #                                      for ssd in sd]).var()])

            # Better to recompute drift coeffs from drift signals
            # -> take into account amplitude factor
            P = self.getVariable('drift').P
            v = np.var([np.dot(P[s].T, sd[s]['drift']) for s in xrange(len(sd))])
            self.trueValue = np.array([v])

    def checkAndSetInitValue(self, variables):

        if self.useTrueValue:
            if self.trueValue is None:
                raise Exception('Needed a true value for %s init but '\
                                    'None defined' %self.name)
            else:
                self.currentValue = self.trueValue.astype(np.float64)



    def sampleNextInternal(self, variables):
        #TODO : comment
        smpldrift = variables[self.samplerEngine.I_DRIFT]
#        print 'shape dimDrift...', smpldrift.dimDrift
#        print 'norm Drift', smpldrift.norm
        #alpha = .5 * (smpldrift.dimDrift*self.nbVox+1) - 1
        alpha = .5 * (smpldrift.dimDrift*self.nbVox)
        beta = 2.0 / smpldrift.norm
        pyhrf.verbose(4, 'eta ~ Ga(%1.3f,%1.3f)'%(alpha,beta))
        self.currentValue[0] = 1.0/random.gamma(alpha,beta)

        #if 0:
            #beta = 1/beta
            #print 'true var drift :', self.trueValue
            #print 'm_theo=%f, v_theo=%f' %(beta/(alpha-1),
                                           #beta**2/((alpha-1)**2 * (alpha-2)))
            #samples = 1.0/random.gamma(alpha,1/beta,1000)
            #print 'm_empir=%f, v_empir=%f' %(samples.mean(), samples.var())




class ETASampler_MultiSess(ETASampler):


    def linkToData(self, dataInput):
        ETASampler.linkToData(self, dataInput)
        self.nbSessions = dataInput.nbSessions
        # self.dataInput = dataInput
        # self.nbVox = self.dataInput.nbVoxels

        # if dataInput.simulData is not None and \
        #         isinstance(dataInput.simulData[0], BOLDModel):
        #     self.trueValue = np.array([dataInput.simulData[0].rdrift.var])



    def sampleNextInternal(self, variables):

        smpldrift = variables[self.samplerEngine.I_DRIFT]
        alpha = .5 * (self.nbSessions*smpldrift.dimDrift*self.nbVox -1)
        beta_d = 0.5*smpldrift.norm
        pyhrf.verbose(4, 'eta ~ Ga(%1.3f,%1.3f)'%(alpha,beta_d))
        self.currentValue[0] = 1.0/random.gamma(alpha,1/beta_d)

        if pyhrf.verbose.verbosity > 3:
            print 'true var drift :', self.trueValue
            print 'm_theo=%f, v_theo=%f' %(beta_d/(alpha-1),
                                           beta_d**2/((alpha-1)**2 * (alpha-2)))
            samples = 1.0/random.gamma(alpha,1/beta_d,1000)
            print 'm_empir=%f, v_empir=%f' %(samples.mean(), samples.var())

