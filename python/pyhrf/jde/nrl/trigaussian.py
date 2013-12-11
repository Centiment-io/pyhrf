

import os
from numpy import *
import numpy.matlib
from numpy.matlib import repmat
from scipy.integrate import trapz
import copy as copyModule

import pyhrf
from pyhrf import xmlio
from pyhrf.tools import resampleToGrid
from pyhrf.xmlio.xmlnumpy import NumpyXMLHandler
from pyhrf.ndarray import xndarray
from pyhrf.jde.intensivecalc import calcCorrEnergies, sampleSmmNrl
from pyhrf.jde.samplerbase import *
from pyhrf.jde.beta import *

from bigaussian import NRLSampler, BiGaussMixtureParamsSampler


class GGGNRLSampler(NRLSampler):

    ## parameters definitions and default values :
    # inherit parameters of parent class: 
    defaultParameters = copyModule.copy(NRLSampler.defaultParameters)
    # update them with specific parameters:
    defaultParameters.update( {
        NRLSampler.P_LABELS_COLORS : array([0.0,0.0,0.0], dtype=float),
        })
    
    ## other class attributes
    L_CI = 0
    L_CA = 1
    L_CD = 2
    CLASSES = array([L_CI, L_CA, L_CD], dtype=int)
    CLASS_NAMES = NRLSampler.CLASS_NAMES + ['deactiv']
    FALSE_POS = 3
    FALSE_NEG = 4

    def __init__(self, parameters=None, xmlHandler=NumpyXMLHandler(),
                 xmlLabel=None, xmlComment=None):
        NRLSampler.__init__(self, parameters, xmlHandler, xmlLabel, xmlComment)
        
    def sampleLabels(self, cond, variables): #varCI, varCA, meanCA):
        print 'GGGNRLSampler ... sampleLabels'
        sMixtP = variables[self.samplerEngine.I_MIXT_PARAM]
        varCI = sMixtP.currentValue[sMixtP.I_VAR_CI]
        varCA = sMixtP.currentValue[sMixtP.I_VAR_CA]
        meanCA = sMixtP.currentValue[sMixtP.I_MEAN_CA]
        meanCD = sMixtP.currentValue[sMixtP.I_MEAN_CD]
        varCD = sMixtP.currentValue[sMixtP.I_VAR_CD]

        #R_lambdaTildeI_A
        #R_lambdaTildeD_A = 1/R_lambdaTildeA_D
        #R_lambdaTildeD_I
        fracLambdaTildeI_A = self.calcFracLambdaTilde(cond, self.L_CI, self.L_CA,
                                                      variables)
        fracLambdaTildeD_A = self.calcFracLambdaTilde(cond, self.L_CD, self.L_CA,
                                                      variables)
        fracLambdaTildeA_D = 1/fracLambdaTildeD_A
        fracLambdaTildeI_D = self.calcFracLambdaTilde(cond, self.L_CI, self.L_CD,
                                                      variables)

        if self.beta[cond] > 0:
            if 1:
                dColI_A = 0 #self.labelsColors[self.L_CI]-self.labelsColors[self.L_CA]
                dColD_A = 0 #self.labelsColors[self.L_CD]-self.labelsColors[self.L_CA]
                dColA_D = 0 #-dColD_A
                dColI_D = 0 #self.labelsColors[self.L_CI]-self.labelsColors[self.L_CD]
                beta = self.beta[cond]
                #TODO : optimize : do it in one C function call !!
                calcCorrEnergies(cond, self.labels, self.corrEnergies,
                                 self.dataInput.neighboursIndexes,
                                 dColI_A, self.nbClasses, self.L_CI, self.L_CA)
                fracLambdaTildeI_A *= exp(beta*self.corrEnergies[cond,:])
                calcCorrEnergies(cond, self.labels, self.corrEnergies,
                                 self.dataInput.neighboursIndexes,
                                 dColD_A, self.nbClasses, self.L_CD, self.L_CA)
                fracLambdaTildeD_A *= exp(beta*self.corrEnergies[cond,:])

                calcCorrEnergies(cond, self.labels, self.corrEnergies,
                                 self.dataInput.neighboursIndexes,
                                 dColA_D, self.nbClasses, self.L_CA, self.L_CD)
                fracLambdaTildeA_D *= exp(beta*self.corrEnergies[cond,:])

                
                calcCorrEnergies(cond, self.labels, self.corrEnergies,
                                 self.dataInput.neighboursIndexes,
                                 dColI_D, self.nbClasses, self.L_CI, self.L_CD)
                fracLambdaTildeI_D *= exp(beta*self.corrEnergies[cond,:])

                #print 'self.corrEnergies :'
                #print self.corrEnergies
            else :
                for i in xrange(self.nbVox):
                    deltaE = self.calcDeltaEnergy(i, cond)
                    fracLambdaTilde[i] *= exp(-self.beta[cond]*deltaE)
        varLambdaApost_A = 1/(1 + fracLambdaTildeI_A + fracLambdaTildeD_A)
        varLambdaApost_D = 1/(1 + fracLambdaTildeI_D + fracLambdaTildeA_D)

        smpl = self.labelsSamples[cond,:]
        #print varLambdaApost_D
        ivD = (smpl<=varLambdaApost_D)
        self.labels[cond, ivD] = self.L_CD
        ivA = bitwise_and(smpl>varLambdaApost_D,
                          smpl<=varLambdaApost_A + varLambdaApost_D)
        self.labels[cond, ivA] = self.L_CA
        self.labels[cond, smpl > varLambdaApost_A + varLambdaApost_D] = self.L_CI


class TriGaussMixtureParamsSampler(BiGaussMixtureParamsSampler):

    I_MEAN_CD = 3
    I_VAR_CD = 4
    NB_PARAMS = 5
    PARAMS_NAMES = ['Mean_Activ', 'Var_Activ', 'Var_Inactiv',
                    'Mean_Deactiv', 'Var_Deactiv']

    P_MEAN_CD_PR_MEAN = 'meanCDPrMean'
    P_MEAN_CD_PR_VAR = 'meanCDPrVar'

    P_VAR_CD_PR_ALPHA = 'varCDPrAlpha'
    P_VAR_CD_PR_BETA = 'varCDPrBeta'

    defaultParameters = BiGaussMixtureParamsSampler.defaultParameters.copy()
    defaultParameters.update({
        P_MEAN_CD_PR_MEAN : -20.,
        P_MEAN_CD_PR_VAR : 10.0,
        #P_VAR_CD_PR_ALPHA : 2.5,
        #P_VAR_CD_PR_BETA : 1.5,
        P_VAR_CD_PR_ALPHA : 2.0001,
        P_VAR_CD_PR_BETA : 1.00001,
        })

    parametersToShow = BiGaussMixtureParamsSampler.parametersToShow + \
                      [P_MEAN_CD_PR_MEAN, P_MEAN_CD_PR_VAR, P_VAR_CD_PR_ALPHA,
                       P_VAR_CD_PR_BETA]
    
    L_CD = GGGNRLSampler.L_CD

    def __init__(self, parameters=None, xmlHandler=NumpyXMLHandler(),
                 xmlLabel=None, xmlComment=None):
        BiGaussMixtureParamsSampler.__init__(self, parameters, xmlHandler,
                                             xmlLabel, xmlComment)
        
        self.varCDPrAlpha = self.parameters[self.P_VAR_CD_PR_ALPHA] 
        self.varCDPrBeta = self.parameters[self.P_VAR_CD_PR_BETA]
        self.meanCDPrMean = self.parameters[self.P_MEAN_CD_PR_MEAN]
        self.meanCDPrVar = self.parameters[self.P_MEAN_CD_PR_VAR]

    def linkToData(self, dataInput):
        BiGaussMixtureParamsSampler.linkToData(self, dataInput)
        self.nrlCD = range(self.nbConditions)
        if self.dataInput.simulData is not None :
            mixtures = self.dataInput.simulData.nrls.getMixture()
            itemsCond = mixtures.items()
            meanCD = zeros(self.nbConditions, dtype=float)
            varCD = zeros(self.nbConditions, dtype=float)
            for cn,mixt in mixtures.iteritems(): 
                genDeactiv = mixt.generators['deactiv']
                indCond = self.dataInput.simulData.nrls.condIds[cn]
                meanCD[indCond] = genDeactiv.mean
                varCD[indCond] = genDeactiv.std**2
            self.trueValue[self.I_MEAN_CD] = meanCD
            self.trueValue[self.I_VAR_CD] = varCD            
        
        

    #TODO: generalize inside parent class
    def checkAndSetInitValue(self, variables):
        
        if self.currentValue is None:
            curValWasNone = True
        else:
            curValWasNone = False
        BiGaussMixtureParamsSampler.checkAndSetInitValue(self, variables)
        #TODO : retrieve simulated components ...

        if curValWasNone:
            if not self.useTrueValue:
                nc = self.nbConditions
                self.currentValue[self.I_MEAN_CD] = zeros(nc) -10.
                self.currentValue[self.I_VAR_CD] = zeros(nc) + 1.

    def getCurrentVars(self):
        return array([self.currentValue[self.I_VAR_CI],
                      self.currentValue[self.I_VAR_CA],
                      self.currentValue[self.I_VAR_CD]])
    
        
    
    def getCurrentMeans(self):
        return array([zeros(self.nbConditions),self.currentValue[self.I_MEAN_CA],
                      self.currentValue[self.I_MEAN_CD]])

    def computeWithJeffreyPriors(self, j, cardCDj):
        if pyhrf.verbose.verbosity >= 3:
            print 'cond %d - card CD = %d' %(j,cardCDj)
            print 'cond %d - cur mean CD = %f' %(j,self.currentValue[self.I_MEAN_CD,j])
            if cardCDj > 0:
                print 'cond %d - nrl CD: %f(v%f)[%f,%f]' %(j,self.nrlCD[j].mean(), 
                                                           self.nrlCD[j].var(),
                                                           self.nrlCD[j].min(), 
                                                           self.nrlCD[j].max())

        if cardCDj > 1:
            nrlC2Centered = self.nrlCD[j] - self.currentValue[self.I_MEAN_CD,j]
            nu2j = dot(nrlC2Centered, nrlC2Centered)
            varCDj = 1.0 / random.gamma(0.5 * (cardCDj + 1) - 1, 2. / nu2j)

            eta2j = mean(self.nrlCD[j])
            meanCDj = random.normal(eta2j, (varCDj / cardCDj)**0.5)

            if pyhrf.verbose.verbosity >= 3:
                print 'varCD ~ InvGamma(%f, nu2j/2=%f)' %(0.5*(cardCDj+1)-1, 
                                                          nu2j/2.)
                print ' -> mean =', (nu2j/2.)/(0.5*(cardCDj+1)-1)
        else :
            pyhrf.verbose(1,'Warning : cardCD <= 1!')
            varCDj = 1.0 / random.gamma(.5, 2.)
            if cardCDj == 0 :
                meanCDj = random.normal(5.0, varCDj**0.5)
            else:
                meanCDj = random.normal(self.nrlCD[j], varCDj**0.5)

        if pyhrf.verbose.verbosity >= 3:
            print 'Sampled components - cond', j
            print 'mean CD =', meanCDj, 'var CD =', varCDj

        return meanCDj, varCDj

    def sampleNextInternal(self, variables):
        #BiGaussMixtureParamsSampler.sampleNextInternal(self, variables)
        nrlsSmpl = variables[self.samplerEngine.I_NRLS]
        cardCD = nrlsSmpl.cardClass[self.L_CD,:]

        if self.hyperPriorFlag:
            for j in xrange(self.nbConditions):
                vICD = nrlsSmpl.voxIdx[nrlsSmpl.L_CD][j]
                self.nrlCD[j] = nrlsSmpl.currentValue[j, vICD]
    
                
                if cardCD[j] > 0:
                    etaj = mean(self.nrlCD[j])
                    nrlCDCentered = self.nrlCD[j] - etaj
                    nuj = .5 * dot(nrlCDCentered, nrlCDCentered)
                    #r = random.gamma(0.5*(cardCA[j]-1),2/nu1j)
                    varCDj = 1.0/random.gamma(0.5*cardCD[j] + self.varCDPrAlpha,
                                              1/(nuj + self.varCDPrBeta))
                    #meanCAj = random.normal(eta1j, (varCAj/cardCA[j])**0.5)
                else :
                    etaj = 0.0
                    varCDj = 1.0/random.gamma(self.varCDPrAlpha, 1/self.varCDPrBeta)
    
                invVarLikelihood = cardCD[j]/varCDj
                meanCDVarAPost = 1/(invVarLikelihood + 1/self.meanCDPrVar)
                rPrMV = self.meanCDPrMean/self.meanCDPrVar
                meanCDMeanAPost = meanCDVarAPost * (etaj*invVarLikelihood + rPrMV)
                meanCDj = random.normal(meanCDMeanAPost, meanCDVarAPost**0.5)
                
                self.currentValue[self.I_MEAN_CD, j] = meanCDj
                self.currentValue[self.I_VAR_CD, j] = varCDj

        else:
            nrlsSmpl = variables[self.samplerEngine.I_NRLS]
            
            #for j in xrange(self.nbConditions):

            for j in random.permutation(self.nbConditions):
                ca = nrlsSmpl.cardClass[self.L_CA,j]
                ci = nrlsSmpl.cardClass[self.L_CI,j]
                cd = nrlsSmpl.cardClass[self.L_CD,j]
                vICI = nrlsSmpl.voxIdx[nrlsSmpl.L_CI][j]
                vICA = nrlsSmpl.voxIdx[nrlsSmpl.L_CA][j]
                vICD = nrlsSmpl.voxIdx[nrlsSmpl.L_CD][j]
                self.nrlCI[j] = nrlsSmpl.currentValue[j, vICI]
                self.nrlCA[j] = nrlsSmpl.currentValue[j, vICA]
                self.nrlCD[j] = nrlsSmpl.currentValue[j, vICD]

                r = BiGaussMixtureParamsSampler.computeWithJeffreyPriors(self,j,
                                                                         ci,ca)
                varCIj, meanCAj, varCAj = r
                meanCD, varCD = self.computeWithJeffreyPriors(j,cd)
                
                
                self.currentValue[self.I_VAR_CI, j] = varCIj
                self.currentValue[self.I_MEAN_CA, j] = meanCAj #absolute(meanCAj)
                self.currentValue[self.I_VAR_CA, j] = varCAj
                self.currentValue[self.I_MEAN_CD,j] = meanCD
                self.currentValue[self.I_VAR_CD,j] = varCD

                pyhrf.verbose(4, 'meanCD,%d = %f' \
                                  %(j,self.currentValue[self.I_MEAN_CD,j]))
                
                pyhrf.verbose(4, 'varCD,%d = %f' \
                                  %(j,self.currentValue[self.I_VAR_CD,j]))

    def finalizeSampling(self):
        BiGaussMixtureParamsSampler.finalizeSampling(self)
        del self.nrlCD

    def getOutputs(self):
        outputs = GibbsSamplerVariable.getOutputs(self)
        mixtp = zeros((3, self.nbConditions, 2))
        mixtp[self.L_CA, :, 0] = self.finalValue[self.I_MEAN_CA,:]
        mixtp[self.L_CA, :, 1] = self.finalValue[self.I_VAR_CA,:]
        mixtp[self.L_CI, :, 0] = 0.
        mixtp[self.L_CI, :, 1] = self.finalValue[self.I_VAR_CI,:]
        mixtp[self.L_CD, :, 0] = self.finalValue[self.I_MEAN_CD,:]
        mixtp[self.L_CD, :, 1] = self.finalValue[self.I_VAR_CD,:]
        #for j in xrange(self.nbConditions):
        #    print 'condition', j
        #    print " var CI = ", self.finalValue[self.I_VAR_CI,j]
        #    print ' mean CA = %1.2e - var CA = %1.2e' %(self.finalValue[self.I_MEAN_CA,j], 
        #                                                self.finalValue[self.I_VAR_CA,j])
        #    print ' mean CD = %1.2e - var CD = %1.2e' %(self.finalValue[self.I_MEAN_CD,j], 
        #                                                self.finalValue[self.I_VAR_CD,j])
        an = ['class','condition','component']
        ad = {'class':['inactiv','activ','deactiv'],
              'condition':self.dataInput.cNames,
              'component':['mean','var']}
        outputs['pm_'+self.name] = xndarray(mixtp, axes_names=an, axes_domains=ad)

        return outputs

